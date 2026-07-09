from core.api_client import RequestsClient
from core import setting


class MemberService:
    """会员相关接口封装"""

    def __init__(self):
        self.client = RequestsClient()

    def get_info(self, token=None):
        """获取会员信息"""
        self.client.url = f"{setting.BASE_URL}/api/member/info"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def activate(self, months, token=None):
        """开通/续费会员"""
        self.client.url = f"{setting.BASE_URL}/api/member/activate"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {"months": months}
        return self.client.send()
