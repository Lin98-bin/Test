"""分类模块 — 数据驱动用例"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import allure
from pytest_assume.plugin import assume
from core.api_client import RequestsClient
from utils.yaml_utils import read_yaml_testcases
from core import setting

test_data = read_yaml_testcases('category_list')


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("冒烟用例")
@allure.epic("分类模块")
@allure.feature("分类列表")
@allure.story("获取分类列表")
@pytest.mark.parametrize("case", test_data)
def test_category_list(case):
    allure.dynamic.title(f"用例：{case['name']}")
    expected = case['expected']
    params = case.get('params', {})

    with allure.step("步骤1：发送获取分类列表请求"):
        url = setting.BASE_URL + "/api/category/list"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url += f"?{qs}"

        client = RequestsClient()
        client.url = url
        client.method = "get"
        client.headers = setting.COMMON_HEADERS.copy()
        resp = client.send()
        resp_json = resp.json()
        print(f"响应：{resp_json}")

    with allure.step("步骤2：断言结果"):
        assume(resp_json.get("code") == expected["code"],
               f"期望 code={expected['code']}，实际={resp_json.get('code')}")

        data = resp_json.get("data", {})
        categories = data.get("list", []) if isinstance(data, dict) else []

        print(f"分类数量：{len(categories)}")
        allure.attach(str(categories)[:500], name="分类列表", attachment_type=allure.attachment_type.JSON)

        if case.get("scenario") == "success":
            assume(len(categories) > 0, "分类列表不应为空")
            assume("id" in categories[0], "分类缺少id字段")
            assume("name" in categories[0], "分类缺少name字段")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
