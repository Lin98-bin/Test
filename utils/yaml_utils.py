import os
import yaml


def read_yaml_testcases(file_path):
    """
    读取 data/{file_path}.yaml 测试数据文件。
    :param file_path: data/ 下的相对路径（不含 .yaml），如 'login' 或 'address/address_add'
    :return: 测试用例列表
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, "data", f"{file_path}.yaml")

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"测试数据文件未找到: {full_path}")

    with open(full_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if data is None:
        return []

    # 兼容 testcases 包装、裸列表、单个用例
    if isinstance(data, dict) and "testcases" in data:
        return data["testcases"]
    elif isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]

    return []
