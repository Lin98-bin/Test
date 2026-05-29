from .config_manager import config

# 加载配置
config.load_config()

# 从配置文件读取
BASE_URL = config.get('server.base_url', 'http://127.0.0.1:5000')
API_TIMEOUT = 10
COMMON_HEADERS = {"Accept": "application/json"}

# 环境配置（保留多环境切换能力）
current_env = config.get('environment', 'test')

ENV_HOST = {
    "test": config.get('server.base_url', 'http://127.0.0.1:5000'),
    "beta": "http://beta-api.com",
    "prod": "https://prod-api.com",
}

ENV_RULE = {
    "test": {"allow_write": True,  "run_mark": "test_run"},
    "beta": {"allow_write": True,  "run_mark": "beta_run"},
    "prod": {"allow_write": False, "run_mark": "prod_run"},
}

current_config = None