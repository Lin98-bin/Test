pipeline {
    agent any

    parameters {
        choice(name: 'ENV', choices: ['test', 'beta', 'prod'], description: '选择运行环境')
    }

    environment {
        PYTHON_PATH = "python"
        PYTHONUTF8 = "1"
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
                    // Windows 环境使用 bat，Linux 环境使用 sh
                    bat 'pip install -r requirements.txt'
                }
            }
        }

        stage('Execute Tests') {
            steps {
                script {
                    echo "[INFO] Running automated tests (Env: ${params.ENV})..."
                    // 执行测试并生成 allure-results
                    bat "python run.py --env=${params.ENV}"
                }
            }
        }
    }

    post {
        always {
            script {
                echo '[INFO] Collecting test results and generating Allure report...'
                // 1. 调用 Jenkins Allure 插件展示原生报告
                allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
                
                // 2. 归档单体 HTML 报告（方便下载发送）
                if (fileExists('allure-report/complete.html')) {
                    archiveArtifacts artifacts: 'allure-report/complete.html', fingerprint: true
                    echo '[SUCCESS] Single HTML report archived.'
                }
            }
        }
        success {
            echo '[SUCCESS] All tests passed!'
        }
        failure {
            echo '[FAILURE] Some tests failed, please check the report.'
        }
    }
}
