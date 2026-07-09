"""将 MySQL 商品数据同步到 Elasticsearch"""
import pymysql
import json
from es_util import init_index, index_goods, delete_index

db = pymysql.connect(
    host="127.0.0.1", user="root", password="root",
    database="pycharm_test", charset="utf8"
)
cursor = db.cursor()

# 查询所有上架商品 + 分类名
cursor.execute("""
    SELECT g.id, g.name, g.price, g.member_price, g.stock, g.image,
           g.specs, g.sales, g.category_id, c.name AS category_name
    FROM goods g LEFT JOIN category c ON g.category_id=c.id
    WHERE g.is_on_sale=1
""")

goods_list = []
for row in cursor.fetchall():
    goods_list.append({
        "id": row[0],
        "name": row[1],
        "price": float(row[2]),
        "member_price": float(row[3]) if row[3] else None,
        "stock": row[4],
        "image": row[5] or "",
        "specs": json.dumps(row[6], ensure_ascii=False) if row[6] else "",
        "sales": row[7] or 0,
        "category_id": row[8],
        "category_name": row[9] or "",
    })

cursor.close()
db.close()

# 重建索引
print(f"Syncing {len(goods_list)} goods to ES...")
init_index()
index_goods(goods_list)
print(f"Done! {len(goods_list)} goods indexed.")
