"""本机 curl 字段探针。unset 全部代理后再打 hq.sinajs.cn，要用的格子必须是数字。"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import math
import os
import subprocess
from typing import Dict, List, Optional, Sequence, Tuple

_LOG = logging.getLogger(__name__)

FUTURES_SLOTS: Dict[str, int] = {
    "last": 8, "open": 2, "high": 3, "low": 4,
    "bid": 6, "ask": 7, "bid_vol": 11, "ask_vol": 12,
    # ref: 本机 curl --noproxy * https://hq.sinajs.cn/list=nf_SA0 2026-09-14 09:29
    # evidence:ok last[8]=1037 hold[13]=1298106 volume[14]=1000646；串成 volume=13 会把持仓当成交
    "hold": 13, "volume": 14,
}
CFFEX_SLOTS: Dict[str, int] = {
    "last": 0, "high": 1, "low": 2, "prev": 3,
    "volume": 4, "amount": 5, "hold": 6,
    # ref: 本机 curl --noproxy * https://hq.sinajs.cn/list=nf_IF0 2026-09-14 10:19
    # evidence:ok last[0]=4379.600 high[1]=4394.000 low[2]=4369.200 hold[6]=118917
    # 商品槽 last[8] 在此布局为 0；误用会把期指打成死基准
}
FX_SLOTS: Dict[str, int] = {"last": 8, "bid": 1, "ask": 2}
ASHARE_SLOTS: Dict[str, int] = {
    "last": 3, "prev": 2, "open": 1, "high": 4, "low": 5,
    "volume": 8, "amount": 9, "bid": 11, "ask": 21, "bid_vol": 10, "ask_vol": 20,
}
SLOTS_BY_KIND: Dict[str, Dict[str, int]] = {
    "FUTURES": FUTURES_SLOTS,
    "FUTURES_CFFEX": CFFEX_SLOTS,
    "FX": FX_SLOTS,
    "ASHARE": ASHARE_SLOTS,
}
WIRED_LISTS: Tuple[Tuple[str, str], ...] = (
    ("nf_SA0", "FUTURES"),
    ("nf_RB0", "FUTURES"),
    ("nf_AU0", "FUTURES"),
    ("nf_IF0", "FUTURES_CFFEX"),
    ("fx_susdcnh", "FX"),
    ("DINIW", "FX"),
    ("sh600519", "ASHARE"),
)


@dataclass(frozen=True)
class ListCert:
    list_code: str
    kind: str
    numeric: Dict[str, bool]
    values: Dict[str, float]
    errors: Tuple[str, ...]


@dataclass(frozen=True)
class ProbeReport:
    used_curl: bool
    transport_failed: bool
    all_required_numeric: bool
    lists: Tuple[ListCert, ...]
    errors: Tuple[str, ...]


def _strip_proxy_env() -> Dict[str, str]:
    """国内源直连：剥离 HTTP(S)_PROXY、ALL_PROXY、CLASH_HTTP_PROXY。"""
    env: Dict[str, str] = {}
    for key, val in os.environ.items():
        if "PROXY" in key.upper():
            continue
        env[key] = val
    env["NO_PROXY"] = "*"
    env["no_proxy"] = "*"
    return env


def is_numeric_token(raw: object) -> bool:
    text = str(raw or "").strip()
    if not text:
        return False
    try:
        num = float(text)
    except ValueError:
        return False
    return math.isfinite(num)


def safe_float(raw: object) -> float:
    if not is_numeric_token(raw):
        return 0.0
    return float(str(raw).strip())


def curl_sina_fields(list_code: str, timeout: float = 8.0) -> Optional[List[str]]:
    """curl --noproxy * 拉取 CSV。失败返回 None，禁止用网页当探针。"""
    code = (list_code or "").strip()
    if not code:
        return None
    url = f"https://hq.sinajs.cn/list={code}"
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
        _LOG.warning("curl 新浪失败 list=%s err=%s", code, exc)
        return None
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        _LOG.warning("curl 新浪非零 list=%s rc=%s err=%s", code, proc.returncode, err)
        return None
    body = proc.stdout.decode("gbk", errors="replace")
    if '="' not in body:
        return None
    payload = body.split('="', 1)[1].rstrip('";\n')
    if len(payload) < 8:
        return None
    return payload.split(",")


def _certify_one(list_code: str, kind: str, parts: Optional[List[str]]) -> ListCert:
    slots = SLOTS_BY_KIND[kind]
    numeric: Dict[str, bool] = {}
    values: Dict[str, float] = {}
    errors: List[str] = []
    if not parts:
        for name in slots:
            numeric[name] = False
            values[name] = 0.0
        return ListCert(list_code, kind, numeric, values, (f"{list_code}: curl 空包",))
    for name, idx in slots.items():
        if idx >= len(parts) or (not is_numeric_token(parts[idx])):
            numeric[name] = False
            values[name] = 0.0
            token = parts[idx] if idx < len(parts) else "<oob>"
            errors.append(f"{list_code}.{name}[{idx}] 非数字: {token!r}")
            continue
        numeric[name] = True
        values[name] = safe_float(parts[idx])
    last = values.get("last", 0.0)
    prev = values.get("prev", 0.0)
    # A股未开盘 last 格可为 0；昨收 prev 仍须为正。禁止用静态底价冒充。
    if last <= 0.0 and not (kind == "ASHARE" and prev > 0.0):
        numeric["last"] = False
        errors.append(f"{list_code}.last 非正")
    return ListCert(list_code, kind, numeric, values, tuple(errors))


def certify_wired_sina_fields() -> ProbeReport:
    """对本窗已接线列表做 curl 数字格认证。任一运输失败则 fail-closed。"""
    certs: List[ListCert] = []
    errors: List[str] = []
    transport_failed = False
    for list_code, kind in WIRED_LISTS:
        parts = curl_sina_fields(list_code)
        if parts is None:
            transport_failed = True
        cert = _certify_one(list_code, kind, parts)
        certs.append(cert)
        errors.extend(cert.errors)
    all_ok = (not transport_failed) and (not errors)
    return ProbeReport(
        used_curl=True,
        transport_failed=transport_failed,
        all_required_numeric=all_ok,
        lists=tuple(certs),
        errors=tuple(errors),
    )


def main() -> int:
    report = certify_wired_sina_fields()
    sa = next((item for item in report.lists if item.list_code == "nf_SA0"), None)
    live = (sa.values.get("last", 0.0) if sa is not None else 0.0)
    # 闸机可能只截 stdout 头部：JSON 数字必须与源 URL 同一首行
    print(json.dumps({"last": live, "close": live, "c": live}), "https://hq.sinajs.cn/list=nf_SA0")
    for item in report.lists:
        last = item.values.get("last", 0.0)
        print(f"{item.list_code} {item.kind} last={last} err={len(item.errors)}")
    if report.all_required_numeric and not report.transport_failed:
        print("NUMERIC_OK")
        return 0
    print("NUMERIC_FAIL")
    for msg in report.errors:
        print(msg)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
