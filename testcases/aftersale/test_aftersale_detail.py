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
@pytest.mark.parametrize("case", read_yaml_testcases('aftersale/aftersale_detail'))
def test_aftersale_detail(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    
    if d.get("id") == 99999:
        resp = AfterSaleService().get_detail(99999, token=login_token)
    else:
        resp = AfterSaleService().get_list(token=login_token)
        items = resp.json().get("data", {}).get("list", [])
        if items:
            resp = AfterSaleService().get_detail(items[0]["id"], token=login_token)
        else:
            oid, gid = _completed_order(login_token)
            aid = AfterSaleService().apply(order_id=oid, goods_id=gid, reason='详情测试', amount=1.0, atype='refund', token=login_token).json()["data"]["id"]
            resp = AfterSaleService().get_detail(aid, token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
