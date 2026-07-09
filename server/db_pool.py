"""MySQL 连接池 — 基于 DBUtils，避免高并发下频繁 TCP 握手"""
import os
import pymysql
from dbutils.pooled_db import PooledDB

_pool = None


def get_pool():
    """懒加载连接池（模块级单例）"""
    global _pool
    if _pool is None:
        _pool = PooledDB(
            creator=pymysql,
            mincached=5,         # 启动时预创建 5 个连接
            maxcached=20,        # 空闲时最多保留 20 个
            maxconnections=50,   # 最大连接数
            blocking=True,       # 连接池满时等待，不直接报错
            ping=1,              # 1=每次取连接时 ping 一下检测可用性
            host=os.environ.get("DB_HOST", "127.0.0.1"),
            port=int(os.environ.get("DB_PORT", "3306")),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASS", "root"),
            database=os.environ.get("DB_NAME", "pycharm_test"),
            charset="utf8",
            cursorclass=pymysql.cursors.Cursor,
        )
    return _pool


def get_db():
    """从连接池获取一个连接（用完后调用方需要 close() 归还到池中）"""
    return get_pool().connection()
