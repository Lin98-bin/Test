import pytest


# 自动把 pytest 标记 → 转成 Allure 套件分组（和你截图完全一致）
def pytest_collection_modifyitems(config, items):
    for item in items:
        # 获取用例上的所有标记
        marks = [m.name for m in item.iter_markers()]

        # 自动匹配分组
        if "smoke" in marks:
            # 冒烟用例
            item._obj.__setattr__("allure_parent_suite", "接口测试套件")
            item._obj.__setattr__("allure_suite", "冒烟测试")
        elif "beta_run" in marks:
            # Beta用例
            item._obj.__setattr__("allure_parent_suite", "接口测试套件")
            item._obj.__setattr__("allure_suite", "Beta测试")
        elif "prod_run" in marks or "test_run" in marks:
            # 全量/生产用例
            item._obj.__setattr__("allure_parent_suite", "接口测试套件")
            item._obj.__setattr__("allure_suite", "全量测试")


# 消除标记警告（解决你日志里的黄色警告）
def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "beta_run: Beta测试")
    config.addinivalue_line("markers", "prod_run: 生产测试")
    config.addinivalue_line("markers", "test_run: 测试环境")