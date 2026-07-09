"""订单模块 — 冒烟用例"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import allure
from pytest_assume.plugin import assume
from service.order_service import OrderService
from service.user_service import UserService


def _create_test_order(token):
    """辅助：下单并返回 order_id"""
    # 确保有地址
    from core.api_client import RequestsClient
    from core import setting
    client = RequestsClient()
    client.url = f"{setting.BASE_URL}/api/address/list"
    client.method = "get"
    client.headers = {"sessionToken": token}
    resp = client.send()
    addrs = resp.json().get("data", {}).get("list", [])
    if not addrs:
        # 创建一个地址
        client.url = f"{setting.BASE_URL}/api/address/add"
        client.method = "post"
        client.headers = {"sessionToken": token}
        client.json = {"address": "测试地址", "contact": "测试", "phone": "13800138000"}
        client.send()

    resp = OrderService().create(goods_id=1, quantity=1, token=token)
    return resp.json()["data"]["order_id"]


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("订单模块")
@allure.feature("订单操作")
@allure.story("创建订单")
@allure.title("创建订单冒烟用例")
def test_order_create(login_token):
    order_id = _create_test_order(login_token)
    assume(order_id is not None)
    assume(order_id > 0)


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("订单模块")
@allure.feature("订单操作")
@allure.story("订单列表")
@allure.title("订单列表冒烟用例")
def test_order_list(login_token):
    resp = OrderService().get_status(order_id=1, token=login_token)
    # get_status 需要 order_id, 这里直接用 list
    from core.api_client import RequestsClient
    from core import setting
    client = RequestsClient()
    client.url = f"{setting.BASE_URL}/api/order/list"
    client.method = "get"
    client.headers = {"sessionToken": login_token}
    resp = client.send()
    resp_json = resp.json()

    assume(resp_json.get("code") == 200)
    assume("list" in resp_json.get("data", {}))


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("订单模块")
@allure.feature("订单操作")
@allure.story("订单详情")
@allure.title("订单详情冒烟用例")
def test_order_detail(login_token):
    order_id = _create_test_order(login_token)

    from core.api_client import RequestsClient
    from core import setting
    client = RequestsClient()
    client.url = f"{setting.BASE_URL}/api/order/detail/{order_id}"
    client.method = "get"
    client.headers = {"sessionToken": login_token}
    resp = client.send()
    resp_json = resp.json()

    assume(resp_json.get("code") == 200)
    assume(resp_json.get("data", {}).get("id") == order_id)


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("订单模块")
@allure.feature("订单操作")
@allure.story("模拟支付")
@allure.title("订单支付冒烟用例")
def test_order_pay(login_token):
    order_id = _create_test_order(login_token)
    resp = OrderService().pay(order_id, token=login_token)
    resp_json = resp.json()

    assume(resp_json.get("code") == 200)


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("订单模块")
@allure.feature("订单操作")
@allure.story("查询订单状态")
@allure.title("订单状态冒烟用例")
def test_order_status(login_token):
    order_id = _create_test_order(login_token)
    resp = OrderService().get_status(order_id, token=login_token)
    resp_json = resp.json()

    assume(resp_json.get("code") == 200)
    assume(resp_json.get("data", {}).get("status") == "pending")


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("订单模块")
@allure.feature("订单操作")
@allure.story("取消订单")
@allure.title("取消订单冒烟用例")
def test_order_cancel(login_token):
    order_id = _create_test_order(login_token)

    from core.api_client import RequestsClient
    from core import setting
    client = RequestsClient()
    client.url = f"{setting.BASE_URL}/api/order/cancel/{order_id}"
    client.method = "put"
    client.headers = {"sessionToken": login_token}
    client.json = {"reason": "冒烟测试取消"}
    resp = client.send()
    resp_json = resp.json()

    assume(resp_json.get("code") == 200)


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
