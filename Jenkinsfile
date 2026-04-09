
// user-service/Jenkinsfile — FIXED (stable + production-safe)

pipeline {
    agent any

    environment {
        SERVICE_NAME = 'user-service'
        IMAGE_NAME   = 'santonix/users'
        IMAGE_TAG    = "${BUILD_NUMBER}"
        DOCKER_CRED  = 'dockerhub'
        DOCKER_IMAGE = 'santonix/ci-python-docker:latest'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.BRANCH = env.BRANCH_NAME ?: sh(
                        script: 'git rev-parse --abbrev-ref HEAD',
                        returnStdout: true
                    ).trim()

                    env.SHORT_SHA = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()

                    env.AUTHOR = sh(
                        script: 'git log -1 --pretty=%an',
                        returnStdout: true
                    ).trim()

                    env.DOCKER_GID = sh(
                        script: "stat -c %g /var/run/docker.sock",
                        returnStdout: true
                    ).trim()

                    echo """
                    Branch:     ${env.BRANCH}
                    Commit:     ${env.SHORT_SHA}
                    Author:     ${env.AUTHOR}
                    Docker GID: ${env.DOCKER_GID}
                    """.stripIndent()
                }
            }
        }

        stage('Python CI (Containerized)') {
            steps {
                script {
                    def dockerArgs = "-v /var/run/docker.sock:/var/run/docker.sock --group-add ${env.DOCKER_GID}"

                    docker.image(env.DOCKER_IMAGE).inside(dockerArgs) {

                        dir('user-service') {

                            sh '''
                                echo "=== Install ==="
                                python -m venv venv
                                . venv/bin/activate
                                pip install -r requirements.txt --quiet

                                echo "=== Lint ==="
                                black app.py --line-length 88
                                flake8 app.py \
                                    --max-line-length=88 \
                                    --extend-ignore=E203,W503 \
                                    --statistics

                                echo "=== Unit Tests ==="
                                pytest tests/ \
                                    --ignore=tests/test_integration.py \
                                    -v \
                                    --junitxml=test-results.xml \
                                    --cov=app \
                                    --cov-report=xml:coverage.xml \
                                    --tb=short

                                echo "=== Security Scan ==="
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
                }
            }
            post {
                always {
                    junit allowEmptyResults: true,
                          testResults: 'user-service/test-results.xml'

                    archiveArtifacts(
                        artifacts: 'user-service/coverage.xml',
                        allowEmptyArchive: true
                    )

                    archiveArtifacts(
                        artifacts: 'user-service/*-report.json',
                        allowEmptyArchive: true
                    )
                }
            }
        }

        stage('Docker Build') {
            steps {
                dir('user-service') {
                    sh """
                        docker build \
                            --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                            --build-arg GIT_COMMIT=${env.SHORT_SHA} \
                            -t ${IMAGE_NAME}:${IMAGE_TAG} \
                            -t ${IMAGE_NAME}:latest \
                            .
                        echo "Built: ${IMAGE_NAME}:${IMAGE_TAG} ✓"
                    """
                }
            }
        }

        stage('Docker Push') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "${DOCKER_CRED}",
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
                        echo "Pushed ✓"
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
            echo "✅ ${SERVICE_NAME} #${BUILD_NUMBER} passed | ${env.BRANCH}"
        }
        failure {
            echo "❌ ${SERVICE_NAME} #${BUILD_NUMBER} failed | ${BUILD_URL}console"
        }
    }
}

