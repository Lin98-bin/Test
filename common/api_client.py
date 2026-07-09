from.environment import API_TIMEOUT
import time
import requests
import json
#增加重试机制
from tenacity import retry,stop_after_attempt,wait_exponential
from .logger import *

try:
    import allure
except ImportError:
    allure = None

# token赋值为空
# 声明token为全局变量，谁都可以调用
global sessionToken
sessionToken = ""


# 新增：全局上下文存储类
class GlobalContext:
    """全局上下文存储器，支持多用户场景和变量传递"""
    _variables = {}

    @classmethod
    def set(cls, key, value):
        cls._variables[key] = value

    @classmethod
    def get(cls, key, default=None):
        return cls._variables.get(key, default)

    @classmethod
    def clear(cls):
        cls._variables.clear()

# 保持向后兼容（面试时可以提到这种平滑过渡的处理）
class TokenStore(GlobalContext):
    @classmethod
    def set_token(cls, user, token):
        cls.set(f"token_{user}", token)

    @classmethod
    def get_token(cls, user="default"):
        return cls.get(f"token_{user}", "")

# 保持向后兼容
sessionToken = ""
class RequestsClient():
    session = requests.Session()
    def __init__(self):
        self.url=None
        self.headers=None
        self.method=None
        self.params=None
        self.data=None
        self.json=None
        self.files=None
        self.resp=None
        #超时断开
        self.timeout = API_TIMEOUT

    #重试机制：最多重试三次，包含首次，总共重试三次，初次失败，第一次重试是2S后，第二次重试是4S
    @retry(
        stop=stop_after_attempt(3),# 最大重试3次（包含首次请求）
        wait=wait_exponential(multiplier=1,min=2,max=10),# 智能等待，不暴力请求服务器
        reraise=True# 最终失败后，=True,抛出原始异常，不掩盖问题
    )

    def send(self):
        #加入捕获异常
        try:
            # 请求日志
            logger.info(f"【接口请求】{self.method} | URL: {self.url}")
            logger.info(f"【请求参数】params: {self.params} | data: {self.data} | json: {self.json}")
            logger.info(f"【请求头】headers: {self.headers}")

            # 发送请求（带超时）
            self.resp=self.session.request(
                url=self.url,
                headers=self.headers,
                method=self.method,
                #查询参数
                params=self.params,
                #表单参数
                data=self.data,
                #json参数
                json=self.json,
                #文件
                files=self.files,
                #超时
                timeout=self.timeout)
            
            # 自动添加 Allure 附件
            if allure:
                try:
                    # 1. 请求基本信息
                    req_info = f"URL: {self.url}\nMethod: {self.method}\nTimeout: {self.timeout}s"
                    allure.attach(req_info, name="Request Info", attachment_type=allure.attachment_type.TEXT)
                    
                    # 2. 请求头 (格式化 JSON)
                    allure.attach(json.dumps(self.headers or {}, indent=2, ensure_ascii=False), 
                                 name="Request Headers", attachment_type=allure.attachment_type.JSON)
                    
                    # 3. 请求体
                    req_body = self.json or self.data or "No Body"
                    if isinstance(req_body, dict):
                        req_body = json.dumps(req_body, indent=2, ensure_ascii=False)
                    allure.attach(str(req_body), name="Request Body", attachment_type=allure.attachment_type.JSON)
                    
                    # 4. 响应体
                    resp_content = self.resp.json() if 'application/json' in self.resp.headers.get('Content-Type', '') else self.resp.text
                    if isinstance(resp_content, dict):
                        resp_content = json.dumps(resp_content, indent=2, ensure_ascii=False)
                    allure.attach(str(resp_content), name="Response Body", attachment_type=allure.attachment_type.JSON)
                except Exception as attach_err:
                    logger.warning(f"Allure 附件添加失败: {attach_err}")

            # 响应日志
            logger.info(f"【接口响应】状态码: {self.resp.status_code} | 响应体: {self.resp.json()}")
            return self.resp
        # 异常捕获 + 打印日志
        except Exception as e:
            logger.error(f"【接口请求失败，准备重试】异常信息: {str(e)}", exc_info=True)
            # 抛出异常，触发重试机制
            raise Exception(f"接口请求异常：{e}")