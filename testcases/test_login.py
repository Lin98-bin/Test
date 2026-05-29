import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.user_api import UserApi
from common.api_client import TokenStore
from common.jsonpath_utils import JsonPathExtractor
from common.data_driven import read_excel
from common.db_handler import db
import pytest
import allure
from pytest_assume.plugin import assume

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
test_data = read_excel(file_path=os.path.join(BASE_DIR, 'data', 'test.xlsx'), sheet_name='Sheet1')

@allure.parent_suite("注册接口测试套-自己练习")
@allure.suite("beta核心用例")
@allure.epic("用户模块")
@allure.feature("登录接口")
@allure.story("用户登录")
@allure.title("登录用例：{casename}")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.beta_run
@pytest.mark.parametrize("casename,username,password,code,msg", test_data)
def test_login(casename, username, password, code, msg):
    user_api = UserApi()
    
    with allure.step("步骤1：发送登录请求"):
        # 使用封装好的 API 对象
        resp = user_api.login(
            username=username,
            password=password,
            token=TokenStore.get_token(username)
        )
        resp_json = resp.json()

    with allure.step("步骤2：断言结果"):
        assume(resp_json.get("code") == 200)
        assume(resp_json.get("msg") == '登录成功')

    with allure.step("步骤3：提取并存储Token"):
        extractor = JsonPathExtractor()
        token = extractor.extract(resp_json, "$.data.token")

        if token:
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
