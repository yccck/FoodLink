"""密码哈希工具（标准库 hashlib.scrypt，无需新增第三方依赖）。

存储格式：``scrypt$<N>$<salt_hex>$<dk_hex>``，可自校验、自描述。
"""
from __future__ import annotations

import hashlib
import hmac
import os

_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1
_KEY_LEN = 64
_SALT_LEN = 16


def hash_password(password: str) -> str:
    """对明文密码做 scrypt 哈希，返回可入库的字符串。"""
    salt = os.urandom(_SALT_LEN)
    dk = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_LEN,
    )
    return "scrypt${}${}${}".format(_SCRYPT_N, salt.hex(), dk.hex())


def verify_password(password: str, stored: str) -> bool:
    """校验明文密码是否与入库哈希一致。兼容旧占位数据（非 scrypt 格式返回 False）。"""
    if not stored:
        return False
    try:
        algo, n_str, salt_hex, dk_hex = stored.split("$")
        if algo != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(dk_hex)
        dk = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n_str),
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=len(expected),
        )
        return hmac.compare_digest(dk, expected)
    except (ValueError, AttributeError):
        return False
