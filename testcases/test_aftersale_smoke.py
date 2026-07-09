"""售后模块 — 冒烟用例"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import allure
from pytest_assume.plugin import assume
from service.aftersale_service import AfterSaleService
from service.order_service import OrderService
from utils.jsonpath_utils import JsonPathExtractor


def _ensure_completed_order(token):
    """辅助：创建一个已完成订单"""
    from core.api_client import RequestsClient
    from core import setting
    client = RequestsClient()
    # 确保地址存在
    client.url = f"{setting.BASE_URL}/api/address/list"
    client.method = "get"
    client.headers = {"sessionToken": token}
    resp = client.send()
    if not resp.json().get("data", {}).get("list", []):
        client.url = f"{setting.BASE_URL}/api/address/add"
        client.method = "post"
        client.headers = {"sessionToken": token}
        client.json = {"address": "售后测试", "contact": "测试", "phone": "13800138000"}
        client.send()

    order = OrderService()
    resp = order.create(goods_id=1, quantity=1, token=token)
    order_id = resp.json()["data"]["order_id"]

    # 支付
    order.pay(order_id, token=token)

    # 确认收货
    client.url = f"{setting.BASE_URL}/api/order/confirm/{order_id}"
    client.method = "put"
    client.headers = {"sessionToken": token}
    client.send()

    return order_id, 1  # order_id, goods_id


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("售后模块")
@allure.feature("售后操作")
@allure.story("申请售后")
@allure.title("申请售后冒烟用例")
def test_aftersale_apply(login_token):
    order_id, goods_id = _ensure_completed_order(login_token)

    with allure.step("申请售后"):
        resp = AfterSaleService().apply(
            order_id=order_id, goods_id=goods_id,
            reason="冒烟测试申请售后", amount=1.00,
            atype="refund", token=login_token
        )
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("售后模块")
@allure.feature("售后操作")
@allure.story("售后列表")
@allure.title("售后列表冒烟用例")
def test_aftersale_list(login_token):
    with allure.step("获取售后列表"):
        resp = AfterSaleService().get_list(token=login_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        assume("list" in resp_json.get("data", {}))


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
