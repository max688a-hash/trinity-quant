"""新浪期货连续日K。本机 curl --noproxy，分钟线源未通则空，禁止用日K冒充。"""

from __future__ import annotations

import json
import logging
import subprocess
from typing import Any, Dict, List, Optional, Sequence

from truth_kernel.sina_field_probe import _strip_proxy_env, is_numeric_token, safe_float

_LOG = logging.getLogger(__name__)
_DAILY_URL = (
    "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/"
    "CB=/InnerFuturesNewService.getDailyKLine?symbol={code}"
)


def sina_continuous_symbol(symbol: str) -> Optional[str]:
    """目录码 → 新浪连续合约。A股/加密/指数返回 None。"""
    raw = (symbol or "").strip().upper().split(".")[0]
    if not raw or raw.endswith("USDT") or raw in {"NHCI", "DXY", "USDCNH"}:
        return None
    if raw[:1].isdigit():
        return None
    if raw.endswith("00") and raw[:-2].isalpha():
        return raw[:-2] + "0"
    if raw.endswith("0") and raw[:-1].isalpha():
        return raw
    if raw.isalpha() and 1 <= len(raw) <= 2:
        return raw + "0"
    return None


def _curl_jsonp(url: str, timeout: float = 10.0) -> Optional[str]:
    wait = max(1, int(timeout))
    cmd: Sequence[str] = (
        "curl", "-sS", "--noproxy", "*",
        "-H", "User-Agent: Mozilla/5.0",
        "-H", "Referer: https://finance.sina.com.cn",
        "--max-time", str(wait),
        url,
    )
    try:
        proc = subprocess.run(
            list(cmd), capture_output=True, env=_strip_proxy_env(), timeout=wait + 2,
        )
    except Exception as exc:
        _LOG.warning("curl 期货日K失败 url=%s err=%s", url, exc)
        return None
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        _LOG.warning("curl 期货日K非零 rc=%s err=%s", proc.returncode, err)
        return None
    return proc.stdout.decode("utf-8", errors="replace")


def _parse_jsonp_rows(body: str) -> Optional[List[Dict[str, Any]]]:
    marker = "CB=("
    idx = body.find(marker)
    if idx < 0:
        return None
    raw = body[idx + len(marker):].strip()
    raw = raw.rstrip(";").rstrip()
    if raw.endswith(")"):
        raw = raw[:-1]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        _LOG.warning("期货日K JSON 无法解析: %s", exc)
        return None
    if not isinstance(payload, list) or not payload:
        return None
    return [row for row in payload if isinstance(row, dict)]


def fetch_futures_daily(symbol: str, count: int = 60) -> List[Dict[str, Any]]:
    """返回最近 count 根真实日K。失败空列表，禁止合成。"""
    code = sina_continuous_symbol(symbol)
    if not code:
        return []
    body = _curl_jsonp(_DAILY_URL.format(code=code))
    if not body:
        return []
    rows = _parse_jsonp_rows(body)
    if not rows:
        return []
    limit = max(5, min(int(count), 240))
    sliced = rows[-limit:]
    out: List[Dict[str, Any]] = []
    for row in sliced:
        close = safe_float(row.get("c"))
        if (not is_numeric_token(row.get("c"))) or close <= 0.0:
            continue
        open_px = safe_float(row.get("o")) or close
        high_px = safe_float(row.get("h")) or close
        low_px = safe_float(row.get("l")) or close
        out.append({
            "date": str(row.get("d") or ""),
            "open": open_px,
            "high": high_px,
            "low": low_px,
            "close": close,
            "vol": safe_float(row.get("v")),
            "hold": safe_float(row.get("p")),
        })
    return out
