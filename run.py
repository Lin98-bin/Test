import os
import pytest
import shutil
import argparse
import subprocess

def run_tests():
    # 1. 解析参数
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="test", help="环境: test/beta/prod")
    parser.add_argument("--m", default=None, help="标记过滤")
    args = parser.parse_args()
    
    # 2. 构造 Pytest 参数
    # --clean-alluredir 会自动清理旧数据，无需手动删除文件夹
    pytest_args = ['-s', '-v', 'testcases/', '--alluredir=allure-results', f'--env={args.env}', '-m', args.env]
    if args.m:
        pytest_args[-1] = f"{args.env} and {args.m}"
    
    print(f"开始测试... 环境: {args.env}")
    pytest.main(pytest_args)
    
    # 3. 注入 Allure 配置
    res_dir = 'allure-results'
    os.makedirs(res_dir, exist_ok=True)
    for f in ['environment.properties', 'categories.json', 'executor.json']:
        src = os.path.join('config', f)
        if os.path.exists(src):
            shutil.copy(src, res_dir)
    
    # 4. 生成报告
    print("生成报告中...")
    subprocess.run("allure generate allure-results -o allure-report --clean --single-file", shell=True)
    print(f"\n报告已生成: {os.path.abspath('allure-report/index.html')}")

if __name__ == "__main__":
    run_tests()
