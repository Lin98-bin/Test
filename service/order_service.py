from core.api_client import RequestsClient
from core import setting

class OrderService:
    """订单相关接口封装"""
    
    def __init__(self):
        self.client = RequestsClient()

    def create(self, goods_id, num=1, token=None):
        """创建订单接口"""
        self.client.url = f"{setting.BASE_URL}/api/order/create"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {
            "goods_id": goods_id,
            "num": num
        }
        return self.client.send()

    def pay(self, order_id, token=None):
        """支付订单接口"""
        self.client.url = f"{setting.BASE_URL}/api/order/pay"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {
            "order_id": order_id
        }
        return self.client.send()

    def get_status(self, order_id, token=None):
        """查询订单状态接口"""
        self.client.url = f"{setting.BASE_URL}/api/order/status/{order_id}"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()
