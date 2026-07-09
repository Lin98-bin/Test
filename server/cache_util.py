"""Redis 缓存工具"""
import redis
import json
from functools import wraps

import os

# Redis 连接（连接池复用）
_pool = redis.ConnectionPool(
    host=os.environ.get("REDIS_HOST", "127.0.0.1"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    db=0, decode_responses=True
)
rds = redis.Redis(connection_pool=_pool)

# 缓存时间
TTL_SHORT = 60         # 1 分钟（商品列表）
TTL_MEDIUM = 300        # 5 分钟（商品详情）
TTL_LONG = 3600         # 1 小时（分类）


def cache_result(ttl=TTL_MEDIUM, prefix=''):
    """装饰器：自动缓存函数返回值（JSON）"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # 构建缓存 key
            key_parts = [prefix] if prefix else [fn.__name__]
            key_parts.append(str(args))
            key_parts.append(str(sorted(kwargs.items())))
            key = ':'.join(key_parts)

            # 读缓存
            cached = rds.get(key)
            if cached:
                return json.loads(cached)

            # 查数据库
            result = fn(*args, **kwargs)
            # 存缓存
            rds.setex(key, ttl, json.dumps(result, ensure_ascii=False, default=str))
            return result
        return wrapper
    return decorator


def cache_get(key):
    """读缓存"""
    val = rds.get(key)
    return json.loads(val) if val else None


def cache_set(key, value, ttl=TTL_MEDIUM):
    """写缓存"""
    rds.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))


def cache_delete(*keys):
    """删缓存"""
    if keys:
        rds.delete(*keys)


def cache_flush_pattern(pattern):
    """按模式批量删缓存"""
    for key in rds.scan_iter(match=pattern):
        rds.delete(key)


# 缓存 key 常量
KEY_CATEGORIES = 'cache:categories'
KEY_GOODS_LIST_PREFIX = 'cache:goods:list'
KEY_GOODS_DETAIL = 'cache:goods:detail'
