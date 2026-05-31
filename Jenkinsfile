pipeline {
    agent any

    // 1. 定时触发：每天凌晨 1 点自动执行
    triggers {
        cron('H 1 * * *')
    }

    environment {
        PYTHON_PATH = "python"
        PYTHONUTF8 = "1"
        // 邮件接收人
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

        // 2. 阶梯执行：Test -> Beta -> Prod
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
                
                // 3. 邮件发送逻辑
                mail to: "${env.EMAIL_RECIPIENT}",
                     subject: "Jenkins 自动化测试任务报告 - Build #${env.BUILD_NUMBER} - ${currentBuild.currentResult}",
                     body: """
                     <html>
                     <body>
                        <h2>自动化测试执行完毕</h2>
                        <p>项目名称：${env.JOB_NAME}</p>
                        <p>构建编号：#${env.BUILD_NUMBER}</p>
                        <p>执行状态：${currentBuild.currentResult}</p>
                        <p>报告链接：<a href="${env.BUILD_URL}allure/">点击查看 Allure 详细报告</a></p>
                        <p>提示：如果需要离线报告，请在 Jenkins 构建页面下载 complete.html 制品。</p>
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
