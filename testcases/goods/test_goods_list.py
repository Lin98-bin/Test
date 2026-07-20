"""商品列表 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.goods_service import GoodsService
from utils.yaml_utils import read_yaml_testcases
from core.db_handler import db


@allure.feature("商品模块")
@allure.story("查询商品列表")
@pytest.mark.parametrize("case", read_yaml_testcases('goods/goods_list'))
def test_goods_list(case):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']

    resp = GoodsService().get_list()
    resp_json = resp.json()

    assume(resp_json.get("code") == expected["code"])
    assume(resp_json.get("msg") in ("查询成功", "ok") or "ok" in str(resp_json.get("msg", "")))

    # DB 断言：验证在售商品数量
    if resp_json.get("code") == 200:
        db_count = db.query("SELECT COUNT(*) AS cnt FROM goods WHERE is_on_sale=1", one=True)
        assume(db_count is not None, "DB: goods 表查询不应为空")
        assume(db_count["cnt"] > 0, f"DB: 在售商品数量应大于0, 实际={db_count['cnt']}")

    data = resp_json.get("data", {})
    goods_list = data.get("list", []) if isinstance(data, dict) else []
    if case.get("scenario") == "success":
        assume(len(goods_list) > 0, "商品列表不应为空")
