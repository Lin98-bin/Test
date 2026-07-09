import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from service.user_service import UserService
from utils.yaml_utils import read_yaml_testcases
import allure
from pytest_assume.plugin import assume

# 1. 读取 YAML 测试数据
test_data = read_yaml_testcases('address')

@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("test全量用例")
@allure.epic("用户模块")
@allure.feature("收货地址接口")
@allure.story("新增地址")
@allure.tag("test")
@pytest.mark.test
@pytest.mark.parametrize("case", test_data)
def test_add_address(case, login_token): # 传入 login_token 夹具
    """新增地址测试用例"""
    allure.dynamic.title(f"用例：{case['name']}")
    user_service = UserService()
    
    address = case['address']
    contact = case['contact']
    phone = case['phone']
    expected = case['expected']
    
    with allure.step(f"步骤1：发送新增地址请求 - {case['name']}"):
        # 调用 Service 方法，并传入从 conftest 拿到的 login_token
        resp = user_service.add_address(
            address_detail=address,
            contact_name=contact,
            contact_phone=phone,
            token=login_token
        )
        resp_json = resp.json()

    with allure.step("步骤2：断言结果"):
        actual_code = resp_json.get("code")
        expected_code = expected.get("code")
        
        assume(actual_code == expected_code, f"状态码不匹配：期望 {expected_code}，实际 {actual_code}")
        
        if "msg" in expected:
            assume(resp_json.get("msg") in (expected["msg"], "ok"))
        if "error" in expected:
            assume(resp_json.get("error") == expected["error"])
            
    print(f"用例【{case['name']}】执行完成")

if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
