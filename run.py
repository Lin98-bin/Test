
import os
import sys
import shutil  # 用来复制文件



# 第一步：执行用例 + 生成allure结果
print("===== 开始执行用例，生成 Allure 结果 =====")
os.system("pytest testcases/test_register.py testcases/test_login.py -v --alluredir=allure-results --clean-alluredir")

# ======================
# 【我加的：自动复制 3 个文件】
# ======================
print("===== 自动复制环境配置文件到 allure-results =====")
files_to_copy = [
    "config/environment.properties",
    "config/categories.json",
    "config/executor.json"
]
#遍历列表里面三个文件
for file in files_to_copy:
    #当前路径如果存在这个文件
    if os.path.exists(file):
        #把三个文件复制到"allure-results/"目录里面
        shutil.copy(file, "allure-results/")

        print(f" 已复制 {file}")

        print(f"✅ 已复制 {file}")


# ======================
# 你原来的打开报告
# ======================

# 第二步：直接打开 Allure 报告
print("===== 启动 Allure 报告服务 =====")
#os.system("allure serve allure-results")