import yaml
import os


def read_yaml(file_path):
    """
    读取 YAML 测试数据文件
    :param file_path: YAML 文件路径
    :return: 测试数据列表
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 返回 testcases 列表
    return data.get('testcases', [])


def read_yaml_testcases(yaml_name):
    """
    从 data/yaml 目录读取测试用例
    :param yaml_name: YAML 文件名（不含扩展名）
    :return: 测试数据列表
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(base_dir, 'data', 'yaml', f'{yaml_name}.yaml')
    return read_yaml(yaml_path)


# 测试
if __name__ == '__main__':
    testcases = read_yaml_testcases('login')
    for case in testcases:
        print(f"用例: {case['name']}, 用户: {case['username']}")