"""商品模块 — 冒烟用例"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import allure
from pytest_assume.plugin import assume
from service.goods_service import GoodsService
from core.db_handler import db


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("商品模块")
@allure.feature("商品查询")
@allure.story("获取商品列表")
@allure.title("商品列表冒烟用例")
def test_goods_list():
    with allure.step("获取商品列表"):
        resp = GoodsService().get_list()
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        data = resp_json.get("data", {})
        assume(len(data.get("list", [])) > 0, "商品列表不应为空")
        assume(data.get("total", 0) > 0)

        # DB 断言：验证在售商品数量
        if resp_json.get("code") == 200:
            db_count = db.query("SELECT COUNT(*) AS cnt FROM goods WHERE is_on_sale=1", one=True)
            assume(db_count is not None, "DB: goods 表查询不应为空")
            assume(db_count["cnt"] > 0, f"DB: 在售商品数量应大于0, 实际={db_count['cnt']}")


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("商品模块")
@allure.feature("商品查询")
@allure.story("获取商品详情")
@allure.title("商品详情冒烟用例")
def test_goods_detail():
    with allure.step("获取商品详情 (id=1)"):
        resp = GoodsService().get_detail(1)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        data = resp_json.get("data", {})
        assume(data.get("id") == 1)
        assume(len(data.get("name", "")) > 0)

        # DB 断言：验证商品 id=1 在数据库中存在
        if resp_json.get("code") == 200:
            db_goods = db.query("SELECT * FROM goods WHERE id=1", one=True)
            assume(db_goods is not None, "DB: 商品 id=1 应存在于 goods 表中")
            assume(db_goods.get("name") == data.get("name"),
                   f"DB: 商品名称应匹配, API返回={data.get('name')}, DB={db_goods.get('name')}")


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("商品模块")
@allure.feature("商品查询")
@allure.story("搜索商品")
@allure.title("商品搜索冒烟用例")
def test_goods_search():
    with allure.step("搜索商品 iPhone"):
        resp = GoodsService().search(keyword="iPhone")
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        data = resp_json.get("data", {})
        assume(data.get("total", 0) > 0, "搜索 iPhone 应有结果")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
