import sys
#帮你找当前文件在哪里
import os
#把这个文件夹，加入 Python 的搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#导入请求封装里面的请求类，以及全局的token
from core.api_client import RequestsClient
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
@allure.parent_suite("注册接口测试套-自己练习")
@allure.suite("master巡检用例:linchuanbin")
@allure.epic("商品模块")
@allure.feature("商品查询接口")
@allure.story("获取商品列表")
@allure.tag("test", "master")
@pytest.mark.master
@allure.title("查询商品列表用例")
@allure.severity(allure.severity_level.NORMAL)
# ====================== 环境标记（关键！） ======================
# 查询接口是只读的，所以三个环境都可以跑
# ==================================================================
@pytest.mark.prod_run  # 专属标记：只有prod环境执行

def test_query_goods():
    with allure.step("1. 初始化请求"):
        test_check = RequestsClient()
        test_check.method = 'get'
        test_check.url = BASE_URL + "/1/classes/Goods"
        test_check.headers = COMMON_HEADERS.copy()

    with allure.step("2. 发送请求"):
        resp = test_check.send()

    with allure.step("3. 报告附加响应数据"):
        allure.attach(resp.text, "商品列表响应", allure.attachment_type.JSON)
        print("商品接口响应：", resp.text)

    with allure.step("4. 断言校验"):
        # 基础状态码断言
        assert resp.status_code == 200

        # 业务逻辑断言（比你原来的更完善）
        resp_json = resp.json()
        assert resp_json.get("code") == 200, "接口返回码错误"
        assert resp_json.get("msg") in ("查询成功", "ok"), "接口返回消息错误"
        assert "data" in resp_json, "响应中缺少data字段"
        assert len(resp_json["data"]) > 0, "商品列表为空"

        # 可选：校验数据结构
        first_goods = resp_json["data"][0]
        assert "id" in first_goods
        assert "name" in first_goods
        assert "price" in first_goods
        assert "stock" in first_goods

if __name__ == '__main__':
    test_query_goods()