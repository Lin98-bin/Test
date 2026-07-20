import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from service.user_service import UserService
from utils.yaml_utils import read_yaml_testcases
from core.db_handler import db
from pytest_assume.plugin import assume

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

    with allure.step("步骤1：发送登录请求"):
        resp = UserService().login(username=case['username'], password=str(case['password']))
        resp_json = resp.json()

    with allure.step("步骤2：断言结果"):
        assume(resp_json.get("code") == expected["code"],
               f"期望 code={expected['code']}，实际={resp_json.get('code')}")
        if "msg" in expected:
            assume(resp_json.get("msg") in (expected["msg"], "ok"),
                   f"期望 msg={expected['msg']}，实际={resp_json.get('msg')}")
        if "error" in expected:
            assume(resp_json.get("error") == expected["error"],
                   f"期望 error={expected['error']}，实际={resp_json.get('error')}")
        if expected["code"] == 200:
            # DB assertion: verify user exists in database
            user = db.query("SELECT id FROM user WHERE username=%s", args=(case['username'],), one=True)
            assume(user is not None, f"用户 {case['username']} 应在数据库中存在")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
