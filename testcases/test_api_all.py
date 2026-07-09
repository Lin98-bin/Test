"""总测试入口 — 自动扫描 data/ 下所有 YAML，按接口执行"""
import sys, os, glob, random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest, allure
from pytest_assume.plugin import assume

from core.api_client import RequestsClient
from core import setting
from service.user_service import UserService
from service.goods_service import GoodsService
from service.order_service import OrderService
from service.cart_service import CartService
from service.category_service import CategoryService
from service.member_service import MemberService
from service.aftersale_service import AfterSaleService
from service.review_service import ReviewService
from service.admin_service import AdminService


# ============================================================
# 路由表: YAML 文件名 → 请求执行函数
# ============================================================
# 格式: (是否需要 token, 是否需要 admin, 执行函数)
# token 值: None=不需要, "user"=login_token, "admin"=admin_token

def _make_url(path):
    return f"{setting.BASE_URL}{path}"


def _get_address_id(token):
    """获取用户的默认地址ID，没有则创建"""
    client = RequestsClient()
    client.url = _make_url("/api/address/list")
    client.method = "get"
    client.headers = {"sessionToken": token}
    resp = client.send()
    addrs = resp.json().get("data", {}).get("list", [])
    if addrs:
        return addrs[0]["id"]
    client.url = _make_url("/api/address/add")
    client.method = "post"
    client.headers = {"sessionToken": token}
    client.json = {"address": "测试地址", "contact": "测试", "phone": "13800138000"}
    resp = client.send()
    return _get_address_id(token)


ENDPOINTS = {
    # ===== 公共接口 (无需token) =====
    "category_list": lambda c, t, a: CategoryService().get_list(),

    "goods_list": lambda c, t, a: goods_list_with_params(c.get("params", {})),
    "goods_detail": lambda c, t, a: GoodsService().get_detail(c["data"]["goods_id"]),
    "goods_search": lambda c, t, a: _goods_search(c),

    # ===== 用户接口 =====
    "user_info": lambda c, t, a: UserService().get_info(token=t),
    "user_update": lambda c, t, a: (
        lambda: [setattr(cl := RequestsClient(), 'url', _make_url("/api/user/update")),
                 setattr(cl, 'method', 'put'),
                 setattr(cl, 'headers', {"sessionToken": t}),
                 setattr(cl, 'json', c.get("data", {})),
                 cl.send()][-1]
    )(),
    "user_logout": lambda c, t, a: UserService().logout(token=t),

    # ===== 购物车接口 =====
    "cart_add": lambda c, t, a: CartService().add(
        goods_id=c["data"]["goods_id"], quantity=c["data"].get("quantity", 1), token=t),
    "cart_list": lambda c, t, a: CartService().get_list(token=t),
    "cart_count": lambda c, t, a: CartService().count(token=t),
    "cart_update": lambda c, t, a: _cart_update(t, c),
    "cart_delete": lambda c, t, a: _cart_delete(t, c),
    "cart_batch_delete": lambda c, t, a: _cart_batch_delete(t, c),

    # ===== 地址接口 =====
    "address_list": lambda c, t, a: (
        lambda: [setattr(cl := RequestsClient(), 'url', _make_url("/api/address/list")),
                 setattr(cl, 'method', 'get'),
                 setattr(cl, 'headers', {"sessionToken": t}),
                 cl.send()][-1]
    )(),
    "address_update": lambda c, t, a: _address_update(t, c),
    "address_delete": lambda c, t, a: _address_delete(t, c),
    "address_default": lambda c, t, a: _address_default(t, c),

    # ===== 订单接口 =====
    "order_create": lambda c, t, a: OrderService().create(
        goods_id=c["data"]["goods_id"], quantity=c["data"].get("quantity", 1), token=t),
    "order_list": lambda c, t, a: _order_list(t, c),
    "order_detail": lambda c, t, a: _order_detail(t, c),
    "order_pay": lambda c, t, a: _order_pay(t, c),
    "order_cancel": lambda c, t, a: _order_cancel(t, c),
    "order_confirm": lambda c, t, a: _order_confirm(t),
    "order_status": lambda c, t, a: OrderService().get_status(_new_order(t), token=t),

    # ===== 会员接口 =====
    "member_info": lambda c, t, a: MemberService().get_info(token=t),
    "member_activate": lambda c, t, a: MemberService().activate(months=c["data"]["months"], token=t),

    # ===== 售后接口 =====
    "aftersale_apply": lambda c, t, a: _aftersale_apply(t, c),
    "aftersale_list": lambda c, t, a: AfterSaleService().get_list(token=t),
    "aftersale_detail": lambda c, t, a: _aftersale_detail(t, c),

    # ===== 评价接口 =====
    "review_add": lambda c, t, a: _review_add(t, c),
    "review_list": lambda c, t, a: ReviewService().get_list(goods_id=c["data"]["goods_id"]),
    "review_my": lambda c, t, a: ReviewService().get_my(token=t),

    # ===== 管理员接口 =====
    "admin_orders_paid": lambda c, t, a: AdminService().get_paid_orders(token=a),
    "admin_order_ship": lambda c, t, a: _admin_ship(t, a, c),
    "admin_aftersale_pending": lambda c, t, a: AdminService().get_pending_aftersale(token=a),
    "admin_aftersale_handle": lambda c, t, a: _admin_handle_aftersale(t, a, c),
}


# ============================================================
# 辅助函数
# ============================================================

def goods_list_with_params(params):
    qs = "&".join(f"{k}={v}" for k, v in params.items()) if params else ""
    url = _make_url(f"/api/goods/list")
    if qs:
        url += f"?{qs}"
    client = RequestsClient()
    client.url = url
    client.method = "get"
    return client.send()


def _goods_search(case):
    kw = case.get("params", {}).get("keyword", "")
    client = RequestsClient()
    client.url = _make_url(f"/api/goods/search?keyword={kw}")
    client.method = "get"
    return client.send()


def _new_order(token):
    """创建一个新订单，返回 order_id"""
    return OrderService().create(goods_id=1, quantity=1, token=token).json()["data"]["order_id"]


def _new_paid_order(token):
    """创建一个已支付订单"""
    oid = _new_order(token)
    OrderService().pay(oid, token=token)
    return oid


def _completed_order(token):
    """创建一个已完成订单，返回 (order_id, goods_id)"""
    oid = _new_paid_order(token)
    client = RequestsClient()
    client.url = _make_url(f"/api/order/confirm/{oid}")
    client.method = "put"
    client.headers = {"sessionToken": token}
    client.send()
    return oid, 1


def _cart_update(token, case):
    data = case.get("data", {})
    cid = data.get("cart_id")
    if cid and cid == 99999:
        return CartService().update(cid, 3, token=token)
    CartService().add(goods_id=12, quantity=1, token=token)
    resp = CartService().get_list(token=token)
    items = resp.json().get("data", {}).get("items", [])
    cid = items[0]["cart_id"] if items else 1
    return CartService().update(cid, 3, token=token)


def _cart_delete(token, case):
    data = case.get("data", {})
    cid = data.get("cart_id")
    if cid and cid == 99999:
        return CartService().delete(cid, token=token)
    CartService().add(goods_id=13, quantity=1, token=token)
    resp = CartService().get_list(token=token)
    items = resp.json().get("data", {}).get("items", [])
    cid = items[0]["cart_id"] if items else 1
    return CartService().delete(cid, token=token)


def _cart_batch_delete(token, case):
    data = case.get("data", {})
    if "ids" in data:
        return CartService().batch_delete(data["ids"], token=token)
    CartService().add(goods_id=14, quantity=1, token=token)
    resp = CartService().get_list(token=token)
    items = resp.json().get("data", {}).get("items", [])
    ids = [items[0]["cart_id"]] if items else [1]
    return CartService().batch_delete(ids, token=token)


def _address_update(token, case):
    data = case.get("data", {})
    aid = data.get("id", _get_address_id(token))
    client = RequestsClient()
    client.url = _make_url("/api/address/update")
    client.method = "put"
    client.headers = {"sessionToken": token}
    client.json = {"id": aid, "contact": data.get("contact", "修改联系人")}
    return client.send()


def _address_delete(token, case):
    data = case.get("data", {})
    aid = data.get("id")
    if aid and aid == 99999:
        client = RequestsClient()
        client.url = _make_url(f"/api/address/delete/{aid}")
        client.method = "delete"
        client.headers = {"sessionToken": token}
        return client.send()
    # 创建新地址再删
    client = RequestsClient()
    client.url = _make_url("/api/address/add")
    client.method = "post"
    client.headers = {"sessionToken": token}
    client.json = {"address": "临时地址", "contact": "临", "phone": "13800138001"}
    resp = client.send()
    new_id = resp.json()["data"]["address_id"]
    client.url = _make_url(f"/api/address/delete/{new_id}")
    client.method = "delete"
    return client.send()


def _address_default(token, case):
    data = case.get("data", {})
    aid = data.get("id")
    if aid and aid == 99999:
        client = RequestsClient()
        client.url = _make_url(f"/api/address/default/{aid}")
        client.method = "put"
        client.headers = {"sessionToken": token}
        return client.send()
    aid = _get_address_id(token)
    client = RequestsClient()
    client.url = _make_url(f"/api/address/default/{aid}")
    client.method = "put"
    client.headers = {"sessionToken": token}
    return client.send()


def _order_list(token, case):
    params = case.get("params", {})
    url = _make_url("/api/order/list")
    if params.get("status"):
        url += f"?status={params['status']}"
    client = RequestsClient()
    client.url = url
    client.method = "get"
    client.headers = {"sessionToken": token}
    return client.send()


def _order_detail(token, case):
    data = case.get("data", {})
    oid = data.get("order_id", _new_order(token))
    client = RequestsClient()
    client.url = _make_url(f"/api/order/detail/{oid}")
    client.method = "get"
    client.headers = {"sessionToken": token}
    return client.send()


def _order_pay(token, case):
    data = case.get("data", {})
    oid = data.get("order_id", _new_order(token))
    return OrderService().pay(oid, token=token)


def _order_cancel(token, case):
    data = case.get("data", {})
    oid = _new_order(token)
    client = RequestsClient()
    client.url = _make_url(f"/api/order/cancel/{oid}")
    client.method = "put"
    client.headers = {"sessionToken": token}
    client.json = {"reason": data.get("reason", "")}
    return client.send()


def _order_confirm(token):
    oid = _new_paid_order(token)
    client = RequestsClient()
    client.url = _make_url(f"/api/order/confirm/{oid}")
    client.method = "put"
    client.headers = {"sessionToken": token}
    return client.send()


def _aftersale_apply(token, case):
    oid, gid = _completed_order(token)
    data = case.get("data", {})
    return AfterSaleService().apply(
        order_id=oid, goods_id=gid,
        reason=data["reason"], amount=data["amount"],
        atype=data.get("atype", "refund"), token=token)


def _aftersale_detail(token, case):
    data = case.get("data", {})
    # 显式传入 id=99999 → 测试"售后不存在"场景
    if "id" in data and data["id"] == 99999:
        return AfterSaleService().get_detail(99999, token=token)
    # 正常场景：查找或创建一个售后
    resp = AfterSaleService().get_list(token=token)
    items = resp.json().get("data", {}).get("list", [])
    if items:
        return AfterSaleService().get_detail(items[0]["id"], token=token)
    # 没有则创建新的
    oid, gid = _completed_order(token)
    apply_resp = AfterSaleService().apply(
        order_id=oid, goods_id=gid, reason="查看详情测试",
        amount=1.00, atype="refund", token=token)
    aid = apply_resp.json()["data"]["id"]
    return AfterSaleService().get_detail(aid, token=token)


def _review_add(token, case):
    oid, gid = _completed_order(token)
    data = case.get("data", {})
    return ReviewService().add(
        order_id=oid, goods_id=gid,
        rating=data.get("rating", 5),
        content=data.get("content", ""), token=token)


def _admin_ship(user_token, admin_token, case):
    oid = _new_paid_order(user_token)
    data = case.get("data", {})
    return AdminService().ship_order(oid, tracking=data.get("tracking", ""), token=admin_token)


def _admin_handle_aftersale(user_token, admin_token, case):
    oid, gid = _completed_order(user_token)
    resp = AfterSaleService().apply(
        order_id=oid, goods_id=gid, reason="管理处理测试",
        amount=1.00, atype="refund", token=user_token)
    as_id = resp.json()["data"]["id"]
    data = case.get("data", {})
    return AdminService().handle_aftersale(
        as_id, action=data["action"], reply=data["reply"], token=admin_token)


# ============================================================
# 加载所有 YAML + 生成测试
# ============================================================

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# 需要 token 的接口
NEED_AUTH = {
    "user_info", "user_update", "user_logout",
    "cart_add", "cart_list", "cart_count", "cart_update", "cart_delete", "cart_batch_delete",
    "address_list", "address_update", "address_delete", "address_default",
    "order_create", "order_list", "order_detail", "order_pay", "order_cancel", "order_confirm", "order_status",
    "member_info", "member_activate",
    "aftersale_apply", "aftersale_list", "aftersale_detail",
    "review_add", "review_my",
}

# 需要 admin 的接口
NEED_ADMIN = {
    "admin_orders_paid", "admin_order_ship", "admin_aftersale_pending", "admin_aftersale_handle",
}

# 旧格式 YAML (被老用例使用), 跳过
SKIP_FILES = {"login.yaml", "register.yaml", "address.yaml", "test.xlsx"}

import yaml


def load_all_testcases():
    """扫描 data/ 下所有 YAML，合并成一个用例列表"""
    all_cases = []
    for fpath in sorted(glob.glob(os.path.join(DATA_DIR, "*.yaml"))):
        fname = os.path.basename(fpath)
        if fname in SKIP_FILES:
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        testcases = data.get("testcases", data if isinstance(data, list) else [])
        if isinstance(testcases, list):
            for case in testcases:
                case["_file"] = fname.replace(".yaml", "")
            all_cases.extend(testcases)
    return all_cases


ALL_CASES = load_all_testcases()


def _test_id(case):
    """生成 pytest 用例 ID"""
    return f"{case.get('_file', '?')}/{case.get('name', '?')}"


@allure.parent_suite("接口自动化测试-自己练习")
@allure.suite("全量YAML数据驱动")
@pytest.mark.parametrize("case", ALL_CASES, ids=_test_id)
def test_api(case, login_token, admin_token):
    endpoint = case.get("_file", "")
    expected = case.get("expected", {})
    name = case.get("name", endpoint)

    allure.dynamic.title(f"[{endpoint}] {name}")

    if endpoint not in ENDPOINTS:
        pytest.skip(f"未注册的端点: {endpoint}")

    need_auth = endpoint in NEED_AUTH
    need_admin = endpoint in NEED_ADMIN
    token = admin_token if need_admin else (login_token if need_auth else None)

    with allure.step(f"执行: {name}"):
        try:
            resp = ENDPOINTS[endpoint](case, token, admin_token)
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = {"_raw": str(resp.text)[:200]}
        except Exception as e:
            resp_json = {"_exception": str(e)}

    with allure.step("断言结果"):
        assume(resp_json.get("code") == expected["code"],
               f"[{endpoint}] {name}: 期望 code={expected['code']}, "
               f"实际={resp_json.get('code')}, body={resp_json}")

    allure.attach(str(resp_json), "响应数据", allure.attachment_type.JSON)


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])
