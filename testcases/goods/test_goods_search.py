"""商品搜索 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from core.api_client import RequestsClient
from utils.yaml_utils import read_yaml_testcases
from core import setting


@allure.feature("商品模块")
@allure.story("搜索商品")
@pytest.mark.parametrize("case", read_yaml_testcases('goods/goods_search'))
def test_goods_search(case):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']
    keyword = case.get('params', {}).get("keyword", "")

    client = RequestsClient()
    client.url = f"{setting.BASE_URL}/api/goods/search?keyword={keyword}"
    client.method = "get"
    client.headers = setting.COMMON_HEADERS.copy()
    resp = client.send()
    resp_json = resp.json()

    assume(resp_json.get("code") == expected["code"])
    if expected["code"] == 200:
        assume(resp_json.get("data", {}).get("total", 0) > 0, f"搜索 {keyword} 应有结果")
