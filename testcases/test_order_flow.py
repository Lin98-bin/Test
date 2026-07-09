import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.user_service import UserService
from service.goods_service import GoodsService
from service.order_service import OrderService
from core.context import TokenStore, OrderStore, GlobalContext
from utils.jsonpath_utils import JsonPathExtractor
import pytest
import allure
from pytest_assume.plugin import assume
import random

@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("beta核心用例")
@allure.feature("订单业务流程")
@allure.story("完整流程：登录-查询商品-下单-支付-查看状态")
@allure.tag("test")
@pytest.mark.test
@allure.title("订单完整业务流程测试")
def test_order_complete_flow(login_token):
    """测试完整的订单业务流程，演示 GlobalContext 子类的协作"""
    user_service = UserService()
    goods_service = GoodsService()
    order_service = OrderService()
    extractor = JsonPathExtractor()

    # 使用 fixture 提供的 token（避免覆盖其他测试的登录状态）
    username = "test_0006"
    token = login_token
    TokenStore.set_token(username, token)

    with allure.step("步骤1：使用已登录的Token"):
        assume(token is not None)
        allure.attach(token[:20], name="当前Token")

    with allure.step("步骤2：获取商品列表并选择第一个商品"):
        current_token = TokenStore.get_token(username)
        resp = goods_service.get_list(token=current_token)
        goods_list = resp.json()["data"]["list"]
        assume(len(goods_list) > 0)
        goods_id = goods_list[0]["id"]
        allure.attach(str(goods_id), name="选择的商品ID")

    with allure.step("步骤3：创建订单"):
        current_token = TokenStore.get_token(username)
        resp = order_service.create(goods_id, num=2, token=current_token)
        resp_json = resp.json()
        order_id = extractor.extract(resp_json, "$.data.order_id")
        
        # 使用 OrderStore 存储订单号 (体现 GlobalContext 子类的不同职责)
        OrderStore.set_order_id(username, order_id)
        
        assume(order_id is not None)
        allure.attach(str(order_id), name="生成的订单号")

    with allure.step("步骤4：支付订单"):
        current_token = TokenStore.get_token(username)
        current_order_id = OrderStore.get_order_id(username)
        
        resp = order_service.pay(current_order_id, token=current_token)
        assume(resp.json().get("code") == 200)
        assume(resp.json().get("msg") == "支付成功")

    with allure.step("步骤5：查看订单支付状态"):
        current_token = TokenStore.get_token(username)
        current_order_id = OrderStore.get_order_id(username)
        
        resp = order_service.get_status(current_order_id, token=current_token)
        resp_json = resp.json()
        status = extractor.extract(resp_json, "$.data.status")
        
        assume(status == "paid")
        print(f"订单 {current_order_id} 状态验证通过：{status}")

    with allure.step("清理环境：演示 GlobalContext.clear()"):
        # 模拟测试结束，清空所有上下文数据
        GlobalContext.clear()
        assume(TokenStore.get_token(username) == "")
        assume(OrderStore.get_order_id(username) is None)
        print("全局上下文已清空")

if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
