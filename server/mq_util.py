"""RabbitMQ 消息队列工具 — 异步下单 + 延迟取消（死信队列）"""
import os
import json
import pika
from datetime import datetime

MQ_HOST = os.environ.get("MQ_HOST", "127.0.0.1")
MQ_PORT = int(os.environ.get("MQ_PORT", "5672"))

# ========== 队列/交换机常量 ==========
QUEUE_ORDER = "mall.order.create"            # 下单队列
QUEUE_NOTIFY = "mall.order.notify"           # 通知队列

# 死信队列 — 订单超时自动取消
EXCHANGE_DELAY = "mall.order.delay.exchange"           # 延迟交换机
QUEUE_DELAY = "mall.order.delay"                        # 延迟队列 (带 TTL)
EXCHANGE_TIMEOUT = "mall.order.timeout.exchange"       # 死信交换机 (自动路由)
QUEUE_TIMEOUT = "mall.order.timeout"                    # 超时取消队列 (worker 消费)
ROUTING_KEY_DELAY = "order.delay"
ROUTING_KEY_TIMEOUT = "order.timeout"

ORDER_TIMEOUT_SECONDS = 900  # 15 分钟

_conn = None
_channel = None


def get_channel():
    """懒加载 MQ 连接，自动声明所有队列和交换机"""
    global _conn, _channel
    if _channel is None or _channel.is_closed:
        _conn = pika.BlockingConnection(
            pika.ConnectionParameters(host=MQ_HOST, port=MQ_PORT)
        )
        _channel = _conn.channel()

        # ---- 普通队列 ----
        _channel.queue_declare(queue=QUEUE_ORDER, durable=True)
        _channel.queue_declare(queue=QUEUE_NOTIFY, durable=True)

        # ---- 死信队列体系 ----
        # 1. 死信交换机（超时后消息路由到这里）
        _channel.exchange_declare(exchange=EXCHANGE_TIMEOUT,
                                  exchange_type='direct', durable=True)

        # 2. 超时处理队列（worker 监听这个队列，收到即取消订单）
        _channel.queue_declare(queue=QUEUE_TIMEOUT, durable=True)
        _channel.queue_bind(exchange=EXCHANGE_TIMEOUT,
                            queue=QUEUE_TIMEOUT,
                            routing_key=ROUTING_KEY_TIMEOUT)

        # 3. 延迟交换机
        _channel.exchange_declare(exchange=EXCHANGE_DELAY,
                                  exchange_type='direct', durable=True)

        # 4. 延迟队列：带 TTL，过期后自动投递到死信交换机
        _channel.queue_declare(
            queue=QUEUE_DELAY, durable=True,
            arguments={
                'x-message-ttl': ORDER_TIMEOUT_SECONDS * 1000,  # 毫秒
                'x-dead-letter-exchange': EXCHANGE_TIMEOUT,      # 过期后投递到死信交换机
                'x-dead-letter-routing-key': ROUTING_KEY_TIMEOUT,
            }
        )
        _channel.queue_bind(exchange=EXCHANGE_DELAY,
                            queue=QUEUE_DELAY,
                            routing_key=ROUTING_KEY_DELAY)

    return _channel


def publish_order_created(order_data):
    """下单后发送消息到队列（异步扣库存+通知）"""
    try:
        ch = get_channel()
        msg = json.dumps(order_data, ensure_ascii=False, default=str)
        ch.basic_publish(
            exchange='',
            routing_key=QUEUE_ORDER,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        return True
    except Exception as e:
        print(f"[MQ] Failed to publish order: {e}")
        return False


def publish_notify(user_id, message):
    """发送通知消息"""
    try:
        ch = get_channel()
        msg = json.dumps({
            "user_id": user_id,
            "message": message,
            "time": str(datetime.now())
        }, ensure_ascii=False)
        ch.basic_publish(
            exchange='',
            routing_key=QUEUE_NOTIFY,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        return True
    except Exception as e:
        print(f"[MQ] Notify failed: {e}")
        return False


def publish_delay_cancel(order_id: int, order_no: str,
                         goods_ids: list, order_items: list,
                         delay_seconds: int = 900):
    """
    发送延迟取消消息到死信队列体系

    流程:
      消息 → EXCHANGE_DELAY → QUEUE_DELAY (TTL=delay_seconds)
           → 过期 → EXCHANGE_TIMEOUT → QUEUE_TIMEOUT
           → mq_worker 消费 → 检查订单状态 → 取消/忽略

    :param order_id:       订单 ID
    :param order_no:       订单号
    :param goods_ids:      涉及的商品 ID 列表（用于回滚库存）
    :param order_items:    订单商品明细（含 quantity）
    :param delay_seconds:  延迟时间(秒)，默认 900 = 15 分钟
    """
    try:
        ch = get_channel()
        msg = json.dumps({
            "order_id": order_id,
            "order_no": order_no,
            "goods_ids": goods_ids,
            "items": [{"goods_id": it["goods_id"], "quantity": it["quantity"]}
                       for it in order_items],
            "created_at": str(datetime.now()),
        }, ensure_ascii=False, default=str)

        # 如果队列还没绑定延迟交换机（从旧连接恢复时），重新声明
        _declare_delay_queue(ch)

        ch.basic_publish(
            exchange=EXCHANGE_DELAY,
            routing_key=ROUTING_KEY_DELAY,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"[MQ] Delay cancel scheduled: order {order_no}, "
              f"timeout={delay_seconds}s")
        return True
    except Exception as e:
        print(f"[MQ] Delay cancel failed: {e}")
        return False


def _declare_delay_queue(ch):
    """确保延迟队列体系已声明（幂等）"""
    try:
        ch.queue_declare(
            queue=QUEUE_DELAY, durable=True,
            arguments={
                'x-message-ttl': ORDER_TIMEOUT_SECONDS * 1000,
                'x-dead-letter-exchange': EXCHANGE_TIMEOUT,
                'x-dead-letter-routing-key': ROUTING_KEY_TIMEOUT,
            }
        )
    except Exception:
        pass  # 已存在则忽略
