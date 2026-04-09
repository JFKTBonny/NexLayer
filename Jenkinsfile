// user-service/Jenkinsfile — fully corrected
pipeline {

    // agent any — works on single node Jenkins
    // no label needed, no agent none issues
    agent any

    environment {
        SERVICE_NAME = 'user-service'
        IMAGE_NAME   = 'santonix/users'
        IMAGE_TAG    = "${BUILD_NUMBER}"
        DOCKER_CRED  = 'dockerhub'
    }

    stages {

        // ── 1. Checkout + resolve GID ────────────────────
        // Runs directly on Jenkins node (agent any)
        // This is where we capture DOCKER_GID safely
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

                    // Verify docker socket is accessible
                    // before trying to use it
                    def socketCheck = sh(
                        script: 'test -S /var/run/docker.sock && echo "OK" || echo "MISSING"',
                        returnStdout: true
                    ).trim()

                    if (socketCheck != 'OK') {
                        error("""
                            Docker socket not found at /var/run/docker.sock
                            Jenkins container must be started with:
                            -v /var/run/docker.sock:/var/run/docker.sock
                        """.stripIndent())
                    }

                    // Now safe to get GID
                    env.DOCKER_GID = sh(
                        script: "stat -c '%g' /var/run/docker.sock",
                        returnStdout: true
                    ).trim()

                    echo """
                        ╔═══════════════════════════════════╗
                        ║  NexLayer — ${SERVICE_NAME}
                        ╠═══════════════════════════════════╣
                        ║  Branch:     ${env.BRANCH}
                        ║  Commit:     ${env.SHORT_SHA}
                        ║  Author:     ${env.AUTHOR}
                        ║  Docker GID: ${env.DOCKER_GID}
                        ╚═══════════════════════════════════╝
                    """.stripIndent()
                }
            }
        }

        // ── 2. Install ───────────────────────────────────
        stage('Install') {
            agent {
                docker {
                    image 'santonix/ci-python-docker:latest'
                    reuseNode true
                    args  """-v /var/run/docker.sock:/var/run/docker.sock
                             --group-add ${env.DOCKER_GID}"""
                }
            }
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

        // ── 3. Lint ──────────────────────────────────────
        stage('Lint') {
            agent {
                docker {
                    image 'santonix/ci-python-docker:latest'
                    reuseNode true
                    args  """-v /var/run/docker.sock:/var/run/docker.sock
                             --group-add ${env.DOCKER_GID}"""
                }
            }
            steps {
                dir('user-service') {
                    sh '''
                        echo "=== Black ==="
                        black app.py --line-length 88
                        echo "Black ✓"

                        echo "=== Flake8 ==="
                        flake8 app.py \
                            --max-line-length=88 \
                            --extend-ignore=E203,W503 \
                            --statistics
                        echo "Flake8 ✓"
                    '''
                }
            }
            post {
                failure {
                    echo "❌ Lint failed on ${env.BRANCH} by ${env.AUTHOR}"
                }
            }
        }

        // ── 4. Unit Tests ────────────────────────────────
        stage('Unit Tests') {
            agent {
                docker {
                    image 'santonix/ci-python-docker:latest'
                    reuseNode true
                    args  """-v /var/run/docker.sock:/var/run/docker.sock
                             --group-add ${env.DOCKER_GID}"""
                }
            }
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

        // ── 5. Security Scan ─────────────────────────────
        stage('Security Scan') {
            agent {
                docker {
                    image 'santonix/ci-python-docker:latest'
                    reuseNode true
                    args  """-v /var/run/docker.sock:/var/run/docker.sock
                             --group-add ${env.DOCKER_GID}"""
                }
            }
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

                        echo "Security scan done ✓"
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

        // ── 6. Docker Build ──────────────────────────────
        // Runs on agent any — docker CLI available via socket
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
                    echo "❌ Docker build failed"
                }
            }
        }

        // ── 7. Docker Push ───────────────────────────────
        stage('Docker Push') {
            when {
                branch 'main'
            }
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

    // ── Post — runs on agent any context ─────────────────
    // agent any guarantees node context is always available
    // post{} sh{} and cleanWs() work without issues
    post {
        always {
            script {
                def img = env.IMAGE_NAME
                def tag = env.IMAGE_TAG
                if (img && tag) {
                    sh "docker rmi ${img}:${tag} || true"
                } else {
                    echo "No image to clean up"
                }
            }
            cleanWs()
        }
        success {
            echo """
                ✅ ${SERVICE_NAME} #${BUILD_NUMBER} passed
                Branch:  ${env.BRANCH}
                Commit:  ${env.SHORT_SHA}
                Author:  ${env.AUTHOR}
                Image:   ${IMAGE_NAME}:${IMAGE_TAG}
            """.stripIndent()
        }
        failure {
            echo """
                ❌ ${SERVICE_NAME} #${BUILD_NUMBER} FAILED
                Branch:  ${env.BRANCH}
                Commit:  ${env.SHORT_SHA}
                Author:  ${env.AUTHOR}
                Logs:    ${BUILD_URL}console
            """.stripIndent()
        }
    }
}