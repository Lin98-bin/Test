from core.api_client import RequestsClient
from core import setting


class AddressService:
    """收货地址相关接口封装"""

    def __init__(self):
        self.client = RequestsClient()

    def add(self, address, contact, phone, token=None):
        """新增收货地址"""
        self.client.url = f"{setting.BASE_URL}/api/address/add"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {"address": address, "contact": contact, "phone": phone}
        return self.client.send()

    def get_list(self, token=None):
        """获取地址列表"""
        self.client.url = f"{setting.BASE_URL}/api/address/list"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def update(self, addr_id, contact=None, address=None, phone=None, token=None):
        """修改地址"""
        self.client.url = f"{setting.BASE_URL}/api/address/update"
        self.client.method = "put"
        self.client.headers = {"sessionToken": token} if token else {}
        body = {"id": addr_id}
        if contact:
            body["contact"] = contact
        if address:
            body["address"] = address
        if phone:
            body["phone"] = phone
        self.client.json = body
        return self.client.send()

    def set_default(self, addr_id, token=None):
        """设为默认地址"""
        self.client.url = f"{setting.BASE_URL}/api/address/default/{addr_id}"
        self.client.method = "put"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def delete(self, addr_id, token=None):
        """删除地址"""
        self.client.url = f"{setting.BASE_URL}/api/address/delete/{addr_id}"
        self.client.method = "delete"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()
