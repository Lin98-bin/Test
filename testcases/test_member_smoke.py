"""会员模块 — 冒烟用例"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import allure
from pytest_assume.plugin import assume
from service.member_service import MemberService


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("会员模块")
@allure.feature("会员信息")
@allure.story("获取会员信息")
@allure.title("会员信息冒烟用例")
def test_member_info(login_token):
    with allure.step("获取会员信息"):
        resp = MemberService().get_info(token=login_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        assume("is_member" in resp_json.get("data", {}))


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("会员模块")
@allure.feature("开通会员")
@allure.story("开通会员")
@allure.title("开通会员冒烟用例")
def test_member_activate(login_token):
    with allure.step("开通 1 个月会员"):
        resp = MemberService().activate(months=1, token=login_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        assume(resp_json.get("data", {}).get("is_member") is True)


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
