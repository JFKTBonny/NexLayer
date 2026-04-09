// user-service/Jenkinsfile — Fixed version
pipeline {

    // Pre-compute docker GID before agent block
    // This runs on the Jenkins host node
    // before spinning up the container
    agent none

    environment {
        SERVICE_NAME = 'user-service'
        IMAGE_NAME   = 'santonix/users'
        IMAGE_TAG    = "${BUILD_NUMBER}"
        DOCKER_CRED  = 'dockerhub'
        SLACK        = '#team-alpha'
        TEAM         = 'Team Alpha'
    }

    stages {

        stage('Checkout') {
            // Run checkout on host agent first
            // to get GID and set up workspace
            agent { label 'linux' }
            steps {
                checkout scm
                script {
                    env.BRANCH    = sh(
                        script: 'git rev-parse --abbrev-ref HEAD',
                        returnStdout: true
                    ).trim()
                    env.SHORT_SHA = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.AUTHOR    = sh(
                        script: 'git log -1 --pretty=%an',
                        returnStdout: true
                    ).trim()

                    // Pre-compute docker socket GID on host
                    // stat -c '%g' uses single quotes inside sh()
                    // so Groovy does not interpolate %g
                    env.DOCKER_GID = sh(
                        script: "stat -c '%g' /var/run/docker.sock",
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

        stage('Build & Test') {
            agent {
                docker {
                    image 'santonix/ci-python-docker:latest'
                    // Use env.DOCKER_GID — already a number now
                    // No shell substitution needed inside docker args
                    args  """-v /var/run/docker.sock:/var/run/docker.sock
                             --group-add ${env.DOCKER_GID}"""
                }
            }
            stages {

                stage('Install') {
                    steps {
                        dir('user-service') {
                            sh '''
                                pip install --upgrade pip --quiet
                                pip install -r requirements.txt --quiet
                                echo "Install done ✓"
                            '''
                        }
                    }
                }

                stage('Lint') {
                    steps {
                        dir('user-service') {
                            sh '''
                                black app.py --line-length 88
                                flake8 app.py \
                                    --max-line-length=88 \
                                    --extend-ignore=E203,W503 \
                                    --statistics
                                echo "Lint passed ✓"
                            '''
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
                                    --tb=short
                            '''
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true,
                                  testResults: 'user-service/test-results.xml'
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
                            archiveArtifacts(
                                artifacts:        'user-service/*-report.json',
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
                    post {
                        failure {
                            sh "docker image prune -f || true"
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
        }
    }

    // ── Fix 2: IMAGE_NAME in post — use env safely ────
    post {
        always {
            script {
                // Guard against IMAGE_NAME not being set
                // when container itself failed to start
                def img = env.IMAGE_NAME
                def tag = env.IMAGE_TAG
                if (img && tag) {
                    sh "docker rmi ${img}:${tag} || true"
                } else {
                    echo "Image tag not set — skipping cleanup"
                }
            }
            cleanWs()
        }

        // ── Fix 3: Replace slackSend with mail ────────
        // Until Slack plugin is installed
        success {
            script {
                echo "✅ ${env.SERVICE_NAME} #${BUILD_NUMBER} passed"
                // Replace slackSend with mail temporarily
                mail(
                    to:      'devops@company.com',
                    subject: "✅ NexLayer ${env.SERVICE_NAME} #${BUILD_NUMBER} passed",
                    body:    """
                        Build passed.
                        Branch:  ${env.BRANCH ?: 'N/A'}
                        Commit:  ${env.SHORT_SHA ?: 'N/A'}
                        Author:  ${env.AUTHOR ?: 'N/A'}
                        Logs:    ${BUILD_URL}
                    """.stripIndent()
                )
            }
        }

        failure {
            script {
                echo "❌ ${env.SERVICE_NAME} #${BUILD_NUMBER} failed"
                mail(
                    to:      'devops@company.com',
                    subject: "❌ NexLayer ${env.SERVICE_NAME} #${BUILD_NUMBER} FAILED",
                    body:    """
                        Build failed.
                        Branch:  ${env.BRANCH ?: 'N/A'}
                        Commit:  ${env.SHORT_SHA ?: 'N/A'}
                        Author:  ${env.AUTHOR ?: 'N/A'}
                        Logs:    ${BUILD_URL}console
                    """.stripIndent()
                )
            }
        }
    }
}