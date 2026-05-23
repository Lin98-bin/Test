import os
import shutil
import sys
import pytest

def main():
    result_dir = "allure-results"
    config_dir = "config"

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

    # 启动 Allure 动态服务（阻塞运行，不关闭则一直可用）
    print("="*60)
    print("Allure 服务已启动，访问以下地址查看报告：")
    print("http://localhost:5050")
    print("注意：不要关闭此窗口，关闭则服务停止")
    print("="*60)
    os.system(f"allure serve {result_dir} -p 5050")

if __name__ == '__main__':
    # 核心：必须加 --alluredir=allure-results，标签才能写入报告
    pytest.main(["-vs", ".", "--alluredir=allure-results"])