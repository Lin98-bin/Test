"""修改用户信息 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from core.api_client import RequestsClient
from utils.yaml_utils import read_yaml_testcases
from core import setting


@allure.feature("用户模块")
@allure.story("修改用户信息")
@pytest.mark.parametrize("case", read_yaml_testcases('user/user_update'))
def test_user_update(case, login_token):
    allure.dynamic.title(case['name'])
    d = case.get('data', {})
    expected = case['expected']

    client = RequestsClient()
    client.url = f"{setting.BASE_URL}/api/user/update"
    client.method = "put"
    client.headers = {"sessionToken": login_token}
    client.json = {"nickname": d.get("nickname", "测试")}
    resp = client.send()
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
