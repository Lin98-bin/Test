"""处理售后 — 数据驱动用例"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from core.api_client import RequestsClient
from service.admin_service import AdminService
from service.order_service import OrderService
from service.aftersale_service import AfterSaleService
from utils.yaml_utils import read_yaml_testcases
from core import setting
from core.db_handler import db

def _completed_order(token, gid=1):
    oid = OrderService().create(goods_id=gid, quantity=1, token=token).json()["data"]["order_id"]
    OrderService().pay(oid, token=token)
    c = RequestsClient()
    c.url = f"{setting.BASE_URL}/api/order/confirm/{oid}"; c.method = "put"; c.headers = {"sessionToken": token}
    c.send()
    return oid, gid

@allure.feature("管理员模块")
@allure.story("处理售后")
@pytest.mark.parametrize("case", read_yaml_testcases('admin/admin_aftersale_handle'))
def test_admin_aftersale_handle(case, login_token, admin_token):
    allure.dynamic.title(case['name'])
    d = case.get('data', {})
    expected = case['expected']

    oid, gid = _completed_order(login_token, gid=2)
    apply_resp = AfterSaleService().apply(
        order_id=oid, goods_id=gid, reason="管理处理测试",
        amount=1.0, atype="refund", token=login_token
    )
    as_id = apply_resp.json()["data"]["id"]

    resp = AdminService().handle_aftersale(
        as_id, action=d.get("action"), reply=d.get("reply", ""), token=admin_token
    )
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])

    # DB 断言：验证售后状态和回复已更新
    if resp_json.get("code") == 200:
        action = d.get("action")
        reply = d.get("reply", "")
        db_as = db.query("SELECT status, reply FROM after_sale WHERE id=%s", args=(as_id,), one=True)
        assume(db_as is not None, f"DB: 售后记录 id={as_id} 应存在")
        status_map = {"approve": "approved", "reject": "rejected"}
        expected_status = status_map.get(action, action)
        assume(db_as.get("status") == expected_status,
               f"DB: status 应匹配, 期望={expected_status}, 实际={db_as.get('status')}")
        assume(db_as.get("reply") == reply,
               f"DB: reply 应匹配, 期望={reply}, 实际={db_as.get('reply')}")
