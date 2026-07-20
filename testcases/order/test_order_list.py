""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.order_service import OrderService
from core.db_handler import db

@allure.feature("order模块")
@pytest.mark.parametrize("case", read_yaml_testcases('order/order_list'))
def test_order_list(case, login_token):
    allure.dynamic.title(case["name"])
    expected = case['expected']
    p = case.get('params', {})

    status = p.get("status") if p else None
    resp = OrderService().get_list(status=status, token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    assume("list" in resp_json.get("data", {}))
    if expected["code"] == 200:
        # DB assertion: verify user has at least one order
        result = db.query("SELECT COUNT(*) as cnt FROM orders WHERE user_id=(SELECT id FROM user WHERE username='test_0006')", one=True)
        assume(result["cnt"] > 0, "数据库中应有至少一条订单记录")
