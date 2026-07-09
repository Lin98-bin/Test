import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import allure
from service.order_service import OrderService
from service.user_service import UserService
from service.goods_service import GoodsService
from pytest_assume.plugin import assume

@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("test全量用例")
@allure.epic("业务流程模块")
@allure.tag("test")
@pytest.mark.test
@allure.feature("订单模块")
@allure.story("新增订单")
@allure.title("订单创建接口-Token验证")
def test_create_order(login_token):
    """
    验证需要 Token 的下单接口
    1. 先通过 goods_service 获取一个商品 ID
    2. 使用 login_token 调用下单接口
    """
    goods_service = GoodsService()
    order_service = OrderService()

    with allure.step("步骤1：获取商品列表并选择第一个商品"):
        resp_goods = goods_service.get_list(token=login_token)
        goods_id = resp_goods.json()["data"][0]["id"]
        allure.attach(str(goods_id), name="选择的商品ID")

    with allure.step("步骤2：使用 Token 提交下单请求"):
        # 这里直接使用了传入的 login_token 夹具
        resp_order = order_service.create(goods_id=goods_id, num=1, token=login_token)
        resp_json = resp_order.json()
        
        assume(resp_json.get("code") == 200)
        assume("order_id" in resp_json.get("data", {}))
        print(f"订单创建成功，订单号：{resp_json['data']['order_id']}")

@allure.parent_suite("接口自动化测试-自己练习")
@allure.feature("用户模块")
@allure.story("收货地址")
@allure.title("新增收货地址测试")
def test_add_shipping_address(login_token):
    """
    验证需要 Token 的新增地址接口
    """
    user_service = UserService()

    with allure.step("步骤1：准备地址数据并发送请求"):
        # 这里直接使用了传入的 login_token 夹具
        resp = user_service.add_address(
            address_detail="上海市浦东新区某某路123号",
            contact_name="林同学",
            contact_phone="13800138000",
            token=login_token
        )
        resp_json = resp.json()

    with allure.step("步骤2：断言结果"):
        assume(resp_json.get("code") == 200)
        assume(resp_json.get("msg") == "新增成功" or "成功" in resp_json.get("msg", ""))
        print(f"收货地址新增成功！")

if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
