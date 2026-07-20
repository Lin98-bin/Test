"""商品高级筛选 — 数据驱动用例（演示查询参数）"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.goods_service import GoodsService
from utils.yaml_utils import read_yaml_testcases
from core.db_handler import db


@allure.feature("商品模块")
@allure.story("商品高级筛选")
@pytest.mark.parametrize("case", read_yaml_testcases('goods/goods_filter'))
def test_goods_filter(case):
    allure.dynamic.title(f"用例：{case['name']}")
    p = case.get('params', {})
    expected = case['expected']

    resp = GoodsService().filter_goods(
        min_price=p.get('min_price', 0),
        max_price=p.get('max_price', 0),
        sort_by=p.get('sort_by', 'id'),
        order=p.get('order', 'desc')
    )
    resp_json = resp.json()

    assume(resp_json.get("code") == expected["code"])

    if expected["code"] == 200:
        data = resp_json.get("data", {})
        goods_list = data.get("list", [])
        assume(len(goods_list) > 0, "筛选结果不应为空")
        assume(data.get("total", 0) > 0, "total应大于0")

        # 验证筛选参数回显
        filters = data.get("filters", {})
        assume(filters.get("min_price") == p.get('min_price', 0))
        assume(filters.get("max_price") == p.get('max_price', 0))

        # DB 断言：验证结果数量一致
        db_count = db.query("SELECT COUNT(*) AS cnt FROM goods WHERE is_on_sale=1", one=True)
        assume(db_count is not None, "DB: goods 表查询不应为空")
        assume(db_count["cnt"] > 0, f"DB: 在售商品数量应大于0, 实际={db_count['cnt']}")

        # 如果是价格区间筛选，验证结果价格都在区间内
        min_p = p.get('min_price', 0)
        max_p = p.get('max_price', 0)
        if min_p > 0:
            for g in goods_list:
                assume(g.get("price", 0) >= min_p, f"价格 {g.get('price')} 应 >= {min_p}")
        if max_p > 0:
            for g in goods_list:
                assume(g.get("price", 0) <= max_p, f"价格 {g.get('price')} 应 <= {max_p}")
