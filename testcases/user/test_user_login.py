import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.api_client import RequestsClient
from utils.yaml_utils import read_yaml_testcases
from pytest_assume.plugin import assume
from core import setting

import pytest
import allure

pytestmark = pytest.mark.run(order=2)  # 登录后跑，等注册先创建用户

test_data = read_yaml_testcases('user/user_login')


@allure.parent_suite("注册接口测试套-自己练习")
@allure.suite("beta核心用例")
@allure.epic("用户模块")
@allure.feature("登录接口")
@allure.story("用户登录")
@allure.severity(allure.severity_level.CRITICAL)

@pytest.mark.beta_run
@pytest.mark.parametrize("case", test_data)
def test_login(case):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']

    with allure.step("步骤1：构造登录请求"):
        client = RequestsClient()
        client.url = setting.BASE_URL + '/login'
        client.method = "post"
        client.headers = setting.COMMON_HEADERS.copy()
        client.json = {
            "username": case['username'],
            "password": str(case['password'])
        }

    with allure.step("步骤2：发送请求"):
        resp = client.send()
        resp_json = resp.json()

    with allure.step("步骤3：断言结果"):
        assume(resp_json.get("code") == expected["code"],
               f"期望 code={expected['code']}，实际={resp_json.get('code')}")
        if "msg" in expected:
            assume(resp_json.get("msg") in (expected["msg"], "ok"),
                   f"期望 msg={expected['msg']}，实际={resp_json.get('msg')}")
        if "error" in expected:
            assume(resp_json.get("error") == expected["error"],
                   f"期望 error={expected['error']}，实际={resp_json.get('error')}")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
