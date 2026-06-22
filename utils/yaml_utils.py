import os
import yaml

def read_yaml_testcases(file_name):
    """
    读取 data 目录下的 YAML 测试数据文件
    :param file_name: 文件名（不含扩展名），如 'login'
    :return: 测试用例列表
    """
    # 1. 定位项目根目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 2. 拼接文件路径 (data/{file_name}.yaml)
    file_path = os.path.join(base_dir, "data", f"{file_name}.yaml")
    
    # 3. 读取 YAML 内容
    if os.path.exists(file_path) is False:
        raise FileNotFoundError(f"测试数据文件未找到: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    # 如果 YAML 文件以 testcases 作为根键，则返回其列表部分
    if isinstance(data, dict) and "testcases" in data:
        return data["testcases"]
        
    return data
