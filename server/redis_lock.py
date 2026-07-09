"""Redis 分布式锁 — 防超卖、防并发冲突"""
import uuid
import time
from cache_util import rds


class RedisLock:
    """
    Redis 分布式锁，基于 SET NX EX + Lua 脚本安全释放

    用法:
        lock = RedisLock("stock:123", expire=5)
        if lock.acquire():
            try:
                # 临界区代码
                ...
            finally:
                lock.release()

        # 或使用上下文管理器:
        with RedisLock("stock:123", expire=5) as lock:
            ...
    """

    # Lua 脚本：只有 value 匹配才删除 key（防止误删别人的锁）
    _UNLOCK_SCRIPT = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
        return redis.call('del', KEYS[1])
    else
        return 0
    end
    """

    def __init__(self, lock_key: str, expire: int = 10,
                 retry_times: int = 3, retry_delay: float = 0.1):
        """
        :param lock_key:    锁的 key，会自动加前缀 "lock:"
        :param expire:      锁过期时间(秒)，防止死锁
        :param retry_times: 获取失败时重试次数
        :param retry_delay: 重试间隔(秒)
        """
        self.lock_key = f"lock:{lock_key}"
        self.lock_value = str(uuid.uuid4())  # 唯一标识，释放时校验
        self.expire = expire
        self.retry_times = retry_times
        self.retry_delay = retry_delay

    def acquire(self) -> bool:
        """尝试获取锁，返回 True/False"""
        for i in range(self.retry_times):
            # SET key value NX EX expire → 原子操作
            if rds.set(self.lock_key, self.lock_value, nx=True, ex=self.expire):
                return True
            if i < self.retry_times - 1:
                time.sleep(self.retry_delay)
        return False

    def release(self):
        """安全释放锁（Lua 脚本保证原子性）"""
        try:
            rds.eval(self._UNLOCK_SCRIPT, 1, self.lock_key, self.lock_value)
        except Exception:
            pass  # Redis 挂了不影响业务，锁会自动过期

    def __enter__(self):
        if not self.acquire():
            raise LockAcquireError(f"获取锁失败: {self.lock_key}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False  # 不吞异常


class LockAcquireError(Exception):
    """锁获取失败异常"""
    pass
