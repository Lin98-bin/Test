""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.system_service import SystemService


@allure.feature("system模块")
@pytest.mark.parametrize("case", read_yaml_testcases('system/system_headers'))
def test_system_headers(case, login_token):
    allure.dynamic.title(case["name"])
    h = case.get('headers', {})
    expected = case['expected']

    # ★ 核心：读取 YAML 中的 header 配置（None 表示不传该 header）
    user_agent = h.get('user_agent')
    tenant_id = h.get('tenant_id')
    device_id = h.get('device_id')

    resp = SystemService().get_headers_info(
        token=login_token,
        user_agent=user_agent,
        tenant_id=tenant_id,
        device_id=device_id
    )
    resp_json = resp.json()

    assume(resp_json.get("code") == expected["code"])

    if expected["code"] == 200:
        data = resp_json.get("data", {})

        # 断言：用户信息正确
        user_info = data.get("user_info", {})
        assume(user_info.get("username") == "test_0006",
               f"username应为test_0006, 实际={user_info.get('username')}")
        assume(user_info.get("user_id") is not None and user_info.get("user_id") > 0,
               "user_id应存在且>0")

        # 断言：接收到的 headers 与发送的一致
        received = data.get("received_headers", {})

        # User-Agent：requests 库自带默认值 python-requests/x.x.x，
        # 只有显式传了 user_agent 才能覆盖。这是真实项目中的关键点。
        if user_agent:
            assume(received.get("User-Agent") == user_agent,
                   f"User-Agent应回显'{user_agent}', 实际='{received.get('User-Agent')}'")
        else:
            assume("python-requests" in received.get("User-Agent", ""),
                   f"未传User-Agent时，requests库默认UA应包含'python-requests'")

        expected_tid = tenant_id if tenant_id else "(not set)"
        assume(received.get("tenantId") == expected_tid,
               f"tenantId应回显'{expected_tid}', 实际='{received.get('tenantId')}'")

        expected_did = device_id if device_id else "(not set)"
        assume(received.get("deviceId") == expected_did,
               f"deviceId应回显'{expected_did}', 实际='{received.get('deviceId')}'")

        # 断言：客户端类型识别
        if "client_type" in expected:
            assume(data.get("client_type") == expected["client_type"],
                   f"client_type应为{expected['client_type']}, "
                   f"实际={data.get('client_type')}")
