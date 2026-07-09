pipeline {
    agent any

    // 1. 定时构建触发器：每日凌晨1点自动运行
    triggers {
        cron('H 1 * * *')
    }

    environment {
        PYTHON_PATH = "python"
        PYTHONUTF8 = "1"
        PYTHONIOENCODING = "UTF-8"
        // 邮件接收人邮箱
        EMAIL_RECIPIENT = "1029633859@qq.com" 
    }

    stages {
        stage('拉取代码') {
            steps {
                script {
                    echo '[信息] 开始从Git仓库拉取代码...'
                    checkout scm
                }
            }
        }

        stage('初始化运行环境') {
            steps {
                script {
                    echo '[信息] 安装项目所需依赖包...'
                    bat 'pip install -r requirements.txt'
                }
            }
        }

        // 2. 串行执行流程：测试环境 → Beta预发环境 → 生产环境
        stage('测试环境执行用例') {
            steps {
                script {
                    echo "[信息] 在TEST测试环境执行自动化测试..."
                    bat "python run.py --env=test"
                }
            }
        }

        stage('Beta预发环境执行用例') {
            steps {
                script {
                    echo "[信息] 在BETA预发环境执行自动化测试..."
                    bat "python run.py --env=beta"
                }
            }
        }

        stage('生产环境执行用例') {
            steps {
                script {
                    echo "[信息] 在PROD生产环境执行自动化测试..."
                    bat "python run.py --env=prod"
                }
            }
        }
    }

    post {
        always {
            script {
                echo '[信息] 收集测试结果并生成Allure可视化报告...'
                allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
                
                // 3. 邮件通知逻辑
                mail to: "${env.EMAIL_RECIPIENT}",
                     subject: "Jenkins自动化测试报告 - 构建号#${env.BUILD_NUMBER} - 运行结果：${currentBuild.currentResult}",
                     body: """
                     <html>
                     <body>
                        <h2>自动化测试任务执行完成</h2>
                        <p>项目名称：${env.JOB_NAME}</p>
                        <p>构建编号：#${env.BUILD_NUMBER}</p>
                        <p>运行状态：${currentBuild.currentResult}</p>
                        <p>测试报告地址：<a href="${env.BUILD_URL}allure/">点击查看Allure完整报告</a></p>
                        <p>备注：可从构建产物下载complete.html用于离线查看报告</p>
                     </body>
                     </html>
                     """,
                     mimeType: 'text/html'
            }
        }
        success {
            echo '[成功] 所有环境测试全部通过！'
        }
        failure {
            echo '[失败] 某一环境测试报错，流水线已中断停止。'
        }
    }
}