"""管理员发货 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.admin_service import AdminService
from service.order_service import OrderService
from core.api_client import RequestsClient
from utils.yaml_utils import read_yaml_testcases
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
        c.json = {"address": "管理测试", "contact": "测", "phone": "13800138000"}
        c.send()


def _new_paid_order(token):
    _ensure_address(token)
    oid = OrderService().create(goods_id=1, quantity=1, token=token).json()["data"]["order_id"]
    OrderService().pay(oid, token=token)
    return oid


@allure.feature("管理员模块")
@allure.story("发货")
@pytest.mark.parametrize("case", read_yaml_testcases('admin/admin_order_ship'))
def test_admin_order_ship(case, login_token, admin_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']

    # 用户下单并支付
    oid = d.get("order_id") or _new_paid_order(login_token)
    tracking = d.get("tracking", "TEST00001")

    # 管理员发货
    resp = AdminService().ship_order(oid, tracking=tracking, token=admin_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
