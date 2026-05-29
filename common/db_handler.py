import pymysql
from pymysql.cursors import DictCursor
from .config_manager import config

# 加载配置
config.load_config()


class DBHandler:
    def __init__(self, host=None, port=None, database=None, user=None, password=None, charset=None):
        # 从配置文件读取默认值
        self.host = host or config.get('database.host', '127.0.0.1')
        self.port = port or config.get('database.port', 3306)
        self.database = database or config.get('database.name', 'pycharm_test')
        self.user = user or config.get('database.user', 'root')
        self.password = password or config.get('database.password', 'root')
        self.charset = charset or config.get('database.charset', 'utf8')

        self.conn = pymysql.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            charset=self.charset,
            cursorclass=DictCursor
        )
        self.cursor = self.conn.cursor()

    def query(self, sql, args=None, one=True):
        self.cursor.execute(sql, args)
        if one:
            return self.cursor.fetchone()
        else:
            return self.cursor.fetchall()

    def execute(self, sql, args=None):
        self.cursor.execute(sql, args)
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()


# 默认实例
db = DBHandler()