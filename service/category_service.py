from core.api_client import RequestsClient
from core import setting


class CategoryService:
    """分类相关接口封装"""

    def __init__(self):
        self.client = RequestsClient()

    def get_list(self):
        """获取分类列表"""
        self.client.url = f"{setting.BASE_URL}/api/category/list"
        self.client.method = "get"
        return self.client.send()
