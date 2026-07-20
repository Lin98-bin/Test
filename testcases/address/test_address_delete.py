"""删除地址 — 数据驱动用例"""
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
@allure.story("删除地址")
@pytest.mark.test
@pytest.mark.parametrize("case", read_yaml_testcases('address/address_delete'))
def test_address_delete(case, login_token):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']
    case_data = case.get("data", {})
    addr_id = case_data.get("id")

    if addr_id and addr_id == 99999:
        pass
    else:
        resp = AddressService().add(address="临时地址", contact="临", phone="13800138002", token=login_token)
        addr_id = resp.json()["data"]["address_id"]

    with allure.step(f"删除地址 id={addr_id}"):
        resp = AddressService().delete(addr_id=addr_id, token=login_token)

    with allure.step("断言结果"):
        assume(resp.json().get("code") == expected["code"])

    if expected["code"] == 200:
        with allure.step("数据库断言-地址已删除"):
            deleted = db.query("select * from address where id = %s", args=(addr_id,), one=True)
            assume(deleted is None, f"地址应已删除，但仍查到 id={addr_id}")
