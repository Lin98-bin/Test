import os
import shutil

# 第一步：执行用例 + 生成allure结果
print("===== 开始执行用例，生成 Allure 结果 =====")
os.system("pytest testcases/test_register.py testcases/test_login.py -v --alluredir=allure-results --clean-alluredir")

# ======================
# 自动复制 3 个配置文件（保留你要的功能）
# ======================
print("===== 自动复制环境配置文件到 allure-results =====")
files_to_copy = [
    "config/environment.properties",
    "config/categories.json",
    "config/executor.json"
]

for file in files_to_copy:
    if os.path.exists(file):
        shutil.copy(file, "allure-results/")
        print(f" 已复制 {file}")

# ======================
# 【关键】只生成静态 HTML 报告，不打开、不弹窗！
# ======================
print("===== 生成静态 Allure HTML 报告 =====")
os.system("allure generate allure-results -o allure-report --clean")

print("\n全部完成！报告已生成在 allure-report 文件夹")