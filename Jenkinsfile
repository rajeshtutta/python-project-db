pipeline {
agent any

environment {
    DOCKERHUB_USER    = 'rajeshtutta123'
    TODO_REPO         = 'usermanagement'
    IMAGE_TAG         = "${env.BUILD_NUMBER}"

    TODO_IMAGE        = "${DOCKERHUB_USER}/${TODO_REPO}:${IMAGE_TAG}"
    TODO_LATEST       = "${DOCKERHUB_USER}/${TODO_REPO}:latest"

    GIT_REPO_URL      = 'https://github.com/rajeshtutta/python-project-db.git'
    GIT_BRANCH        = 'main'

    K8S_NAMESPACE     = 'rajesh'
    CAL_PORT          = '8087'
    SONARQUBE_ENV     = 'sq'
}

stages {

    stage('Checkout') {
        steps {
            echo "Cloning ${GIT_REPO_URL} @ ${GIT_BRANCH}"
            git branch: "${GIT_BRANCH}", url: "${GIT_REPO_URL}"
        }
    }

    stage('Install Dependencies') {
        steps {
            sh """
                python3 -m pip install --upgrade pip
                python3 -m pip install --user -r requirements.txt
            """
        }
    }

    stage('Test') {
        steps {
            sh """
               export ENV=test
               python3 -m pip install pytest pytest-cov
               python3 -m pytest --cov=app --cov-report=xml:coverage.xml test_app.py
            """
        }
    }

stage('SonarQube Analysis') {
    steps {
        withSonarQubeEnv('sq') {
            script {
                def scannerHome = tool 'sq'
                sh """
                ${scannerHome}/bin/sonar-scanner \
                -Dsonar.projectKey=3-tier-user-management-app \
                -Dsonar.sources=. \
                -Dsonar.test.inclusions=test_*.py \
                -Dsonar.exclusions=venv/**,__pycache__/**,.dockerignore \
                -Dsonar.python.coverage.reportPaths=coverage.xml
                """
            }
        }
    }
}

    stage('Quality Gate') {
        steps {
            timeout(time: 1, unit: 'MINUTES') {
                waitForQualityGate abortPipeline: true
            }
        }
    }

    stage('Build Artifact') {
        steps {
            sh """
            pip3 install build setuptools wheel twine
            python3 -m build
            """
        }
    }

    stage('Upload to Nexus') {
        steps {
            withCredentials([usernamePassword(credentialsId: 'nexus-cred', passwordVariable: 'passwd', usernameVariable: 'username')]) {
                sh """
                python3 -m twine upload --repository-url http://100.48.68.130:8081/repository/python/ \
                -u $username -p $passwd dist/*
                """
            }
        }
    }

    stage('Build Docker Images') {
        steps {
            sh """
                docker build --no-cache -t ${TODO_IMAGE} -t ${TODO_LATEST} -f Dockerfile .
                echo "Built ${TODO_IMAGE}"
            """
        }
    }
    stage('Run with Docker Compose') {
        steps {
            sh """
                echo "Stopping any existing containers..."
                docker-compose down || true
    
                echo "Starting application using docker-compose..."
                docker-compose up -d --build
    
                echo "Waiting for app to be healthy..."
                sleep 10
    
                docker ps
            """
        }
    }
    

    stage('Push to DockerHub') {
        steps {
            echo "Logging in to DockerHub as ${DOCKERHUB_USER}..."
            withCredentials([usernamePassword(
                credentialsId: 'dockerhub-cred',
                usernameVariable: 'DOCKER_USER',
                passwordVariable: 'DOCKER_PASS'
            )]) {
                sh """
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                    docker push ${TODO_IMAGE}
                    docker push ${TODO_LATEST}
                    docker logout
                """
            }
        }
    }

    stage('Install Helm') {
            steps {
                sh '''
                curl -LO https://get.helm.sh/helm-v3.14.0-linux-amd64.tar.gz
                tar -zxvf helm-v3.14.0-linux-amd64.tar.gz
                mv linux-amd64/helm ./helm
                chmod +x ./helm
                '''
            }
        }

        stage('Setup Kubeconfig') {
            steps {
                sh '''
                aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
                kubectl get nodes
                '''
            }
        }

        stage('Deploy Monitoring (Prometheus + Grafana)') {
            steps {
                sh '''
                ./helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
                ./helm repo update

                ./helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
                --namespace monitoring --create-namespace \
                --set grafana.service.type=LoadBalancer
                '''
            }
        }

        stage('Get Grafana Password') {
            steps {
                sh '''
                echo "Grafana Admin Password:"
                kubectl get secret monitoring-grafana \
                -n monitoring \
                -o jsonpath="{.data.admin-password}" | base64 --decode
                echo ""
                '''
            }
        }

    stage('Deploy to Kubernetes') {
    steps {
        sh """
            echo "Creating namespace if not exists..."
            kubectl create namespace ${K8S_NAMESPACE} || true

            echo "Preparing deployment file..."
            cp projectdeploy.yml /tmp/all-apps.yml

            echo "Updating image to ${TODO_IMAGE}..."
            sed -i "s|image:.*usermanagement.*|image: ${TODO_IMAGE}|g" /tmp/all-apps.yml

            echo "Deploying to Kubernetes..."
            kubectl apply -n ${K8S_NAMESPACE} -f /tmp/all-apps.yml

            echo "Restarting deployment..."
            kubectl rollout restart deployment myuserapp -n ${K8S_NAMESPACE}

            echo "Checking rollout status..."
            kubectl rollout status deployment/myuserapp -n ${K8S_NAMESPACE}

            echo "Deployment successful!"
        """
    }
}

        stage('Wait for LoadBalancer') {
            steps {
                sh '''
                echo "Waiting for LoadBalancer to be ready..."
                sleep 60
                '''
            }
        }

        stage('Get Application URL') {
            steps {
                script {
                    def url = sh(
                        script: '''
                        kubectl get svc python-svc \
                        -o jsonpath="{.status.loadBalancer.ingress[0].hostname}{.status.loadBalancer.ingress[0].ip}"
                        ''',
                        returnStdout: true
                    ).trim()

                    env.APP_URL = url
                    echo "Application URL: ${env.APP_URL}"
                }
            }
        }
    }

    post {

        success {
            emailext(
                subject: "SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
Build SUCCESS 🎉

Application URL:
http://${env.APP_URL}

Jenkins URL:
${env.BUILD_URL}
""",
                to: "${RECIPIENTS}"
            )
        }

        failure {
            emailext(
                subject: "FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
Build FAILED ❌

Check logs:
${env.BUILD_URL}
""",
                to: "${RECIPIENTS}"
            )
        }

        always {
            archiveArtifacts artifacts: 'zomato-build.zip', fingerprint: true
        }
    }
}
