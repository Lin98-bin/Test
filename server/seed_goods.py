"""种子数据 — 含图片占位 URL"""
import pymysql

db = pymysql.connect(host='127.0.0.1', user='root', password='root', database='pycharm_test', charset='utf8')
c = db.cursor()

c.execute('SET FOREIGN_KEY_CHECKS=0')
c.execute('DELETE FROM goods')
c.execute('DELETE FROM cart')
c.execute('ALTER TABLE goods AUTO_INCREMENT=1')
c.execute('SET FOREIGN_KEY_CHECKS=1')

# 用 picsum 生成占位图，每个商品固定一张
def img(seed):
    return f'https://picsum.photos/seed/{seed}/400/400'

goods = [
    ('iPhone 15 Pro Max 256GB', 8999.00, 7999.00, 1, 156, 2340,
     '[{"name":"颜色","values":["原色钛金属","蓝色钛金属","白色钛金属","黑色钛金属"]},{"name":"存储","values":["256GB","512GB","1TB"]}]',
     img('iphone15')),
    ('MacBook Pro 14英寸 M3', 12999.00, 11499.00, 2, 89, 1520,
     '[{"name":"颜色","values":["深空黑","银色"]},{"name":"内存","values":["16GB","32GB"]}]',
     img('macbook')),
    ('索尼 WH-1000XM5 头戴式耳机', 2499.00, 2199.00, 1, 200, 980,
     '[{"name":"颜色","values":["黑色","铂金银","午夜蓝"]}]',
     img('sony')),
    ('Nike Air Jordan 1 复古运动鞋', 1299.00, 1099.00, 4, 180, 5600,
     '[{"name":"颜色","values":["黑白","红黑","蓝白"]},{"name":"尺码","values":["39","40","41","42","43"]}]',
     img('jordan')),
    ('良品铺子 坚果大礼包 1.5kg', 168.00, 148.00, 5, 320, 8900,
     '[{"name":"规格","values":["1.5kg装","2.5kg装"]}]',
     img('nuts')),
    ('戴森 V12 无线吸尘器', 3999.00, 3499.00, 3, 75, 430,
     '[{"name":"颜色","values":["金色","银色"]}]',
     img('dyson')),
    ('海尔 三门冰箱 300L', 3299.00, 2899.00, 3, 60, 210,
     '[{"name":"颜色","values":["银色","白色"]}]',
     img('haier')),
    ('华为 MatePad Pro 12.6英寸', 4299.00, 3799.00, 2, 95, 780,
     '[{"name":"颜色","values":["星河蓝","曜石灰"]},{"name":"存储","values":["128GB","256GB"]}]',
     img('matepad')),
    ('SK-II 神仙水 230ml', 1590.00, 1390.00, 6, 150, 2300,
     '[{"name":"规格","values":["230ml","330ml"]}]',
     img('sk2')),
    ("Arcteryx Beta AR 冲锋衣", 7200.00, 6480.00, 4, 45, 320,
     '[{"name":"颜色","values":["黑色","蓝色","红色"]},{"name":"尺码","values":["S","M","L","XL"]}]',
     img('arcteryx')),
    ('农夫山泉 矿泉水 550ml*24瓶', 48.00, 42.00, 5, 500, 15000,
     '[{"name":"规格","values":["550ml*24瓶","1.5L*12瓶"]}]',
     img('water')),
    ('iPad Air M2 11英寸', 4799.00, 4299.00, 2, 110, 650,
     '[{"name":"颜色","values":["星光色","深空灰","紫色","蓝色"]},{"name":"存储","values":["128GB","256GB","512GB"]}]',
     img('ipad')),

    # 运动户外
    ('Nike Dri-FIT 速干T恤', 299.00, 259.00, 7, 200, 3200,
     '[{"name":"颜色","values":["黑色","白色","灰色"]},{"name":"尺码","values":["S","M","L","XL"]}]',
     img('niketee')),
    ('Adidas Ultraboost 跑鞋', 1099.00, 899.00, 7, 150, 1800,
     '[{"name":"颜色","values":["黑白","全黑","蓝白"]},{"name":"尺码","values":["38","39","40","41","42","43"]}]',
     img('ultraboost')),
    ('Keep 瑜伽垫 加厚防滑', 159.00, 129.00, 7, 300, 5600,
     '[{"name":"颜色","values":["紫色","蓝色","粉色","灰色"]},{"name":"厚度","values":["6mm","8mm","10mm"]}]',
     img('yogamat')),
    ('探路者 户外双人帐篷', 499.00, 399.00, 7, 80, 450,
     '[{"name":"颜色","values":["军绿色","橙色"]}]',
     img('tent')),

    # 图书音像
    ('深入理解计算机系统 第3版', 139.00, 119.00, 8, 500, 8900,
     '[{"name":"版本","values":["平装","精装"]}]',
     img('csapp')),
    ('三体 全集 (全三册)', 93.00, 79.00, 8, 600, 15000,
     '[{"name":"版本","values":["平装版","典藏版"]}]',
     img('santi')),
    ('Python编程：从入门到实践 第3版', 109.00, 89.00, 8, 400, 7200,
     '[{"name":"版本","values":["纸质版","纸质+电子版"]}]',
     img('pybook')),
    ('周杰伦 最伟大的作品 CD', 128.00, 108.00, 8, 200, 2300,
     '[{"name":"版本","values":["标准版","限量版"]}]',
     img('jaycd')),
]

for name, price, mp, cat_id, stock, sales, specs_json, image_url in goods:
    c.execute(
        'INSERT INTO goods(name, price, member_price, category_id, stock, sales, specs, image, is_on_sale) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,1)',
        (name, price, mp, cat_id, stock, sales, specs_json, image_url)
    )

db.commit()
c.execute('SELECT COUNT(*) FROM goods')
print(f'Total goods: {c.fetchone()[0]}')
c.close()
db.close()
print('Done!')
