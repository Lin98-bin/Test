import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.api_client import RequestsClient
from core.context import TokenStore
from utils.jsonpath_utils import JsonPathExtractor
from core import setting

def pytest_addoption(parser):
    """增加命令行参数 --env"""
    parser.addoption(
        "--env", action="store", default="test", help="set test environment: test, beta or prod"
    )
#前置：：环境切换
@pytest.fixture(scope="session", autouse=True)
def set_env(request):
    """根据命令行参数，调用 setting.py 的切换函数"""
    env = request.config.getoption("--env")
    setting.change_env(env)
    return env
#前置：登录提取token并存入全局存储器
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

    # 提取 token（如果接口返回了 token 就提取，没返回就用 cookie/session 认证）
    extractor = JsonPathExtractor()
    token = extractor.extract(resp_json, "$.data.token")

    if token:
        TokenStore.set_token(username, token)
        print(f"【Fixture】Token获取成功：{token[:20]}...")
    else:
        # 接口不返回 token，可能是 session/cookie 认证
        print(f"【Fixture】接口未返回token，使用Session认证（登录状态已保持）")
        TokenStore.set_token(username, "SESSION_AUTH")

    return token

#前置：登录管理员账号获取 token
@pytest.fixture(scope="session")
def admin_token():
    """
    会话级 fixture：确保 test_0006 是管理员，登录后返回 admin token
    """
    from core.db_handler import db
    username = "test_0006"
    password = "123456"

    # 确保 test_0006 是管理员
    try:
        db.execute("UPDATE user SET is_admin=1 WHERE username=%s", (username,))
        print(f"\n【Fixture】已将 {username} 设为管理员")
    except Exception as e:
        print(f"\n【Fixture】设置管理员失败: {e}")

    # 重新登录获取含 is_admin=1 的 JWT
    print(f"\n【Fixture】正在登录管理员账号...")
    client = RequestsClient()
    client.url = setting.BASE_URL + '/login'
    client.method = "post"
    client.json = {"username": username, "password": password}

    resp = client.send()
    resp_json = resp.json()
    extractor = JsonPathExtractor()
    token = extractor.extract(resp_json, "$.data.token")

    if token:
        print(f"【Fixture】Admin Token获取成功：{token[:20]}...")
    return token

def _cleanup(db, username):
    """清理指定用户的测试数据"""
    try:
        user = db.query("SELECT id FROM user WHERE username=%s", args=(username,), one=True)
        if user:
            uid = user["id"]
            db.execute("DELETE FROM cart WHERE user_id=%s", (uid,))
            db.execute("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE user_id=%s)", (uid,))
            db.execute("DELETE FROM review WHERE user_id=%s", (uid,))
            db.execute("DELETE FROM after_sale WHERE user_id=%s", (uid,))
            db.execute("DELETE FROM orders WHERE user_id=%s", (uid,))
            db.execute("DELETE FROM address WHERE user_id=%s AND is_default=0", (uid,))
            db.execute("UPDATE user SET is_member=0, member_expire=NULL WHERE id=%s", (uid,))
        db.execute("UPDATE goods SET stock=100 WHERE stock=0")
        db.execute("DELETE FROM user WHERE username LIKE 'test_flow_%'")
        print(f"【Fixture】测试数据清理完成")
    except Exception as e:
        print(f"【Fixture】清理失败: {e}")



@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """前置：清理上次残留  →  后置：清理本次产生的测试数据"""
    from core.db_handler import db
    username = "test_0006"

    _cleanup(db, username)   # 前置
    yield                    # 跑所有测试
    _cleanup(db, username)   # 后置
