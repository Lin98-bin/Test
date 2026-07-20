""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.review_service import ReviewService
from core.db_handler import db

@allure.feature("review模块")
@pytest.mark.parametrize("case", read_yaml_testcases('review/review_list'))
def test_review_list(case):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    
    resp = ReviewService().get_list(goods_id=d.get('goods_id', 1))
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])

    # DB 断言：验证该商品的评论数量
    if resp_json.get("code") == 200:
        gid = d.get('goods_id', 1)
        db_count = db.query("SELECT COUNT(*) AS cnt FROM review WHERE goods_id=%s", args=(gid,), one=True)
        assume(db_count is not None, "DB: review 表查询不应为空")
        assume(db_count["cnt"] > 0, f"DB: goods_id={gid} 的评论数量应大于0, 实际={db_count['cnt']}")
