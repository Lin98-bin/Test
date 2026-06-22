import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.user_service import UserService
from core.context import TokenStore
from utils.jsonpath_utils import JsonPathExtractor
from utils.yaml_utils import read_yaml_testcases
from utils.db_handler import db
import pytest
import allure
from pytest_assume.plugin import assume

# 从 YAML 读取测试数据
test_data = read_yaml_testcases('login')
@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("test全量用例")
@allure.epic("用户模块")
@allure.feature("登录接口")
@allure.story("用户登录")
@allure.tag("test", "beta")
@pytest.mark.test
@pytest.mark.beta
@allure.title("登录用例：{case[name]}")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("case", test_data)
def test_login(case):
    user_service = UserService()
    
    username = case['username']
    password = case['password']
    expected = case['expected']
    
    with allure.step(f"步骤1：发送登录请求 - {case['name']}"):
        # 使用封装好的 Service 对象
        resp = user_service.login(
            username=username,
            password=password,
            token=TokenStore.get_token(username)
        )
        resp_json = resp.json()

    with allure.step("步骤2：断言结果"):
        actual_code = resp_json.get("code")
        expected_code = expected.get("code")
        assume(actual_code == expected_code, f"状态码不匹配：期望 {expected_code}，实际 {actual_code}")
        
        if "msg" in expected:
            assume(resp_json.get("msg") == expected["msg"])
        if "error" in expected:
            assume(resp_json.get("error") == expected["error"])

    # 只有成功登录才提取 Token 和查数据库
    if actual_code == 200:
        with allure.step("步骤3：提取并存储Token"):
            extractor = JsonPathExtractor()
            token = extractor.extract(resp_json, "$.data.token")

            if token is not None and token != "":
                TokenStore.set_token(username, token)
                print(f"Token提取成功：{token[:20]}...")
                allure.attach(token, name="提取的Token", attachment_type=allure.attachment_type.TEXT)

        with allure.step("步骤4：数据库断言 - 验证用户信息"):
            sql = "SELECT * FROM user WHERE username = %s"
            user_data = db.query(sql, args=(username,))
            assume(user_data is not None, f"数据库中未找到用户: {username}")
            assume(user_data["username"] == username)
            print(f"数据库查询成功：用户 {username} 存在")

if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
