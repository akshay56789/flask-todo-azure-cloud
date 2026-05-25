from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import urllib.parse
from werkzeug.utils import secure_filename
import uuid
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Robust database URL parser to handle SQLite, PostgreSQL, and Azure SQL (both ADO.NET and standard SQLAlchemy URLs)
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # If the user pasted a raw Azure ADO.NET or ODBC connection string (starts with Server=tcp: or contains Driver=)
    if "Server=tcp:" in database_url or "server=tcp:" in database_url or "Driver=" in database_url or "DRIVER=" in database_url:
        # If Driver is not specified in the raw connection string, append ODBC Driver 18 (default on Azure)
        if "Driver=" not in database_url and "DRIVER=" not in database_url:
            if not database_url.endswith(';'):
                database_url += ';'
            database_url += "Driver={ODBC Driver 18 for SQL Server};"
        
        # Clean boolean properties for ODBC (ODBC Driver 18 strictness requires yes/no instead of True/False)
        import re
        database_url = re.sub(r'(?i)encrypt=true', 'Encrypt=yes', database_url)
        database_url = re.sub(r'(?i)encrypt=false', 'Encrypt=no', database_url)
        database_url = re.sub(r'(?i)trustservercertificate=true', 'TrustServerCertificate=yes', database_url)
        database_url = re.sub(r'(?i)trustservercertificate=false', 'TrustServerCertificate=no', database_url)

        # URL-encode the raw connection string and format it for SQLAlchemy using pyodbc
        params = urllib.parse.quote_plus(database_url)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"
    else:
        # It's a standard SQLAlchemy connection string (e.g. mssql+pyodbc://..., postgresql://...)
        # Note: If your password contains special characters like @, :, or /, they must be URL-encoded.
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback to local SQLite for development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    complete = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(500), nullable=True)
    image_blob_name = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f'<Todo {self.id}>'

# Azure Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
AZURE_STORAGE_CONTAINER = os.environ.get('AZURE_STORAGE_CONTAINER', 'todo-images')

azure_blob_service_client = None
azure_container_client = None

if AZURE_STORAGE_CONNECTION_STRING:
    try:
        azure_blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        azure_container_client = azure_blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)
        # Create container if it doesn't exist and set public access to 'blob'
        if not azure_container_client.exists():
            azure_container_client.create_container(public_access='blob')
        print(" * SUCCESS: Azure Blob Storage client initialized successfully!", flush=True)
    except Exception as e:
        print(f" * WARNING: Failed to initialize Azure Blob Storage client: {e}. Falling back to Local Storage.", flush=True)
        azure_blob_service_client = None
        azure_container_client = None

# Local Fallback Uploads Directory Setup
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create database tables if they don't exist
with app.app_context():
    db.create_all()
    
    # Auto-migration: check if columns exist and add them if they don't.
    dialect = app.config['SQLALCHEMY_DATABASE_URI'].split('://')[0]
    try:
        from sqlalchemy import text
        try:
            db.session.execute(text("ALTER TABLE todo ADD COLUMN image_url VARCHAR(500)"))
            db.session.commit()
            print(" * MIGRATION: Added image_url column successfully.", flush=True)
        except Exception:
            db.session.rollback()
        
        try:
            db.session.execute(text("ALTER TABLE todo ADD COLUMN image_blob_name VARCHAR(500)"))
            db.session.commit()
            print(" * MIGRATION: Added image_blob_name column successfully.", flush=True)
        except Exception:
            db.session.rollback()
            
    except Exception as migration_error:
        print(f" * WARNING: Auto-migration encountered an error: {migration_error}", flush=True)

    print(f" * SUCCESS: Database connection established using dialect: '{dialect}'", flush=True)
    print(" * SUCCESS: Database tables verified/created successfully!", flush=True)

@app.route('/db-test')
def db_test():
    try:
        from sqlalchemy import text
        # Perform a fast and simple database test query
        db.session.execute(text("SELECT 1"))
        
        dialect = app.config['SQLALCHEMY_DATABASE_URI'].split('://')[0]
        return {
            "status": "success",
            "message": "Database connection is healthy!",
            "database_dialect": dialect,
            "using_azure_sql": "mssql" in dialect
        }, 200
    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to connect to the database.",
            "error_details": str(e)
        }, 500

@app.route('/')
def index():
    todo_list = Todo.query.all()
    azure_active = (azure_container_client is not None)
    return render_template('index.html', todo_list=todo_list, azure_active=azure_active)

@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title')
    image_file = request.files.get('image')
    
    image_url = None
    image_blob_name = None
    
    if image_file and image_file.filename != '':
        # Generate a unique, secure filename
        original_filename = secure_filename(image_file.filename)
        ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        if azure_container_client:
            try:
                # Upload to Azure Blob Storage
                blob_client = azure_container_client.get_blob_client(unique_filename)
                # Upload the stream directly
                blob_client.upload_blob(image_file.stream, content_type=image_file.content_type)
                image_url = blob_client.url
                image_blob_name = unique_filename
                print(f" * UPLOAD: Uploaded file {unique_filename} to Azure Blob Storage.", flush=True)
            except Exception as upload_error:
                print(f" * ERROR: Failed to upload file to Azure: {upload_error}", flush=True)
        
        # Local Fallback if Azure is inactive OR if Azure upload failed
        if not image_url:
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                # Seek stream to start in case it was partially read during the failed Azure upload attempt
                image_file.stream.seek(0)
                image_file.save(file_path)
                image_url = url_for('static', filename=f'uploads/{unique_filename}')
                image_blob_name = unique_filename
                print(f" * UPLOAD: Saved file {unique_filename} locally (Local Fallback).", flush=True)
            except Exception as local_error:
                print(f" * ERROR: Failed to save file locally: {local_error}", flush=True)
                
    if title:
        new_todo = Todo(
            title=title, 
            complete=False, 
            image_url=image_url, 
            image_blob_name=image_blob_name
        )
        db.session.add(new_todo)
        db.session.commit()
        
    return redirect(url_for('index'))

@app.route('/update/<int:todo_id>')
def update(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.complete = not todo.complete
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>')
def delete(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    
    # Clean up associated image
    if todo.image_blob_name:
        is_local = todo.image_url and 'static/uploads' in todo.image_url
        
        if not is_local and azure_container_client:
            try:
                blob_client = azure_container_client.get_blob_client(todo.image_blob_name)
                blob_client.delete_blob()
                print(f" * DELETE: Deleted blob {todo.image_blob_name} from Azure Blob Storage.", flush=True)
            except Exception as delete_error:
                print(f" * ERROR: Failed to delete blob from Azure: {delete_error}", flush=True)
        else:
            # Delete local file
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], todo.image_blob_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f" * DELETE: Deleted local file {todo.image_blob_name}.", flush=True)
            except Exception as local_delete_error:
                print(f" * ERROR: Failed to delete local file: {local_delete_error}", flush=True)
                
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete-image/<int:todo_id>')
def delete_image(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    
    if todo.image_blob_name:
        is_local = todo.image_url and 'static/uploads' in todo.image_url
        
        if not is_local and azure_container_client:
            try:
                blob_client = azure_container_client.get_blob_client(todo.image_blob_name)
                blob_client.delete_blob()
                print(f" * DELETE-IMAGE: Deleted blob {todo.image_blob_name} from Azure Blob Storage.", flush=True)
            except Exception as delete_error:
                print(f" * ERROR: Failed to delete blob from Azure: {delete_error}", flush=True)
        else:
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], todo.image_blob_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f" * DELETE-IMAGE: Deleted local file {todo.image_blob_name}.", flush=True)
            except Exception as local_delete_error:
                print(f" * ERROR: Failed to delete local file: {local_delete_error}", flush=True)
                
        todo.image_url = None
        todo.image_blob_name = None
        db.session.commit()
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)
