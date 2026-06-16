pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t flask-todo:${BUILD_NUMBER} .'
            }
        }

        stage('Run Container') {
            steps {
                sh '''
                docker rm -f flask-test || true
                docker run -d -p 5000:5000 --name flask-test flask-todo:${BUILD_NUMBER}
                '''
            }
        }
    }
}

