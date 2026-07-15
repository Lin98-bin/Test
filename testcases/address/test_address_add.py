"""新增地址 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.user_service import UserService
from utils.yaml_utils import read_yaml_testcases
from common.db_handler import db


@allure.parent_suite("接口自动化测试-自己练习")
@allure.epic("用户模块")
@allure.feature("收货地址接口")
@allure.story("新增地址")
@pytest.mark.test
@pytest.mark.parametrize("case", read_yaml_testcases('address/address_add'))
def test_add_address(case, login_token):
    allure.dynamic.title(f"用例：{case['name']}")
    address = case['address']
    contact = case['contact']
    phone = case['phone']
    expected = case['expected']

    with allure.step("发送新增地址请求"):
        resp = UserService().add_address(address_detail=address, contact_name=contact, contact_phone=phone, token=login_token)
        resp_json = resp.json()

    with allure.step("断言响应"):
        assume(resp_json.get("code") == expected["code"], f"期望 code={expected['code']}，实际={resp_json.get('code')}")
        if "msg" in expected:
            assume(resp_json.get("msg") in (expected["msg"], expected.get("msg2", expected["msg"])))
        if "error" in expected:
            assume(resp_json.get("error") == expected["error"])

    if expected["code"] == 200:
        with allure.step("数据库断言"):
            addr = db.query("select * from address where contact = %s and phone = %s order by id desc limit 1", args=(contact, phone), one=True)
            assume(addr is not None, f"数据库未查到地址: {contact}, {phone}")
            assume(addr["address"] == address)
            assume(addr["contact"] == contact)
            assume(addr["phone"] == phone)
