"""分类模块 — 冒烟用例"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import allure
from pytest_assume.plugin import assume
from service.category_service import CategoryService


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("分类模块")
@allure.feature("分类列表")
@allure.story("获取分类列表")
@allure.title("分类列表冒烟用例")
def test_category_list():
    with allure.step("获取分类列表"):
        resp = CategoryService().get_list()
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        categories = resp_json.get("data", {}).get("list", [])
        assume(len(categories) > 0, "分类列表不应为空")
        assume("id" in categories[0])
        assume("name" in categories[0])


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
