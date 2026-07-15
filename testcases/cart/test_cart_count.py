""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.cart_service import CartService

@allure.feature("cart模块")
@pytest.mark.parametrize("case", read_yaml_testcases('cart/cart_count'))
def test_cart_count(case, login_token):
    allure.dynamic.title(case["name"])
    expected = case['expected']
    
    resp = CartService().count(token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    assume("count" in resp_json.get("data", {}))
