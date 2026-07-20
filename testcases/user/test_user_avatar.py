""" generated test """

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest, allure
from pytest_assume.plugin import assume
from utils.yaml_utils import read_yaml_testcases
from service.common_service import CommonService
from core.db_handler import db


# 用于生成最小合法图片的辅助函数
def _create_test_image(filepath, ext="png"):
    """创建最小合法图片文件用于上传测试"""
    import struct, zlib

    if ext == "png":
        # 最小合法PNG (1x1 红色像素)
        def chunk(chunk_type, data):
            c = chunk_type + data
            crc = struct.pack(">I", zlib.crc32(c) & 0xffffffff)
            return struct.pack(">I", len(data)) + c + crc

        ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)  # 1x1, RGB
        raw = b'\x00' + b'\xff\x00\x00'  # filter=0, R=255, G=0, B=0
        idat = zlib.compress(raw)

        with open(filepath, "wb") as f:
            f.write(b'\x89PNG\r\n\x1a\n')
            f.write(chunk(b'IHDR', ihdr))
            f.write(chunk(b'IDAT', idat))
            f.write(chunk(b'IEND', b''))

    elif ext in ("jpg", "jpeg"):
        # 最小合法JPEG (SOI + APP0 + DQT + SOF0 + DHT + SOS + EOI)
        data = bytearray()
        # SOI
        data += b'\xff\xd8'
        # APP0
        data += b'\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        # DQT
        data += b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444'
        # SOF0 (1x1)
        data += b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
        # DHT
        data += b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\n\x0b'
        # SOS
        data += b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x7f\x00'
        # EOI
        data += b'\xff\xd9'
        with open(filepath, "wb") as f:
            f.write(data)

    elif ext == "gif":
        # 最小合法GIF (1x1 透明)
        data = (
            b'GIF89a'           # Header
            b'\x01\x00'         # Width = 1 (little-endian)
            b'\x01\x00'         # Height = 1
            b'\xf0\x00'         # Packed: global color table, 2 colors
            b'\x00'             # Background color index
            b'\x00'             # Pixel aspect ratio
            b'\xff\xff\xff'     # Color 0: white
            b'\xff\x00\x00'     # Color 1: red
            b'\x21\xf9\x04\x00\x00\x00\x00\x00'  # Graphic control extension
            b'\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00'  # Image descriptor + data
            b'\x3b'             # Trailer
        )
        with open(filepath, "wb") as f:
            f.write(data)


@allure.feature("user模块")
@pytest.mark.parametrize("case", read_yaml_testcases('user/user_avatar'))
def test_user_avatar(case, login_token, tmp_path):
    allure.dynamic.title(case["name"])
    d = case.get('data', {})
    expected = case['expected']
    ext = d.get('ext', 'png')

    # 创建测试图片文件
    test_file = tmp_path / f"test_avatar.{ext}"
    _create_test_image(str(test_file), ext)

    resp = CommonService().upload_avatar(file_path=str(test_file), token=login_token)
    resp_json = resp.json()
    assume(resp_json.get("code") == expected["code"])

    if expected["code"] == 200:
        data = resp_json.get("data", {})
        assume(data.get("avatar_url") is not None and len(data.get("avatar_url", "")) > 0,
               "avatar_url应不为空")
        assume(data.get("file_size", 0) > 0, "file_size应>0")

        # 验证文件扩展名
        file_name = data.get("file_name", "")
        assume(file_name.endswith(f".{ext}"), f"文件名应以.{ext}结尾, 实际={file_name}")

        # DB 断言：验证头像URL已更新
        user = db.query("SELECT avatar FROM user WHERE username='test_0006'", one=True)
        assume(user is not None, "DB: test_0006 用户应存在")
        assume(user.get("avatar") == data.get("avatar_url"),
               f"DB avatar应为 {data.get('avatar_url')}, 实际={user.get('avatar')}")
