"""修改地址 — 数据驱动用例"""
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
@allure.story("修改地址")
@pytest.mark.test
@pytest.mark.parametrize("case", read_yaml_testcases('address/address_update'))
def test_address_update(case, login_token):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']
    case_data = case.get("data", {})
    addr_id = case_data.get("id") or _get_address_id(login_token)

    with allure.step(f"修改地址 id={addr_id}"):
        resp = AddressService().update(addr_id=addr_id, contact=case_data.get("contact", "修改"), token=login_token)

    with allure.step("断言结果"):
        resp_json = resp.json()
        assume(resp_json.get("code") == expected["code"])

        # DB 断言：验证 contact 已更新
        if resp_json.get("code") == 200:
            contact_val = case_data.get("contact", "修改")
            db_addr = db.query("SELECT contact FROM address WHERE id=%s", args=(addr_id,), one=True)
            assume(db_addr is not None, f"DB: 地址 id={addr_id} 应存在")
            assume(db_addr.get("contact") == contact_val,
                   f"DB: contact 应匹配, 期望={contact_val}, 实际={db_addr.get('contact')}")
