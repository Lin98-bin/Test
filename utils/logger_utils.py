import os
import logging
from logging.handlers import TimedRotatingFileHandler

# 确定 log 文件夹路径
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log")

# 如果当前目录没有 log，就创建 log
if not os.path.exists(log_path):
    os.mkdir(log_path)

# 创建 logger 对象
logger = logging.getLogger("test_apiauto_logger")
logger.setLevel(logging.INFO)

# 日志输出格式
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(message)s")

# 全局只有一个日志对象，避免重复打印
if logger.handlers:
    logger.handlers.clear()

# 控制台输出
sh = logging.StreamHandler()
sh.setFormatter(formatter)
logger.addHandler(sh)

# 文件输出 — 固定文件名，由 TimedRotatingFileHandler 自动按天切割
log_file_path = os.path.join(log_path, "test.log")
fh = TimedRotatingFileHandler(
    filename=log_file_path,
    when="midnight",      # 每天凌晨切割
    interval=1,           # 1 天切一次
    backupCount=7,        # 保留最近 7 份
    encoding="utf-8",
)
fh.setFormatter(formatter)
logger.addHandler(fh)
