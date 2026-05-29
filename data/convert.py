"""
Excel 转 YAML 工具
测试人员用 Excel 维护，执行前转换为 YAML
"""

import openpyxl
import yaml
import os


def excel_to_yaml(excel_path, yaml_path, sheet_name='Sheet1'):
    """
    将 Excel 转换为 YAML
    """
    # 读取 Excel
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb[sheet_name]

    # 获取表头
    headers = [cell.value for cell in sheet[1]]

    # 读取数据
    testcases = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row[0] is None:  # 跳过空行
            continue

        case = {
            'name': row[0],
            'username': row[1],
            'password': str(row[2]),
            'expected': {
                'code': row[3],
                'msg': row[4] if row[4] else None,
                'error': row[5] if len(row) > 5 and row[5] else None
            }
        }
        # 清理 None 值
        case['expected'] = {k: v for k, v in case['expected'].items() if v is not None}
        testcases.append(case)

    # 生成 YAML
    data = {'testcases': testcases}

    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    print(f"✅ 转换完成：{excel_path} → {yaml_path}")
    print(f"   共 {len(testcases)} 条用例")


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Excel 转 YAML
    excel_to_yaml(
        os.path.join(base_dir, 'test.xlsx'),
        os.path.join(base_dir, 'yaml', 'login.yaml')
    )