from core.api_client import RequestsClient
from core import setting


class SystemService:
    """系统工具接口封装 — 演示多自定义 Header 用法

    展示如何在一个请求中同时携带：
        sessionToken  （鉴权 token）
        User-Agent    （模拟客户端类型）
        tenantId      （多租户 ID）
        deviceId      （设备标识）
    """

    def __init__(self):
        self.client = RequestsClient()

    def get_headers_info(self, token=None, user_agent=None,
                         tenant_id=None, device_id=None):
        """回显请求头 — 演示多 Header 组合传参

        :param token:      登录令牌（放入 sessionToken header）
        :param user_agent: 模拟的 User-Agent（如 iPhone/Chrome）
        :param tenant_id:  租户 ID（多租户系统必备）
        :param device_id:  设备标识（APP 接口必带）
        """
        self.client.url = f"{setting.BASE_URL}/api/system/headers"
        self.client.method = "get"

        # ★ 核心：多 Header 拼装方式
        # 先放入鉴权 token
        headers = {"sessionToken": token} if token else {}

        # 再逐个叠加业务 Header（只传非空的，避免无意义的 header）
        if user_agent:
            headers["User-Agent"] = user_agent
        if tenant_id:
            headers["tenantId"] = tenant_id
        if device_id:
            headers["deviceId"] = device_id

        self.client.headers = headers

        # 清理残留参数
        self.client.params = None
        self.client.data = None
        self.client.json = None
        self.client.files = None

        return self.client.send()
