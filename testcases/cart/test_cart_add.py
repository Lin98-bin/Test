""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.cart_service import CartService
from core.db_handler import db

@allure.feature("cart模块")
@pytest.mark.parametrize("case", read_yaml_testcases('cart/cart_add'))
def test_cart_add(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    
    resp = CartService().add(goods_id=d.get('goods_id'), quantity=d.get('quantity', 1), token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    if expected["code"] == 200:
        goods_id = d.get('goods_id')
        quantity = d.get('quantity', 1)
        row = db.query(
            "SELECT * FROM cart WHERE user_id=(SELECT id FROM user WHERE username=%s) AND goods_id=%s ORDER BY id DESC LIMIT 1",
            args=('test_0006', goods_id),
            one=True
        )
        assume(row is not None, "cart add: DB row should exist")
        assume(row.get("goods_id") == goods_id, f"cart add: goods_id mismatch, expected {goods_id}, got {row.get('goods_id')}")
        assume(row.get("quantity") == quantity, f"cart add: quantity mismatch, expected {quantity}, got {row.get('quantity')}")
