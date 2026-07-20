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
from core.db_handler import db

def _new_paid_order(token):
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

    # DB 断言：验证订单状态已更新为 shipped 且 tracking_no 匹配
    if resp_json.get("code") == 200:
        db_order = db.query("SELECT status, tracking_no FROM orders WHERE id=%s", args=(oid,), one=True)
        assume(db_order is not None, f"DB: 订单 id={oid} 应存在")
        assume(db_order.get("status") == 'shipped', f"DB: status 应为 'shipped', 实际={db_order.get('status')}")
        assume(db_order.get("tracking_no") == tracking,
               f"DB: tracking_no 应匹配, 期望={tracking}, 实际={db_order.get('tracking_no')}")
