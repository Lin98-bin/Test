"""购物车模块 — 冒烟用例"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import allure
from pytest_assume.plugin import assume
from service.cart_service import CartService
from common.db_handler import db


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("购物车模块")
@allure.feature("购物车CRUD")
@allure.story("加入购物车")
@allure.title("加入购物车冒烟用例")
def test_cart_add(login_token):
    with allure.step("加入购物车"):
        resp = CartService().add(goods_id=1, quantity=1, token=login_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)

    with allure.step("数据库断言：购物车记录已写入"):
        cart_item = db.query(
            "select * from cart where user_id = (select id from user where username = 'test_0006') and goods_id = %s order by id desc limit 1",
            args=(1,), one=True
        )
        assume(cart_item is not None, "数据库未查到购物车记录")
        assume(cart_item["goods_id"] == 1, f"商品ID不一致")
        assume(cart_item["quantity"] == 1, f"数量不一致: 期望=1, 实际={cart_item['quantity']}")


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("购物车模块")
@allure.feature("购物车CRUD")
@allure.story("获取购物车列表")
@allure.title("购物车列表冒烟用例")
def test_cart_list(login_token):
    with allure.step("获取购物车列表"):
        resp = CartService().get_list(token=login_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        assume("items" in resp_json.get("data", {}))


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("购物车模块")
@allure.feature("购物车CRUD")
@allure.story("购物车数量")
@allure.title("购物车数量冒烟用例")
def test_cart_count(login_token):
    with allure.step("获取购物车数量"):
        resp = CartService().count(token=login_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        assume("count" in resp_json.get("data", {}))


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("购物车模块")
@allure.feature("购物车CRUD")
@allure.story("修改购物车")
@allure.title("修改购物车数量冒烟用例")
def test_cart_update(login_token):
    cart = CartService()
    # 先加一个
    cart.add(goods_id=2, quantity=1, token=login_token)
    # 查 list 拿 cart_id
    resp = cart.get_list(token=login_token)
    items = resp.json().get("data", {}).get("items", [])
    assume(len(items) > 0, "购物车应有商品")

    cart_id = items[0]["cart_id"]

    with allure.step("修改数量为 3"):
        resp = cart.update(cart_id, 3, token=login_token)

    assume(resp.json().get("code") == 200)

    with allure.step("数据库断言：数量已更新"):
        cart_item = db.query("select quantity from cart where id = %s", args=(cart_id,), one=True)
        assume(cart_item is not None, f"数据库未查到购物车记录 id={cart_id}")
        assume(cart_item["quantity"] == 3, f"数量未更新: 期望=3, 实际={cart_item['quantity']}")


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("购物车模块")
@allure.feature("购物车CRUD")
@allure.story("删除购物车项")
@allure.title("删除购物车冒烟用例")
def test_cart_delete(login_token):
    cart = CartService()
    cart.add(goods_id=3, quantity=1, token=login_token)
    resp = cart.get_list(token=login_token)
    items = resp.json().get("data", {}).get("items", [])
    assume(len(items) > 0)

    cart_id = items[0]["cart_id"]
    with allure.step(f"删除 cart_id={cart_id}"):
        resp = cart.delete(cart_id, token=login_token)

    assume(resp.json().get("code") == 200)

    with allure.step("数据库断言：购物车记录已删除"):
        cart_item = db.query("select * from cart where id = %s", args=(cart_id,), one=True)
        assume(cart_item is None, f"购物车记录应已被删除，但仍查到 id={cart_id}")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
