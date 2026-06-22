# -*- coding: utf-8 -*-

class GlobalContext:
    """全局上下文存储器，支持多用户场景和变量传递"""
    _variables = {}

    @classmethod
    def set(cls, key, value):
        cls._variables[key] = value

    @classmethod
    def get(cls, key, default=None):
        return cls._variables.get(key, default)

    @classmethod
    def clear(cls):
        cls._variables.clear()

# 保持向后兼容（面试时可以提到这种平滑过渡的处理）
class TokenStore(GlobalContext):
    @classmethod
    def set_token(cls, user, token):
        cls.set(f"token_{user}", token)

    @classmethod
    def get_token(cls, user="default"):
        return cls.get(f"token_{user}", "")

class OrderStore(GlobalContext):
    """订单数据存储器"""
    @classmethod
    def set_order_id(cls, user, order_id):
        cls.set(f"order_{user}", order_id)

    @classmethod
    def get_order_id(cls, user):
        return cls.get(f"order_{user}")
