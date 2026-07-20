"""获取用户信息 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.user_service import UserService
from utils.yaml_utils import read_yaml_testcases
from core.db_handler import db


@allure.feature("用户模块")
@allure.story("获取用户信息")
@pytest.mark.parametrize("case", read_yaml_testcases('user/user_info'))
def test_user_info(case, login_token):
    allure.dynamic.title(case['name'])
    expected = case['expected']

    resp = UserService().get_info(token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    assume(resp_json.get("data", {}).get("username") == "test_0006")
    if expected["code"] == 200:
        # DB assertion: verify user exists in database
        user = db.query("SELECT username, nickname FROM user WHERE username='test_0006'", one=True)
        assume(user is not None, "test_0006 应在数据库中存在")
        assume(user["username"] == "test_0006", "数据库用户名应为test_0006")
