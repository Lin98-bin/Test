""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.review_service import ReviewService
from core.db_handler import db

@allure.feature("review模块")
@pytest.mark.parametrize("case", read_yaml_testcases('review/review_my'))
def test_review_my(case, login_token):
    allure.dynamic.title(case["name"])
    expected = case['expected']
    
    resp = ReviewService().get_my(token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])

    # DB 断言：验证 test_0006 用户的评论数量
    if resp_json.get("code") == 200:
        db_count = db.query(
            "SELECT COUNT(*) AS cnt FROM review WHERE user_id=(SELECT id FROM user WHERE username='test_0006')",
            one=True
        )
        assume(db_count is not None, "DB: review 表查询不应为空")
        assume(db_count["cnt"] > 0, f"DB: test_0006 的评论数量应大于0, 实际={db_count['cnt']}")
