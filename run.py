import os
import shutil
import sys
import pytest

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




if __name__ == '__main__':
    main()