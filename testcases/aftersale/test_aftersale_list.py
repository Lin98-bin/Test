""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.aftersale_service import AfterSaleService

@allure.feature("aftersale模块")
@pytest.mark.parametrize("case", read_yaml_testcases('aftersale/aftersale_list'))
def test_aftersale_list(case, login_token):
    allure.dynamic.title(case["name"])
    expected = case['expected']
    
    resp = AfterSaleService().get_list(token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    assume("list" in resp_json.get("data", {}))
