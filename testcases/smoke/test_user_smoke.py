"""用户模块 — 冒烟用例"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import allure
from pytest_assume.plugin import assume
from service.user_service import UserService
from common.db_handler import db


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("用户模块")
@allure.feature("用户信息")
@allure.story("获取用户信息")
@allure.title("用户信息冒烟用例")
def test_user_info(login_token):
    with allure.step("获取用户信息"):
        resp = UserService().get_info(token=login_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        assume(resp_json.get("data", {}).get("username") == "test_0006")


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("用户模块")
@allure.feature("用户信息")
@allure.story("修改用户信息")
@allure.title("修改昵称冒烟用例")
def test_user_update(login_token):
    with allure.step("修改昵称"):
        resp = UserService().get_info(token=login_token)
        # 注意：update 接口在 service 里没封装，直接调用
        from core.api_client import RequestsClient
        from core import setting
        client = RequestsClient()
        client.url = f"{setting.BASE_URL}/api/user/update"
        client.method = "put"
        client.headers = {"sessionToken": login_token}
        client.json = {"nickname": "冒烟测试"}
        resp = client.send()
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)

    with allure.step("数据库断言：昵称已更新"):
        user = db.query("select nickname from user where username = 'test_0006'", one=True)
        assume(user is not None, "数据库未查到用户 test_0006")
        assume(user["nickname"] == "冒烟测试", f"昵称未更新: 期望=冒烟测试, 实际={user['nickname']}")


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("用户模块")
@allure.feature("退出登录")
@allure.story("退出登录")
@allure.title("退出登录冒烟用例")
def test_user_logout(login_token):
    with allure.step("退出登录"):
        resp = UserService().logout(token=login_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
