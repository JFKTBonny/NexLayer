// nexlayer-users/Jenkinsfile — with full user/permission checks
pipeline {
    agent {
        docker {
            image 'santonix/ci-python-docker:latest'
            args  '''-v /var/run/docker.sock:/var/run/docker.sock
                     --group-add $(stat -c '%g' /var/run/docker.sock)'''
        }
    }

    environment {
        SERVICE_NAME = 'user-service'
        IMAGE_NAME   = 'santonix/users'
        IMAGE_TAG    = "${BUILD_NUMBER}"
    }

    stages {

        stage('Environment Check') {
            steps {
                sh '''
                    echo "=== User Context ==="
                    echo "Whoami:  $(whoami)"
                    echo "UID:     $(id -u)"
                    echo "GID:     $(id -g)"
                    echo "Groups:  $(id -Gn)"

                    echo ""
                    echo "=== Docker Socket ==="
                    ls -la /var/run/docker.sock
                    stat -c "Socket GID: %g" /var/run/docker.sock

                    echo ""
                    echo "=== Docker Access Test ==="
                    docker version --format "Docker CLI: {{.Client.Version}}"
                    docker info --format "Server: {{.ServerVersion}}"

                    echo ""
                    echo "=== Python Tools ==="
                    python --version
                    pip --version
                    pytest --version
                    flake8 --version
                '''
            }
        }

        stage('Install App Dependencies') {
            steps {
                dir('user-service') {
                    sh 'pip install -r requirements.txt --quiet'
                }
            }
        }

        stage('Lint') {
            steps {
                dir('user-service') {
                    sh '''
                        flake8 app.py \
                            --max-line-length=120 \
                            --statistics \
                            --count
                    '''
                }
            }
            post {
                failure {
                    echo "❌ Lint failed"
                }
            }
        }

        stage('Unit Tests') {
            steps {
                dir('user-service') {
                    sh '''
                        pytest tests/ \
                            --ignore=tests/test_integration.py \
                            -v \
                            --junitxml=test-results.xml \
                            --cov=app \
                            --cov-report=xml:coverage.xml \
                            --cov-fail-under=70 \
                            --tb=short
                    '''
                }
            }
            post {
                always {
                    junit allowEmptyResults: true,
                          testResults: 'user-service/test-results.xml'
                    archiveArtifacts artifacts: 'user-service/coverage.xml',
                                     allowEmptyArchive: true
                }
            }
        }

        stage('Security Scan') {
            steps {
                dir('user-service') {
                    sh '''
                        bandit -r app.py \
                            -f json \
                            -o bandit-report.json \
                            --severity-level medium || true

                        safety check \
                            -r requirements.txt \
                            --json \
                            -o safety-report.json || true
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'user-service/*-report.json',
                                     allowEmptyArchive: true
                }
            }
        }

        stage('Docker Build') {
            steps {
                script {
                    // Verify docker access before attempting build
                    def dockerCheck = sh(
                        script: 'docker info > /dev/null 2>&1 && echo "OK" || echo "FAIL"',
                        returnStdout: true
                    ).trim()

                    if (dockerCheck == 'FAIL') {
                        error("Docker daemon not accessible — check socket mount and group permissions")
                    }
                }
                dir('user-service') {
                    sh """
                        docker build \
                            --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                            -t ${IMAGE_NAME}:${IMAGE_TAG} \
                            -t ${IMAGE_NAME}:latest \
                            .

                        echo "Image size: \$(docker image inspect ${IMAGE_NAME}:${IMAGE_TAG} \
                            --format='{{.Size}}' | numfmt --to=iec)"
                    """
                }
            }
            post {
                success {
                    echo "✅ Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
                }
                failure {
                    sh 'docker image prune -f || true'
                    echo "❌ Docker build failed"
                }
            }
        }

        stage('Docker Push') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo ${DOCKER_PASS} | docker login \
                            -u ${DOCKER_USER} \
                            --password-stdin

                        docker push ${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${IMAGE_NAME}:latest

                        docker logout
                        echo "✅ Pushed ${IMAGE_NAME}:${IMAGE_TAG}"
                    """
                }
            }
        }
    }

    post {
        always {
            sh "docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true"
            cleanWs()
        }
        success {
            slackSend channel: '#nexlayer-builds',
                color: 'good',
                message: "✅ *user-service* #${BUILD_NUMBER} passed"
        }
        failure {
            slackSend channel: '#nexlayer-alerts',
                color: 'danger',
                message: "❌ *user-service* #${BUILD_NUMBER} failed | ${BUILD_URL}console"
        }
    }
}