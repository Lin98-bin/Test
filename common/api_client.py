from.environment import API_TIMEOUT
import time
import requests
#增加重试机制
from tenacity import retry,stop_after_attempt,wait_exponential
from .logger import *
#token赋值为空
#声明token会全局变量，谁都可以调用
global sessionToken
sessionToken=""
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
                params=self.params,
                data=self.data,
                json=self.json,
                files=self.files,
                #超时
                timeout=self.timeout)
            # 响应日志
            logger.info(f"【接口响应】状态码: {self.resp.status_code} | 响应体: {self.resp.json()}")
            return self.resp
        # 异常捕获 + 打印日志
        except Exception as e:
            logger.error(f"【接口请求失败，准备重试】异常信息: {str(e)}", exc_info=True)
            # 抛出异常，触发重试机制
            raise Exception(f"接口请求异常：{e}")