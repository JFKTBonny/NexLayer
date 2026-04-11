// notification-service/Jenkinsfile
pipeline {
    agent any

    environment {
        SERVICE_NAME = 'notification-service'
        IMAGE_NAME   = 'santonix/notify'
        IMAGE_TAG    = "${BUILD_NUMBER}"
        DOCKER_CRED  = 'dockerhub'
        CI           = 'true'
        NODE_ENV     = 'test'
        // npm cache in workspace — always writable
        NPM_CONFIG_CACHE = "${WORKSPACE}/.npm-cache"
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

                    echo """
                        Service:  ${SERVICE_NAME}
                        Branch:   ${env.BRANCH}
                        Commit:   ${env.SHORT_SHA}
                        Author:   ${env.AUTHOR}
                    """.stripIndent()
                }
            }
        }

        // ── Node: verify tools ────────────────────────────
        stage('Pre-flight') {
            steps {
                sh '''
                    echo "=== Tool Versions ==="
                    node --version
                    npm --version
                    docker --version
                '''
            }
        }

        // ── Node: npm ci — uses workspace cache ───────────
        // NPM_CONFIG_CACHE points to workspace
        // no permission issues unlike global npm cache
        stage('Install') {
            steps {
                dir('notification-service') {
                    sh '''
                        mkdir -p ${NPM_CONFIG_CACHE}

                        npm ci \
                            --prefer-offline \
                            --cache ${NPM_CONFIG_CACHE}

                        echo "npm install done ✓"
                    '''
                }
            }
            post {
                failure {
                    echo "❌ npm install failed — check package.json"
                }
            }
        }

        // ── Node: eslint ──────────────────────────────────
        stage('Lint') {
            steps {
                dir('notification-service') {
                    sh '''
                        echo "=== ESLint ==="

                        # Create eslint config if missing
                        if [ ! -f .eslintrc.json ]; then
                            cat > .eslintrc.json << EOF
{
  "env":     { "node": true, "es2021": true, "jest": true },
  "extends": "eslint:recommended",
  "rules":   {
    "no-unused-vars": "warn",
    "no-console":     "off",
    "semi":           ["error", "always"]
  }
}
EOF
                        fi

                        npx eslint app.js \
                            --format=checkstyle \
                            --output-file eslint-report.xml || true

                        npx eslint app.js || true

                        echo "Lint done ✓"
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts(
                        artifacts:        'notification-service/eslint-report.xml',
                        allowEmptyArchive: true
                    )
                }
                failure {
                    echo "❌ Lint failed on ${env.BRANCH}"
                }
            }
        }

        // ── Node: jest tests ──────────────────────────────
        stage('Unit Tests') {
            steps {
                dir('notification-service') {
                    sh '''
                        # Install jest-junit for XML reports
                        npm install --save-dev jest-junit \
                            --cache ${NPM_CONFIG_CACHE} \
                            --quiet

                        npx jest \
                            --forceExit \
                            --detectOpenHandles \
                            --coverage \
                            --coverageDirectory=coverage \
                            --reporters=default \
                            --reporters=jest-junit \
                            --testEnvironment=node

                        echo "Tests passed ✓"
                    '''
                }
            }
            post {
                always {
                    // Node uses jest-junit XML
                    junit(
                        allowEmptyResults: true,
                        testResults:       'notification-service/junit.xml'
                    )
                    publishHTML([
                    reportDir: 'order-service/target/site/jacoco',
                    reportFiles: 'index.html',
                    reportName: 'JaCoCo Coverage — Orders',
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true
                ])
                }
                failure {
                    echo "❌ Tests failed — ${env.BRANCH} | ${env.SHORT_SHA}"
                }
            }
        }

        // ── Node: npm audit ───────────────────────────────
        stage('Security Scan') {
            steps {
                dir('notification-service') {
                    sh '''
                        echo "=== npm audit ==="
                        npm audit \
                            --audit-level=high \
                            --json > audit-report.json || true

                        npm audit --audit-level=high || true

                        echo "Security scan done ✓"
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts(
                        artifacts:        'notification-service/audit-report.json',
                        allowEmptyArchive: true
                    )
                }
            }
        }

        // ── Node: optional build step ─────────────────────
        stage('Build') {
            steps {
                dir('notification-service') {
                    sh '''
                        if node -e \
                            "const p=require('./package.json'); \
                            process.exit(p.scripts && p.scripts.build ? 0 : 1)" \
                            2>/dev/null; then
                            npm run build
                            echo "Build done ✓"
                        else
                            echo "No build script defined — skipping ✓"
                        fi
                    '''
                }
            }
        }

        // ── Docker: build image ───────────────────────────
        stage('Docker Build') {
            steps {
                dir('notification-service') {
                    sh """
                        docker build \
                            --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                            --build-arg GIT_COMMIT=${env.SHORT_SHA} \
                            --build-arg NODE_ENV=production \
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

        // ── Docker: push — main only ──────────────────────
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
            sh "docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true"
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


// ###################################### ORDER SERVICE JENKINSFILE ####################################################

// // order-service/Jenkinsfile
// pipeline {
//     agent any

//     environment {
//         SERVICE_NAME = 'order-service'
//         IMAGE_NAME   = 'santonix/orders'
//         IMAGE_TAG    = "${BUILD_NUMBER}"
//         DOCKER_CRED  = 'dockerhub-creds'
//         MAVEN_OPTS = "-Dmaven.repo.local=$WORKSPACE/.m2"
//     }

//     stages {

//         stage('Checkout') {
//             steps {
//                 checkout scm
//                 script {
//                     env.BRANCH = env.BRANCH_NAME ?: sh(
//                         script: 'git rev-parse --abbrev-ref HEAD',
//                         returnStdout: true
//                     ).trim()
//                     env.SHORT_SHA = sh(
//                         script: 'git rev-parse --short HEAD',
//                         returnStdout: true
//                     ).trim()
//                     env.AUTHOR = sh(
//                         script: 'git log -1 --pretty=%an',
//                         returnStdout: true
//                     ).trim()

//                     echo """
//                         Service:  ${SERVICE_NAME}
//                         Branch:   ${env.BRANCH}
//                         Commit:   ${env.SHORT_SHA}
//                         Author:   ${env.AUTHOR}
//                     """.stripIndent()
//                 }
//             }
//         }

//         // ── Java: verify tools on Jenkins node ───────────
//         stage('Pre-flight') {
//             steps {
//                 sh '''
//                     echo "=== Tool Versions ==="
//                     java -version
//                     mvn -version
//                     docker --version
//                 '''
//             }
//         }

//         // ── Java: compile ─────────────────────────────────
//         stage('Compile') {
//             steps {
//                 dir('order-service') {
//                     sh '''
//                         echo "=== Compiling ==="
//                         export MAVEN_CONFIG=/tmp/.m2
//                         export MAVEN_OPTS="-Dmaven.repo.local=/tmp/.m2"
//                         mkdir -p /tmp/.m2
//                         mvn -B clean compile
//                     '''
//                 }
//             }
//             post {
//                 failure {
//                     echo "❌ Compile failed — check Java source errors"
//                 }
//             }
//         }

//         // ── Java: checkstyle lint ─────────────────────────
//         stage('Lint') {
//             steps {
//                 dir('order-service') {
//                     sh """
//                         echo "=== Checkstyle ==="
//                         mvn checkstyle:check ${MAVEN_OPTS} || true

//                         echo "Lint done ✓"
//                     """
//                 }
//             }
//             post {
//                 always {
//                     archiveArtifacts(
//                         artifacts:        'order-service/target/checkstyle-result.xml',
//                         allowEmptyArchive: true
//                     )
//                 }
//                 failure {
//                     echo "❌ Lint failed on ${env.BRANCH}"
//                 }
//             }
//         }

//         // ── Java: unit tests with surefire ────────────────
//         stage('Unit Tests') {
//             steps {
//                 dir('order-service') {
//                     sh """
//                         mvn test ${MAVEN_OPTS}
//                         echo "Unit tests passed ✓"
//                     """
//                 }
//             }
//             post {
//                 always {
//                     // Java uses surefire XML reports
//                     junit(
//                         allowEmptyResults: true,
//                         testResults:       'order-service/target/surefire-reports/*.xml'
//                     )
//                 }
//                 failure {
//                     echo "❌ Unit tests failed — ${env.BRANCH} | ${env.SHORT_SHA}"
//                 }
//             }
//         }

//         // ── Java: JaCoCo coverage report ──────────────────
//         stage('Code Coverage') {
//             steps {
//                 dir('order-service') {
//                     sh """
//                         mvn jacoco:report ${MAVEN_OPTS}
//                         echo "Coverage report generated ✓"
//                     """
//                 }
//             }
//             post {
//                 always {
//                     publishHTML([
//                         reportDir: 'order-service/target/site/jacoco',
//                         reportFiles: 'index.html',
//                         reportName: 'JaCoCo Coverage — Orders',
//                         keepAll: true,
//                         alwaysLinkToLastBuild: true,
//                         allowMissing: true
//                     ])
//                 }
//             }
//         }

//         // ── Java: OWASP dependency check ──────────────────
//         stage('Security Scan') {
//             steps {
//                 dir('order-service') {
//                     sh """
//                         echo "=== OWASP Dependency Check ==="
//                         mvn dependency-check:check \
//                             -DfailBuildOnCVSS=9 \
//                             ${MAVEN_OPTS} || true

//                         echo "Security scan done ✓"
//                     """
//                 }
//             }
//             post {
//                 always {
//                     archiveArtifacts(
//                         artifacts:        'order-service/target/dependency-check-report.html',
//                         allowEmptyArchive: true
//                     )
//                 }
//             }
//         }

//         // ── Java: integration tests with failsafe ─────────
//         stage('Integration Tests') {
//             when {
//                 expression {
//                     env.BRANCH ==~ /(main|develop|release\/.*|hotfix\/.*)/
//                 }
//             }
//             steps {
//                 dir('order-service') {
//                     sh """
//                         mvn verify -Pintegration ${MAVEN_OPTS}
//                         echo "Integration tests passed ✓"
//                     """
//                 }
//             }
//             post {
//                 always {
//                     junit(
//                         allowEmptyResults: true,
//                         testResults:       'order-service/target/failsafe-reports/*.xml'
//                     )
//                 }
//                 failure {
//                     echo "❌ Integration tests failed"
//                 }
//             }
//         }

//         // ── Java: package jar ─────────────────────────────
//         stage('Package') {
//             steps {
//                 dir('order-service') {
//                     sh """
//                         mvn package -DskipTests ${MAVEN_OPTS}
//                         echo "Package done ✓"
//                         ls -lh target/*.jar
//                     """
//                     archiveArtifacts(
//                         artifacts:    'target/*.jar',
//                         fingerprint:  true,
//                         onlyIfSuccessful: true
//                     )
//                     stash(
//                         name:     'order-jar',
//                         includes: 'target/*.jar'
//                     )
//                 }
//             }
//         }

//         // ── Docker: build image ───────────────────────────
//         stage('Docker Build') {
//             steps {
//                 dir('order-service') {
//                     sh """
//                         docker build \
//                             --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
//                             --build-arg GIT_COMMIT=${env.SHORT_SHA} \
//                             -t ${IMAGE_NAME}:${IMAGE_TAG} \
//                             -t ${IMAGE_NAME}:latest \
//                             .
//                         echo "Built: ${IMAGE_NAME}:${IMAGE_TAG} ✓"
//                     """
//                 }
//             }
//             post {
//                 failure {
//                     sh "docker image prune -f || true"
//                     echo "❌ Docker build failed"
//                 }
//             }
//         }

//         // ── Docker: push — main only ──────────────────────
//         stage('Docker Push') {
//             when { branch 'main' }
//             steps {
//                 withCredentials([usernamePassword(
//                     credentialsId: "${DOCKER_CRED}",
//                     usernameVariable: 'DOCKER_USER',
//                     passwordVariable: 'DOCKER_PASS'
//                 )]) {
//                     sh """
//                         echo ${DOCKER_PASS} | docker login \
//                             -u ${DOCKER_USER} \
//                             --password-stdin
//                         docker push ${IMAGE_NAME}:${IMAGE_TAG}
//                         docker push ${IMAGE_NAME}:latest
//                         docker logout
//                         echo "Pushed: ${IMAGE_NAME}:${IMAGE_TAG} ✓"
//                     """
//                 }
//             }
//         }
//     }

//     post {
//         always {
//             sh "docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true"
//             cleanWs()
//         }
//         success {
//             echo """
//                 ✅ ${SERVICE_NAME} #${BUILD_NUMBER} passed
//                 Branch: ${env.BRANCH}
//                 Commit: ${env.SHORT_SHA}
//                 Author: ${env.AUTHOR}
//                 Image:  ${IMAGE_NAME}:${IMAGE_TAG}
//             """.stripIndent()
//         }
//         failure {
//             echo """
//                 ❌ ${SERVICE_NAME} #${BUILD_NUMBER} FAILED
//                 Branch: ${env.BRANCH}
//                 Commit: ${env.SHORT_SHA}
//                 Author: ${env.AUTHOR}
//                 Logs:   ${BUILD_URL}console
//             """.stripIndent()
//         }
//     }
// }


//  ############################ USER SERVICE  #########################################################################


// // user-service/Jenkinsfile — FIXED (stable + production-safe)

// pipeline {
//     agent any

//     environment {
//         SERVICE_NAME = 'user-service'
//         IMAGE_NAME   = 'santonix/users'
//         IMAGE_TAG    = "${BUILD_NUMBER}"
//         DOCKER_CRED  = 'dockerhub'
//         DOCKER_IMAGE = 'santonix/ci-python-docker:latest'
//     }

//     stages {

//         stage('Checkout') {
//             steps {
//                 checkout scm
//                 script {
//                     env.BRANCH = env.BRANCH_NAME ?: sh(
//                         script: 'git rev-parse --abbrev-ref HEAD',
//                         returnStdout: true
//                     ).trim()

//                     env.SHORT_SHA = sh(
//                         script: 'git rev-parse --short HEAD',
//                         returnStdout: true
//                     ).trim()

//                     env.AUTHOR = sh(
//                         script: 'git log -1 --pretty=%an',
//                         returnStdout: true
//                     ).trim()

//                     env.DOCKER_GID = sh(
//                         script: "stat -c %g /var/run/docker.sock",
//                         returnStdout: true
//                     ).trim()

//                     echo """
//                     Branch:     ${env.BRANCH}
//                     Commit:     ${env.SHORT_SHA}
//                     Author:     ${env.AUTHOR}
//                     Docker GID: ${env.DOCKER_GID}
//                     """.stripIndent()
//                 }
//             }
//         }

//         stage('Python CI (Containerized)') {
//             steps {
//                 script {
//                     def dockerArgs = "-v /var/run/docker.sock:/var/run/docker.sock --group-add ${env.DOCKER_GID}"

//                     docker.image(env.DOCKER_IMAGE).inside(dockerArgs) {

//                         dir('user-service') {

//                             sh '''
//                                 echo "=== Install ==="
//                                 export HOME=/tmp
//                                 export PATH=$HOME/.local/bin:$PATH
//                                 pip install -r requirements.txt --quiet

//                                 echo "=== Lint ==="
//                                 black app.py --line-length 88
//                                 flake8 app.py \
//                                     --max-line-length=88 \
//                                     --extend-ignore=E203,W503 \
//                                     --statistics

//                                 echo "=== Unit Tests ==="
//                                 pytest tests/ \
//                                     --ignore=tests/test_integration.py \
//                                     -v \
//                                     --junitxml=test-results.xml \
//                                     --cov=app \
//                                     --cov-report=xml:coverage.xml \
//                                     --tb=short

//                                 echo "=== Security Scan ==="
//                                 bandit -r app.py \
//                                     -f json \
//                                     -o bandit-report.json \
//                                     --severity-level medium || true

//                                 safety check \
//                                     -r requirements.txt \
//                                     --json \
//                                     -o safety-report.json || true
//                             '''
//                         }
//                     }
//                 }
//             }
//             post {
//                 always {
//                     junit allowEmptyResults: true,
//                           testResults: 'user-service/test-results.xml'

//                     archiveArtifacts(
//                         artifacts: 'user-service/coverage.xml',
//                         allowEmptyArchive: true
//                     )

//                     archiveArtifacts(
//                         artifacts: 'user-service/*-report.json',
//                         allowEmptyArchive: true
//                     )
//                 }
//             }
//         }

//         stage('Docker Build') {
//             steps {
//                 dir('user-service') {
//                     sh """
//                         docker build \
//                             --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
//                             --build-arg GIT_COMMIT=${env.SHORT_SHA} \
//                             -t ${IMAGE_NAME}:${IMAGE_TAG} \
//                             -t ${IMAGE_NAME}:latest \
//                             .
//                         echo "Built: ${IMAGE_NAME}:${IMAGE_TAG} ✓"
//                     """
//                 }
//             }
//         }

//         stage('Docker Push') {
//             when { branch 'main' }
//             steps {
//                 withCredentials([usernamePassword(
//                     credentialsId: "${DOCKER_CRED}",
//                     usernameVariable: 'DOCKER_USER',
//                     passwordVariable: 'DOCKER_PASS'
//                 )]) {
//                     sh """
//                         echo ${DOCKER_PASS} | docker login \
//                             -u ${DOCKER_USER} \
//                             --password-stdin

//                         docker push ${IMAGE_NAME}:${IMAGE_TAG}
//                         docker push ${IMAGE_NAME}:latest

//                         docker logout
//                         echo "Pushed ✓"
//                     """
//                 }
//             }
//         }
//     }

//     post {
//         always {
//             sh "docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true"
//             cleanWs()
//         }
//         success {
//             echo "✅ ${SERVICE_NAME} #${BUILD_NUMBER} passed | ${env.BRANCH}"
//         }
//         failure {
//             echo "❌ ${SERVICE_NAME} #${BUILD_NUMBER} failed | ${BUILD_URL}console"
//         }
//     }
// }

