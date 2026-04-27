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

    stage('Deploy to Kubernetes') {
        steps {
            sh """
                kubectl apply -f namespace.yml

                cp projectdeploy.yml /tmp/all-apps.yml

                sed -i 's|rajesh/usermanagement:v1|${TODO_IMAGE}|g' /tmp/all-apps.yml

                kubectl apply -f /tmp/all-apps.yml
                kubectl rollout restart deployment myuserapp -n ${K8S_NAMESPACE}
                kubectl rollout status deployment/myuserapp -n ${K8S_NAMESPACE}
            """
        }
    }

    // ================= NEW STAGES =================

stage('Install Prometheus') {
    steps {
        sh """
        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
        helm repo update

        helm upgrade --install prometheus prometheus-community/prometheus \
          -n monitoring --create-namespace \
          --set alertmanager.enabled=false \
          --set server.persistentVolume.enabled=false \
          --set server.service.type=LoadBalancer
        """
    }
}

stage('Install Grafana') {
    steps {
        sh """
        helm repo add grafana https://grafana.github.io/helm-charts || true
        helm repo update

        helm upgrade --install grafana grafana/grafana \
          -n monitoring \
          --set persistence.enabled=false \
          --set service.type=LoadBalancer
        """
    }
}

stage('Get Monitoring URLs') {
    steps {
        sh """
        echo "Waiting for LoadBalancer External IPs..."
        sleep 30

        echo "Prometheus Service:"
        kubectl get svc prometheus-server -n monitoring

        echo "Grafana Service:"
        kubectl get svc grafana -n monitoring
        """
    }
}

stage('Get Grafana Password') {
    steps {
        sh """
        echo "Grafana Admin Password:"
        kubectl get secret grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 --decode
        echo ""
        """
    }
}
