""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from core.api_client import RequestsClient
from core import setting
from service.order_service import OrderService

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
@pytest.mark.parametrize("case", read_yaml_testcases('order/order_cancel'))
def test_order_cancel(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    oid = _new_order(login_token)
    
    c = RequestsClient()
    c.url = f"{setting.BASE_URL}/api/order/cancel/{oid}"
    c.method = "put"
    c.headers = {"sessionToken": login_token}
    c.json = {"reason": d.get("reason", "")}
    resp = c.send()
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
