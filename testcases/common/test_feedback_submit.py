""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.common_service import CommonService
from core.db_handler import db


@allure.feature("common模块")
@pytest.mark.parametrize("case", read_yaml_testcases('common/feedback_submit'))
def test_feedback_submit(case, login_token):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']

    resp = CommonService().submit_feedback(
        contact=d.get('contact', ''),
        content=d.get('content', ''),
        fb_type=d.get('type', 'suggestion'),
        token=login_token
    )
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])

    if expected["code"] == 200:
        # 验证返回数据包含反馈ID
        data = resp_json.get("data", {})
        assume(data.get("id") is not None and data.get("id") > 0, "反馈ID应存在且>0")
        assume(data.get("type") == d.get('type', 'suggestion'), f"反馈类型应为 {d.get('type')}")
        assume(data.get("contact") == d.get('contact', ''), f"联系方式应为 {d.get('contact')}")

        # DB 断言：验证反馈记录已写入
        feedback = db.query(
            "SELECT * FROM feedback WHERE user_id=(SELECT id FROM user WHERE username=%s) ORDER BY id DESC LIMIT 1",
            args=('test_0006',),
            one=True
        )
        assume(feedback is not None, "DB: feedback 记录应存在")
        assume(feedback.get("contact") == d.get('contact', ''), f"DB: contact应为 {d.get('contact')}")
        assume(feedback.get("type") == d.get('type', 'suggestion'), f"DB: type应为 {d.get('type')}")
