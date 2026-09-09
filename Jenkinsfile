pipeline {
    agent any

    environment {
        REGISTRY = 'localhost:5000'
        IMAGE_NAME = 'voice-agent-backend'
        IMAGE_TAG = 'local'
        DEPLOYMENT_NAME = 'backend'
        CONTAINER_NAME = 'backend'
    }

    stages {
        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ."
            }
        }

        stage('Push to Registry') {
            steps {
                sh "docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh """
                    export KUBECONFIG=/var/jenkins_home/.kube/config
                    kubectl set image deployment/${DEPLOYMENT_NAME} ${CONTAINER_NAME}=${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                    kubectl rollout status deployment/${DEPLOYMENT_NAME}
                """
            }
        }
    }
}