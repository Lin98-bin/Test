from jsonpath_ng import parse


class JsonPathExtractor:
    """
    jsonpath 提取工具类
    用法：
        extractor = JsonPathExtractor()
        token = extractor.extract(response.json(), "$.data.token")
    """

    def extract(self, data, jsonpath_expr):
        """
        从数据中提取单个值
        :param data: dict/list 类型的数据
        :param jsonpath_expr: jsonpath 表达式，如 "$.data.token"
        :return: 提取到的值，未找到返回 None
        """
        try:
            jsonpath_expr = parse(jsonpath_expr)
            result = jsonpath_expr.find(data)
            if len(result) > 0:
                return result[0].value
            return None
        except Exception as e:
            print(f"jsonpath 提取失败: {e}")
            return None

    def extract_all(self, data, jsonpath_expr):
        """
        从数据中提取所有匹配的值（返回列表）
        :param data: dict/list 类型的数据
        :param jsonpath_expr: jsonpath 表达式
        :return: 列表
        """
        try:
            jsonpath_expr = parse(jsonpath_expr)
            result = jsonpath_expr.find(data)
            return [match.value for match in result]
        except Exception as e:
            print(f"jsonpath 提取失败: {e}")
            return []
