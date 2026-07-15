""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.order_service import OrderService
from core.api_client import RequestsClient
from core import setting

def _ensure_address(token):
    c = RequestsClient()
    c.url = f"{setting.BASE_URL}/api/address/list"
    c.method = "get"
    c.headers = {"sessionToken": token}
    if not c.send().json().get("data", {}).get("list", []):
        c.url = f"{setting.BASE_URL}/api/address/add"
        c.method = "post"
        c.headers = {"sessionToken": token}
        c.json = {"address": "订单测试", "contact": "测", "phone": "13800138000"}
        c.send()

def _new_order(token, gid=1, qty=1):
    _ensure_address(token)
    return OrderService().create(goods_id=gid, quantity=qty, token=token).json()["data"]["order_id"]

def _new_paid_order(token):
    oid = _new_order(token)
    OrderService().pay(oid, token=token)
    return oid

@allure.feature("order模块")
@pytest.mark.parametrize("case", read_yaml_testcases('order/order_create'))
def test_order_create(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    
    _ensure_address(login_token)
    resp = OrderService().create(goods_id=d.get('goods_id'), quantity=d.get('quantity', 1), token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    if expected["code"] == 200:
        assume("order_id" in resp_json.get("data", {}))
