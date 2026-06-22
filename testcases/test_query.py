import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.goods_service import GoodsService
import pytest
import allure
from pytest_assume.plugin import assume

@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("master只读用例")
@allure.epic("商品模块")
@allure.feature("商品查询接口")
@allure.story("获取商品列表")
@allure.tag("test", "master")
@pytest.mark.master
@allure.title("查询商品列表用例")
def test_query_goods(login_token):
    goods_service = GoodsService()
    
    with allure.step("1. 发送查询请求"):
        # 统一使用 GoodsService 封装的方法
        resp = goods_service.get_list(token=login_token)
        resp_json = resp.json()

    with allure.step("2. 报告附加响应数据"):
        allure.attach(resp.text, "商品列表响应", allure.attachment_type.JSON)
        print("商品接口响应：", resp.text)

    with allure.step("3. 断言校验"):
        assert resp.status_code == 200
        assert resp_json.get("code") == 200, "接口返回码错误"
        assert resp_json.get("msg") == "查询成功", "接口返回消息错误"
        assert "data" in resp_json, "响应中缺少data字段"
        assert len(resp_json["data"]) > 0, "商品列表为空"
        
        first_goods = resp_json["data"][0]
        assert "id" in first_goods
        assert "name" in first_goods
        assert "price" in first_goods
        assert "stock" in first_goods

if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
