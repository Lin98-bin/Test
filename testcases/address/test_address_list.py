"""地址列表 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.address_service import AddressService
from utils.yaml_utils import read_yaml_testcases
from core.db_handler import db


@allure.parent_suite("接口自动化测试-自己练习")
@allure.epic("用户模块")
@allure.feature("收货地址接口")
@allure.story("获取地址列表")
@pytest.mark.test
@pytest.mark.parametrize("case", read_yaml_testcases('address/address_list'))
def test_address_list(case, login_token):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']

    with allure.step("发送获取地址列表请求"):
        resp = AddressService().get_list(token=login_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == expected["code"])
        assume(isinstance(resp_json.get("data", {}).get("list", []), list))

        # DB 断言：验证 test_0006 用户的地址数量
        if resp_json.get("code") == 200:
            db_count = db.query(
                "SELECT COUNT(*) AS cnt FROM address WHERE user_id=(SELECT id FROM user WHERE username='test_0006')",
                one=True
            )
            assume(db_count is not None, "DB: address 表查询不应为空")
            assume(db_count["cnt"] > 0, f"DB: test_0006 的地址数量应大于0, 实际={db_count['cnt']}")
