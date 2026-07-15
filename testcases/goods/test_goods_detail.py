"""商品详情 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from core.api_client import RequestsClient
from utils.yaml_utils import read_yaml_testcases
from core import setting


@allure.feature("商品模块")
@allure.story("查询商品详情")
@pytest.mark.parametrize("case", read_yaml_testcases('goods/goods_detail'))
def test_goods_detail(case):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']
    goods_id = case.get('data', {}).get('goods_id')

    client = RequestsClient()
    client.url = f"{setting.BASE_URL}/api/goods/detail/{goods_id}"
    client.method = "get"
    client.headers = setting.COMMON_HEADERS.copy()
    resp = client.send()
    resp_json = resp.json()

    assume(resp_json.get("code") == expected["code"])
    if expected["code"] == 200:
        assume(resp_json.get("data", {}).get("id") == goods_id)
