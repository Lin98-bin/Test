from core.api_client import RequestsClient
from core import setting

class UserService:
    """用户相关接口封装"""
    
    def __init__(self):
        self.client = RequestsClient()

    def login(self, username, password, token=None):
        """登录接口"""
        self.client.url = f"{setting.BASE_URL}/login"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {
            "username": username,
            "password": str(password)
        }
        return self.client.send()

    def register(self, username, password):
        """注册接口"""
        self.client.url = f"{setting.BASE_URL}/register"
        self.client.method = "post"
        self.client.json = {
            "username": username,
            "password": str(password)
        }
        return self.client.send()

    def get_info(self, token):
        """获取用户信息接口"""
        self.client.url = f"{setting.BASE_URL}/api/user/info"
        self.client.method = "get"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def logout(self, token):
        """退出登录接口"""
        self.client.url = f"{setting.BASE_URL}/api/logout"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        return self.client.send()

    def update_info(self, nickname, token):
        """修改用户信息接口"""
        self.client.url = f"{setting.BASE_URL}/api/user/update"
        self.client.method = "put"
        self.client.headers = {"sessionToken": token} if token else {}
        self.client.json = {"nickname": nickname}
        return self.client.send()
