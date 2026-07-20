"""全局上下文演示 — 文件2：取 → 用 → 清 → 验证已清"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from service.goods_service import GoodsService
from service.cart_service import CartService
from core.context import GlobalContext, GoodsStore
from core.db_handler import db


@allure.feature("全局上下文演示")
@allure.story("跨文件传递：set → get → clear")
@allure.title("文件2：GoodsStore.get() → 使用 → GlobalContext.clear() → 验证清空")
def test_goods_context_consume(login_token):
    """文件2：从全局上下文取出商品，使用，然后清空，验证 clear 生效"""

    # ========== get：跨文件取值 ==========
    with allure.step("步骤1：GoodsStore.get_selected_xxx() — 跨文件取值"):
        goods_id = GoodsStore.get_selected_id("test_0006")
        goods_name = GoodsStore.get_selected_name("test_0006")

        assume(goods_id is not None, "应从文件1拿到 goods_id，实际为 None")
        assume(goods_name is not None, "应从文件1拿到 goods_name，实际为 None")

        allure.attach(f"取到的值：id={goods_id}, name={goods_name}")

    # ========== 用：两个接口消费 goods_id ==========
    with allure.step("步骤2：用 goods_id 查商品详情"):
        resp = GoodsService().get_detail(goods_id)
        resp_json = resp.json()
        assume(resp_json["code"] == 200, f"查详情失败: {resp_json}")
        detail_name = resp_json["data"]["name"]
        assume(detail_name == goods_name,
               f"文件1选的是'{goods_name}'，文件2查到的是'{detail_name}'，应一致")

    with allure.step("步骤3：用 goods_id 加入购物车"):
        resp = CartService().add(goods_id=goods_id, quantity=1, token=login_token)
        resp_json = resp.json()
        assume(resp_json["code"] == 200, f"加购失败: {resp_json}")

        # DB 断言购物车落库
        row = db.query(
            "SELECT * FROM cart WHERE user_id=(SELECT id FROM user WHERE username=%s) AND goods_id=%s ORDER BY id DESC LIMIT 1",
            args=('test_0006', goods_id), one=True
        )
        assume(row is not None, "购物车记录应存在")
        assume(row["goods_id"] == goods_id, f"购物车 goods_id 应为 {goods_id}")

    # ========== clear：清空 ==========
    with allure.step("步骤4：GlobalContext.clear() — 清空"):
        GlobalContext.clear()
        print("\n🧹 GlobalContext.clear() 已执行，_variables 字典已清空")

    # ========== 验证已清空 ==========
    with allure.step("步骤5：再次 get — 验证 clear 生效"):
        after_clear_id = GoodsStore.get_selected_id("test_0006")
        after_clear_name = GoodsStore.get_selected_name("test_0006")

        assume(after_clear_id is None,
               f"clear 后 goods_id 应为 None，实际={after_clear_id} ← 脏数据！")
        assume(after_clear_name is None,
               f"clear 后 goods_name 应为 None，实际={after_clear_name} ← 脏数据！")

    print("\n✅ 文件2完成：set → get → 用 → clear → 验证清空，完整闭环")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
