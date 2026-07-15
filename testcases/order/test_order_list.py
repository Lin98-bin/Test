""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from core.api_client import RequestsClient
from core import setting

@allure.feature("order模块")
@pytest.mark.parametrize("case", read_yaml_testcases('order/order_list'))
def test_order_list(case, login_token):
    allure.dynamic.title(case["name"])
    expected = case['expected']
    p = case.get('params', {})
    
    url = f"{setting.BASE_URL}/api/order/list"
    if p.get("status"):
        url += f"?status={p['status']}"
    c = RequestsClient()
    c.url = url
    c.method = "get"
    c.headers = {"sessionToken": login_token}
    resp = c.send()
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    assume("list" in resp_json.get("data", {}))
