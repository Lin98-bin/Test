from core.api_client import RequestsClient
from core import setting

class OrderService:
    """订单相关接口封装"""
    
    def __init__(self):
        self.client = RequestsClient()

    def create(self, goods_id, quantity=1, token=None, address_id=None):
        """创建订单接口"""
        self.client.url = f"{setting.BASE_URL}/api/order/create"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        body = {
            "goods_id": goods_id,
            "quantity": quantity,
        }
        if address_id:
            body["address_id"] = address_id
        # 如果没有传 address_id，先去查默认地址
        else:
            from core.api_client import RequestsClient
            client = RequestsClient()
            client.url = f"{setting.BASE_URL}/api/address/list"
            client.method = "get"
            client.headers = {"sessionToken": token}
            resp = client.send()
            addrs = resp.json().get("data", {}).get("list", [])
            if not addrs:
                # 自动创建地址
                client.url = f"{setting.BASE_URL}/api/address/add"
                client.method = "post"
                client.headers = {"sessionToken": token}
                client.json = {"address": "测试地址", "contact": "测试", "phone": "13800138000"}
                client.send()
                # 重新获取地址列表
                client.url = f"{setting.BASE_URL}/api/address/list"
                client.method = "get"
                client.headers = {"sessionToken": token}
                resp = client.send()
                addrs = resp.json().get("data", {}).get("list", [])
            default_addr = next((a for a in addrs if a.get("is_default")), addrs[0])
            body["address_id"] = default_addr["id"]
        self.client.json = body
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
