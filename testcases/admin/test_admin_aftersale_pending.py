"""查看待处理售后 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.admin_service import AdminService
from utils.yaml_utils import read_yaml_testcases
from core.db_handler import db


@allure.feature("管理员模块")
@allure.story("待处理售后")
@pytest.mark.parametrize("case", read_yaml_testcases('admin/admin_aftersale_pending'))
def test_admin_aftersale_pending(case, admin_token):
    allure.dynamic.title(case['name'])
    expected = case['expected']

    resp = AdminService().get_pending_aftersale(token=admin_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])

    # DB 断言：验证待处理售后数量
    if resp_json.get("code") == 200:
        db_count = db.query("SELECT COUNT(*) AS cnt FROM after_sale WHERE status='pending'", one=True)
        assume(db_count is not None, "DB: after_sale 表查询不应为空")
        assume(db_count["cnt"] > 0, f"DB: pending 状态售后数量应大于0, 实际={db_count['cnt']}")
