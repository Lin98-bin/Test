import os
import shutil
import sys
import pytest

import sys
import os
import subprocess

def main():
    root_path = os.path.dirname(os.path.abspath(__file__))
    result_dir = os.path.join(root_path, "allure-results")
    config_dir = os.path.join(root_path, "config")
    # 获取当前脚本所在的根目录

    # 清理历史数据
    if os.path.exists(result_dir):
        shutil.rmtree(result_dir)
    os.makedirs(result_dir, exist_ok=True)

    # 复制 Allure 配置文件（环境、分类信息）
    config_files = ["categories.json", "environment.properties", "executor.json"]
    for file in config_files:
        src = os.path.join(config_dir, file)
        dst = os.path.join(result_dir, file)
        if os.path.exists(src):
            shutil.copy(src, dst)

    # 执行测试用例
    print("开始执行测试用例...")
    pytest_cmd = f'"{sys.executable}" -m pytest testcases/ -v -s --alluredir={result_dir}'
    os.system(pytest_cmd)


def run_test():
    print("===== 开始执行自动化测试用例 =====")

    # 1. 运行 pytest，生成 allure 报告数据
    pytest_cmd = [sys.executable, "-m", "pytest", "-v", "-s", "--alluredir=allure-results"]
    result = subprocess.run(pytest_cmd)

    # 2. 判断用例结果
    if result.returncode == 0:
        print("所有用例执行通过！")
    else:
        print("有用例失败！")

    # 3. 打开 allure 报告（修复版！Windows 必用）
    print("===== 打开 Allure 报告 =====")
    os.system("allure serve allure-results")  # 用这个就不会报错！

if __name__ == '__main__':
    main()
    run_test()