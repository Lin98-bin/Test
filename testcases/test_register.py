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
# ====================== 在这里加 Allure 装饰器 ======================
@allure.parent_suite("注册接口测试套-自己练习")  # 这行是顶层！
@allure.suite("测试接口")
@allure.epic("用户模块")           # 一级大模块
@allure.feature("注册接口")        # 二级功能
@allure.story("用户注册")          # 三级场景
@allure.title("注册用例：{casename}")  # 用例标题（动态显示）
@allure.severity(allure.severity_level.CRITICAL)  # 严重级别

# ==================================================================
#注册函数
@pytest.mark.parametrize("casename,username,password,code,msg", test_data)
def test_register(casename, username, password, code, msg):
    with allure.step("步骤1：构造请求"):
        test_register=RequestsClient()
        test_register.url=BASE_URL+'/register'
        test_register.method="post"
        test_register.headers = {
        "Accept": "application/json",
        }

        test_register.json = {
            "username": username,
            "password": str(password)
        }
    with allure.step("步骤2：发送请求"):
        resp=test_register.send()
        resp_json = resp.json()
        print(f"接口返回{resp_json}")
    with allure.step("步骤3：断言结果"):
        #业务断言
        #断言返回码
        assume (resp_json.get("code") == 200)
        #断言返回注册信息
        assume (resp_json.get("msg") == '注册成功！')
    with allure.step("步骤4：数据库断言"):
        #数据库断言
        #先查数据
        sql="select * from user where username= %s"
        user=db.query(sql,args=(username,),one=True)

        #数据库断言
        #如果数据库查到了改用户就通过，查不到就输出：数据库未查到用户
        assume(user is not None,
               f"数据库未查到用户 {username}")
        # 如果数据库查到了改用户就通过，查不到就输出：用户名不一致
        assume(user["username"] == username,
               "用户名不一致")





if __name__ == '__main__':
    test_register()