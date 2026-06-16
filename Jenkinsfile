pipeline {
    agent any

    stages {
        stage('Docker Version') {
            steps {
                sh 'docker --version'
            }
        }

        stage('Docker PS') {
            steps {
                sh 'docker ps'
            }
        }
    }
}
}
