""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.aftersale_service import AfterSaleService
from core.db_handler import db

@allure.feature("aftersale模块")
@pytest.mark.parametrize("case", read_yaml_testcases('aftersale/aftersale_list'))
def test_aftersale_list(case, login_token):
    allure.dynamic.title(case["name"])
    expected = case['expected']
    
    resp = AfterSaleService().get_list(token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    assume("list" in resp_json.get("data", {}))

    # DB 断言：验证 test_0006 用户的售后记录数量
    if resp_json.get("code") == 200:
        db_count = db.query(
            "SELECT COUNT(*) AS cnt FROM after_sale WHERE user_id=(SELECT id FROM user WHERE username='test_0006')",
            one=True
        )
        assume(db_count is not None, "DB: after_sale 表查询不应为空")
        assume(db_count["cnt"] > 0, f"DB: test_0006 的售后记录数量应大于0, 实际={db_count['cnt']}")
