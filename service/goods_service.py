from core.api_client import RequestsClient
from core import setting

class GoodsService:
    """商品相关接口封装"""
    
    def __init__(self):
        self.client = RequestsClient()

    def get_list(self, token=None):
        """获取商品列表"""
        self.client.url = f"{setting.BASE_URL}/api/goods"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def get_detail(self, goods_id, token=None):
        """获取商品详情"""
        self.client.url = f"{setting.BASE_URL}/api/goods/detail/{goods_id}"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def search(self, keyword, token=None):
        """搜索商品"""
        self.client.url = f"{setting.BASE_URL}/api/goods/search?keyword={keyword}"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def filter_goods(self, min_price=0, max_price=0, sort_by="id", order="desc", token=None):
        """商品高级筛选 — 演示查询参数用法"""
        self.client.url = f"{setting.BASE_URL}/api/goods/filter"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.params = {
            "min_price": min_price,
            "max_price": max_price,
            "sort_by": sort_by,
            "order": order
        }
        return self.client.send()
