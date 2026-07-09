import os
import yaml

# 1. 动态定位项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YAML_PATH = os.path.join(BASE_DIR, "config", "config.yaml")

# 2. 一次性读取所有环境配置
with open(YAML_PATH, 'r', encoding='utf-8') as f:
    _all_config = yaml.safe_load(f)

# 3. 定义全局变量（默认指向 test 环境）
API_TIMEOUT = 10
ENV = "test"
BASE_URL = _all_config[ENV]['base_url']
DB_CONF = _all_config[ENV].get('db', {})

def change_env(new_env):
    """
    环境切换函数：供 conftest.py 调用
    """
    global ENV, BASE_URL, DB_CONF
    if new_env in _all_config:
        ENV = new_env
        BASE_URL = _all_config[new_env]['base_url']
        DB_CONF = _all_config[new_env].get('db', {})
        print(f"--- 环境已成功切换至: {ENV} ---")
