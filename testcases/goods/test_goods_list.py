"""商品列表 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from core.api_client import RequestsClient
from utils.yaml_utils import read_yaml_testcases
from core import setting


@allure.feature("商品模块")
@allure.story("查询商品列表")
@pytest.mark.parametrize("case", read_yaml_testcases('goods/goods_list'))
def test_goods_list(case):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']
    params = case.get('params', {})

    url = f"{setting.BASE_URL}/api/goods/list"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    client = RequestsClient()
    client.url = url
    client.method = "get"
    client.headers = setting.COMMON_HEADERS.copy()
    resp = client.send()
    resp_json = resp.json()

    assume(resp_json.get("code") == expected["code"])
    assume(resp_json.get("msg") in ("查询成功", "ok") or "ok" in str(resp_json.get("msg", "")))

    data = resp_json.get("data", {})
    goods_list = data.get("list", []) if isinstance(data, dict) else []
    if case.get("scenario") == "success":
        assume(len(goods_list) > 0, "商品列表不应为空")
