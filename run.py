import os
import pytest
import shutil
import argparse
import subprocess

def run_tests():
    """执行测试并生成报告"""
    # 1. 解析命令行参数
    parser = argparse.ArgumentParser(description="接口自动化测试运行入口")
    parser.add_argument("--env", default="test", help="输入运行环境: test, beta 或 prod")
    args = parser.parse_args()

    env = args.env
    print(f"[INFO] Start automated testing... Env: {env}")

    # 2. 清理旧的报告数据
    if os.path.exists('allure-results'):
        shutil.rmtree('allure-results')

    # 3. 执行 pytest
    # 将 --env 参数传递给 pytest，由 conftest.py 接收
    pytest_args = ['-s', '-v', 'testcases/', '--alluredir=./allure-results', f'--env={env}']
    pytest.main(pytest_args)

    # --- Load Allure Metadata ---
    config_dir = './config'
    results_dir = './allure-results'
    # List of files to load into Allure
    allure_config_files = ['environment.properties', 'categories.json', 'executor.json']

    print("\n[INFO] Loading Allure metadata...")
    for file_name in allure_config_files:
        src_file = os.path.join(config_dir, file_name)
        if os.path.exists(src_file):
            shutil.copy(src_file, results_dir)
            print(f"  - Loaded: {file_name}")
    # ------------------------------------------------------------------

    # 4. 生成静态 HTML 报告目录
    print("\n[INFO] Generating standard Allure report...")
    subprocess.run(
        "allure generate ./allure-results -o ./allure-report --clean",
        shell=True, check=True,
    )

    # 5. 将报告压缩成单个可直接打开的静态 HTML 文件
    print("\n[INFO] Combining into single static HTML report...")
    try:
        subprocess.run(
            "allure-combine ./allure-report",
            shell=True, check=True,
        )
        print("[SUCCESS] Combined successfully! Check complete.html in allure-report directory.")
        print("[TIP] You can double-click complete.html to view in browser.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[ERROR] Combination failed: {e}")

if __name__ == "__main__":
    run_tests()
