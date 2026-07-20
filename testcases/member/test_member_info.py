""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.member_service import MemberService
from core.db_handler import db

@allure.feature("member模块")
@pytest.mark.parametrize("case", read_yaml_testcases('member/member_info'))
def test_member_info(case, login_token):
    allure.dynamic.title(case["name"])
    expected = case['expected']
    
    resp = MemberService().get_info(token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    assume("is_member" in resp_json.get("data", {}))

    # DB 断言：验证用户 is_member 字段存在
    if resp_json.get("code") == 200:
        db_user = db.query("SELECT is_member FROM user WHERE username='test_0006'", one=True)
        assume(db_user is not None, "DB: test_0006 用户应存在")
        assume("is_member" in db_user, "DB: user 表应包含 is_member 字段")
