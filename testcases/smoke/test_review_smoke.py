"""评价模块 — 冒烟用例"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import allure
from pytest_assume.plugin import assume
from service.review_service import ReviewService
from service.order_service import OrderService
from core.api_client import RequestsClient
from core import setting
from core.db_handler import db


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("评价模块")
@allure.feature("商品评价")
@allure.story("发表评价")
@allure.title("发表评价冒烟用例")
def test_review_add(login_token):
    """先创建一个已完成订单，再发表评价"""
    client = RequestsClient()
    # 确保地址
    client.url = f"{setting.BASE_URL}/api/address/list"
    client.method = "get"
    client.headers = {"sessionToken": login_token}
    resp = client.send()
    if not resp.json().get("data", {}).get("list", []):
        client.url = f"{setting.BASE_URL}/api/address/add"
        client.method = "post"
        client.headers = {"sessionToken": login_token}
        client.json = {"address": "评价测试", "contact": "测试", "phone": "13800138000"}
        client.send()

    # 下单 → 支付 → 确认收货
    order = OrderService()
    resp = order.create(goods_id=5, quantity=1, token=login_token)
    order_id = resp.json()["data"]["order_id"]
    order.pay(order_id, token=login_token)
    client.url = f"{setting.BASE_URL}/api/order/confirm/{order_id}"
    client.method = "put"
    client.headers = {"sessionToken": login_token}
    client.send()

    with allure.step("发表评价"):
        resp = ReviewService().add(
            order_id=order_id, goods_id=5,
            rating=5, content="冒烟测试好评", token=login_token
        )
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        review_id = resp_json.get("data", {}).get("id")

    if review_id:
        with allure.step("数据库断言：评价记录已写入"):
            review = db.query("select * from review where id = %s", args=(review_id,), one=True)
            assume(review is not None, f"数据库未查到评价记录 id={review_id}")
            assume(review["order_id"] == order_id, f"订单ID不一致")
            assume(review["goods_id"] == 5, f"商品ID不一致")
            assume(review["rating"] == 5, f"评分不一致: 期望=5, 实际={review['rating']}")
            assume(review["content"] == "冒烟测试好评", f"评价内容不一致")


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("评价模块")
@allure.feature("商品评价")
@allure.story("查看评价")
@allure.title("商品评价列表冒烟用例")
def test_review_list():
    with allure.step("获取商品评价列表"):
        resp = ReviewService().get_list(goods_id=1)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("评价模块")
@allure.feature("商品评价")
@allure.story("我的评价")
@allure.title("我的评价冒烟用例")
def test_review_my(login_token):
    with allure.step("获取我的评价"):
        resp = ReviewService().get_my(token=login_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
