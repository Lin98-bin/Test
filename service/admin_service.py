from core.api_client import RequestsClient
from core import setting


class AdminService:
    """管理员接口封装"""

    def __init__(self):
        self.client = RequestsClient()

    def get_paid_orders(self, token=None):
        """获取待发货订单列表"""
        self.client.url = f"{setting.BASE_URL}/api/admin/orders/paid"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def ship_order(self, order_id, tracking="", token=None):
        """发货"""
        self.client.url = f"{setting.BASE_URL}/api/admin/order/ship/{order_id}"
        self.client.method = "put"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {"tracking": tracking} if tracking else {}
        return self.client.send()

    def get_pending_aftersale(self, token=None):
        """获取待处理售后列表"""
        self.client.url = f"{setting.BASE_URL}/api/admin/aftersale/pending"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def handle_aftersale(self, as_id, action, reply, token=None):
        """处理售后"""
        self.client.url = f"{setting.BASE_URL}/api/admin/aftersale/{as_id}"
        self.client.method = "put"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {"action": action, "reply": reply}
        return self.client.send()
