"""商品模块 — 冒烟用例"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import allure
from pytest_assume.plugin import assume
from service.goods_service import GoodsService


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


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("商品模块")
@allure.feature("商品查询")
@allure.story("搜索商品")
@allure.title("商品搜索冒烟用例")
def test_goods_search():
    with allure.step("搜索商品 iPhone"):
        GoodsService().get_list()
        # /api/goods/search 内部复用 goods_list, 传 keyword 参数
        from core.api_client import RequestsClient
        from core import setting
        client = RequestsClient()
        client.url = f"{setting.BASE_URL}/api/goods/search?keyword=iPhone"
        client.method = "get"
        resp = client.send()
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        data = resp_json.get("data", {})
        assume(data.get("total", 0) > 0, "搜索 iPhone 应有结果")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
