""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from core.api_client import RequestsClient
from core import setting
from service.order_service import OrderService
from core.db_handler import db

def _new_order(token, gid=1, qty=1):
    return OrderService().create(goods_id=gid, quantity=qty, token=token).json()["data"]["order_id"]

@allure.feature("order模块")
@pytest.mark.parametrize("case", read_yaml_testcases('order/order_pay'))
def test_order_pay(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    oid = d.get("order_id") or _new_order(login_token)
    
    resp = OrderService().pay(oid, token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    if expected["code"] == 200:
        # DB assertion: verify order status changed to 'paid'
        status_row = db.query("SELECT status FROM orders WHERE id=%s", args=(oid,), one=True)
        assume(status_row is not None, f"订单 {oid} 应在数据库中存在")
        assume(status_row["status"] == "paid", f"订单状态应为paid，实际={status_row['status']}")
