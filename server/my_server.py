from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import pymysql
import uuid
import jwt
import re
import json
import hashlib
import os
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY

# Prometheus 指标
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request latency', ['endpoint'])
from cache_util import rds, cache_get, cache_set, cache_delete, cache_flush_pattern
from cache_util import KEY_CATEGORIES, KEY_GOODS_LIST_PREFIX, KEY_GOODS_DETAIL, TTL_SHORT, TTL_MEDIUM, TTL_LONG
from es_util import search_goods as es_search
from mq_util import publish_order_created, publish_notify, publish_delay_cancel
from redis_lock import RedisLock
from db_pool import get_db

app = Flask(__name__)
CORS(app)

TOKEN_EXPIRE_HOURS = 24
PASSWORD_SALT = "mini_mall_2026"
JWT_SECRET = os.environ.get("JWT_SECRET", "mini_mall_jwt_secret_2026")


# ============================================
# 异常 & 工具
# ============================================

def hash_password(password):
    """SHA256 + salt 加密密码"""
    return hashlib.sha256((password + PASSWORD_SALT).encode()).hexdigest()


def invalidate_goods_cache(goods_id=None):
    """清除商品相关缓存（下单/取消/修改时调用）"""
    cache_flush_pattern(f"{KEY_GOODS_LIST_PREFIX}:*")
    if goods_id:
        cache_delete(f"{KEY_GOODS_DETAIL}:{goods_id}")
    else:
        cache_flush_pattern(f"{KEY_GOODS_DETAIL}:*")
class AuthError(Exception):
    def __init__(self, message, code=401):
        self.message = message
        self.code = code


@app.before_request
def track_request():
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path).inc()

@app.errorhandler(AuthError)
def handle_auth_error(error):
    return jsonify({"code": error.code, "error": error.message})


# ===== get_db() 已改为连接池，从 db_pool 导入，删除原函数 =====


def generate_token(user_id, username, is_member=0, is_admin=0):
    """生成 JWT Token（无状态，不查库）"""
    payload = {
        "user_id": user_id,
        "username": username,
        "is_member": is_member,
        "is_admin": is_admin,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def get_user_by_token(token):
    """
    JWT 解码鉴权（无 DB 查询）

    返回与旧代码兼容的 list 格式:
        [user_id, username, status, token_expire, is_member, member_expire, is_admin]
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return [
            payload["user_id"],           # [0]
            payload["username"],           # [1]
            1,                             # [2] status (JWT 不存，默认 1=active)
            None,                          # [3] token_expire (JWT 自带过期)
            payload.get("is_member", 0),   # [4]
            None,                          # [5] member_expire (JWT 不存长字段)
            payload.get("is_admin", 0),    # [6]
        ]
    except jwt.ExpiredSignatureError:
        return -1  # 过期，与旧代码兼容
    except Exception:
        return None


def require_auth():
    """鉴权 — JWT 解码，零 DB 查询"""
    token = request.headers.get("sessionToken", "")
    user = get_user_by_token(token)
    if user == -1:
        raise AuthError("login expired, please login again")
    if not user:
        raise AuthError("not logged in")
    return user


def user_to_dict(u):
    """将 user 元组转为字典 (id, username, status, token_expire, is_member, member_expire)"""
    return {
        "id": u[0], "username": u[1], "status": u[2],
        "is_member": bool(u[4]), "member_expire": str(u[5]) if u[5] else None
    }


# ============================================
# 一、用户模块
# ============================================
@app.route('/api/user/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        if not username or not password:
            return jsonify({"code": 400, "error": "username and password required"})
        if len(username) < 4:
            return jsonify({"code": 400, "error": "username must be at least 4 characters"})
        if len(password) < 6:
            return jsonify({"code": 400, "error": "password must be at least 6 characters"})

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM user WHERE username=%s", (username,))
        if cursor.fetchone():
            cursor.close(); db.close()
            return jsonify({"code": 400, "error": "username already exists"})

        token_expire = datetime.now() + timedelta(hours=TOKEN_EXPIRE_HOURS)
        cursor.execute(
            "INSERT INTO user(username, password, token, token_expire, status, create_time, is_member, is_admin) VALUES(%s,%s,%s,%s,1,NOW(),0,0)",
            (username, hash_password(password), '', token_expire)
        )
        db.commit()
        uid = cursor.lastrowid
        # JWT 无状态生成（新用户 is_member=0, is_admin=0）
        token = generate_token(uid, username, is_member=0, is_admin=0)
        cursor.close(); db.close()
        return jsonify({"code": 200, "msg": "ok", "data": {"token": token, "user_id": uid, "username": username}})
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})


@app.route('/api/user/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, username, status, is_member, is_admin FROM user WHERE username=%s AND password=%s", (username, hash_password(password)))
        user = cursor.fetchone()
        if not user:
            cursor.close(); db.close()
            return jsonify({"code": 401, "error": "wrong username or password"})

        # JWT 无状态生成，不再存 token 到数据库
        token = generate_token(user[0], user[1], is_member=user[3] or 0, is_admin=user[4] or 0)
        token_expire = datetime.now() + timedelta(hours=TOKEN_EXPIRE_HOURS)
        cursor.execute("UPDATE user SET token_expire=%s WHERE id=%s", (token_expire, user[0]))
        db.commit()
        cursor.close(); db.close()
        return jsonify({"code": 200, "msg": "ok", "data": {"token": token, "user_id": user[0], "username": user[1]}})
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})


@app.route('/api/user/info', methods=['GET'])
def user_info():
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, status, create_time, nickname, is_member, member_expire, is_admin FROM user WHERE id=%s", (u[0],))
    row = cursor.fetchone()
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "ok", "data": {
        "id": row[0], "username": row[1], "status": row[2],
        "create_time": str(row[3]), "nickname": row[4] or '',
        "is_member": bool(row[5]), "member_expire": str(row[6]) if row[6] else None,
        "is_admin": bool(row[7])
    }})


@app.route('/api/user/update', methods=['PUT'])
def user_update():
    u = require_auth()
    data = request.get_json()
    nickname = data.get('nickname', '').strip()
    if nickname:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE user SET nickname=%s WHERE id=%s", (nickname, u[0]))
        db.commit()
        cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "ok"})


@app.route('/api/user/logout', methods=['POST'])
def logout():
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE user SET token=NULL, token_expire=NULL WHERE id=%s", (u[0],))
    db.commit()
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "ok"})


# ============================================
# Prometheus 监控指标
# ============================================
@app.route('/metrics')
def metrics():
    return Response(generate_latest(REGISTRY), mimetype='text/plain')


# ============================================
# Alertmanager Webhook 接收端点
# ============================================
import logging
alert_logger = logging.getLogger('alertmanager')

@app.route('/alert', methods=['POST'])
def alert_receiver():
    """
    接收 Alertmanager 推送的告警，打印到控制台/日志

    Alertmanager 发过来的 JSON 格式:
    {
      "receiver": "default-webhook",
      "status": "firing" | "resolved",
      "alerts": [
        {
          "status": "firing",
          "labels": {"alertname": "...", "severity": "..."},
          "annotations": {"summary": "...", "description": "..."},
          "startsAt": "...",
          "endsAt": "..."
        }
      ]
    }
    """
    try:
        data = request.get_json(force=True)
        status = data.get('status', 'unknown')
        alerts = data.get('alerts', [])

        for alert in alerts:
            alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
            severity = alert.get('labels', {}).get('severity', 'info')
            alert_status = alert.get('status', status)
            summary = alert.get('annotations', {}).get('summary', '')
            desc = alert.get('annotations', {}).get('description', '')

            # 控制台输出
            emoji = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(severity, '⚪')
            resolve_tag = '[RESOLVED]' if alert_status == 'resolved' else '[FIRING]'
            print(f"\n{emoji} {resolve_tag} [{severity}] {alert_name}")
            print(f"   Summary: {summary}")
            print(f"   Detail:  {desc}")

        return jsonify({"code": 200, "msg": "ok", "received": len(alerts)})
    except Exception as e:
        print(f"[Alert] Failed to parse webhook: {e}")
        return jsonify({"code": 400, "error": str(e)}), 400


# ============================================
# 二、分类模块
# ============================================
@app.route('/api/category/list', methods=['GET'])
def category_list():
    try:
        # 先读 Redis 缓存
        cached = cache_get(KEY_CATEGORIES)
        if cached:
            return jsonify({"code": 200, "msg": "ok", "data": {"list": cached}})

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, name, parent_id, sort_order FROM category ORDER BY sort_order, id")
        rows = cursor.fetchall()
        cursor.close(); db.close()
        cats = [{"id": r[0], "name": r[1], "parent_id": r[2], "sort_order": r[3]} for r in rows]
        # 写入 Redis，1 小时有效
        cache_set(KEY_CATEGORIES, cats, TTL_LONG)
        return jsonify({"code": 200, "msg": "ok", "data": {"list": cats}})
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})


# ============================================
# 三、商品模块（增强版）
# ============================================
@app.route('/api/goods/list', methods=['GET'])
def goods_list():
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        category_id = request.args.get('category_id', 0, type=int)
        keyword = request.args.get('keyword', '', type=str)

        # ES 搜索（有关键词或分类筛选时优先用 ES）
        if keyword or category_id:
            try:
                result = es_search(keyword, category_id, page, page_size)
                # ES 有结果才用 ES，否则回退 MySQL
                if result["total"] > 0:
                    return jsonify({"code": 200, "msg": "ok(es)", "data": result})
            except Exception:
                pass  # ES 不可用时回退 MySQL

        # Redis 缓存 key
        cache_key = f"{KEY_GOODS_LIST_PREFIX}:p{page}:s{page_size}:c{category_id}:k{keyword}"
        cached = cache_get(cache_key)
        if cached:
            return jsonify({"code": 200, "msg": "ok(cached)", "data": cached})

        db = get_db()
        cursor = db.cursor()
        where = ["is_on_sale=1"]
        params = []

        if category_id:
            where.append("category_id=%s")
            params.append(category_id)
        if keyword:
            where.append("name LIKE %s")
            params.append(f'%{keyword}%')

        wheresql = " WHERE " + " AND ".join(where) if where else ""
        offset = (page - 1) * page_size
        cursor.execute(
            f"SELECT id, name, price, member_price, stock, image, specs, sales, category_id FROM goods{wheresql} ORDER BY id DESC LIMIT %s OFFSET %s",
            params + [page_size, offset]
        )
        rows = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) FROM goods{wheresql}", params)
        total = cursor.fetchone()[0]
        cursor.close(); db.close()

        goods = [{
            "id": r[0], "name": r[1], "price": float(r[2]),
            "member_price": float(r[3]) if r[3] else None,
            "stock": r[4], "image": r[5] or '',
            "specs": json.loads(r[6]) if r[6] else [],
            "sales": r[7] or 0, "category_id": r[8]
        } for r in rows]

        result = {"list": goods, "total": total, "page": page, "page_size": page_size}
        cache_set(cache_key, result, TTL_SHORT)
        return jsonify({"code": 200, "msg": "ok", "data": result})
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})


@app.route('/api/goods/detail/<int:goods_id>', methods=['GET'])
def goods_detail(goods_id):
    try:
        # Redis 缓存
        cache_key = f"{KEY_GOODS_DETAIL}:{goods_id}"
        cached = cache_get(cache_key)
        if cached:
            return jsonify({"code": 200, "msg": "ok(cached)", "data": cached})

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, name, price, member_price, stock, image, images, specs, sales, category_id, create_time FROM goods WHERE id=%s",
            (goods_id,))
        g = cursor.fetchone()
        if not g:
            cursor.close(); db.close()
            return jsonify({"code": 404, "error": "goods not found"})

        # 获取分类名
        cat_name = ''
        if g[9]:
            cursor.execute("SELECT name FROM category WHERE id=%s", (g[9],))
            cr = cursor.fetchone()
            if cr:
                cat_name = cr[0]
        cursor.close(); db.close()

        data = {
            "id": g[0], "name": g[1], "price": float(g[2]),
            "member_price": float(g[3]) if g[3] else None,
            "stock": g[4], "image": g[5] or '',
            "images": json.loads(g[6]) if g[6] else [],
            "specs": json.loads(g[7]) if g[7] else [],
            "sales": g[8] or 0, "category_id": g[9],
            "category_name": cat_name, "create_time": str(g[10])
        }
        cache_set(cache_key, data, TTL_MEDIUM)
        return jsonify({"code": 200, "msg": "ok", "data": data})
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})


@app.route('/api/goods/search', methods=['GET'])
def goods_search():
    keyword = request.args.get('keyword', '', type=str)
    if not keyword:
        return jsonify({"code": 400, "error": "keyword required"})
    # 复用 goods_list
    return goods_list()


# ============================================
# 四、购物车模块（增强版）
# ============================================
@app.route('/api/cart/add', methods=['POST'])
def cart_add():
    u = require_auth()
    data = request.get_json()
    goods_id = data.get('goods_id', 0)
    quantity = data.get('quantity', 1)
    specs = data.get('specs', '')

    if not goods_id or quantity < 1:
        return jsonify({"code": 400, "error": "invalid params"})

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT stock, name FROM goods WHERE id=%s", (goods_id,))
    goods = cursor.fetchone()
    if not goods:
        cursor.close(); db.close()
        return jsonify({"code": 404, "error": "goods not found"})
    if goods[0] < quantity:
        cursor.close(); db.close()
        return jsonify({"code": 400, "error": f"insufficient stock, current: {goods[0]}"})

    cursor.execute("SELECT id, quantity FROM cart WHERE user_id=%s AND goods_id=%s AND specs=%s", (u[0], goods_id, specs))
    exist = cursor.fetchone()
    if exist:
        cursor.execute("UPDATE cart SET quantity=quantity+%s WHERE id=%s", (quantity, exist[0]))
    else:
        cursor.execute("INSERT INTO cart(user_id, goods_id, specs, quantity) VALUES(%s,%s,%s,%s)", (u[0], goods_id, specs, quantity))
    db.commit()
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "added to cart"})


@app.route('/api/cart/list', methods=['GET'])
def cart_list():
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT c.id, c.goods_id, g.name, g.price, g.member_price, g.image, c.specs, c.quantity, g.stock
        FROM cart c JOIN goods g ON c.goods_id=g.id
        WHERE c.user_id=%s ORDER BY c.id DESC
    """, (u[0],))
    rows = cursor.fetchall()
    cursor.close(); db.close()

    # 判断用户是否会员
    is_member = bool(u[4])
    items = []
    total = 0
    for r in rows:
        price = float(r[4]) if (is_member and r[4]) else float(r[3])
        subtotal = price * r[7]
        total += subtotal
        items.append({
            "cart_id": r[0], "goods_id": r[1], "goods_name": r[2],
            "price": price, "original_price": float(r[3]),
            "member_price": float(r[4]) if r[4] else None,
            "image": r[5] or '', "specs": r[6] or '',
            "quantity": r[7], "stock": r[8], "subtotal": round(subtotal, 2)
        })
    return jsonify({"code": 200, "msg": "ok", "data": {"items": items, "total": len(items), "total_price": round(total, 2)}})


@app.route('/api/cart/count', methods=['GET'])
def cart_count():
    """购物车商品数量（用于角标）"""
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM cart WHERE user_id=%s", (u[0],))
    cnt = cursor.fetchone()[0]
    cursor.close(); db.close()
    return jsonify({"code": 200, "data": {"count": cnt}})


@app.route('/api/cart/update', methods=['PUT'])
def cart_update():
    u = require_auth()
    data = request.get_json()
    cart_id = data.get('cart_id', 0)
    quantity = data.get('quantity', 0)
    if quantity < 0:
        return jsonify({"code": 400, "error": "invalid quantity"})
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM cart WHERE id=%s AND user_id=%s", (cart_id, u[0]))
    if not cursor.fetchone():
        cursor.close(); db.close()
        return jsonify({"code": 404, "error": "cart item not found"})
    if quantity == 0:
        cursor.execute("DELETE FROM cart WHERE id=%s", (cart_id,))
    else:
        cursor.execute("UPDATE cart SET quantity=%s WHERE id=%s", (quantity, cart_id))
    db.commit()
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "ok"})


@app.route('/api/cart/delete/<int:cart_id>', methods=['DELETE'])
def cart_delete(cart_id):
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM cart WHERE id=%s AND user_id=%s", (cart_id, u[0]))
    affected = cursor.rowcount
    db.commit()
    cursor.close(); db.close()
    if affected == 0:
        return jsonify({"code": 404, "error": "cart item not found"})
    return jsonify({"code": 200, "msg": "deleted"})


@app.route('/api/cart/batch_delete', methods=['POST'])
def cart_batch_delete():
    """批量删除购物车"""
    u = require_auth()
    data = request.get_json()
    ids = data.get('ids', [])
    if not ids:
        return jsonify({"code": 400, "error": "ids required"})
    db = get_db()
    cursor = db.cursor()
    placeholders = ','.join(['%s'] * len(ids))
    cursor.execute(f"DELETE FROM cart WHERE id IN ({placeholders}) AND user_id=%s", ids + [u[0]])
    db.commit()
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "deleted"})


# ============================================
# 五、地址模块
# ============================================
@app.route('/api/address/add', methods=['POST'])
def address_add():
    u = require_auth()
    data = request.get_json()
    address = data.get('address', '').strip()
    contact = data.get('contact', '').strip()
    phone = data.get('phone', '').strip()
    if not address or not contact or not phone:
        return jsonify({"code": 400, "error": "address/contact/phone required"})
    if not re.match(r'^1[3-9]\d{9}$', phone):
        return jsonify({"code": 400, "error": "invalid phone"})

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM address WHERE user_id=%s", (u[0],))
    is_default = 1 if cursor.fetchone()[0] == 0 else 0
    cursor.execute("INSERT INTO address(user_id, address, contact, phone, is_default) VALUES(%s,%s,%s,%s,%s)",
                   (u[0], address, contact, phone, is_default))
    db.commit()
    aid = cursor.lastrowid
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "ok", "data": {"address_id": aid}})


@app.route('/api/address/list', methods=['GET'])
def address_list():
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, address, contact, phone, is_default FROM address WHERE user_id=%s ORDER BY is_default DESC, id DESC", (u[0],))
    rows = cursor.fetchall()
    cursor.close(); db.close()
    addrs = [{"id": r[0], "address": r[1], "contact": r[2], "phone": r[3], "is_default": bool(r[4])} for r in rows]
    return jsonify({"code": 200, "msg": "ok", "data": {"list": addrs, "total": len(addrs)}})


@app.route('/api/address/update', methods=['PUT'])
def address_update():
    u = require_auth()
    data = request.get_json()
    aid = data.get('id', 0)
    address = data.get('address', '').strip()
    contact = data.get('contact', '').strip()
    phone = data.get('phone', '').strip()

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM address WHERE id=%s AND user_id=%s", (aid, u[0]))
    if not cursor.fetchone():
        cursor.close(); db.close()
        return jsonify({"code": 404, "error": "address not found"})

    updates, params = [], []
    if address:
        updates.append("address=%s"); params.append(address)
    if contact:
        updates.append("contact=%s"); params.append(contact)
    if phone:
        if not re.match(r'^1[3-9]\d{9}$', phone):
            cursor.close(); db.close()
            return jsonify({"code": 400, "error": "invalid phone"})
        updates.append("phone=%s"); params.append(phone)
    if updates:
        params.append(aid)
        cursor.execute(f"UPDATE address SET {','.join(updates)} WHERE id=%s", params)
    db.commit()
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "ok"})


@app.route('/api/address/delete/<int:addr_id>', methods=['DELETE'])
def address_delete(addr_id):
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM address WHERE id=%s AND user_id=%s", (addr_id, u[0]))
    affected = cursor.rowcount
    db.commit()
    cursor.close(); db.close()
    if affected == 0:
        return jsonify({"code": 404, "error": "address not found"})
    return jsonify({"code": 200, "msg": "deleted"})


@app.route('/api/address/default/<int:addr_id>', methods=['PUT'])
def address_set_default(addr_id):
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM address WHERE id=%s AND user_id=%s", (addr_id, u[0]))
    if not cursor.fetchone():
        cursor.close(); db.close()
        return jsonify({"code": 404, "error": "address not found"})
    cursor.execute("UPDATE address SET is_default=0 WHERE user_id=%s", (u[0],))
    cursor.execute("UPDATE address SET is_default=1 WHERE id=%s", (addr_id,))
    db.commit()
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "set as default"})


# ============================================
# 六、订单模块（多商品版）
# ============================================
@app.route('/api/order/create', methods=['POST'])
def order_create():
    """创建订单 — 支持从购物车结算或单品立即购买"""
    u = require_auth()
    data = request.get_json()

    cart_ids = data.get('cart_ids', [])  # 从购物车结算: 选中的cart_id列表
    goods_id = data.get('goods_id', 0)   # 单品立即购买
    quantity = data.get('quantity', 1)
    specs = data.get('specs', '')
    address_id = data.get('address_id', 0)

    if not address_id:
        return jsonify({"code": 400, "error": "please select an address"})

    db = get_db()
    cursor = db.cursor()

    # 验证地址
    cursor.execute("SELECT id, address, contact, phone FROM address WHERE id=%s AND user_id=%s", (address_id, u[0]))
    addr = cursor.fetchone()
    if not addr:
        cursor.close(); db.close()
        return jsonify({"code": 404, "error": "address not found"})
    addr_snapshot = f"{addr[1]} | {addr[2]} {addr[3]}"

    is_member = bool(u[4])
    order_items = []

    if cart_ids:
        # 从购物车结算
        placeholders = ','.join(['%s'] * len(cart_ids))
        cursor.execute(f"""
            SELECT c.id, c.goods_id, g.name, g.price, g.member_price, g.image, c.specs, c.quantity, g.stock
            FROM cart c JOIN goods g ON c.goods_id=g.id
            WHERE c.id IN ({placeholders}) AND c.user_id=%s
        """, cart_ids + [u[0]])
        rows = cursor.fetchall()
        if not rows:
            cursor.close(); db.close()
            return jsonify({"code": 400, "error": "no items selected"})

        for r in rows:
            cart_id, gid, gname, gprice, gmember, gimage, gspecs, qty, gstock = r
            if gstock < qty:
                cursor.close(); db.close()
                return jsonify({"code": 400, "error": f"'{gname}' insufficient stock"})
            price = float(gmember) if (is_member and gmember) else float(gprice)
            order_items.append({
                "goods_id": gid, "goods_name": gname, "image": gimage or '',
                "specs": gspecs, "price": price, "quantity": qty,
                "subtotal": round(price * qty, 2), "cart_id": cart_id
            })
    elif goods_id:
        # 单品立即购买
        cursor.execute("SELECT id, name, price, member_price, image, stock FROM goods WHERE id=%s", (goods_id,))
        g = cursor.fetchone()
        if not g:
            cursor.close(); db.close()
            return jsonify({"code": 404, "error": "goods not found"})
        if g[5] < quantity:
            cursor.close(); db.close()
            return jsonify({"code": 400, "error": "insufficient stock"})
        price = float(g[3]) if (is_member and g[3]) else float(g[2])
        order_items.append({
            "goods_id": g[0], "goods_name": g[1], "image": g[4] or '',
            "specs": specs, "price": price, "quantity": quantity,
            "subtotal": round(price * quantity, 2), "cart_id": 0
        })
    else:
        return jsonify({"code": 400, "error": "no goods specified"})

    total = round(sum(it["subtotal"] for it in order_items), 2)
    order_no = datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:6].upper()

    # ========== Redis 分布式锁：防超卖 ==========
    locks = []
    locked_goods_ids = sorted(set(it["goods_id"] for it in order_items))
    try:
        for gid in locked_goods_ids:
            lock = RedisLock(f"stock:{gid}", expire=5, retry_times=5, retry_delay=0.1)
            if not lock.acquire():
                cursor.close(); db.close()
                return jsonify({"code": 429, "error": "系统繁忙，请稍后重试"})
            locks.append(lock)

        # 双重检查：持锁后再次确认库存（防止 lock 前库存已变）
        for it in order_items:
            cursor.execute("SELECT stock FROM goods WHERE id=%s", (it["goods_id"],))
            current_stock = cursor.fetchone()
            if not current_stock or current_stock[0] < it["quantity"]:
                cursor.close(); db.close()
                return jsonify({"code": 400, "error": f"'{it['goods_name']}' 库存不足"})

        # 创建订单
        cursor.execute(
            """INSERT INTO orders(order_no, user_id, goods_id, goods_name, price, quantity, total, status, address_id, address_snapshot)
               VALUES(%s,%s,%s,%s,%s,%s,%s,'pending',%s,%s)""",
            (order_no, u[0], order_items[0]["goods_id"], order_items[0]["goods_name"],
             order_items[0]["price"], order_items[0]["quantity"], total, address_id, addr_snapshot)
        )
        order_id = cursor.lastrowid

        # 插入 order_items + 扣库存 + 清购物车
        for it in order_items:
            cursor.execute(
                "INSERT INTO order_items(order_id, goods_id, goods_name, image, specs, price, quantity, subtotal) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                (order_id, it["goods_id"], it["goods_name"], it["image"], it["specs"], it["price"], it["quantity"], it["subtotal"])
            )
            cursor.execute("UPDATE goods SET stock=stock-%s, sales=sales+%s WHERE id=%s", (it["quantity"], it["quantity"], it["goods_id"]))
            if it["cart_id"]:
                cursor.execute("DELETE FROM cart WHERE id=%s", (it["cart_id"],))

        db.commit()

        # 发延迟队列消息：15分钟未支付自动取消
        try:
            publish_delay_cancel(order_id, order_no, locked_goods_ids, order_items, delay_seconds=900)
        except Exception:
            pass

    finally:
        # ========== 释放所有锁 ==========
        for lock in locks:
            lock.release()

    cursor.close(); db.close()
    # 清除商品缓存（库存变化）
    invalidate_goods_cache()
    # 异步发送 MQ 消息（非阻塞，MQ 挂了不影响下单）
    try:
        publish_order_created({"order_id": order_id, "order_no": order_no, "user_id": u[0], "total": total})
        publish_notify(u[0], f"订单 {order_no} 已创建，金额 ${total}")
    except Exception:
        pass
    return jsonify({"code": 200, "msg": "order created", "data": {"order_id": order_id, "order_no": order_no, "total": total}})


@app.route('/api/order/list', methods=['GET'])
def order_list():
    u = require_auth()
    status = request.args.get('status', '', type=str)
    db = get_db()
    cursor = db.cursor()
    if status:
        cursor.execute(
            "SELECT id, order_no, total, status, pay_time, create_time FROM orders WHERE user_id=%s AND status=%s ORDER BY id DESC",
            (u[0], status))
    else:
        cursor.execute(
            "SELECT id, order_no, total, status, pay_time, create_time FROM orders WHERE user_id=%s ORDER BY id DESC",
            (u[0],))
    rows = cursor.fetchall()

    orders = []
    for r in rows:
        # 查 order_items 中的商品缩略信息
        cursor.execute("SELECT id, goods_id, goods_name, image, quantity FROM order_items WHERE order_id=%s", (r[0],))
        items = cursor.fetchall()
        orders.append({
            "id": r[0], "order_no": r[1], "total": float(r[2]),
            "status": r[3], "pay_time": str(r[4]) if r[4] else None,
            "create_time": str(r[5]),
            "items": [{"id": it[0], "goods_id": it[1], "goods_name": it[2], "image": it[3], "quantity": it[4]} for it in items],
            "item_count": len(items)
        })
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "ok", "data": {"list": orders, "total": len(orders)}})


@app.route('/api/order/detail/<int:order_id>', methods=['GET'])
def order_detail(order_id):
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, order_no, total, status, address_id, address_snapshot, tracking_no, pay_time, create_time FROM orders WHERE id=%s AND user_id=%s",
        (order_id, u[0]))
    o = cursor.fetchone()
    if not o:
        cursor.close(); db.close()
        return jsonify({"code": 404, "error": "order not found"})

    # 查询 order_items
    cursor.execute("SELECT id, goods_id, goods_name, image, specs, price, quantity, subtotal FROM order_items WHERE order_id=%s", (order_id,))
    items = cursor.fetchall()

    # 查询关联售后
    cursor.execute("SELECT id, type, reason, amount, status FROM after_sale WHERE order_id=%s AND user_id=%s", (order_id, u[0]))
    after_sales = cursor.fetchall()

    cursor.close(); db.close()

    return jsonify({"code": 200, "msg": "ok", "data": {
        "id": o[0], "order_no": o[1], "total": float(o[2]),
        "status": o[3], "address_id": o[4], "address_snapshot": o[5] or '',
        "tracking_no": o[6] or '', "pay_time": str(o[7]) if o[7] else None,
        "create_time": str(o[8]),
        "items": [{
            "id": it[0], "goods_id": it[1], "goods_name": it[2],
            "image": it[3], "specs": it[4], "price": float(it[5]),
            "quantity": it[6], "subtotal": float(it[7])
        } for it in items],
        "after_sales": [{"id": a[0], "type": a[1], "reason": a[2], "amount": float(a[3]), "status": a[4]} for a in after_sales]
    }})


@app.route('/api/order/pay', methods=['POST'])
def order_pay():
    u = require_auth()
    data = request.get_json()
    order_id = data.get('order_id', 0)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, status FROM orders WHERE id=%s AND user_id=%s", (order_id, u[0]))
    o = cursor.fetchone()
    if not o:
        cursor.close(); db.close()
        return jsonify({"code": 404, "error": "order not found"})
    if o[1] != 'pending':
        cursor.close(); db.close()
        return jsonify({"code": 400, "error": f"order status is '{o[1]}', cannot pay"})
    cursor.execute("UPDATE orders SET status='paid', pay_time=NOW() WHERE id=%s", (order_id,))
    db.commit()
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "payment successful"})


@app.route('/api/order/cancel/<int:order_id>', methods=['PUT'])
def order_cancel(order_id):
    u = require_auth()
    data = request.get_json() or {}
    reason = data.get('reason', '').strip()

    if not reason:
        return jsonify({"code": 400, "error": "cancellation reason required"})
    if len(reason) < 2:
        return jsonify({"code": 400, "error": "reason too short"})

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, status FROM orders WHERE id=%s AND user_id=%s", (order_id, u[0]))
    o = cursor.fetchone()
    if not o:
        cursor.close(); db.close()
        return jsonify({"code": 404, "error": "order not found"})
    if o[1] != 'pending':
        cursor.close(); db.close()
        return jsonify({"code": 400, "error": "only pending orders can be cancelled"})

    # 恢复库存
    cursor.execute("SELECT goods_id, quantity FROM order_items WHERE order_id=%s", (order_id,))
    for it in cursor.fetchall():
        cursor.execute("UPDATE goods SET stock=stock+%s, sales=sales-%s WHERE id=%s", (it[1], it[1], it[0]))

    cursor.execute("UPDATE orders SET status='cancelled', cancel_reason=%s WHERE id=%s", (reason, order_id))
    db.commit()
    cursor.close(); db.close()
    invalidate_goods_cache()
    return jsonify({"code": 200, "msg": "order cancelled"})


@app.route('/api/order/confirm/<int:order_id>', methods=['PUT'])
def order_confirm(order_id):
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, status FROM orders WHERE id=%s AND user_id=%s", (order_id, u[0]))
    o = cursor.fetchone()
    if not o:
        cursor.close(); db.close()
        return jsonify({"code": 404, "error": "order not found"})
    if o[1] not in ('paid', 'shipped'):
        cursor.close(); db.close()
        return jsonify({"code": 400, "error": f"order status is '{o[1]}', cannot confirm receipt"})
    cursor.execute("UPDATE orders SET status='completed' WHERE id=%s", (order_id,))
    db.commit()
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "order confirmed", "data": {"status": "completed"}})


@app.route('/api/order/status/<int:order_id>', methods=['GET'])
def order_status(order_id):
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, order_no, status FROM orders WHERE id=%s AND user_id=%s", (order_id, u[0]))
    o = cursor.fetchone()
    cursor.close(); db.close()
    if not o:
        return jsonify({"code": 404, "error": "order not found"})
    return jsonify({"code": 200, "msg": "ok", "data": {"order_id": o[0], "order_no": o[1], "status": o[2]}})


# ============================================
# 七、会员模块
# ============================================
@app.route('/api/member/info', methods=['GET'])
def member_info():
    u = require_auth()
    return jsonify({"code": 200, "msg": "ok", "data": {
        "is_member": bool(u[4]),
        "member_expire": str(u[5]) if u[5] else None,
        "username": u[1]
    }})


@app.route('/api/member/activate', methods=['POST'])
def member_activate():
    """开通/续费会员（模拟支付）"""
    u = require_auth()
    data = request.get_json()
    months = data.get('months', 1)  # 默认开1个月

    if months not in [1, 3, 12]:
        return jsonify({"code": 400, "error": "months must be 1, 3, or 12"})

    db = get_db()
    cursor = db.cursor()

    # 计算新的到期时间
    if u[4] and u[5] and datetime.now() < u[5]:
        # 已是会员，续费
        new_expire = u[5] + timedelta(days=30 * months)
    else:
        new_expire = datetime.now() + timedelta(days=30 * months)

    cursor.execute("UPDATE user SET is_member=1, member_expire=%s WHERE id=%s", (new_expire, u[0]))
    db.commit()
    cursor.close(); db.close()

    return jsonify({"code": 200, "msg": "member activated", "data": {
        "is_member": True,
        "member_expire": str(new_expire)
    }})


# ============================================
# 八、售后模块
# ============================================
@app.route('/api/aftersale/apply', methods=['POST'])
def aftersale_apply():
    u = require_auth()
    data = request.get_json()
    order_id = data.get('order_id', 0)
    order_item_id = data.get('order_item_id', 0)
    goods_id = data.get('goods_id', 0)
    atype = data.get('type', 'refund')  # refund / return
    reason = data.get('reason', '').strip()
    amount = data.get('amount', 0)

    if not order_id or not goods_id or not reason or amount <= 0:
        return jsonify({"code": 400, "error": "order_id, goods_id, reason and amount are required"})
    if len(reason) < 4:
        return jsonify({"code": 400, "error": "reason must be at least 4 characters"})

    db = get_db()
    cursor = db.cursor()

    # 验证订单属于当前用户且已完成
    cursor.execute("SELECT id, status FROM orders WHERE id=%s AND user_id=%s", (order_id, u[0]))
    o = cursor.fetchone()
    if not o:
        cursor.close(); db.close()
        return jsonify({"code": 404, "error": "order not found"})
    if o[1] != 'completed':
        cursor.close(); db.close()
        return jsonify({"code": 400, "error": "can only apply after-sale for completed orders"})

    # 获取商品名
    goods_name = ''
    if goods_id:
        cursor.execute("SELECT name FROM goods WHERE id=%s", (goods_id,))
        g = cursor.fetchone()
        if g:
            goods_name = g[0]

    cursor.execute(
        "INSERT INTO after_sale(user_id, order_id, order_item_id, goods_id, goods_name, type, reason, amount, status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'pending')",
        (u[0], order_id, order_item_id, goods_id, goods_name, atype, reason, amount)
    )
    db.commit()
    aid = cursor.lastrowid
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "after-sale application submitted", "data": {"id": aid}})


@app.route('/api/aftersale/list', methods=['GET'])
def aftersale_list():
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT a.id, a.order_id, o.order_no, a.goods_name, a.type, a.reason, a.amount, a.status, a.reply, a.create_time, a.update_time
           FROM after_sale a LEFT JOIN orders o ON a.order_id=o.id
           WHERE a.user_id=%s ORDER BY a.id DESC""",
        (u[0],))
    rows = cursor.fetchall()
    cursor.close(); db.close()

    items = [{
        "id": r[0], "order_id": r[1], "order_no": r[2] or '',
        "goods_name": r[3], "type": r[4], "reason": r[5],
        "amount": float(r[6]), "status": r[7], "reply": r[8] or '',
        "create_time": str(r[9]), "update_time": str(r[10])
    } for r in rows]
    return jsonify({"code": 200, "msg": "ok", "data": {"list": items, "total": len(items)}})


@app.route('/api/aftersale/detail/<int:as_id>', methods=['GET'])
def aftersale_detail(as_id):
    u = require_auth()
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, order_id, goods_name, type, reason, amount, status, reply, create_time, update_time FROM after_sale WHERE id=%s AND user_id=%s",
        (as_id, u[0]))
    a = cursor.fetchone()
    cursor.close(); db.close()
    if not a:
        return jsonify({"code": 404, "error": "after-sale not found"})
    return jsonify({"code": 200, "msg": "ok", "data": {
        "id": a[0], "order_id": a[1], "goods_name": a[2],
        "type": a[3], "reason": a[4], "amount": float(a[5]),
        "status": a[6], "reply": a[7] or '',
        "create_time": str(a[8]), "update_time": str(a[9])
    }})


# ============================================
# 九、管理员售后处理
# ============================================
@app.route('/api/admin/aftersale/pending', methods=['GET'])
def admin_aftersale_pending():
    """管理员查看所有待处理售后"""
    u = require_auth()
    if not u[6]:  # is_admin
        return jsonify({"code": 403, "error": "admin only"})
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT a.id, a.user_id, u2.username, a.order_id, a.goods_name, a.type,
                  a.reason, a.amount, a.status, a.create_time
           FROM after_sale a LEFT JOIN user u2 ON a.user_id=u2.id
           WHERE a.status='pending' ORDER BY a.id DESC""")
    rows = cursor.fetchall()
    cursor.close(); db.close()
    items = [{
        "id": r[0], "user_id": r[1], "username": r[2] or '',
        "order_id": r[3], "goods_name": r[4], "type": r[5],
        "reason": r[6], "amount": float(r[7]), "status": r[8],
        "create_time": str(r[9])
    } for r in rows]
    return jsonify({"code": 200, "msg": "ok", "data": {"list": items, "total": len(items)}})


@app.route('/api/admin/aftersale/<int:as_id>', methods=['PUT'])
def admin_aftersale_handle(as_id):
    """管理员处理售后（同意/拒绝）"""
    u = require_auth()
    if not u[6]:
        return jsonify({"code": 403, "error": "admin only"})
    data = request.get_json() or {}
    action = data.get('action', '')  # 'approve' or 'reject'
    reply = data.get('reply', '').strip()

    if action not in ('approve', 'reject'):
        return jsonify({"code": 400, "error": "action must be approve or reject"})
    if not reply:
        return jsonify({"code": 400, "error": "reply required"})

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, status FROM after_sale WHERE id=%s", (as_id,))
    a = cursor.fetchone()
    if not a:
        cursor.close(); db.close()
        return jsonify({"code": 404, "error": "after-sale not found"})
    if a[1] != 'pending':
        cursor.close(); db.close()
        return jsonify({"code": 400, "error": "already processed"})

    new_status = 'approved' if action == 'approve' else 'rejected'
    cursor.execute("UPDATE after_sale SET status=%s, reply=%s WHERE id=%s", (new_status, reply, as_id))
    db.commit()
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "ok", "data": {"status": new_status}})


@app.route('/api/admin/order/ship/<int:order_id>', methods=['PUT'])
def admin_order_ship(order_id):
    """管理员发货"""
    u = require_auth()
    if not u[6]:
        return jsonify({"code": 403, "error": "admin only"})
    data = request.get_json() or {}
    tracking = data.get('tracking', '').strip()
    if not tracking:
        import random
        tracking = ''.join([str(random.randint(0,9)) for _ in range(12)])
    if len(tracking) < 8:
        return jsonify({"code": 400, "error": "invalid tracking number"})

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, status FROM orders WHERE id=%s", (order_id,))
    o = cursor.fetchone()
    if not o:
        cursor.close(); db.close()
        return jsonify({"code": 404, "error": "order not found"})
    if o[1] != 'paid':
        cursor.close(); db.close()
        return jsonify({"code": 400, "error": "only paid orders can be shipped"})

    cursor.execute("UPDATE orders SET status='shipped', tracking_no=%s WHERE id=%s", (tracking, order_id))
    db.commit()
    cursor.close(); db.close()
    return jsonify({"code": 200, "msg": "shipped", "data": {"tracking_no": tracking}})


@app.route('/api/admin/orders/paid', methods=['GET'])
def admin_orders_paid():
    """管理员查看待发货订单"""
    u = require_auth()
    if not u[6]:
        return jsonify({"code": 403, "error": "admin only"})
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT o.id, o.order_no, o.total, o.status, o.address_snapshot, o.create_time, u2.username
           FROM orders o LEFT JOIN user u2 ON o.user_id=u2.id
           WHERE o.status='paid' ORDER BY o.id ASC""")
    rows = cursor.fetchall()
    cursor.close(); db.close()
    items = [{
        "id": r[0], "order_no": r[1], "total": float(r[2]),
        "status": r[3], "address": r[4] or '', "create_time": str(r[5]),
        "username": r[6] or ''
    } for r in rows]
    return jsonify({"code": 200, "msg": "ok", "data": {"list": items}})


# ============================================
# 十、评价模块
# ============================================
@app.route('/api/review/add', methods=['POST'])
def review_add():
    try:
        u = require_auth()
        data = request.get_json()
        order_id = data.get('order_id', 0)
        goods_id = data.get('goods_id', 0)
        rating = data.get('rating', 5)
        content = data.get('content', '').strip()

        if not order_id or not goods_id:
            return jsonify({"code": 400, "error": "order_id and goods_id required"})

        if rating < 1 or rating > 5:
            return jsonify({"code": 400, "error": "rating must be 1-5"})
        if not content:
            return jsonify({"code": 400, "error": "review content required"})

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, status FROM orders WHERE id=%s AND user_id=%s", (order_id, u[0]))
        o = cursor.fetchone()
        if not o:
            cursor.close(); db.close()
            return jsonify({"code": 404, "error": "order not found"})
        if o[1] != 'completed':
            cursor.close(); db.close()
            return jsonify({"code": 400, "error": "can only review completed orders"})

        cursor.execute("SELECT id FROM review WHERE order_id=%s AND user_id=%s AND goods_id=%s", (order_id, u[0], goods_id))
        if cursor.fetchone():
            cursor.close(); db.close()
            return jsonify({"code": 400, "error": "already reviewed"})

        cursor.execute("INSERT INTO review(user_id, order_id, goods_id, rating, content) VALUES(%s,%s,%s,%s,%s)",
                       (u[0], order_id, goods_id, rating, content))
        db.commit()
        cursor.close(); db.close()
        return jsonify({"code": 200, "msg": "review submitted"})
    except AuthError:
        raise
    except Exception as e:
        return jsonify({"code": 500, "error": f"review failed: {str(e)}"})


@app.route('/api/review/list/<int:goods_id>', methods=['GET'])
def review_list(goods_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT r.rating, r.content, u.username, r.create_time
            FROM review r JOIN user u ON r.user_id=u.id
            WHERE r.goods_id=%s ORDER BY r.id DESC
        """, (goods_id,))
        rows = cursor.fetchall()
        cursor.close(); db.close()
        reviews = [{"rating": r[0], "content": r[1], "username": r[2], "create_time": str(r[3])} for r in rows]
        return jsonify({"code": 200, "msg": "ok", "data": {"list": reviews, "total": len(reviews)}})
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})


@app.route('/api/review/my', methods=['GET'])
def review_my():
    """获取当前用户的所有评价"""
    u = require_auth()
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT r.id, r.order_id, r.goods_id, g.name, r.rating, r.content, r.create_time
            FROM review r LEFT JOIN goods g ON r.goods_id=g.id
            WHERE r.user_id=%s ORDER BY r.id DESC
        """, (u[0],))
        rows = cursor.fetchall()
        cursor.close(); db.close()
        reviews = [{
            "id": r[0], "order_id": r[1], "goods_id": r[2],
            "goods_name": r[3] or '', "rating": r[4],
            "content": r[5] or '', "create_time": str(r[6])
        } for r in rows]
        return jsonify({"code": 200, "msg": "ok", "data": {"list": reviews, "total": len(reviews)}})
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})


# ============================================
# 十、兼容旧接口
# ============================================
@app.route('/register', methods=['POST'])
def register_old(): return register()

@app.route('/login', methods=['POST'])
def login_old(): return login()

@app.route('/1/classes/Goods', methods=['GET'])
def goods_old():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, name, price, stock FROM goods")
        rows = cursor.fetchall()
        cursor.close(); db.close()
        return jsonify({"code": 200, "msg": "ok", "data": [{"id": r[0], "name": r[1], "price": float(r[2]), "stock": r[3]} for r in rows]})
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})

@app.route('/api/user/address/add', methods=['POST'])
def address_add_old(): return address_add()

@app.route('/api/order/create', methods=['POST'])
def order_create_old(): return order_create()

@app.route('/api/order/pay', methods=['POST'])
def order_pay_old(): return order_pay()

@app.route('/api/order/status/<int:order_id>', methods=['GET'])
def order_status_old(order_id): return order_status(order_id)

@app.route('/api/goods', methods=['GET'])
def goods_list_old(): return goods_list()

@app.route('/api/logout', methods=['POST'])
def logout_old(): return logout()


if __name__ == '__main__':
    import os
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    app.run(debug=False, host=host, port=5000)
