pipeline {
    agent any

    // ==================== 触发器 ====================
    triggers {
        cron('H 1 * * *')   // 每日凌晨 1 点自动构建
    }

    // ==================== 全局环境变量 ====================
    environment {
        PYTHON_PATH      = "python"
        PYTHONUTF8       = "1"
        PYTHONIOENCODING = "UTF-8"

        // Docker 镜像仓库
        DOCKER_REGISTRY  = "docker.io/linchuanbin"
        IMAGE_NAME       = "mini-mall-api"
        IMAGE_TAG        = "${env.BUILD_NUMBER}"

        // 邮件接收人
        EMAIL_RECIPIENT  = "1029633859@qq.com"

        // 部署目标服务器
        TEST_SERVER      = "test-server.example.com"
        BETA_SERVER      = "beta-server.example.com"
        PROD_SERVER      = "prod-server.example.com"
    }

    // ==================== 参数 ====================
    parameters {
        choice(name: 'DEPLOY_TO', choices: ['test', 'beta', 'prod'],
               description: '选择要部署的目标环境（prod 需审批）')
        booleanParam(name: 'SKIP_TESTS', defaultValue: false,
                     description: '跳过测试阶段（紧急修复时使用）')
    }

    // ==================== 流水线阶段 ====================
    stages {

        // ============ CI 部分 ============

        stage('1. 拉取代码') {
            steps {
                script {
                    echo '[CI] 开始从 Git 仓库拉取代码...'
                    checkout scm
                }
            }
        }

        stage('2. 初始化运行环境') {
            steps {
                script {
                    echo '[CI] 安装项目依赖...'
                    bat 'pip install -r requirements.txt'
                }
            }
        }

        stage('3. 自动化测试 — 测试环境') {
            when { expression { !params.SKIP_TESTS } }
            steps {
                script {
                    echo '[CI] 在 TEST 环境执行自动化测试...'
                    bat "python run.py --env=test"
                }
            }
        }

        stage('4. 自动化测试 — 预发环境') {
            when { expression { !params.SKIP_TESTS } }
            steps {
                script {
                    echo '[CI] 在 BETA 环境执行自动化测试...'
                    bat "python run.py --env=beta"
                }
            }
        }

        // ============ CD 部分 ============

        stage('5. 构建 Docker 镜像') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    echo "[CD] 构建 Docker 镜像: ${IMAGE_NAME}:${IMAGE_TAG}"
                    bat """
                        docker build -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .
                        docker tag  ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest
                    """
                }
            }
        }

        stage('6. 推送镜像到仓库') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    echo "[CD] 推送镜像到仓库: ${DOCKER_REGISTRY}"
                    // 需要先在 Jenkins 凭据管理中配置 Docker Hub 账号
                    withCredentials([usernamePassword(
                        credentialsId: 'docker-hub-credentials',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        bat """
                            docker login -u ${DOCKER_USER} -p ${DOCKER_PASS}
                            docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                            docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest
                            docker logout
                        """
                    }
                }
            }
        }

        stage('7. 部署到测试环境') {
            when {
                expression { params.DEPLOY_TO == 'test' }
            }
            steps {
                script {
                    echo "[CD] 部署到 TEST 环境: ${TEST_SERVER}"
                    // 将 docker-compose.yml 和 deploy.sh 上传到目标服务器
                    sshagent(['test-server-ssh-key']) {
                        sh """
                            scp docker-compose.yml deploy.sh ${TEST_SERVER}:/opt/mini-mall/
                            ssh ${TEST_SERVER} 'cd /opt/mini-mall && bash deploy.sh test ${IMAGE_TAG}'
                        """
                    }
                }
            }
        }

        stage('8. 冒烟测试') {
            when {
                expression { params.DEPLOY_TO == 'test' }
            }
            steps {
                script {
                    echo "[CD] 执行冒烟测试，验证部署是否成功..."
                    sleep 10  // 等待服务完全就绪
                    bat "python run.py --env=test -k 'test_login or test_register or test_goods_list'"
                }
            }
        }

        stage('9. 部署到预发环境 ⏸') {
            when {
                expression { params.DEPLOY_TO == 'beta' }
            }
            input {
                message "是否确认部署到 BETA 预发环境？"
                ok "确认部署"
            }
            steps {
                script {
                    echo "[CD] 部署到 BETA 环境: ${BETA_SERVER}"
                    sshagent(['beta-server-ssh-key']) {
                        sh """
                            scp docker-compose.yml deploy.sh ${BETA_SERVER}:/opt/mini-mall/
                            ssh ${BETA_SERVER} 'cd /opt/mini-mall && bash deploy.sh beta ${IMAGE_TAG}'
                        """
                    }
                }
            }
        }

        stage('10. 部署到生产环境 ⏸⏸') {
            when {
                expression { params.DEPLOY_TO == 'prod' }
            }
            input {
                message "⚠️  即将部署到 PRODUCTION 生产环境！请确认：\n1. 预发环境已验证通过\n2. 已通知相关干系人\n3. 已准备好回滚方案"
                ok "确认发布到生产"
            }
            steps {
                script {
                    echo "[CD] 部署到 PROD 环境: ${PROD_SERVER}"
                    sshagent(['prod-server-ssh-key']) {
                        sh """
                            scp docker-compose.yml deploy.sh ${PROD_SERVER}:/opt/mini-mall/
                            ssh ${PROD_SERVER} 'cd /opt/mini-mall && bash deploy.sh prod ${IMAGE_TAG}'
                        """
                    }
                }
            }
        }
    }

    // ==================== 后置处理 ====================
    post {
        always {
            script {
                echo '[INFO] 收集测试结果并生成 Allure 报告...'
                allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]

                // 邮件通知
                mail to: "${env.EMAIL_RECIPIENT}",
                     subject: "Jenkins CI/CD 报告 - ${env.JOB_NAME} #${env.BUILD_NUMBER} - ${currentBuild.currentResult}",
                     body: """
                     <html>
                     <body>
                        <h2>CI/CD 流水线执行完成</h2>
                        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
                            <tr><td>项目名称</td><td>${env.JOB_NAME}</td></tr>
                            <tr><td>构建编号</td><td>#${env.BUILD_NUMBER}</td></tr>
                            <tr><td>镜像版本</td><td>${env.IMAGE_TAG}</td></tr>
                            <tr><td>部署环境</td><td>${params.DEPLOY_TO}</td></tr>
                            <tr><td>运行结果</td><td><b>${currentBuild.currentResult}</b></td></tr>
                        </table>
                        <br/>
                        <p>📊 <a href="${env.BUILD_URL}allure/">点击查看 Allure 测试报告</a></p>
                        <p>🐳 镜像: ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}</p>
                        <p>📦 构建产物: <a href="${env.BUILD_URL}">complete.html（离线报告）</a></p>
                        ${currentBuild.currentResult == 'FAILURE' ? '<p style="color:red;">⚠️ 流水线失败，请检查日志并确认是否需要回滚</p>' : ''}
                     </body>
                     </html>
                     """,
                     mimeType: 'text/html'
            }
            // 清理 Docker 构建缓存
            bat 'docker image prune -f'  // Windows Jenkins 节点用 bat
        }
        success {
            echo '[SUCCESS] CI/CD 流水线全部通过！'
        }
        failure {
            echo '[FAILURE] 流水线失败，请检查日志。如已部署，请考虑执行回滚。'
        }
    }
}
