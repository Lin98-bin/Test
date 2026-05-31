pipeline {
    agent any

    // 1. Scheduled trigger: Runs daily at 01:00 AM
    triggers {
        cron('H 1 * * *')
    }

    environment {
        PYTHON_PATH = "python"
        PYTHONUTF8 = "1"
        PYTHONIOENCODING = "UTF-8"
        // Email recipient
        EMAIL_RECIPIENT = "1029633859@qq.com" 
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    echo '[INFO] Start pulling code from Git...'
                    checkout scm
                }
            }
        }

        stage('Prepare Environment') {
            steps {
                script {
                    echo '[INFO] Installing project dependencies...'
                    bat 'pip install -r requirements.txt'
                }
            }
        }

        // 2. Sequential execution: Test -> Beta -> Prod
        stage('Test Environment') {
            steps {
                script {
                    echo "[INFO] Running tests in TEST environment..."
                    bat "python run.py --env=test"
                }
            }
        }

        stage('Beta Environment') {
            steps {
                script {
                    echo "[INFO] Running tests in BETA environment..."
                    bat "python run.py --env=beta"
                }
            }
        }

        stage('Prod Environment') {
            steps {
                script {
                    echo "[INFO] Running tests in PROD environment..."
                    bat "python run.py --env=prod"
                }
            }
        }
    }

    post {
        always {
            script {
                echo '[INFO] Collecting test results and generating Allure report...'
                allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
                
                // 3. Email notification logic
                mail to: "${env.EMAIL_RECIPIENT}",
                     subject: "Jenkins Test Report - Build #${env.BUILD_NUMBER} - ${currentBuild.currentResult}",
                     body: """
                     <html>
                     <body>
                        <h2>Automated Test Execution Completed</h2>
                        <p>Project Name: ${env.JOB_NAME}</p>
                        <p>Build Number: #${env.BUILD_NUMBER}</p>
                        <p>Status: ${currentBuild.currentResult}</p>
                        <p>Report Link: <a href="${env.BUILD_URL}allure/">Click to view Allure Report</a></p>
                        <p>Note: Download complete.html from build artifacts for offline viewing.</p>
                     </body>
                     </html>
                     """,
                     mimeType: 'text/html'
            }
        }
        success {
            echo '[SUCCESS] All environments passed!'
        }
        failure {
            echo '[FAILURE] Pipeline stopped due to failure in one of the stages.'
        }
    }
}
