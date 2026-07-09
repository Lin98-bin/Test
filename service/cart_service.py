from core.api_client import RequestsClient
from core import setting


class CartService:
    """购物车相关接口封装"""

    def __init__(self):
        self.client = RequestsClient()

    def add(self, goods_id, quantity=1, specs="", token=None):
        """加入购物车"""
        self.client.url = f"{setting.BASE_URL}/api/cart/add"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {"goods_id": goods_id, "quantity": quantity, "specs": specs}
        return self.client.send()

    def get_list(self, token=None):
        """获取购物车列表"""
        self.client.url = f"{setting.BASE_URL}/api/cart/list"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def count(self, token=None):
        """获取购物车数量"""
        self.client.url = f"{setting.BASE_URL}/api/cart/count"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def update(self, cart_id, quantity, token=None):
        """修改购物车商品数量"""
        self.client.url = f"{setting.BASE_URL}/api/cart/update"
        self.client.method = "put"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {"cart_id": cart_id, "quantity": quantity}
        return self.client.send()

    def delete(self, cart_id, token=None):
        """删除购物车单项"""
        self.client.url = f"{setting.BASE_URL}/api/cart/delete/{cart_id}"
        self.client.method = "delete"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def batch_delete(self, ids, token=None):
        """批量删除购物车"""
        self.client.url = f"{setting.BASE_URL}/api/cart/batch_delete"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {"ids": ids}
        return self.client.send()
