import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.user_api import UserApi
from common.data_driven import read_excel
from common.db_handler import db
import pytest
import allure
from pytest_assume.plugin import assume

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 动态拼接路径，确保在 Jenkins 或其他电脑上都能运行
test_data = read_excel(file_path=os.path.join(BASE_DIR, 'data', 'test.xlsx'), sheet_name='Sheet1')

@allure.parent_suite("注册接口测试套-自己练习")
@allure.suite("test全量用例")
@allure.epic("用户模块")
@allure.feature("注册接口")
@allure.story("用户注册")
@allure.title("注册用例：{casename}")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.test_run
@pytest.mark.parametrize("casename,username,password,code,msg", test_data)
def test_register(casename, username, password, code, msg):
    user_api = UserApi()
    
    with allure.step("步骤1：发送注册请求"):
        resp = user_api.register(username, password)
        resp_json = resp.json()
        print(f"接口返回{resp_json}")
        
    with allure.step("步骤2：断言结果"):
        assume(resp_json.get("code") == 200)
        assume(resp_json.get("msg") == '注册成功')
        
    with allure.step("步骤3：数据库校验"):
        sql = "SELECT * FROM user WHERE username = %s"
        user = db.query(sql, [username])
        assume(user is not None)
        assume(user["username"] == username)

if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
