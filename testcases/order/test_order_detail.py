""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.order_service import OrderService
from core.api_client import RequestsClient
from core import setting
from core.db_handler import db

def _new_order(token, gid=1, qty=1):
    return OrderService().create(goods_id=gid, quantity=qty, token=token).json()["data"]["order_id"]

@allure.feature("order模块")
@pytest.mark.parametrize("case", read_yaml_testcases('order/order_detail'))
def test_order_detail(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    oid = d.get("order_id") or _new_order(login_token)
    
    c = RequestsClient()
    c.url = f"{setting.BASE_URL}/api/order/detail/{oid}"
    c.method = "get"
    c.headers = {"sessionToken": login_token}
    resp = c.send()
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    if expected["code"] == 200:
        assume(resp_json.get("data", {}).get("id") == oid)
        # DB assertion: verify order exists in database with valid status
        order = db.query("SELECT * FROM orders WHERE id=%s", args=(oid,), one=True)
        assume(order is not None, f"订单 {oid} 应在数据库中存在")
        assume(order.get("id") == oid, f"订单ID应匹配")
        assume(order.get("status") in ("pending", "paid", "cancelled", "received", "shipped"),
               f"订单状态应有效，实际={order.get('status')}")
