import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler

log_path=os.path.join (os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"log")

if not os.path.exists(log_path):
    os.mkdir(log_path)

log_file_name=time.strftime("%y-%m-%d")+".log"
log_file_path=os.path.join(log_path,log_file_name)
with open(log_file_path,"w",encoding="utf-8") as f:
    f.write("")

logger=logging.getLogger("test_apiauto_logger")
logger.setLevel(logging.INFO)

formatter=logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(message)s")

if logger.handlers:
    logger.handlers.clear()

sh=logging.StreamHandler()
sh.setFormatter(formatter)
logger.addHandler(sh)

fh=TimedRotatingFileHandler(
    filename=log_file_path,
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8",
)
fh.setFormatter(formatter)
logger.addHandler(fh)

logging.shutdown()
