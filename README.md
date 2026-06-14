# Flask Azure DevOps Project

## Overview

This project demonstrates an end-to-end cloud-native application deployment using Flask, Docker, Azure services, Infrastructure as Code, and CI/CD automation.

The application is a Todo web app with file upload and delete functionality. Files are stored in Azure Blob Storage and application data is stored in Azure SQL Database.

The goal of this project was to build a practical DevOps portfolio project covering deployment, cloud services, automation, and Infrastructure as Code.

---

## Features

* Create Todo items
* View Todo items
* Delete Todo items
* Upload files/images
* Delete uploaded files
* Azure SQL integration
* Azure Blob Storage integration
* Dockerized deployment
* Automated CI/CD deployment
* Infrastructure as Code using Bicep

---

## Architecture

```
Developer
    ↓
git push
    ↓
GitHub Actions
    ↓
Build Docker Image
    ↓
Push Docker Image to Docker Hub
    ↓
Azure App Service
    ↓
Docker Container (Flask App)
      ↙               ↘
Azure SQL         Azure Blob Storage
```

---

## Tech Stack

### Frontend

* HTML
* CSS
* Bootstrap

### Backend

* Flask
* SQLAlchemy
* PyODBC

### Containerization

* Docker
* Docker Hub

### Cloud Services

* Azure App Service
* Azure SQL Database
* Azure Blob Storage

### Infrastructure as Code

* Bicep

### CI/CD

* GitHub Actions

---

## Project Structure

```
flask-azure-devops-project/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── main.bicep
├── .github/
│   └── workflows/
│       └── deploy.yml
│
├── templates/
├── static/
├── README.md
```

---

## Docker Configuration

Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python","app.py"]
```

Build image:

```bash
docker build -t flask-todo-app .
```

Run locally:

```bash
docker run -d -p 5000:5000 flask-todo-app
```

---

## Azure Resources Created

Resources used:

* Resource Group
* App Service Plan (B1)
* Azure App Service (Linux)
* Azure SQL Server
* Azure SQL Database
* Storage Account
* Blob Container

Region:

East US

---

## Database Configuration

Database:

Azure SQL Database

Connection string stored in App Service environment variables:

```
DATABASE_URL
```

Application uses SQLAlchemy and PyODBC.

Example:

```python
connection_string=os.environ.get("DB_CONNECTION_STRING")
```

---

## Blob Storage Configuration

Container:

```
todo-images
```

Environment variable:

```
AZURE_STORAGE_CONNECTION_STRING
```

Blob functionality:

* Upload images/files
* Delete images/files

Example:

```python
connection_string=os.environ.get(
    "AZURE_STORAGE_CONNECTION_STRING"
)
```

---

## Infrastructure as Code

Infrastructure was deployed using Bicep.

Provisioned resources:

* App Service Plan
* Web App
* SQL Server
* SQL Database
* Storage Account
* Blob Container

Deployment command:

```bash
az deployment group create \
--resource-group <RESOURCE_GROUP_NAME> \
--template-file main.bicep
```

---

## CI/CD Pipeline

GitHub Actions pipeline automatically:

1. Triggers on push to main branch
2. Builds Docker image
3. Pushes image to Docker Hub
4. Deploys latest image to Azure App Service

Workflow:

```
Code Change
    ↓
git push
    ↓
GitHub Actions
    ↓
Docker Build
    ↓
Docker Hub
    ↓
Azure App Service Deployment
```

GitHub Secrets used:

* DOCKER_USERNAME
* DOCKER_PASSWORD
* AZURE_WEBAPP_PUBLISH_PROFILE

---

## Challenges and Troubleshooting

Issues encountered:

* Docker Desktop startup issues
* Virtualization setup issues
* Docker push authorization issues
* SQLAlchemy connection errors
* Azure App Service deployment issues
* Publish profile validation issues
* Blob access configuration issues

Resolution involved:

* Environment variable configuration
* Docker image tagging corrections
* Azure deployment troubleshooting
* GitHub Actions debugging

---

## Future Improvements

* Kubernetes deployment
* Terraform implementation
* Azure Key Vault integration
* Application Insights monitoring
* Health endpoint
* VNet and Private Endpoint implementation
* Managed Identity authentication

---

## Learning Outcomes

This project helped strengthen understanding of:

* Docker containerization
* Azure cloud services
* Infrastructure as Code
* CI/CD pipelines
* Cloud databases
* Blob storage
* Automated deployment workflows
* Troubleshooting production deployments
