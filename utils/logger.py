import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler

#log文件夹：先确定存放日志的文件夹的名，路径，以及是否存在：log

#确定好log文件夹存放的目录
log_path=os.path.join (os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"log")

#如果当前目录没有log，就创建log
if not os.path.exists(log_path):
    os.mkdir(log_path)


#确定日志文件名以及存放路径，按天生成
#日志文件名
log_file_name=time.strftime("%y-%m-%d")+".log"
#日志放哪里
log_file_path=os.path.join(log_path,log_file_name)
#创建空日志文件：创建一个空的日志文件，清空里面所有内容（相当于初始化日志）
with open(log_file_path,"w",encoding="utf-8") as f:
    f.write("")


#创建logger对象，确定日志的输出格式


#创建一个logger对象
logger=logging.getLogger("test_apiauto_logger")
#给日志定级别，有 五个级别，debug，info，warring，error，critical
logger.setLevel(logging.INFO)

#确定日志的输出格式:时间，日志级别，文件名，日志内容
formatter=logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(message)s")

#全局只能有一个日志对象，避免重复打印：防止日志重复打印！
# 判断列表里有没有处理器（不为空）
if logger.handlers:
    # 清空整个列表，移除所有处理器
    logger.handlers.clear()

#日志输出形式：控制台输出
#创建一个对象接收控制台输入
sh=logging.StreamHandler()
#控制台输出格式：
sh.setFormatter(formatter)
#把控制台输出器绑定到日志器上
logger.addHandler(sh)

#日志输出第二个形式:文件输出
fh=TimedRotatingFileHandler(
    filename=log_file_path,#主日志文件名
    when="midnight",#每天凌晨切割：每天一到 凌晨 00:00（半夜 12 点），自动把今天的日志封存，新建一个新日志文件
    interval=1,# 间隔：1天切一次
    backupCount=7,# 保留最近7份日志，旧的自动删
    encoding="utf-8",  # 编码，防止中文乱码
)
#确定日志在文件输出的格式
fh.setFormatter(formatter)
#把日志处理器绑定进来
logger.addHandler(fh)

logging.shutdown()#强制刷新日志到文件
