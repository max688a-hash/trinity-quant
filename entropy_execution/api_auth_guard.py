"""
entropy_execution/api_auth_guard.py
===================================
HTTP 管理面鉴权与网络暴露面守卫。

1. 默认只绑定 127.0.0.1；对外暴露必须显式设置 TRINITY_BIND_HOST；
2. 真金/密钥库/自动巡航等高危接口必须携带 `X-Trinity-Token`（与 TRINITY_API_TOKEN 常量时间比对）；
   令牌未配置时高危接口 fail-closed 返回 403；
3. CORS 默认同源，仅当 TRINITY_CORS_ORIGIN 显式配置时才回填该 Origin，严禁 `*`。
"""

import os
from typing import Mapping, Optional

from entropy_execution.live_safety_key import resolve_api_token, verify_api_token

BIND_HOST_ENV = "TRINITY_BIND_HOST"
CORS_ORIGIN_ENV = "TRINITY_CORS_ORIGIN"
TOKEN_HEADER = "X-Trinity-Token"

PROTECTED_POST_PATHS = frozenset({
    "/api/real_money/toggle",
    "/api/real_money/order",
    "/api/real_money/unlock",
    "/api/vault/save",
    "/api/autopilot/toggle",
})
PROTECTED_GET_PATHS = frozenset({
    "/api/vault/status",
})


def resolve_bind_host() -> str:
    """服务监听地址；默认仅本机回环"""
    return os.environ.get(BIND_HOST_ENV, "127.0.0.1").strip() or "127.0.0.1"


def resolve_cors_origin() -> Optional[str]:
    """允许的跨域 Origin；未配置返回 None（同源）。显式 `*` 视为未配置。"""
    origin = os.environ.get(CORS_ORIGIN_ENV, "").strip()
    if not origin or origin == "*":
        return None
    return origin


def is_protected(method: str, path: str) -> bool:
    """该请求是否属于必须鉴权的高危接口"""
    if method.upper() == "POST":
        return path in PROTECTED_POST_PATHS
    return path in PROTECTED_GET_PATHS


def authorize(method: str, path: str, headers: Mapping[str, str]) -> Optional[str]:
    """
    返回 None 表示放行；否则返回拒绝原因。
    未配置 TRINITY_API_TOKEN 时，高危接口一律拒绝。
    """
    if not is_protected(method, path):
        return None
    if not resolve_api_token():
        return "管理令牌未配置 (TRINITY_API_TOKEN)，高危接口已锁闭"
    candidate = headers.get(TOKEN_HEADER, "") or headers.get(TOKEN_HEADER.lower(), "")
    if not verify_api_token(candidate):
        return "管理令牌缺失或错误"
    return None
