from flask import Flask, request, jsonify
import pymysql
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

# JWT 密钥（生产环境应该放在环境变量）
JWT_SECRET = "your-secret-key-here"
JWT_EXPIRED_DAYS = 7


# ============ 数据库连接 ============
def get_db():
    try:
        return pymysql.connect(
            host="127.0.0.1",
            user="root",
            password="root",
            database="pycharm_test",
            charset="utf8",
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print("数据库连接失败：", e)
        raise


# ============ JWT Token 工具 ============
def generate_token(username):
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXPIRED_DAYS),
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token


def decode_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============ 登录鉴权装饰器 ============
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('sessionToken') or request.headers.get('Authorization')
        if not token:
            return jsonify({"code": 401, "error": "缺少Token，请先登录"})
        if token.startswith('Bearer '):
            token = token[7:]
        payload = decode_token(token)
        if not payload:
            return jsonify({"code": 401, "error": "Token无效或已过期"})
        request.current_user = payload
        return f(*args, **kwargs)

    return decorated_function


# ============ 1. 注册接口（调试模式） ============
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"code": 400, "error": "用户名和密码不能为空"})

        db = get_db()
        cursor = db.cursor()

        # 【调试阶段】允许重复注册，存在则更新密码
        cursor.execute("SELECT id FROM user WHERE username=%s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.execute(
                "UPDATE user SET password=%s, status=1 WHERE username=%s",
                (password, username)
            )
        else:
            cursor.execute(
                "INSERT INTO user(username, password, status, create_time) VALUES(%s, %s, 1, NOW())",
                (username, password)
            )

        db.commit()
        token = generate_token(username)
        cursor.close()
        db.close()

        return jsonify({
            "code": 200,
            "msg": "注册成功",
            "data": {"token": token, "username": username}
        })

    except Exception as e:
        return jsonify({"code": 500, "error": "注册失败", "detail": str(e)})


# ============ 2. 登录接口 ============
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"code": 400, "error": "用户名和密码不能为空"})

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM user WHERE username=%s AND password=%s AND status=1",
            (username, password)
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            token = generate_token(username)
            return jsonify({
                "code": 200,
                "msg": "登录成功",
                "data": {"token": token, "username": username, "user_id": user.get('id')}
            })
        else:
            return jsonify({"code": 401, "error": "用户名或密码错误，或用户已被禁用"})

    except Exception as e:
        return jsonify({"code": 500, "error": "登录失败", "detail": str(e)})


# ============ 3. 商品查询接口 ============
@app.route('/api/goods', methods=['GET'])
@login_required
def get_goods():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM goods LIMIT 10")
        goods = cursor.fetchall()
        cursor.close()
        db.close()

        if not goods:
            goods = [
                {"id": 1, "name": "iPhone 15", "price": 5999, "stock": 100},
                {"id": 2, "name": "MacBook Pro", "price": 14999, "stock": 50},
                {"id": 3, "name": "AirPods Pro", "price": 1899, "stock": 200}
            ]

        return jsonify({"code": 200, "msg": "查询成功", "data": goods})

    except Exception as e:
        return jsonify({"code": 500, "error": "查询商品失败", "detail": str(e)})


# ============ 4. 用户信息接口 ============
@app.route('/api/user/info', methods=['GET'])
@login_required
def get_user_info():
    try:
        username = request.current_user.get('username')
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, username, status, create_time FROM user WHERE username=%s",
            (username,)
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            return jsonify({"code": 200, "msg": "查询成功", "data": user})
        else:
            return jsonify({"code": 404, "error": "用户不存在"})

    except Exception as e:
        return jsonify({"code": 500, "error": "查询失败", "detail": str(e)})


# ============ 5. 退出登录 ============
@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    return jsonify({"code": 200, "msg": "退出成功"})


# ============ 6. 订单相关接口 (内存存储演示) ============
orders_db = {}

@app.route('/api/order/create', methods=['POST'])
@login_required
def create_order():
    data = request.get_json()
    goods_id = data.get('goods_id')
    num = data.get('num', 1)
    
    if not goods_id:
        return jsonify({"code": 400, "error": "商品ID不能为空"})
    
    order_id = f"ORD{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    orders_db[order_id] = {
        "order_id": order_id,
        "goods_id": goods_id,
        "num": num,
        "status": "unpaid",
        "username": request.current_user.get('username')
    }
    
    return jsonify({
        "code": 200, 
        "msg": "订单创建成功", 
        "data": {"order_id": order_id}
    })

@app.route('/api/order/pay', methods=['POST'])
@login_required
def pay_order():
    data = request.get_json()
    order_id = data.get('order_id')
    
    if not order_id or order_id not in orders_db:
        return jsonify({"code": 404, "error": "订单不存在"})
    
    orders_db[order_id]['status'] = 'paid'
    return jsonify({"code": 200, "msg": "支付成功", "data": {"order_id": order_id, "status": "paid"}})

@app.route('/api/order/status/<order_id>', methods=['GET'])
@login_required
def get_order_status(order_id):
    if order_id not in orders_db:
        return jsonify({"code": 404, "error": "订单不存在"})
    
    return jsonify({"code": 200, "msg": "查询成功", "data": orders_db[order_id]})


# ============ 健康检查 ============
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "code": 200,
        "msg": "服务正常运行",
        "data": {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0.0"
        }
    })


if __name__ == '__main__':
    print("=" * 50)
    print(" 服务启动成功！（调试模式：允许重复注册）")
    print("=" * 50)
    print("接口列表：")
    print("  POST /register       - 注册（已存在则更新密码）")
    print("  POST /login          - 登录")
    print("  GET  /api/goods      - 查询商品（需登录）")
    print("  GET  /api/user/info  - 用户信息（需登录）")
    print("  POST /api/logout     - 退出登录")
    print("  GET  /health         - 健康检查")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)