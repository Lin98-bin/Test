"""地址列表 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from core.api_client import RequestsClient
from utils.yaml_utils import read_yaml_testcases
from core import setting


@allure.parent_suite("接口自动化测试-自己练习")
@allure.epic("用户模块")
@allure.feature("收货地址接口")
@allure.story("获取地址列表")
@pytest.mark.test
@pytest.mark.parametrize("case", read_yaml_testcases('address/address_list'))
def test_address_list(case, login_token):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']

    with allure.step("发送获取地址列表请求"):
        client = RequestsClient()
        client.url = f"{setting.BASE_URL}/api/address/list"
        client.method = "get"
        client.headers = {"sessionToken": login_token}
        resp = client.send()
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == expected["code"])
        assume(isinstance(resp_json.get("data", {}).get("list", []), list))
