""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.aftersale_service import AfterSaleService
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
        c.json = {"address": "售后测试", "contact": "测", "phone": "13800138000"}
        c.send()

def _completed_order(token, gid=1):
    _ensure_address(token)
    oid = OrderService().create(goods_id=gid, quantity=1, token=token).json()["data"]["order_id"]
    OrderService().pay(oid, token=token)
    c = RequestsClient()
    c.url = f"{setting.BASE_URL}/api/order/confirm/{oid}"
    c.method = "put"
    c.headers = {"sessionToken": token}
    c.send()
    return oid, gid

@allure.feature("aftersale模块")
@pytest.mark.parametrize("case", read_yaml_testcases('aftersale/aftersale_apply'))
def test_aftersale_apply(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    oid, gid = _completed_order(login_token)
    
    resp = AfterSaleService().apply(order_id=oid, goods_id=gid, reason=d.get('reason', ''), amount=d.get('amount', 1.0), atype=d.get('atype', 'refund'), token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
