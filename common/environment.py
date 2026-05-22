#环境配置（目前只有测试环境跑得痛）
ENV_HOST={
    "test":"http://127.0.0.1:5000",
    "beta": "http://127.0.0.1:5000/beta",
    "master": "http://127.0.0.1:5000/master",

}
#当前在跑的环境：切换环境改这里就行
RUN_ENV="test"

#自动获取域名
BASE_URL=ENV_HOST[RUN_ENV]

#公共请求头
COMMON_HEADERS={
    "Accept":"application/json",

}

#接口最多等 10 秒，超时就断开，防止脚本卡死！
API_TIMEOUT = 10