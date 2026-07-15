""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.review_service import ReviewService

@allure.feature("review模块")
@pytest.mark.parametrize("case", read_yaml_testcases('review/review_list'))
def test_review_list(case):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    
    resp = ReviewService().get_list(goods_id=d.get('goods_id', 1))
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
