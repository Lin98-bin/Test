import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.goods_api import GoodsApi
import pytest
import allure
from pytest_assume.plugin import assume

@allure.feature("商品模块")
@allure.story("查询商品")
def test_query_goods(login_token):  # 使用 fixture
    goods_api = GoodsApi()

    with allure.step("步骤1：发送查询商品请求"):
        resp = goods_api.get_list(token=login_token)
        resp_json = resp.json()
        print(f"响应：{resp_json}")

    with allure.step("步骤2：断言结果"):
        assume(resp_json.get("code") == 200)
        assume(resp_json.get("data") is not None)
        assume(resp_json.get("msg") == "查询成功")

        goods_list = resp_json.get("data", [])
        print(f"商品数量：{len(goods_list)}")
        allure.attach(str(goods_list), name="商品列表", attachment_type=allure.attachment_type.JSON)

if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
