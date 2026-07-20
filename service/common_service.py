from core.api_client import RequestsClient
from core import setting


class CommonService:
    """通用接口封装 — 演示表单参数 & 文件上传"""

    def __init__(self):
        self.client = RequestsClient()

    def submit_feedback(self, contact, content, fb_type="suggestion", token=None):
        """提交用户反馈 — 演示表单参数（data）

        :param contact: 联系方式
        :param content: 反馈内容
        :param fb_type: 反馈类型 suggestion/bug/complaint/other
        :param token: 登录令牌
        """
        self.client.url = f"{setting.BASE_URL}/api/feedback/submit"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        # ★ 使用 data 而非 json，以表单参数方式提交
        self.client.data = {
            "contact": contact,
            "content": content,
            "type": fb_type
        }
        # 清除可能的残留参数，避免请求参数污染
        self.client.json = None
        self.client.files = None
        self.client.params = None
        return self.client.send()

    def upload_avatar(self, file_path, token=None):
        """上传用户头像 — 演示文件上传参数（files）

        :param file_path: 本地图片文件路径
        :param token: 登录令牌
        """
        self.client.url = f"{setting.BASE_URL}/api/user/avatar"
        self.client.method = "post"
        self.client.headers = {"sessionToken": token} if token else {}
        # 清除可能的残留参数，避免请求参数污染
        self.client.data = None
        self.client.json = None
        self.client.params = None
        # ★ 使用 files 参数上传文件
        f = open(file_path, "rb")
        self.client.files = {"avatar": f}
        try:
            return self.client.send()
        finally:
            f.close()  # 确保文件句柄被关闭
