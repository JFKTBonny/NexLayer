
// nexlayer-users/Jenkinsfile — FIXED & CONSISTENT

pipeline {
    agent any

    environment {
        SERVICE_NAME = 'user-service'
        IMAGE_NAME   = 'santonix/users'
        IMAGE_TAG    = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.DOCKER_GID = sh(
                        script: "stat -c %g /var/run/docker.sock",
                        returnStdout: true
                    ).trim()

                    env.BRANCH = sh(
                        script: 'git rev-parse --abbrev-ref HEAD',
                        returnStdout: true
                    ).trim()

                    env.SHORT_SHA = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                }
            }
        }

        stage('CI Pipeline') {
            steps {
                script {

                    def dockerArgs = "--group-add ${env.DOCKER_GID} -v /var/run/docker.sock:/var/run/docker.sock"

                    docker.image('santonix/ci-python-docker:latest').inside(dockerArgs) {

                        sh '''
                            echo "=== User Context ==="
                            whoami
                            id

                            echo ""
                            echo "=== Docker Access ==="
                            docker version
                            docker info

                            echo ""
                            echo "=== Install Dependencies ==="
                            cd user-service
                            pip install -r requirements.txt --quiet

                            echo ""
                            echo "=== Lint ==="
                            flake8 app.py \
                                --max-line-length=120 \
                                --statistics \
                                --count

                            echo ""
                            echo "=== Unit Tests ==="
                            pytest tests/ \
                                --ignore=tests/test_integration.py \
                                -v \
                                --junitxml=test-results.xml \
                                --cov=app \
                                --cov-report=xml:coverage.xml \
                                --cov-fail-under=70 \
                                --tb=short

                            echo ""
                            echo "=== Security Scan ==="
                            bandit -r app.py \
                                -f json \
                                -o bandit-report.json \
                                --severity-level medium || true

                            safety check \
                                -r requirements.txt \
                                --json \
                                -o safety-report.json || true

                            echo ""
                            echo "=== Docker Build ==="
                            docker build \
                                --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                                -t ${IMAGE_NAME}:${IMAGE_TAG} \
                                -t ${IMAGE_NAME}:latest \
                                .

                            echo "Image size:"
                            docker image inspect ${IMAGE_NAME}:${IMAGE_TAG} \
                                --format='{{.Size}}'
                        '''
                    }
                }
            }
            post {
                always {
                    junit allowEmptyResults: true,
                          testResults: 'user-service/test-results.xml'

                    archiveArtifacts artifacts: 'user-service/coverage.xml',
                                     allowEmptyArchive: true

                    archiveArtifacts artifacts: 'user-service/*-report.json',
                                     allowEmptyArchive: true
                }
                success {
                    echo "✅ CI pipeline completed"
                }
                failure {
                    echo "❌ CI pipeline failed"
                }
            }
        }

        stage('Docker Push') {
            when { branch 'main' }
            steps {
                script {
                    def dockerArgs = "--group-add ${env.DOCKER_GID} -v /var/run/docker.sock:/var/run/docker.sock"

                    docker.image('santonix/ci-python-docker:latest').inside(dockerArgs) {

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
        }
    }

    post {
        always {
            script {
                def dockerGid = sh(
                    script: "stat -c %g /var/run/docker.sock",
                    returnStdout: true
                ).trim()

                docker.image('santonix/ci-python-docker:latest').inside(
                    "--group-add ${dockerGid} -v /var/run/docker.sock:/var/run/docker.sock"
                ) {
                    sh "docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true"
                }
            }
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

