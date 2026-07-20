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

# token
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


class GoodsStore(GlobalContext):
    """商品数据存储器 — 演示 set / get / clear 跨文件传递"""
    @classmethod
    def set_selected(cls, user, goods_id, goods_name):
        cls.set(f"goods_id_{user}", goods_id)
        cls.set(f"goods_name_{user}", goods_name)

    @classmethod
    def get_selected_id(cls, user):
        return cls.get(f"goods_id_{user}")

    @classmethod
    def get_selected_name(cls, user):
        return cls.get(f"goods_name_{user}")
