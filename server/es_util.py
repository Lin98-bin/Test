"""Elasticsearch 工具 — 商品搜索"""
import os
import json
from elasticsearch import Elasticsearch

ES_HOST = os.environ.get("ES_HOST", "127.0.0.1")
ES_PORT = os.environ.get("ES_PORT", "9200")
GOODS_INDEX = "mini_mall_goods"

_es = None


def get_es():
    """懒加载 ES 连接"""
    global _es
    if _es is None:
        _es = Elasticsearch(f"http://{ES_HOST}:{ES_PORT}")
    return _es


def init_index():
    """创建商品索引"""
    es = get_es()
    try:
        es.indices.delete(index=GOODS_INDEX, ignore=[404])
    except Exception:
        pass
    es.indices.create(index=GOODS_INDEX, body={
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {"properties": {
                "id": {"type": "integer"},
                "name": {"type": "text", "analyzer": "standard"},
                "price": {"type": "float"},
                "member_price": {"type": "float"},
                "stock": {"type": "integer"},
                "image": {"type": "keyword"},
                "sales": {"type": "integer"},
                "category_id": {"type": "integer"},
                "category_name": {"type": "keyword"},
                "specs": {"type": "text"},
            }}
        })


def index_goods(goods_list):
    """批量索引商品"""
    es = get_es()
    for g in goods_list:
        es.index(index=GOODS_INDEX, id=g["id"], body=g)
    es.indices.refresh(index=GOODS_INDEX)


def search_goods(keyword="", category_id=0, page=1, page_size=20):
    """ES 搜索商品"""
    es = get_es()
    try:
        es.indices.get(index=GOODS_INDEX)
    except Exception:
        return {"list": [], "total": 0}

    must = []
    if keyword:
        must.append({"query_string": {"fields": ["name"], "query": f"*{keyword}*"}})
    if category_id:
        must.append({"term": {"category_id": category_id}})

    body = {
        "query": {"bool": {"must": must}} if must else {"match_all": {}},
        "from": (page - 1) * page_size,
        "size": page_size,
        "sort": [{"id": "desc"}],
    }

    result = es.search(index=GOODS_INDEX, body=body)
    hits = result["hits"]["hits"]
    total = result["hits"]["total"]["value"]
    goods = [h["_source"] for h in hits]
    return {"list": goods, "total": total}


def delete_index():
    """删除索引"""
    es = get_es()
    if es.indices.exists(index=GOODS_INDEX):
        es.indices.delete(index=GOODS_INDEX)
