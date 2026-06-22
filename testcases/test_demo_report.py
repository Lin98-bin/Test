import pytest
import allure

@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("test全量用例")
@allure.feature("演示报告分类")
@allure.tag("test")
@pytest.mark.test
@allure.story("正常通过用例")
def test_success_demo():
    """这个用例会正常通过，不会出现在'类别'里"""
    assert True

@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("test全量用例")
@allure.feature("演示报告分类")
@allure.tag("test")
@pytest.mark.test
@allure.story("断言失败用例")
def test_fail_demo():
    """这个用例会断言失败，出现在'业务功能缺陷'里"""
    allure.attach("期望值: 200, 实际值: 400", name="失败原因")
    assert 200 == 400

@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("test全量用例")
@allure.feature("演示报告分类")
@allure.tag("test")
@pytest.mark.beta
@allure.story("脚本报错用例")
def test_broken_demo():
    """这个用例会抛出异常，出现在'测试脚本异常'里"""
    raise Exception("数据库连接超时 (模拟脚本异常)")

@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("test全量用例")
@allure.feature("演示报告分类")
@allure.tag("test")
@pytest.mark.master
@allure.story("跳过执行用例")
def test_skip_demo():
    """这个用例会被跳过，出现在'跳过执行用例'里"""
    pytest.skip("演示跳过逻辑")
