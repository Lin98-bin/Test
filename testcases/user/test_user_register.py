import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import random
import string

from core.api_client import RequestsClient
from utils.yaml_utils import read_yaml_testcases
from pytest_assume.plugin import assume
from common.db_handler import db
from core import setting

import pytest
import allure

pytestmark = pytest.mark.run(order=1)  # 注册先跑，登录后跑

test_data = read_yaml_testcases('user/user_register')


@allure.parent_suite("注册接口测试套-自己练习")
@allure.suite("test全量用例")
@allure.epic("用户模块")
@allure.feature("注册接口")
@allure.story("用户注册")
@allure.severity(allure.severity_level.CRITICAL)

@pytest.mark.test_run
@pytest.mark.parametrize("case", test_data)
def test_register(case):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']
    is_success = (expected.get("code") == 200)

    # 成功场景加随机后缀避免用户名重复
    username = case['username']
    if is_success and username:
        suffix = ''.join(random.choices(string.digits, k=4))
        username = f"{username}_{suffix}"

    with allure.step("步骤1：构造请求"):
        client = RequestsClient()
        client.url = setting.BASE_URL + '/register'
        client.method = "post"
        client.headers = setting.COMMON_HEADERS.copy()
        client.json = {
            "username": username,
            "password": str(case['password'])
        }

    with allure.step("步骤2：发送请求"):
        resp = client.send()
        resp_json = resp.json()
        print(f"接口返回: {resp_json}")

    with allure.step("步骤3：断言结果"):
        assume(resp_json.get("code") == expected["code"],
               f"期望 code={expected['code']}，实际={resp_json.get('code')}")
        if "msg" in expected:
            assume(resp_json.get("msg") in (expected["msg"], "ok"),
                   f"期望 msg={expected['msg']}，实际={resp_json.get('msg')}")
        if "error" in expected:
            assume(resp_json.get("error") == expected["error"],
                   f"期望 error={expected['error']}，实际={resp_json.get('error')}")

    # 成功场景：数据库断言用户确实写入了
    if is_success:
        with allure.step("步骤4：数据库断言"):
            sql = "select * from user where username = %s"
            user = db.query(sql, args=(username,), one=True)
            assume(user is not None, f"数据库未查到用户 {username}")
            assume(user["username"] == username, f"用户名不一致: 期望={username}, 实际={user['username']}")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
