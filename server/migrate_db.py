"""数据库迁移脚本 — 迷你电子商城 MVP"""
import pymysql

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "root",
    "database": "pycharm_test",
    "charset": "utf8",
}

def migrate():
    db = pymysql.connect(**DB_CONFIG)
    cursor = db.cursor()

    # ============================================
    # 1. 新建 category 分类表
    # ============================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            parent_id INT DEFAULT 0,
            sort_order INT DEFAULT 0,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    """)

    # ============================================
    # 2. 扩展 goods 商品表
    # ============================================
    cols_to_add = [
        ("image", "VARCHAR(500) DEFAULT '' COMMENT '商品主图URL'"),
        ("images", "TEXT COMMENT '多图JSON数组'"),
        ("member_price", "DECIMAL(10,2) DEFAULT NULL COMMENT '会员价'"),
        ("category_id", "INT DEFAULT 0 COMMENT '分类ID'"),
        ("specs", "TEXT COMMENT '规格JSON，如[{\"name\":\"颜色\",\"values\":[\"红\",\"蓝\"]}]'"),
        ("sales", "INT DEFAULT 0 COMMENT '销量'"),
        ("is_on_sale", "TINYINT DEFAULT 1 COMMENT '1上架 0下架'"),
    ]
    for col_name, col_def in cols_to_add:
        try:
            cursor.execute(f"ALTER TABLE goods ADD COLUMN {col_name} {col_def}")
        except Exception:
            pass  # 字段已存在则跳过

    # ============================================
    # 3. 扩展 user 用户表 — 会员字段
    # ============================================
    user_cols = [
        ("is_member", "TINYINT DEFAULT 0 COMMENT '0非会员 1会员'"),
        ("member_expire", "DATETIME DEFAULT NULL COMMENT '会员到期时间'"),
        ("nickname", "VARCHAR(50) DEFAULT '' COMMENT '昵称'"),
    ]
    for col_name, col_def in user_cols:
        try:
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_def}")
        except Exception:
            pass

    # ============================================
    # 4. 扩展 cart 购物车表 — 规格字段
    # ============================================
    try:
        cursor.execute("ALTER TABLE cart ADD COLUMN specs VARCHAR(200) DEFAULT '' COMMENT '选中的规格，如颜色:红,尺码:XL'")
    except Exception:
        pass

    # ============================================
    # 5. 新建 order_items 订单商品表（支持多商品订单）
    # ============================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            goods_id INT NOT NULL,
            goods_name VARCHAR(100) DEFAULT '',
            image VARCHAR(500) DEFAULT '',
            specs VARCHAR(200) DEFAULT '',
            price DECIMAL(10,2) DEFAULT 0,
            quantity INT DEFAULT 1,
            subtotal DECIMAL(10,2) DEFAULT 0,
            INDEX idx_order (order_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    """)

    # ============================================
    # 6. 扩展 orders 订单表 — 收货地址快照、物流单号
    # ============================================
    order_cols = [
        ("address_snapshot", "VARCHAR(500) DEFAULT '' COMMENT '收货地址快照'"),
        ("tracking_no", "VARCHAR(50) DEFAULT '' COMMENT '物流单号'"),
        ("pay_method", "VARCHAR(20) DEFAULT 'simulated' COMMENT '支付方式'"),
    ]
    for col_name, col_def in order_cols:
        try:
            cursor.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_def}")
        except Exception:
            pass
    # 确保 status 有 shipped 枚举值
    try:
        cursor.execute("ALTER TABLE orders MODIFY status ENUM('pending','paid','shipped','received','completed','cancelled') DEFAULT 'pending'")
    except Exception:
        pass

    # ============================================
    # 7. 新建 after_sale 售后表
    # ============================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS after_sale (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            order_id INT NOT NULL,
            order_item_id INT DEFAULT 0 COMMENT '售后商品项ID',
            goods_id INT DEFAULT 0,
            goods_name VARCHAR(100) DEFAULT '',
            type ENUM('refund','return') DEFAULT 'refund' COMMENT '仅退款/退货退款',
            reason VARCHAR(500) DEFAULT '' COMMENT '申请原因',
            amount DECIMAL(10,2) DEFAULT 0 COMMENT '退款金额',
            status ENUM('pending','approved','rejected','completed') DEFAULT 'pending' COMMENT '处理中/已同意/已拒绝/已完成',
            reply VARCHAR(500) DEFAULT '' COMMENT '管理员回复',
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user (user_id),
            INDEX idx_order (order_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    """)

    # ============================================
    # 8. 新建 feedback 反馈表  &  扩展 user 表 avatar 字段
    # ============================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type ENUM('suggestion','bug','complaint','other') DEFAULT 'suggestion' COMMENT '反馈类型',
            contact VARCHAR(200) DEFAULT '' COMMENT '联系方式',
            content VARCHAR(1000) DEFAULT '' COMMENT '反馈内容',
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    """)
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN avatar VARCHAR(500) DEFAULT '' COMMENT '头像URL'")
    except Exception:
        pass

    # ============================================
    # 9. 种子数据 — 插入默认分类和示例商品
    # ============================================
    cursor.execute("SELECT COUNT(*) FROM category")
    if cursor.fetchone()[0] == 0:
        categories = ["手机数码", "电脑办公", "家用电器", "服饰鞋包", "食品生鲜", "美妆护肤", "运动户外", "图书音像"]
        for i, name in enumerate(categories):
            cursor.execute("INSERT INTO category(name, sort_order) VALUES(%s, %s)", (name, i))

    cursor.execute("SELECT COUNT(*) FROM goods")
    if cursor.fetchone()[0] == 0:
        goods_data = [
            ("iPhone 15 Pro Max 256GB", 8999.00, 7999.00, 1,
             '[{"name":"颜色","values":["原色钛金属","蓝色钛金属","白色钛金属","黑色钛金属"]},{"name":"存储","values":["256GB","512GB","1TB"]}]'),
            ("MacBook Pro 14英寸 M3", 12999.00, 11499.00, 2,
             '[{"name":"颜色","values":["深空黑","银色"]},{"name":"内存","values":["16GB","32GB"]}]'),
            ("索尼 WH-1000XM5 头戴式耳机", 2499.00, 2199.00, 1,
             '[{"name":"颜色","values":["黑色","铂金银","午夜蓝"]}]'),
            ("Nike Air Jordan 1 复古运动鞋", 1299.00, 1099.00, 4,
             '[{"name":"颜色","values":["黑白","红黑","蓝白"]},{"name":"尺码","values":["39","40","41","42","43"]}]'),
            ("良品铺子 坚果大礼包 1.5kg", 168.00, 148.00, 5,
             '[{"name":"规格","values":["1.5kg装","2.5kg装"]}]'),
            ("戴森 V12 无线吸尘器", 3999.00, 3499.00, 3,
             '[{"name":"颜色","values":["金色","银色"]}]'),
            ("海尔 三门冰箱 300L", 3299.00, 2899.00, 3,
             '[{"name":"颜色","values":["银色","白色"]]'),
            ("华为 MatePad Pro 12.6英寸", 4299.00, 3799.00, 2,
             '[{"name":"颜色","values":["星河蓝","曜石灰"]},{"name":"存储","values":["128GB","256GB"]}]'),
            ("SK-II 神仙水 230ml", 1590.00, 1390.00, 6,
             '[{"name":"规格","values":["230ml","330ml"]}]'),
            ("Arc''teryx Beta AR 冲锋衣", 7200.00, 6480.00, 4,
             '[{"name":"颜色","values":["黑色","蓝色","红色"]},{"name":"尺码","values":["S","M","L","XL"]}]'),
            ("农夫山泉 矿泉水 550ml*24", 48.00, 42.00, 5,
             '[{"name":"规格","values":["550ml*24瓶","1.5L*12瓶"]}]'),
            ("iPad Air M2 11英寸", 4799.00, 4299.00, 2,
             '[{"name":"颜色","values":["星光色","深空灰","紫色","蓝色"]},{"name":"存储","values":["128GB","256GB","512GB"]}]'),
        ]
        for name, price, member_price, cat_id, specs in goods_data:
            import random
            stock = random.randint(50, 200)
            sales = random.randint(10, 1000)
            cursor.execute(
                """INSERT INTO goods(name, price, member_price, category_id, specs, stock, sales, image, is_on_sale)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,'',1)""",
                (name, price, member_price, cat_id, specs, stock, sales)
            )

    db.commit()
    cursor.close()
    db.close()
    print("✅ 数据库迁移完成！")

if __name__ == "__main__":
    migrate()
