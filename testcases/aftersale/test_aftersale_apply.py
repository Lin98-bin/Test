""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure, uuid
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.aftersale_service import AfterSaleService
from service.order_service import OrderService
from core.api_client import RequestsClient
from core import setting
from core.db_handler import db

def _completed_order_via_db(gid=1):
    """DB 直插已完成订单 — 不依赖下单/支付/确认接口，测试隔离"""
    uid_row = db.query("SELECT id FROM user WHERE username='test_0006'", one=True)
    uid = uid_row["id"]

    goods = db.query("SELECT name FROM goods WHERE id=%s", args=(gid,), one=True)
    goods_name = goods["name"] if goods else "测试商品"

    addr = db.query("SELECT id FROM address WHERE user_id=%s LIMIT 1", args=(uid,), one=True)
    addr_id = addr["id"] if addr else 1

    order_no = f"TEST_{uuid.uuid4().hex[:12].upper()}"

    db.execute(
        "INSERT INTO orders(order_no, user_id, goods_id, goods_name, price, quantity, total, status, address_id, address_snapshot) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,'completed',%s,%s)",
        (order_no, uid, gid, goods_name, 99.00, 1, 99.00, addr_id, "DB直插测试订单")
    )

    oid = db.query("SELECT LAST_INSERT_ID() as id", one=True)["id"]
    return oid, gid

@allure.feature("aftersale模块")
@pytest.mark.parametrize("case", read_yaml_testcases('aftersale/aftersale_apply'))
def test_aftersale_apply(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    oid, gid = _completed_order_via_db()
    
    resp = AfterSaleService().apply(order_id=oid, goods_id=gid, reason=d.get('reason', ''), amount=d.get('amount', 1.0), atype=d.get('atype', 'refund'), token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])

    # DB 断言：验证售后记录已写入数据库
    if resp_json.get("code") == 200:
        uid_row = db.query("SELECT id FROM user WHERE username='test_0006'", one=True)
        uid = uid_row["id"]
        db_as = db.query(
            "SELECT * FROM after_sale WHERE user_id=%s ORDER BY id DESC LIMIT 1",
            args=(uid,), one=True
        )
        assume(db_as is not None, "DB: 最新售后记录应存在")
        atype = d.get('atype', 'refund')
        assume(db_as.get("type") == atype, f"DB: type 应为 {atype}, 实际={db_as.get('type')}")
        assume(db_as.get("status") == 'pending', f"DB: status 应为 'pending', 实际={db_as.get('status')}")
