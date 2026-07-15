"""处理售后 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from core.api_client import RequestsClient
from service.admin_service import AdminService
from service.order_service import OrderService
from service.aftersale_service import AfterSaleService
from utils.yaml_utils import read_yaml_testcases
from core import setting


def _ensure_address(token):
    c = RequestsClient()
    c.url = f"{setting.BASE_URL}/api/address/list"; c.method = "get"; c.headers = {"sessionToken": token}
    if not c.send().json().get("data", {}).get("list", []):
        c.url = f"{setting.BASE_URL}/api/address/add"; c.method = "post"; c.headers = {"sessionToken": token}
        c.json = {"address": "管理测试", "contact": "测", "phone": "13800138000"}; c.send()

def _completed_order(token, gid=1):
    _ensure_address(token)
    oid = OrderService().create(goods_id=gid, quantity=1, token=token).json()["data"]["order_id"]
    OrderService().pay(oid, token=token)
    c = RequestsClient()
    c.url = f"{setting.BASE_URL}/api/order/confirm/{oid}"; c.method = "put"; c.headers = {"sessionToken": token}
    c.send()
    return oid, gid


@allure.feature("管理员模块")
@allure.story("处理售后")
@pytest.mark.parametrize("case", read_yaml_testcases('admin/admin_aftersale_handle'))
def test_admin_aftersale_handle(case, login_token, admin_token):
    allure.dynamic.title(case['name'])
    d = case.get('data', {})
    expected = case['expected']

    oid, gid = _completed_order(login_token, gid=2)
    apply_resp = AfterSaleService().apply(
        order_id=oid, goods_id=gid, reason="管理处理测试",
        amount=1.0, atype="refund", token=login_token
    )
    as_id = apply_resp.json()["data"]["id"]

    resp = AdminService().handle_aftersale(
        as_id, action=d.get("action"), reply=d.get("reply", ""), token=admin_token
    )
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
