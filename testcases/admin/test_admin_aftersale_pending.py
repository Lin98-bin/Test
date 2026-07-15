"""查看待处理售后 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.admin_service import AdminService
from utils.yaml_utils import read_yaml_testcases


@allure.feature("管理员模块")
@allure.story("待处理售后")
@pytest.mark.parametrize("case", read_yaml_testcases('admin/admin_aftersale_pending'))
def test_admin_aftersale_pending(case, admin_token):
    allure.dynamic.title(case['name'])
    expected = case['expected']

    resp = AdminService().get_pending_aftersale(token=admin_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
