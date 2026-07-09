import pymysql
from pymysql.cursors import DictCursor
from core import setting

class DBHandler:
    def __init__(self):
        self._conn = None
        self._cursor = None

    def query(self, sql, args=None, one=True):
        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, args)
            if one is True:
                return cursor.fetchone()
            else:
                return cursor.fetchall()

    def execute(self, sql, args=None):
        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, args)
            conn.commit()

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _get_connection(self):
        """动态获取数据库连接，确保环境切换后配置生效"""
        conf = setting.DB_CONF
        
        # 如果已经有连接，简单检查是否可用
        if self._conn is not None:
            try:
                self._conn.ping(reconnect=True)
                return self._conn
            except:
                pass

        # 创建新连接
        self._conn = pymysql.connect(
            host=conf.get('host'),
            port=conf.get('port', 3306),
            database=conf.get('database'),
            user=conf.get('user'),
            password=conf.get('password'),
            charset=conf.get('charset', 'utf8'),
            cursorclass=DictCursor
        )
        return self._conn


# 默认实例
db = DBHandler()
