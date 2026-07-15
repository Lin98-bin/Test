
import pymysql
from pymysql.cursors import DictCursor
from core import setting
class DBHandler:
    def __init__(self,host,port,database,user,password,charset="utf8"):
        self.conn=pymysql.connect(
            #地址
            host=host,
            #端口
            port=port,
            #数据库
            database=database,
            #用户名
            user=user,
            #密码
            password=password,
            #编码
            charset=charset,
            #数据库返回【字典】，而不是【元组】
            cursorclass=DictCursor,
            # 开启自动提交，否则 REPEATABLE-READ 隔离导致查不到其他连接写入的数据
            autocommit=True
        )
        #创建一个游标对象
        self.cursor=self.conn.cursor()
    #查询类
    def query(self,sql,args=None,one=True):
        #用游标执行语句
        self.cursor.execute(sql,args)
        if one:
            #如果one=True，返回一条数据
            return self.cursor.fetchone()
        else:
            #否则全部返回
            return self.cursor.fetchall()
    #执行类：增删改
    def execute(self,sql,args=None):
    #游标执行语句
        self.cursor.execute(sql,args)
    #执行类语句需要确认提交
        self.conn.commit()

    def close(self):
        #执行完语句记得关闭
        self.cursor.close()
        #记得断开连接
        self.conn.close()

db=DBHandler(
    host=setting.DB_CONF.get("host", "127.0.0.1"),
    port=setting.DB_CONF.get("port", 3306),
    database=setting.DB_CONF.get("database", "pycharm_test"),
    user=setting.DB_CONF.get("user", "root"),
    password=setting.DB_CONF.get("password", "root"),
    charset=setting.DB_CONF.get("charset", "utf8")
)
