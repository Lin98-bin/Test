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

@allure.feature("order模块")
@pytest.mark.parametrize("case", read_yaml_testcases('order/order_create'))
def test_order_create(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    
    resp = OrderService().create(goods_id=d.get('goods_id'), quantity=d.get('quantity', 1), token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    if expected["code"] == 200:
        assume("order_id" in resp_json.get("data", {}))
        # DB assertion: verify order created in database
        order_id = resp_json["data"]["order_id"]
        order = db.query("SELECT * FROM orders WHERE id=%s", args=(order_id,), one=True)
        assume(order is not None, f"订单 {order_id} 应在数据库中存在")
        assume(order.get("status") == "pending", f"订单状态应为pending，实际={order.get('status')}")
        goods_id = d.get('goods_id')
        quantity = d.get('quantity', 1)
        assume(str(order.get("goods_id")) == str(goods_id), f"goods_id应匹配，期望={goods_id}，实际={order.get('goods_id')}")
        assume(order.get("quantity") == quantity, f"quantity应匹配，期望={quantity}，实际={order.get('quantity')}")
