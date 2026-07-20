""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.review_service import ReviewService
from service.order_service import OrderService
from core.api_client import RequestsClient
from core import setting
from core.db_handler import db

def _completed_order(token, gid=1):
    oid = OrderService().create(goods_id=gid, quantity=1, token=token).json()["data"]["order_id"]
    OrderService().pay(oid, token=token)
    c = RequestsClient()
    c.url = f"{setting.BASE_URL}/api/order/confirm/{oid}"
    c.method = "put"
    c.headers = {"sessionToken": token}
    c.send()
    return oid

@allure.feature("review模块")
@pytest.mark.parametrize("case", read_yaml_testcases('review/review_add'))
def test_review_add(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    oid = _completed_order(login_token, gid=5)
    
    resp = ReviewService().add(order_id=oid, goods_id=5, rating=d.get('rating', 5), content=d.get('content', ''), token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])

    # DB 断言：验证评论已写入数据库
    if resp_json.get("code") == 200:
        uid_row = db.query("SELECT id FROM user WHERE username='test_0006'", one=True)
        uid = uid_row["id"]
        db_review = db.query(
            "SELECT * FROM review WHERE user_id=%s ORDER BY id DESC LIMIT 1",
            args=(uid,), one=True
        )
        assume(db_review is not None, "DB: 最新评论应存在")
        assume(db_review.get("order_id") == oid,
               f"DB: order_id 应匹配, 期望={oid}, 实际={db_review.get('order_id')}")
        assume(db_review.get("rating") == d.get('rating', 5),
               f"DB: rating 应匹配, 期望={d.get('rating', 5)}, 实际={db_review.get('rating')}")
