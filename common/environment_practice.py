#环境配置：三个环境，test,beta,master
# test 环境：跑所有用例（包括增删改）
# beta 环境：跑核心流程用例（只读或有回滚机制）
# master 环境：只跑只读的冒烟用例，绝对不写数据
ENV_HOST={
"test":"http://127.0.0.1:5000",
"beta":"http://127.0.0.1:5000",
"master":"http://127.0.0.1:5000",
}
#当前在跑的环境
ENV_RUN="test"
#只能获取域名
BASE_URL=ENV_HOST[ENV_RUN]

#公共请求头
COMMON_Headers={
    "Accept":"application/json"
}

#接口最多等待10S，10S不响应直接断开
API_TIMEOUT = 10
