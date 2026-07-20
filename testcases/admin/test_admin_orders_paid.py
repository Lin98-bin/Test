"""查看待发货订单 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.admin_service import AdminService
from utils.yaml_utils import read_yaml_testcases
from core.db_handler import db


@allure.feature("管理员模块")
@allure.story("待发货订单")
@pytest.mark.parametrize("case", read_yaml_testcases('admin/admin_orders_paid'))
def test_admin_orders_paid(case, admin_token):
    allure.dynamic.title(case['name'])
    expected = case['expected']

    resp = AdminService().get_paid_orders(token=admin_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    assume("list" in resp_json.get("data", {}))

    # DB 断言：验证待付款订单数量
    if resp_json.get("code") == 200:
        db_count = db.query("SELECT COUNT(*) AS cnt FROM orders WHERE status='paid'", one=True)
        assume(db_count is not None, "DB: orders 表查询不应为空")
        assume(db_count["cnt"] > 0, f"DB: paid 状态订单数量应大于0, 实际={db_count['cnt']}")
