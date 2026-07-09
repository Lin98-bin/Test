"""管理员模块 — 冒烟用例"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import allure
from pytest_assume.plugin import assume
from service.admin_service import AdminService
from service.order_service import OrderService
from service.aftersale_service import AfterSaleService


def _create_paid_order(token):
    """辅助：创建一个已支付订单"""
    from core.api_client import RequestsClient
    from core import setting
    client = RequestsClient()
    client.url = f"{setting.BASE_URL}/api/address/list"
    client.method = "get"
    client.headers = {"sessionToken": token}
    resp = client.send()
    if not resp.json().get("data", {}).get("list", []):
        client.url = f"{setting.BASE_URL}/api/address/add"
        client.method = "post"
        client.headers = {"sessionToken": token}
        client.json = {"address": "管理测试", "contact": "测试", "phone": "13800138000"}
        client.send()

    order = OrderService()
    resp = order.create(goods_id=1, quantity=1, token=token)
    order_id = resp.json()["data"]["order_id"]
    order.pay(order_id, token=token)
    return order_id


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("管理员模块")
@allure.feature("订单管理")
@allure.story("待发货订单")
@allure.title("管理员查看待发货订单冒烟用例")
def test_admin_paid_orders(admin_token):
    with allure.step("查看待发货订单"):
        resp = AdminService().get_paid_orders(token=admin_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)
        assume("list" in resp_json.get("data", {}))


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("管理员模块")
@allure.feature("订单管理")
@allure.story("发货")
@allure.title("管理员发货冒烟用例")
def test_admin_ship_order(admin_token, login_token):
    order_id = _create_paid_order(login_token)
    with allure.step(f"对订单 {order_id} 发货"):
        resp = AdminService().ship_order(order_id, tracking="TEST00001", token=admin_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("管理员模块")
@allure.feature("售后处理")
@allure.story("待处理售后")
@allure.title("管理员查看待处理售后冒烟用例")
def test_admin_pending_aftersale(admin_token):
    with allure.step("查看待处理售后"):
        resp = AdminService().get_pending_aftersale(token=admin_token)
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("管理员模块")
@allure.feature("售后处理")
@allure.story("处理售后")
@allure.title("管理员处理售后冒烟用例")
def test_admin_handle_aftersale(admin_token, login_token):
    # 准备：用户申请售后
    from service.order_service import OrderService
    from core.api_client import RequestsClient
    from core import setting
    client = RequestsClient()
    client.url = f"{setting.BASE_URL}/api/address/list"
    client.method = "get"
    client.headers = {"sessionToken": login_token}
    resp = client.send()
    if not resp.json().get("data", {}).get("list", []):
        client.url = f"{setting.BASE_URL}/api/address/add"
        client.method = "post"
        client.headers = {"sessionToken": login_token}
        client.json = {"address": "售后测试", "contact": "测试", "phone": "13800138000"}
        client.send()

    order = OrderService()
    resp = order.create(goods_id=2, quantity=1, token=login_token)
    order_id = resp.json()["data"]["order_id"]
    order.pay(order_id, token=login_token)
    client.url = f"{setting.BASE_URL}/api/order/confirm/{order_id}"
    client.method = "put"
    client.headers = {"sessionToken": login_token}
    client.send()

    aftersale = AfterSaleService()
    resp = aftersale.apply(
        order_id=order_id, goods_id=2, reason="管理测试售后",
        amount=1.00, atype="refund", token=login_token
    )
    as_id = resp.json()["data"]["id"]

    with allure.step(f"处理售后 id={as_id}"):
        resp = AdminService().handle_aftersale(
            as_id, action="approve", reply="同意退款", token=admin_token
        )
        resp_json = resp.json()

    with allure.step("断言结果"):
        assume(resp_json.get("code") == 200)


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
