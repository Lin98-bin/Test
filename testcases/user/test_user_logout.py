"""退出登录 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.user_service import UserService
from utils.yaml_utils import read_yaml_testcases


@allure.feature("用户模块")
@allure.story("退出登录")
@pytest.mark.parametrize("case", read_yaml_testcases('user/user_logout'))
def test_user_logout(case, login_token):
    allure.dynamic.title(case['name'])
    expected = case['expected']

    resp = UserService().logout(token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
