"""
entropy_execution/live_safety_key.py
====================================
真金实盘点燃 / 熔断解锁安全密钥解析器。

密钥只允许来自进程环境变量，严禁写入源码或仓库配置文件。
未配置密钥时，任何点燃与解锁请求一律拒绝（fail-closed）。
"""

import os
import secrets

SAFETY_KEY_ENV = "TRINITY_LIVE_COMBAT_SAFETY_KEY"
API_TOKEN_ENV = "TRINITY_API_TOKEN"
MIN_SECRET_LENGTH = 16


def resolve_live_combat_safety_key() -> str:
    """从环境变量读取安全密钥；未配置返回空串"""
    return os.environ.get(SAFETY_KEY_ENV, "").strip()


def is_live_combat_safety_key_configured() -> bool:
    """密钥是否已配置且长度达标"""
    return len(resolve_live_combat_safety_key()) >= MIN_SECRET_LENGTH


def verify_live_combat_safety_key(candidate: str) -> bool:
    """常量时间比对候选密钥；未配置时恒为 False"""
    expected = resolve_live_combat_safety_key()
    if len(expected) < MIN_SECRET_LENGTH:
        return False
    return secrets.compare_digest(str(candidate or ""), expected)


def resolve_api_token() -> str:
    """HTTP 管理接口令牌；未配置返回空串"""
    return os.environ.get(API_TOKEN_ENV, "").strip()


def verify_api_token(candidate: str) -> bool:
    """常量时间比对 HTTP 管理令牌；未配置时恒为 False"""
    expected = resolve_api_token()
    if len(expected) < MIN_SECRET_LENGTH:
        return False
    return secrets.compare_digest(str(candidate or ""), expected)
