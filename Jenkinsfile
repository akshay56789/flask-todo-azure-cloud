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
                docker run -d --name flask-test-${BUILD_NUMBER} \
                flask-todo:${BUILD_NUMBER}
                '''
            }
        }
    }
}

