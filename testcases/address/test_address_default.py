"""设为默认地址 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.address_service import AddressService
from utils.yaml_utils import read_yaml_testcases
from core.db_handler import db


def _get_address_id(token):
    resp = AddressService().get_list(token=token)
    addrs = resp.json().get("data", {}).get("list", [])
    if addrs:
        return addrs[0]["id"]
    resp = AddressService().add(address="测试地址", contact="测试", phone="13800138001", token=token)
    return resp.json()["data"]["address_id"]


@allure.parent_suite("接口自动化测试-自己练习")
@allure.epic("用户模块")
@allure.feature("收货地址接口")
@allure.story("设为默认地址")
@pytest.mark.test
@pytest.mark.parametrize("case", read_yaml_testcases('address/address_default'))
def test_set_default_address(case, login_token):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']
    case_data = case.get("data", {})
    addr_id = case_data.get("id") or _get_address_id(login_token)

    with allure.step(f"设为默认地址 id={addr_id}"):
        resp = AddressService().set_default(addr_id=addr_id, token=login_token)

    with allure.step("断言结果"):
        assume(resp.json().get("code") == expected["code"])

    if expected["code"] == 200:
        with allure.step("数据库断言"):
            addr = db.query("select is_default from address where id = %s", args=(addr_id,), one=True)
            assume(addr is not None)
            assume(addr["is_default"] == 1)
