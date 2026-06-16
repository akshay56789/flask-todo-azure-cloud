pipeline {
    agent any

    stages {

        stage('Environment') {
            steps {
                sh 'whoami'
                sh 'hostname'
                sh 'java -version'
                sh 'git --version'
            }
        }
    }
}
