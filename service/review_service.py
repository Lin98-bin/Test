from core.api_client import RequestsClient
from core import setting


class ReviewService:
    """评价相关接口封装"""

    def __init__(self):
        self.client = RequestsClient()

    def add(self, order_id, goods_id, rating=5, content="好评", token=None):
        """发表评价"""
        self.client.url = f"{setting.BASE_URL}/api/review/add"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {
            "order_id": order_id,
            "goods_id": goods_id,
            "rating": rating,
            "content": content,
        }
        return self.client.send()

    def get_list(self, goods_id):
        """获取商品评价列表"""
        self.client.url = f"{setting.BASE_URL}/api/review/list/{goods_id}"
        self.client.method = "get"
        return self.client.send()

    def get_my(self, token=None):
        """获取我的评价"""
        self.client.url = f"{setting.BASE_URL}/api/review/my"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()
