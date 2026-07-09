"""RabbitMQ Worker — 异步消费：下单处理 + 超时取消"""
import json
import pika
import os
import time
from datetime import datetime
from db_pool import get_db

MQ_HOST = os.environ.get("MQ_HOST", "127.0.0.1")
MQ_PORT = int(os.environ.get("MQ_PORT", "5672"))

QUEUE_ORDER = "mall.order.create"
QUEUE_NOTIFY = "mall.order.notify"
QUEUE_TIMEOUT = "mall.order.timeout"


# ============================================================
# 处理器 1：下单异步处理
# ============================================================
def process_order(ch, method, properties, body):
    """处理下单消息：记录日志、模拟异步任务"""
    data = json.loads(body)
    order_no = data.get("order_no", "?")
    user_id = data.get("user_id", "?")
    total = data.get("total", 0)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Order received: {order_no}")
    print(f"  User: {user_id}, Amount: ${total}")

    # 模拟耗时处理
    print(f"  -> Processing order...")
    time.sleep(0.2)
    print(f"  [DONE] Order {order_no} processed.")

    ch.basic_ack(delivery_tag=method.delivery_tag)


# ============================================================
# 处理器 2：通知消息
# ============================================================
def process_notify(ch, method, properties, body):
    """处理通知消息"""
    data = json.loads(body)
    print(f"[NOTIFY] User {data['user_id']}: {data['message']}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


# ============================================================
# 处理器 3：超时取消订单（死信队列消费者）
# ============================================================
def process_timeout_cancel(ch, method, properties, body):
    """
    处理超时取消消息（来自死信队列）

    消息在延迟队列里等了 15 分钟，过期后自动路由到这里。
    检查订单是否 still pending → 取消 + 回滚库存。
    如果已支付 → 忽略。
    """
    data = json.loads(body)
    order_id = data.get("order_id")
    order_no = data.get("order_no", "?")
    items = data.get("items", [])
    created_at = data.get("created_at", "unknown")

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⏰ Timeout triggered: {order_no}")
    print(f"  Created at: {created_at}")

    db = None
    try:
        db = get_db()
        cursor = db.cursor()

        # 1. 查当前订单状态
        cursor.execute("SELECT id, status FROM orders WHERE id=%s", (order_id,))
        order = cursor.fetchone()

        if not order:
            print(f"  [SKIP] Order {order_id} not found — already deleted?")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        current_status = order[1]
        if current_status != 'pending':
            print(f"  [SKIP] Order {order_no} status={current_status}, not pending, ignore.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # 2. 状态为 pending → 取消订单，回滚库存
        print(f"  -> Cancelling order {order_no}...")

        cursor.execute(
            "UPDATE orders SET status='cancelled', cancel_reason=%s WHERE id=%s",
            ("超时未支付，系统自动取消", order_id)
        )

        # 3. 回滚库存
        for it in items:
            goods_id = it["goods_id"]
            qty = it["quantity"]
            cursor.execute(
                "UPDATE goods SET stock=stock+%s, sales=sales-%s WHERE id=%s",
                (qty, qty, goods_id)
            )
            print(f"  -> Restored {qty} stock for goods #{goods_id}")

        db.commit()
        print(f"  [DONE] Order {order_no} auto-cancelled, stock restored.")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"  [ERROR] Timeout cancel failed: {e}")
        # 不 ack, MQ 会重新投递
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        if db:
            try:
                cursor.close()
                db.close()
            except Exception:
                pass


# ============================================================
# 主入口
# ============================================================
def main():
    print("=" * 55)
    print("  Mini Mall - MQ Worker")
    print(f"  Listening on {MQ_HOST}:{MQ_PORT}")
    print("  Queues:")
    print(f"    1. {QUEUE_ORDER}     — 下单异步处理")
    print(f"    2. {QUEUE_NOTIFY}    — 通知消息")
    print(f"    3. {QUEUE_TIMEOUT}   — 超时取消 (DLX)")
    print("=" * 55)

    # ===== 重试连接 RabbitMQ（最多 30 次，间隔 2s） =====
    max_retries = 30
    for attempt in range(1, max_retries + 1):
        try:
            conn = pika.BlockingConnection(
                pika.ConnectionParameters(host=MQ_HOST, port=MQ_PORT,
                                          heartbeat=600,
                                          blocked_connection_timeout=300)
            )
            print(f"✅ Connected to RabbitMQ (attempt {attempt})")
            break
        except Exception as e:
            if attempt < max_retries:
                print(f"⏳ Waiting for RabbitMQ... ({attempt}/{max_retries})")
                time.sleep(2)
            else:
                print(f"❌ Failed to connect after {max_retries} attempts: {e}")
                raise

    channel = conn.channel()

    # 声明队列 (幂等)
    channel.queue_declare(queue=QUEUE_ORDER, durable=True)
    channel.queue_declare(queue=QUEUE_NOTIFY, durable=True)
    channel.queue_declare(queue=QUEUE_TIMEOUT, durable=True)

    # 每次只取一条，处理完再取下一条
    channel.basic_qos(prefetch_count=1)

    # 绑定消费者
    channel.basic_consume(queue=QUEUE_ORDER,
                          on_message_callback=process_order)
    channel.basic_consume(queue=QUEUE_NOTIFY,
                          on_message_callback=process_notify)
    channel.basic_consume(queue=QUEUE_TIMEOUT,
                          on_message_callback=process_timeout_cancel)

    print("Waiting for messages. Press Ctrl+C to stop.\n")
    channel.start_consuming()


if __name__ == "__main__":
    main()
