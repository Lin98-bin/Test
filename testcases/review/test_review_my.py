""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.review_service import ReviewService

@allure.feature("review模块")
@pytest.mark.parametrize("case", read_yaml_testcases('review/review_my'))
def test_review_my(case, login_token):
    allure.dynamic.title(case["name"])
    expected = case['expected']
    
    resp = ReviewService().get_my(token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
