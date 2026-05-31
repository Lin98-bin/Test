import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common.api_client import RequestsClient, TokenStore
from common.jsonpath_utils import JsonPathExtractor
from common import setting

def pytest_addoption(parser):
    """增加命令行参数 --env"""
    parser.addoption(
        "--env", action="store", default="test", help="set test environment: test, beta or prod"
    )

@pytest.fixture(scope="session", autouse=True)
def set_env(request):
    """根据命令行参数，调用 setting.py 的切换函数"""
    env = request.config.getoption("--env")
    setting.change_env(env)
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
    client.url = setting.BASE_URL + '/login'
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