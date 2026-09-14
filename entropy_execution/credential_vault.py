"""
entropy_execution/credential_vault.py
=====================================
真实券商实盘钥匙本地加密保险箱 (CredentialVault)。

1. 主密钥只允许来自环境变量 TRINITY_VAULT_MASTER_KEY（或调用方显式传入），源码中不存在默认口令；
   未配置主密钥时保存/读取一律失败（fail-closed）。
2. 密文格式：nonce(16B) || HMAC-SHA256-CTR 密文 || HMAC-SHA256 认证标签；
   密钥由 PBKDF2-HMAC-SHA256(200k 轮, 随机盐) 派生，篡改或口令错误 → 解密返回 None。
3. 对外仅暴露脱敏视图；原始凭据只在网关握手时读取。
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
from typing import Any, Dict, Optional

VAULT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "broker_vault.enc.json")
MASTER_KEY_ENV = "TRINITY_VAULT_MASTER_KEY"
GATEWAY_NAMES = ("CTP_FUTURES", "QMT_STOCK", "BINANCE_CRYPTO")
_PBKDF2_ROUNDS = 200_000
_SENSITIVE_FIELDS = frozenset({"password", "api_secret", "auth_code", "token", "secret"})


def resolve_vault_master_key(explicit: Optional[str] = None) -> str:
    """显式口令优先，否则读环境变量；空串表示未配置"""
    if explicit:
        return explicit
    return os.environ.get(MASTER_KEY_ENV, "").strip()


def _derive_keys(master_key: str, salt: bytes) -> tuple[bytes, bytes]:
    material = hashlib.pbkdf2_hmac("sha256", master_key.encode("utf-8"), salt, _PBKDF2_ROUNDS, dklen=64)
    return material[:32], material[32:]


def _keystream_xor(data: bytes, enc_key: bytes, nonce: bytes) -> bytes:
    out = bytearray()
    for block_idx in range(0, len(data), 32):
        block = hmac.new(enc_key, nonce + block_idx.to_bytes(8, "big"), hashlib.sha256).digest()
        chunk = data[block_idx:block_idx + 32]
        out.extend(b ^ k for b, k in zip(chunk, block))
    return bytes(out)


def encrypt_payload(plaintext: bytes, master_key: str) -> str:
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(16)
    enc_key, mac_key = _derive_keys(master_key, salt)
    ct = _keystream_xor(plaintext, enc_key, nonce)
    tag = hmac.new(mac_key, nonce + ct, hashlib.sha256).digest()
    return base64.b64encode(salt + nonce + ct + tag).decode("ascii")


def decrypt_payload(encoded: str, master_key: str) -> Optional[bytes]:
    try:
        blob = base64.b64decode(encoded.encode("ascii"))
    except ValueError:
        return None
    if len(blob) < 64:
        return None
    salt, nonce, ct, tag = blob[:16], blob[16:32], blob[32:-32], blob[-32:]
    enc_key, mac_key = _derive_keys(master_key, salt)
    expected = hmac.new(mac_key, nonce + ct, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, tag):
        return None
    return _keystream_xor(ct, enc_key, nonce)


class CredentialVault:
    """实盘柜台认证钥匙本地加密与脱敏隔离中枢"""

    def __init__(self, vault_path: str = VAULT_FILE) -> None:
        self.vault_path = vault_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)

    def _load_raw_vault(self) -> Dict[str, str]:
        if not os.path.exists(self.vault_path):
            return {}
        try:
            with open(self.vault_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save_raw_vault(self, data: Dict[str, str]) -> None:
        with open(self.vault_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.chmod(self.vault_path, 0o600)

    def save_gateway_credentials(self, gateway: str, creds: Dict[str, Any], master_key: Optional[str] = None) -> bool:
        """加密持久化指定网关的实盘登录凭证；主密钥缺失返回 False"""
        key = resolve_vault_master_key(master_key)
        if not key or not isinstance(creds, dict) or not creds:
            return False
        with self._lock:
            vault = self._load_raw_vault()
            vault[gateway.upper()] = encrypt_payload(json.dumps(creds).encode("utf-8"), key)
            self._save_raw_vault(vault)
            return True

    def get_gateway_credentials(self, gateway: str, master_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """解密获取原始通信凭据（仅供网关握手）；口令错误/篡改/未配置 → None"""
        key = resolve_vault_master_key(master_key)
        if not key:
            return None
        with self._lock:
            encoded = self._load_raw_vault().get(gateway.upper())
        if not encoded:
            return None
        raw = decrypt_payload(encoded, key)
        if raw is None:
            return None
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return parsed if isinstance(parsed, dict) else None

    def get_all_credentials(self, master_key: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """按网关返回可解密的全部原始凭据（供 GatewayConnectionManager 握手）"""
        result: Dict[str, Dict[str, Any]] = {}
        for gw in GATEWAY_NAMES:
            creds = self.get_gateway_credentials(gw, master_key)
            if creds:
                result[gw] = creds
        return result

    def clear_gateway_credentials(self, gateway: str) -> bool:
        """物理清除指定网关的实盘凭据"""
        with self._lock:
            vault = self._load_raw_vault()
            gw = gateway.upper()
            if gw not in vault:
                return False
            del vault[gw]
            self._save_raw_vault(vault)
            return True

    def get_masked_status(self, master_key: Optional[str] = None) -> Dict[str, Any]:
        """脱敏安全状态概览（可直接面向前端 UI）"""
        result: Dict[str, Any] = {}
        for gw in GATEWAY_NAMES:
            creds = self.get_gateway_credentials(gw, master_key)
            if not creds:
                result[gw] = {"is_configured": False, "masked_info": "未配置真实实盘凭据", "fields_count": 0}
                continue
            masked: Dict[str, str] = {}
            for k, v in creds.items():
                s = str(v)
                if k in _SENSITIVE_FIELDS:
                    masked[k] = "******"
                elif len(s) >= 6:
                    masked[k] = f"{s[:2]}...{s[-2:]}"
                elif len(s) > 2:
                    masked[k] = f"{s[:1]}***"
                else:
                    masked[k] = "***"
            result[gw] = {"is_configured": True, "masked_info": masked, "fields_count": len(creds)}
        return result
