# 你原来的所有代码，完全不动！
COMMON_HEADERS = {"Accept": "application/json"}
API_TIMEOUT = 10
BASE_URL = "http://127.0.0.1:5000"  # 这个是默认值，会被动态覆盖

# 我之前新增的三环境域名，保留不动
ENV_HOST = {
    "test": "shturl.cc/psLiZGtEn",
    "beta": "http://beta-api.com",
    "prod": "https://prod-api.com",
}

# 新增：环境权限+用例规则，保留不动
ENV_RULE = {
    "test": {"allow_write": True,  "run_mark": "test_run"},
    "beta": {"allow_write": True,  "run_mark": "beta_run"},
    "prod": {"allow_write": False, "run_mark": "prod_run"},
}

# 全局变量，保留不动
current_env = "test"
current_config = None