"""商品搜索 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.goods_service import GoodsService
from utils.yaml_utils import read_yaml_testcases
from core.db_handler import db


@allure.feature("商品模块")
@allure.story("搜索商品")
@pytest.mark.parametrize("case", read_yaml_testcases('goods/goods_search'))
def test_goods_search(case):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']
    keyword = case.get('params', {}).get("keyword", "")

    resp = GoodsService().search(keyword=keyword)
    resp_json = resp.json()

    assume(resp_json.get("code") == expected["code"])
    if expected["code"] == 200:
        assume(resp_json.get("data", {}).get("total", 0) > 0, f"搜索 {keyword} 应有结果")

        # DB 断言：验证搜索关键词在数据库中有匹配
        db_count = db.query("SELECT COUNT(*) AS cnt FROM goods WHERE name LIKE %s", args=(f"%{keyword}%",), one=True)
        assume(db_count is not None, "DB: goods 表查询不应为空")
        assume(db_count["cnt"] > 0, f"DB: 搜索 '{keyword}' 应有匹配结果, 实际={db_count['cnt']}")
