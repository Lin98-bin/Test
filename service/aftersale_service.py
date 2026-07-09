from core.api_client import RequestsClient
from core import setting


class AfterSaleService:
    """售后相关接口封装"""

    def __init__(self):
        self.client = RequestsClient()

    def apply(self, order_id, goods_id, reason, amount,
              atype="refund", order_item_id=0, token=None):
        """申请售后"""
        self.client.url = f"{setting.BASE_URL}/api/aftersale/apply"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {
            "order_id": order_id,
            "order_item_id": order_item_id,
            "goods_id": goods_id,
            "type": atype,
            "reason": reason,
            "amount": amount,
        }
        return self.client.send()

    def get_list(self, token=None):
        """获取售后列表"""
        self.client.url = f"{setting.BASE_URL}/api/aftersale/list"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def get_detail(self, as_id, token=None):
        """获取售后详情"""
        self.client.url = f"{setting.BASE_URL}/api/aftersale/detail/{as_id}"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()
