from flask import Flask, request, jsonify
import pymysql

app = Flask(__name__)

# 连接数据库（带异常捕获）
def get_db():
    try:
        return pymysql.connect(
            host="127.0.0.1",
            user="root",
            password="root",
            database="pycharm_test",
            charset="utf8"
        )
    except Exception as e:
        print("数据库连接失败：", e)
        raise

# 注册接口（加了异常捕获，永远不会超时）
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"code": 400, "error": "用户名密码不能为空"})

        db = get_db()
        cursor = db.cursor()

        # 插入数据
        cursor.execute(
            "INSERT INTO user(username,password) VALUES(%s,%s)",
            (username, password)
        )
        db.commit()

        cursor.close()
        db.close()

        return jsonify({"code": 200, "msg": "注册成功！"})

    except Exception as e:
        # 关键：出错必须返回，否则会一直卡死
        return jsonify({
            "code": 500,
            "error": "注册失败",
            "detail": str(e)
        })

# 登录接口（正常）
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM user WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            return jsonify({"code": 200, "msg": "登录成功"})
        else:
            return jsonify({"code": 401, "error": "用户名或密码错误"})
    except:
        return jsonify({"code": 500, "error": "服务器异常"})


# 新增：商品查询接口（GET方法，只读，适合生产环境巡检）
# 新增：商品查询接口
@app.route('/1/classes/Goods', methods=['GET'])
def get_goods():
    try:
        goods_list = [
            {"id": 1, "name": "iPhone 15", "price": 5999, "stock": 100},
            {"id": 2, "name": "MacBook Pro", "price": 14999, "stock": 50},
            {"id": 3, "name": "AirPods Pro", "price": 1899, "stock": 200}
        ]

        return jsonify({
            "code": 200,
            "msg": "查询成功",
            "data": goods_list
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "error": "查询商品失败",
            "detail": str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)