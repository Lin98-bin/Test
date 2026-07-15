import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from service.user_service import UserService
from service.goods_service import GoodsService
from core.context import GlobalContext, TokenStore
from utils.jsonpath_utils import JsonPathExtractor
from common.db_handler import db
import pytest
import allure
from pytest_assume.plugin import assume
import random

@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("test全量用例")
@allure.feature("业务流程")
@allure.story("用户全流程测试")
@allure.tag("test")
@pytest.mark.test
@allure.title("用户完整业务流程测试")
def test_user_complete_flow():
    """测试完整用户业务流程"""
    user_service = UserService()
    goods_service = GoodsService()
    extractor = JsonPathExtractor()

    # 生成随机用户名，避免重复
    username = f"test_flow_{random.randint(10000, 99999)}"
    password = "123456"

    with allure.step("步骤1：注册新用户"):
        resp = user_service.register(username, password)
        resp_json = resp.json()
        print(f"注册响应：{resp_json}")

        assume(resp_json.get("code") == 200)
        assume(resp_json.get("msg") in ("注册成功", "ok"))

        token = extractor.extract(resp_json, "$.data.token")
        assume(token is not None, "注册后应返回token")
        allure.attach(username, name="注册用户名", attachment_type=allure.attachment_type.TEXT)

        # 数据库断言：用户已写入
        with allure.step("步骤1.1：数据库断言-用户已写入"):
            user = db.query("select * from user where username = %s", args=(username,), one=True)
            assume(user is not None, f"数据库未查到用户 {username}")
            assume(user["username"] == username, f"用户名不一致")

    with allure.step("步骤2：使用新用户登录"):
        resp = user_service.login(username, password)
        resp_json = resp.json()
        print(f"登录响应：{resp_json}")

        assume(resp_json.get("code") == 200)
        assume(resp_json.get("msg") in ("登录成功", "ok"))

        token = extractor.extract(resp_json, "$.data.token")
        # 存储 Token 到全局上下文
        TokenStore.set_token(username, token)
        
        assume(token is not None, "登录后应返回token")
        allure.attach(token[:30], name="登录Token", attachment_type=allure.attachment_type.TEXT)

    with allure.step("步骤3：查询商品列表"):
        # 从全局上下文获取 Token
        current_token = TokenStore.get_token(username)
        resp = goods_service.get_list(token=current_token)
        resp_json = resp.json()
        print(f"商品查询响应：{resp_json}")

        assume(resp_json.get("code") == 200)
        assume(resp_json.get("msg") in ("查询成功", "ok"))

        goods_list = resp_json.get("data", [])
        assume(len(goods_list) > 0, "商品列表不应为空")
        allure.attach(str(goods_list), name="商品列表", attachment_type=allure.attachment_type.JSON)

    with allure.step("步骤4：查询用户信息"):
        current_token = TokenStore.get_token(username)
        resp = user_service.get_info(token=current_token)
        resp_json = resp.json()
        print(f"用户信息响应：{resp_json}")

        assume(resp_json.get("code") == 200)
        user_data = resp_json.get("data", {})
        assume(user_data.get("username") == username, "用户名应一致")
        allure.attach(str(user_data), name="用户信息", attachment_type=allure.attachment_type.JSON)

    with allure.step("步骤5：退出登录"):
        current_token = TokenStore.get_token(username)
        resp = user_service.logout(token=current_token)
        resp_json = resp.json()
        print(f"退出登录响应：{resp_json}")

        assume(resp_json.get("code") == 200)
        assume(resp_json.get("msg") in ("退出成功", "ok"))

    print(f"\nComplete business flow test passed! User: {username}")

if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
