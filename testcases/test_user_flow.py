import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.user_api import UserApi
from api.goods_api import GoodsApi
from common.api_client import GlobalContext, TokenStore
from common.jsonpath_utils import JsonPathExtractor
import pytest
import allure
from pytest_assume.plugin import assume
import random

@allure.feature("用户业务流程")
@allure.story("完整流程：注册-登录-查询-退出")
def test_user_complete_flow():
    """测试完整用户业务流程"""
    user_api = UserApi()
    goods_api = GoodsApi()
    extractor = JsonPathExtractor()

    # 生成随机用户名，避免重复
    username = f"test_flow_{random.randint(10000, 99999)}"
    password = "123456"

    with allure.step("步骤1：注册新用户"):
        resp = user_api.register(username, password)
        resp_json = resp.json()
        print(f"注册响应：{resp_json}")

        assume(resp_json.get("code") == 200)
        assume(resp_json.get("msg") == "注册成功")

        token = extractor.extract(resp_json, "$.data.token")
        assume(token is not None, "注册后应返回token")
        allure.attach(username, name="注册用户名", attachment_type=allure.attachment_type.TEXT)

    with allure.step("步骤2：使用新用户登录"):
        resp = user_api.login(username, password)
        resp_json = resp.json()
        print(f"登录响应：{resp_json}")

        assume(resp_json.get("code") == 200)
        assume(resp_json.get("msg") == "登录成功")

        token = extractor.extract(resp_json, "$.data.token")
        # 存储 Token 到全局上下文
        TokenStore.set_token(username, token)
        
        assume(token is not None, "登录后应返回token")
        allure.attach(token[:30], name="登录Token", attachment_type=allure.attachment_type.TEXT)

    with allure.step("步骤3：查询商品列表"):
        # 从全局上下文获取 Token
        current_token = TokenStore.get_token(username)
        resp = goods_api.get_list(token=current_token)
        resp_json = resp.json()
        print(f"商品查询响应：{resp_json}")

        assume(resp_json.get("code") == 200)
        assume(resp_json.get("msg") == "查询成功")

        goods_list = resp_json.get("data", [])
        assume(len(goods_list) > 0, "商品列表不应为空")
        allure.attach(str(goods_list), name="商品列表", attachment_type=allure.attachment_type.JSON)

    with allure.step("步骤4：查询用户信息"):
        current_token = TokenStore.get_token(username)
        resp = user_api.get_info(token=current_token)
        resp_json = resp.json()
        print(f"用户信息响应：{resp_json}")

        assume(resp_json.get("code") == 200)
        user_data = resp_json.get("data", {})
        assume(user_data.get("username") == username, "用户名应一致")
        allure.attach(str(user_data), name="用户信息", attachment_type=allure.attachment_type.JSON)

    with allure.step("步骤5：退出登录"):
        current_token = TokenStore.get_token(username)
        resp = user_api.logout(token=current_token)
        resp_json = resp.json()
        print(f"退出登录响应：{resp_json}")

        assume(resp_json.get("code") == 200)
        assume(resp_json.get("msg") == "退出成功")

    print(f"\nComplete business flow test passed! User: {username}")

if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
