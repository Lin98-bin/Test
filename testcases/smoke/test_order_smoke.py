"""订单模块 — 冒烟用例"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import allure
from pytest_assume.plugin import assume
from service.order_service import OrderService
from service.user_service import UserService
from common.db_handler import db


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

    with allure.step("数据库断言：订单已写入"):
        order = db.query("select * from orders where id = %s", args=(order_id,), one=True)
        assume(order is not None, f"数据库未查到订单 id={order_id}")
        assume(order["status"] == "pending", f"订单状态应为pending，实际={order['status']}")
        assume(order["goods_id"] == 1, f"商品ID不一致")
        assume(order["quantity"] == 1, f"数量不一致")


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("订单模块")
@allure.feature("订单操作")
@allure.story("订单列表")
@allure.title("订单列表冒烟用例")
def test_order_list(login_token):
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

    with allure.step("数据库断言：订单详情与DB一致"):
        order = db.query("select * from orders where id = %s", args=(order_id,), one=True)
        assume(order is not None, f"数据库未查到订单 id={order_id}")
        assume(order["id"] == order_id, f"订单ID不一致")


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

    with allure.step("数据库断言：订单状态已变为paid"):
        order = db.query("select status from orders where id = %s", args=(order_id,), one=True)
        assume(order is not None, f"数据库未查到订单 id={order_id}")
        assume(order["status"] == "paid", f"订单状态应为paid，实际={order['status']}")


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

    with allure.step("数据库断言：订单状态与DB一致"):
        order = db.query("select status from orders where id = %s", args=(order_id,), one=True)
        assume(order is not None, f"数据库未查到订单 id={order_id}")
        assume(order["status"] == "pending", f"订单状态应为pending，实际={order['status']}")


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

    with allure.step("数据库断言：订单状态已变为cancelled"):
        order = db.query("select status, cancel_reason from orders where id = %s", args=(order_id,), one=True)
        assume(order is not None, f"数据库未查到订单 id={order_id}")
        assume(order["status"] == "cancelled", f"订单状态应为cancelled，实际={order['status']}")
        assume(order["cancel_reason"] == "冒烟测试取消", f"取消原因不一致")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
