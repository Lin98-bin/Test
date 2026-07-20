""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.cart_service import CartService
from core.db_handler import db

def _get_cart_id(token):
    cart = CartService()
    resp = cart.get_list(token=token)
    items = resp.json().get("data",{}).get("items",[])
    if items: return items[0]["cart_id"]
    cart.add(goods_id=1, quantity=1, token=token)
    return cart.get_list(token=token).json()["data"]["items"][0]["cart_id"]

@allure.feature("cart模块")
@pytest.mark.parametrize("case", read_yaml_testcases('cart/cart_batch_delete'))
def test_cart_batch_delete(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    ids = d["ids"] if "ids" in d else [_get_cart_id(login_token)]
    if "ids" not in d:
        CartService().add(goods_id=2, quantity=1, token=login_token)
        ids.append(_get_cart_id(login_token))
    
    resp = CartService().batch_delete(ids, token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    if expected["code"] == 200:
        placeholders = ','.join(['%s'] * len(ids))
        rows = db.query(
            f"SELECT * FROM cart WHERE id IN ({placeholders})",
            args=tuple(ids),
            one=False
        )
        assume(len(rows) == 0, f"cart batch delete: DB should have no rows for ids={ids}, got {len(rows)}")
