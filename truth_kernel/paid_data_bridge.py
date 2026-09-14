"""
truth_kernel/paid_data_bridge.py
================================
TRINITY QUANT 商业收费数据源与专业专线适配桥接器。

凭证来源优先级：进程环境变量 > 本地 configs/api_credentials.env（已被 .gitignore 排除）。
`is_configured` 仅表示密钥已填写；`is_active` 必须经 `probe_liveness()` 向服务端真实探活后才为 True，
严禁以“字符串非空”冒充“商业数据源已激活”。
"""

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, replace
from typing import Dict, Optional

_DEFAULT_BASE_URL = "https://ai-tool.indevs.in"
_ENV_KEYS = ("QR_TUSHARE_KEY", "TUSHARE_REPLAY_API_KEY", "QR_TUSHARE_BASE")


@dataclass(frozen=True)
class PaidApiCredentials:
    """商业 API 凭证实体"""
    tushare_key: str
    replay_api_key: str
    api_base_url: str
    is_configured: bool
    is_active: bool
    liveness_detail: str = "UNPROBED"


def _parse_env_file(path: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not os.path.exists(path):
        return values
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    return values


class PaidDataBridge:
    """商业收费数据源桥接器"""

    def __init__(self, config_env_path: Optional[str] = None) -> None:
        if config_env_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_env_path = os.path.join(base_dir, "configs", "api_credentials.env")
        self._config_path = config_env_path
        self._credentials: Optional[PaidApiCredentials] = None
        self.reload_credentials()

    def reload_credentials(self) -> None:
        """重新加载商业密钥（不发起网络请求，is_active 归零）"""
        file_vals = _parse_env_file(self._config_path)
        merged = {k: os.environ.get(k, file_vals.get(k, "")) for k in _ENV_KEYS}
        key = merged["QR_TUSHARE_KEY"]
        is_configured = bool(key) and key.upper() != "PLACEHOLDER"
        self._credentials = PaidApiCredentials(
            tushare_key=key,
            replay_api_key=merged["TUSHARE_REPLAY_API_KEY"],
            api_base_url=merged["QR_TUSHARE_BASE"] or _DEFAULT_BASE_URL,
            is_configured=is_configured,
            is_active=False,
            liveness_detail="UNPROBED" if is_configured else "NOT_CONFIGURED",
        )

    def probe_liveness(self, timeout_seconds: float = 3.0) -> PaidApiCredentials:
        """
        向商业数据服务发起一次真实鉴权请求（Tushare 兼容协议 `api_name=trade_cal`）。
        只有服务端返回 code == 0 才判定激活。
        """
        creds = self.credentials
        if not creds.is_configured:
            return creds
        body = json.dumps({
            "api_name": "trade_cal",
            "token": creds.tushare_key,
            "params": {"exchange": "SSE", "start_date": "20240101", "end_date": "20240105"},
            "fields": "cal_date,is_open",
        }).encode("utf-8")
        req = urllib.request.Request(
            creds.api_base_url.rstrip("/"),
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": "TRINITY-QUANT/1.0"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            probed = replace(creds, is_active=False, liveness_detail=f"UNREACHABLE: {exc}")
            self._credentials = probed
            return probed
        ok = isinstance(payload, dict) and payload.get("code") == 0
        detail = "AUTHENTICATED" if ok else f"REJECTED: {payload.get('msg') if isinstance(payload, dict) else payload}"
        probed = replace(creds, is_active=ok, liveness_detail=detail)
        self._credentials = probed
        return probed

    @property
    def credentials(self) -> PaidApiCredentials:
        """获取当前凭证（is_active 仅在探活成功后为 True）"""
        if self._credentials is None:
            self.reload_credentials()
        assert self._credentials is not None
        return self._credentials
