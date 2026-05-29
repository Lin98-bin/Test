import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common.api_client import RequestsClient, TokenStore
from common.jsonpath_utils import JsonPathExtractor
from common.environment import BASE_URL
from common.config_manager import config

def pytest_addoption(parser):
    """增加命令行参数 --env"""
    parser.addoption(
        "--env", action="store", default="test", help="set test environment: test, beta or prod"
    )

@pytest.fixture(scope="session", autouse=True)
def set_env(request):
    """根据命令行参数设置全局环境配置"""
    env = request.config.getoption("--env")
    print(f"\n【配置】当前运行环境: {env}")
    # 这里可以根据 env 动态修改 config 对象的属性
    config.set("environment", env)
    
    # 动态调整 BASE_URL 等逻辑可以在这里实现
    if env == "prod":
        config.set("server.base_url", "https://prod-api.com")
    elif env == "beta":
        config.set("server.base_url", "http://beta-api.com")
    
    return env

@pytest.fixture(scope="session")
def login_token():
    """
    会话级 fixture：整个测试会话只登录一次
    返回：token 字符串
    """
    username = "test_0006"
    password = "123456"

    print(f"\n【Fixture】正在登录获取Token...")

    client = RequestsClient()
    client.url = BASE_URL + '/login'
    client.method = "post"
    client.json = {
        "username": username,
        "password": password
    }

    resp = client.send()
    resp_json = resp.json()

    # 提取 token
    extractor = JsonPathExtractor()
    token = extractor.extract(resp_json, "$.data.token")

    # 存储到 TokenStore
    TokenStore.set_token(username, token)

    print(f"【Fixture】Token获取成功：{token[:20]}...")

    return token