import hashlib
import base64
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad

# 加密工具类（纯代码，无测试）
class EncryptUtil:
    # 全局统一配置密钥
    AES_KEY = "1234567890123456"
    AES_IV = "6543210987654321"

    # RSA 假密钥（仅用于展示封装格式，无实际加密效果）
    RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArandomfakekey1234567890
-----END PUBLIC KEY-----"""
    RSA_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCrandomfakekey123456
-----END RSA PRIVATE KEY-----"""

    # ========== MD5加密（不可逆） ==========
    @staticmethod
    def md5_encrypt(content):
        """MD5加密"""
        md5_obj = hashlib.md5(content.encode("utf-8"))
        return md5_obj.hexdigest()

    # ========== AES-ECB 加解密 ==========
    @staticmethod
    def aes_ecb_encrypt(plain_text):
        """AES-ECB加密"""
        key = EncryptUtil.AES_KEY.encode("utf-8")
        cipher = AES.new(key, AES.MODE_ECB)
        data = pad(plain_text.encode("utf-8"), AES.block_size)
        enc_bytes = cipher.encrypt(data)
        return base64.b64encode(enc_bytes).decode()

    @staticmethod
    def aes_ecb_decrypt(cipher_text):
        """AES-ECB解密"""
        key = EncryptUtil.AES_KEY.encode("utf-8")
        cipher = AES.new(key, AES.MODE_ECB)
        data = base64.b64decode(cipher_text)
        dec_bytes = cipher.decrypt(data)
        return unpad(dec_bytes, AES.block_size).decode("utf-8")

    # ========== AES-CBC 加解密（企业常用） ==========
    @staticmethod
    def aes_cbc_encrypt(plain_text):
        """AES-CBC加密"""
        key = EncryptUtil.AES_KEY.encode("utf-8")
        iv = EncryptUtil.AES_IV.encode("utf-8")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data = pad(plain_text.encode("utf-8"), AES.block_size)
        enc_bytes = cipher.encrypt(data)
        return base64.b64encode(enc_bytes).decode()

    @staticmethod
    def aes_cbc_decrypt(cipher_text):
        """AES-CBC解密"""
        key = EncryptUtil.AES_KEY.encode("utf-8")
        iv = EncryptUtil.AES_IV.encode("utf-8")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data = base64.b64decode(cipher_text)
        dec_bytes = cipher.decrypt(data)
        return unpad(dec_bytes, AES.block_size).decode("utf-8")

    # ========== RSA 公钥加密 ==========
    @staticmethod
    def rsa_encrypt(plain_text):
        """RSA公钥加密（仅展示封装格式）"""
        pub_key = RSA.import_key(EncryptUtil.RSA_PUBLIC_KEY)
        cipher = PKCS1_v1_5.new(pub_key)
        enc_bytes = cipher.encrypt(plain_text.encode("utf-8"))
        return base64.b64encode(enc_bytes).decode()

    # ========== RSA 私钥解密 ==========
    @staticmethod
    def rsa_decrypt(cipher_text):
        """RSA私钥解密（仅展示封装格式）"""
        pri_key = RSA.import_key(EncryptUtil.RSA_PRIVATE_KEY)
        cipher = PKCS1_v1_5.new(pri_key)
        data = base64.b64decode(cipher_text)
        dec_bytes = cipher.decrypt(data, b"")
        return dec_bytes.decode("utf-8")

# ===================== 测试代码（写在类外面！） =====================
if __name__ == '__main__':
    text = "林传镔123"
    print("===== MD5加密 =====")
    print(EncryptUtil.md5_encrypt(text))

    print("\n===== AES-ECB 加解密 =====")
    ecb_mi = EncryptUtil.aes_ecb_encrypt(text)
    ecb_ming = EncryptUtil.aes_ecb_decrypt(ecb_mi)
    print("密文：", ecb_mi)
    print("解密：", ecb_ming)

    print("\n===== AES-CBC 加解密 =====")
    cbc_mi = EncryptUtil.aes_cbc_encrypt(text)
    cbc_ming = EncryptUtil.aes_cbc_decrypt(cbc_mi)
    print("密文：", cbc_mi)
    print("解密：", cbc_ming)

    print("\n===== RSA 加解密（仅展示调用格式，密钥为假无法运行） =====")
    # 因为密钥是假的，所以注释掉，仅看写法
    # rsa_mi = EncryptUtil.rsa_encrypt(text)
    # rsa_ming = EncryptUtil.rsa_decrypt(rsa_mi)
    # print("RSA密文：", rsa_mi)
    # print("RSA解密：", rsa_ming)