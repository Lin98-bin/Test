#让你能操作Python 解释器的环境、路径
import sys
#帮你找当前文件在哪里
import os
#把这个文件夹，加入 Python 的搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#导入请求封装里面的请求类，以及全局的token
from common.api_client import RequestsClient, sessionToken
#导入数据驱动里面的读取excel的读取方法
from common.data_driven import read_excel
#导入pytest中的assume
from pytest_assume.plugin import assume
#数据库封装方法导入
from common.db_handler import DBHandler
#导入数据库对象
from common.db_handler import db
from common.environment import BASE_URL,COMMON_HEADERS


#导入pytest
import pytest
#导入requests
import requests
import pytest
#导入pymysql连接数据库
import pymysql
#导入allure，生成allure报告
import allure
test_data = read_excel(file_path=r'E:\soft\test.xlsx', sheet_name='Sheet1')
# 登录函数
# ====================== 在这里加 Allure 装饰器 ======================
@allure.parent_suite("注册接口测试套-自己练习")
@allure.suite("beta") # 这行是顶层！
@allure.suite("测试接口")
@allure.epic("用户模块")
@allure.feature("登录接口")
@allure.story("用户登录")
@allure.title("登录用例：{casename}")
@allure.severity(allure.severity_level.CRITICAL)
# ==================================================================

@pytest.mark.beta_run  # 专属标记：只有beta环境执行
@pytest.mark.parametrize("casename,username,password,code,msg", test_data)
def test_login(casename, username, password, code, msg):
    with allure.step("步骤1：构造登录请求"):
        test_login=RequestsClient()
        test_login.url=BASE_URL+'/login'
        test_login.method="post"
        test_login.headers = {

                "sessionToken":sessionToken
        }
        test_login.json = {
            "username": username,
            "password": str(password)
        }
    with allure.step("步骤2：发送请求"):
        test_login.resp=test_login.send()
        test_login.resp_json = test_login.resp.json()
        # print(test_login.resp_json)
    with allure.step("步骤3：断言结果"):
        #业务断言
        #返回码code断言
        assume (test_login.resp_json.get("code") == 200)
        #msg断言
        assume(test_login.resp_json.get("msg")=='登录成功')


if __name__ == '__main__':
    test_login()