"""修改用户信息 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.user_service import UserService
from utils.yaml_utils import read_yaml_testcases
from core.db_handler import db


@allure.feature("用户模块")
@allure.story("修改用户信息")
@pytest.mark.parametrize("case", read_yaml_testcases('user/user_update'))
def test_user_update(case, login_token):
    allure.dynamic.title(case['name'])
    d = case.get('data', {})
    expected = case['expected']

    resp = UserService().update_info(nickname=d.get("nickname", "测试"), token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    if expected["code"] == 200:
        # DB assertion: verify nickname updated in database
        nickname = d.get("nickname", "测试")
        user = db.query("SELECT nickname FROM user WHERE username='test_0006'", one=True)
        assume(user is not None, "test_0006 应在数据库中存在")
        assume(user["nickname"] == nickname, f"数据库nickname应为{nickname}，实际={user['nickname']}")
