""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.member_service import MemberService
from core.db_handler import db

@allure.feature("member模块")
@pytest.mark.parametrize("case", read_yaml_testcases('member/member_activate'))
def test_member_activate(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    
    resp = MemberService().activate(months=d.get('months'), token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])
    if expected["code"] == 200:
        assume(resp_json.get("data", {}).get("is_member") is True)

        # DB 断言：验证数据库中 is_member=1
        db_user = db.query("SELECT is_member FROM user WHERE username='test_0006'", one=True)
        assume(db_user is not None, "DB: test_0006 用户应存在")
        assume(db_user["is_member"] == 1, f"DB: is_member 应为1, 实际={db_user['is_member']}")
