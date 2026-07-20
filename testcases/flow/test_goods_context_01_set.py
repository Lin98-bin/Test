"""全局上下文演示 — 文件1：选商品 → 存入 GoodsStore"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.goods_service import GoodsService
from core.context import GoodsStore
from core.db_handler import db


@allure.feature("全局上下文演示")
@allure.story("跨文件传递：set → get → clear")
@allure.title("文件1：选商品 → GoodsStore.set_selected()")
def test_goods_context_set(login_token):
    """文件1：查询商品列表，选第一个商品，存入全局上下文"""

    with allure.step("步骤1：查询商品列表，取第一个商品"):
        resp = GoodsService().get_list()
        resp_json = resp.json()
        assume(resp_json["code"] == 200)

        goods_list = resp_json["data"]["list"]
        assume(len(goods_list) > 0, "商品列表不应为空")

        first_goods = goods_list[0]
        goods_id = first_goods["id"]
        goods_name = first_goods["name"]

        allure.attach(f"id={goods_id}, name={goods_name}", name="选中的商品")

    with allure.step("步骤2：存入 GoodsStore（跨文件传递）"):
        GoodsStore.set_selected("test_0006", goods_id, goods_name)
        # ↓ 存入后 _variables 的状态：
        # {"goods_id_test_0006": goods_id, "goods_name_test_0006": goods_name}

    with allure.step("步骤3：DB 断言 — 该商品确实存在"):
        goods = db.query("SELECT id, name FROM goods WHERE id=%s", args=(goods_id,), one=True)
        assume(goods is not None, f"DB 中应有 goods_id={goods_id}")
        assume(goods["name"] == goods_name, f"商品名应为{goods_name}, 实际={goods['name']}")

    print(f"\n✅ 文件1完成：goods_id={goods_id}, goods_name={goods_name} 已存入 GoodsStore")
    print("   文件2将通过 GoodsStore.get_selected_xxx() 取出并使用")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
