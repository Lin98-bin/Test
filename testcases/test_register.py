import sys
import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.user_api import UserApi
from common.yaml_driven import read_yaml_testcases
from common.db_handler import db
import pytest
import allure
from pytest_assume.plugin import assume

# 从 YAML 读取测试数据
test_data = read_yaml_testcases('register')

@allure.parent_suite("注册接口测试套-自己练习")
@allure.suite("test全量用例")
@allure.epic("用户模块")
@allure.feature("注册接口")
@allure.story("用户注册")
@allure.title("注册用例：{case[name]}")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.test_run
@pytest.mark.parametrize("case", test_data)
def test_register(case):
    user_api = UserApi()
    
    username = case['username']
    password = case['password']
    expected = case['expected']

    with allure.step(f"步骤1：发送注册请求 - {case['name']}"):
        resp = user_api.register(username, password)
        resp_json = resp.json()
        print(f"接口返回：{resp_json}")
        
    with allure.step("步骤2：断言结果"):
        # 断言状态码
        actual_code = resp_json.get("code")
        expected_code = expected.get("code")
        assume(actual_code == expected_code, f"状态码不匹配：期望 {expected_code}，实际 {actual_code}")
        
        # 断言消息
        if "msg" in expected:
            assume(resp_json.get("msg") == expected["msg"])
        if "error" in expected:
            assume(resp_json.get("error") == expected["error"])
            
    # 只有成功注册才进行数据库校验
    if actual_code == 200:
        with allure.step("步骤3：数据库校验"):
            sql = "SELECT * FROM user WHERE username = %s"
            user = db.query(sql, [username])
            assume(user is not None, f"数据库中未找到用户: {username}")
            assume(user["username"] == username)

if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
