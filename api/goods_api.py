from common.api_client import RequestsClient
from common import setting

class GoodsApi:
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
        self.client.url = f"{setting.BASE_URL}/api/goods/{goods_id}"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()
