""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.cart_service import CartService

def _get_cart_id(token):
    cart = CartService()
    resp = cart.get_list(token=token)
    items = resp.json().get("data",{}).get("items",[])
    if items: return items[0]["cart_id"]
    cart.add(goods_id=1, quantity=1, token=token)
    return cart.get_list(token=token).json()["data"]["items"][0]["cart_id"]

@allure.feature("cart模块")
@pytest.mark.parametrize("case", read_yaml_testcases('cart/cart_update'))
def test_cart_update(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    cart_id = d.get("cart_id") or _get_cart_id(login_token)
    
    resp = CartService().update(cart_id, d.get("quantity", 3), token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
