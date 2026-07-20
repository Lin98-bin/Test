""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.cart_service import CartService
from core.db_handler import db

@allure.feature("cart模块")
@pytest.mark.parametrize("case", read_yaml_testcases('cart/cart_count'))
def test_cart_count(case, login_token):
    allure.dynamic.title(case["name"])
    expected = case['expected']
    
    resp = CartService().count(token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    assume("count" in resp_json.get("data", {}))
    if expected["code"] == 200:
        row = db.query(
            "SELECT COUNT(*) AS cnt FROM cart WHERE user_id=(SELECT id FROM user WHERE username=%s)",
            args=('test_0006',),
            one=True
        )
        db_count = row["cnt"] if row else 0
        api_count = resp_json.get("data", {}).get("count", 0)
        assume(db_count == api_count, f"cart count: count mismatch, DB={db_count}, API={api_count}")
