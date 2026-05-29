import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.user_api import UserApi
from common.jsonpath_utils import JsonPathExtractor
from common.yaml_driven import read_yaml_testcases
from common.api_client import TokenStore
from common.db_handler import db
import pytest
import allure
from pytest_assume.plugin import assume

# 读取 YAML 测试数据
test_data = read_yaml_testcases('login')


@allure.feature("登录接口")
@allure.story("YAML数据驱动测试")
@pytest.mark.parametrize("case", test_data)
def test_login_yaml(case):
    """
    使用 YAML 数据驱动的登录测试
    """
    name = case['name']
    username = case['username']
    password = case['password']
    expected = case['expected']

    user_api = UserApi()

    with allure.step(f"步骤1：发送登录请求 - {name}"):
        # 使用封装好的 API 对象，而不是手动构建请求
        resp = user_api.login(
            username=username,
            password=password,
            token=TokenStore.get_token(username)
        )
        resp_json = resp.json()
        print(f"\n【{name}】响应：{resp_json}")

    with allure.step("步骤2：断言结果"):
        # 断言 code
        actual_code = resp_json.get("code")
        expected_code = expected.get("code")
        assume(actual_code == expected_code,
               f"状态码不匹配：期望 {expected_code}，实际 {actual_code}")

        # 断言 msg 或 error
        if "msg" in expected:
            assume(resp_json.get("msg") == expected["msg"])
        if "error" in expected:
            assume(resp_json.get("error") == expected["error"])

    # 只有登录成功才提取 token 和查数据库
    if actual_code == 200:
        with allure.step("步骤3：提取并存储Token"):
            extractor = JsonPathExtractor()
            token = extractor.extract(resp_json, "$.data.token")

            if token:
                TokenStore.set_token(username, token)
                print(f"Token提取成功：{token[:20]}...")
                allure.attach(token, name="提取的Token", attachment_type=allure.attachment_type.TEXT)

        with allure.step("步骤4：数据库断言"):
            sql = "SELECT * FROM user WHERE username = %s"
            user_data = db.query(sql, args=(username,))

            assume(user_data is not None, f"数据库中未找到用户: {username}")
            assume(user_data["username"] == username)
            print(f"数据库验证成功：用户 {username} 存在")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])