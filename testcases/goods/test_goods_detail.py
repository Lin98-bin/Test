"""商品详情 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.goods_service import GoodsService
from utils.yaml_utils import read_yaml_testcases
from core.db_handler import db


@allure.feature("商品模块")
@allure.story("查询商品详情")
@pytest.mark.parametrize("case", read_yaml_testcases('goods/goods_detail'))
def test_goods_detail(case):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']
    goods_id = case.get('data', {}).get('goods_id')

    resp = GoodsService().get_detail(goods_id=goods_id)
    resp_json = resp.json()

    assume(resp_json.get("code") == expected["code"])
    if expected["code"] == 200:
        assume(resp_json.get("data", {}).get("id") == goods_id)

        # DB 断言：验证商品在数据库中存在且名称匹配
        db_goods = db.query("SELECT * FROM goods WHERE id=%s", args=(goods_id,), one=True)
        assume(db_goods is not None, f"DB: goods 表中应存在 id={goods_id} 的商品")
        assume(db_goods.get("name") == resp_json.get("data", {}).get("name"),
               f"DB: 商品名称应匹配, API返回={resp_json.get('data', {}).get('name')}, DB={db_goods.get('name')}")
