// user-service/Jenkinsfile
pipeline {
    agent any

    environment {
        SERVICE_NAME = 'user-service'
        IMAGE_NAME   = 'santonix/users'
        IMAGE_TAG    = "${BUILD_NUMBER}"
        DOCKER_CRED  = 'dockerhub'
        // Use workspace-local virtualenv — no permission issues
        VENV_DIR     = "${WORKSPACE}/venv"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.BRANCH = sh(
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

                    // Get docker GID safely
                    def socketExists = sh(
                        script: 'test -S /var/run/docker.sock && echo yes || echo no',
                        returnStdout: true
                    ).trim()

                    env.DOCKER_GID = socketExists == 'yes'
                        ? sh(script: "stat -c '%g' /var/run/docker.sock", returnStdout: true).trim()
                        : '0'

                    echo """
                        Branch:     ${env.BRANCH}
                        Commit:     ${env.SHORT_SHA}
                        Author:     ${env.AUTHOR}
                        Docker GID: ${env.DOCKER_GID}
                        Venv:       ${env.VENV_DIR}
                    """.stripIndent()
                }
            }
        }

        // ── Install directly on Jenkins node ─────────────
        // No Docker container — no permission issues
        // Uses a virtualenv in the workspace (always writable)
        stage('Install') {
            steps {
                dir('user-service') {
                    sh """
                        echo "=== Creating virtualenv in workspace ==="
                        python3 -m venv ${VENV_DIR}

                        echo "=== Activating and installing ==="
                        . ${VENV_DIR}/bin/activate

                        pip install --upgrade pip --quiet
                        pip install -r requirements.txt --quiet
                        pip install \
                            black==24.3.0 \
                            flake8==7.0.0 \
                            bandit \
                            safety \
                            pytest \
                            pytest-flask \
                            pytest-cov \
                            --quiet

                        echo "=== Installed tools ==="
                        python --version
                        pip --version
                        pytest --version
                        black --version
                        flake8 --version
                        bandit --version

                        echo "Install done ✓"
                    """
                }
            }
            post {
                failure {
                    echo "❌ Install failed — check requirements.txt"
                }
            }
        }

        // ── Lint — uses virtualenv on Jenkins node ────────
        stage('Lint') {
            steps {
                dir('user-service') {
                    sh """
                        . ${VENV_DIR}/bin/activate

                        echo "=== Black (auto-format) ==="
                        black app.py --line-length 88
                        echo "Black ✓"

                        echo "=== Flake8 (lint) ==="
                        flake8 app.py \
                            --max-line-length=88 \
                            --extend-ignore=E203,W503 \
                            --statistics
                        echo "Flake8 ✓"
                    """
                }
            }
            post {
                failure {
                    echo "❌ Lint failed on ${env.BRANCH}"
                }
            }
        }

        // ── Unit Tests — uses virtualenv on Jenkins node ──
        stage('Unit Tests') {
            steps {
                dir('user-service') {
                    sh """
                        . ${VENV_DIR}/bin/activate

                        pytest tests/ \
                            --ignore=tests/test_integration.py \
                            -v \
                            --junitxml=test-results.xml \
                            --cov=app \
                            --cov-report=xml:coverage.xml \
                            --tb=short

                        echo "Tests passed ✓"
                    """
                }
            }
            post {
                always {
                    junit allowEmptyResults: true,
                          testResults: 'user-service/test-results.xml'
                    archiveArtifacts(
                        artifacts:        'user-service/coverage.xml',
                        allowEmptyArchive: true
                    )
                }
                failure {
                    echo "❌ Tests failed — ${env.BRANCH} | ${env.SHORT_SHA}"
                }
            }
        }

        // ── Security Scan — uses virtualenv ───────────────
        stage('Security Scan') {
            steps {
                dir('user-service') {
                    sh """
                        . ${VENV_DIR}/bin/activate

                        echo "=== Bandit ==="
                        bandit -r app.py \
                            -f json \
                            -o bandit-report.json \
                            --severity-level medium || true
                        echo "Bandit done ✓"

                        echo "=== Safety ==="
                        safety check \
                            -r requirements.txt \
                            --json \
                            -o safety-report.json || true
                        echo "Safety done ✓"
                    """
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

        // ── Docker Build — runs on Jenkins node directly ──
        // Docker CLI available via socket mount on Jenkins
        stage('Docker Build') {
            steps {
                dir('user-service') {
                    sh """
                        echo "=== Building Docker image ==="
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
                    echo "❌ Docker build failed"
                }
            }
        }

        // ── Docker Push — main branch only ────────────────
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
                        echo "Pushed: ${IMAGE_NAME}:${IMAGE_TAG} ✓"
                    """
                }
            }
        }
    }

    post {
        always {
            script {
                // Clean up image if it was built
                sh "docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true"
                // Clean up virtualenv with workspace
            }
            cleanWs()
        }
        success {
            echo """
                ✅ ${SERVICE_NAME} #${BUILD_NUMBER} passed
                Branch: ${env.BRANCH}
                Commit: ${env.SHORT_SHA}
                Author: ${env.AUTHOR}
                Image:  ${IMAGE_NAME}:${IMAGE_TAG}
            """.stripIndent()
        }
        failure {
            echo """
                ❌ ${SERVICE_NAME} #${BUILD_NUMBER} FAILED
                Branch: ${env.BRANCH}
                Commit: ${env.SHORT_SHA}
                Author: ${env.AUTHOR}
                Logs:   ${BUILD_URL}console
            """.stripIndent()
        }
    }
}