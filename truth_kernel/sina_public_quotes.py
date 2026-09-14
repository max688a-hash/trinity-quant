"""新浪公开 CSV。字段下标只许来自本机 curl 探针认证过的槽位。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from truth_kernel.sina_field_probe import (
    ASHARE_SLOTS,
    CFFEX_SLOTS,
    FUTURES_SLOTS,
    FX_SLOTS,
    curl_sina_fields,
    is_numeric_token,
    safe_float,
)


@dataclass(frozen=True)
class SinaSlice:
    """新浪字段切片。缺量必须为 0，严禁填 10/1000 演播盘口。"""

    name: str
    last: float
    open: float
    high: float
    low: float
    volume: float
    open_interest: float
    amount: float
    bid1: float
    ask1: float
    bid_vol1: float
    ask_vol1: float
    change_pct: float
    time_str: str
    source: str


def _clock_text(raw: str, fallback: str) -> str:
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) >= 6:
        return f"{digits[:2]}:{digits[2:4]}:{digits[4:6]}"
    if ":" in raw:
        return raw
    return fallback


def _slot(parts: List[str], slots: Dict[str, int], name: str) -> float:
    idx = int(slots[name])
    if idx < 0 or idx >= len(parts):
        return 0.0
    return safe_float(parts[idx])


def fetch_sina_fields(list_code: str, timeout: float = 8.0) -> Optional[List[str]]:
    return curl_sina_fields(list_code, timeout=timeout)


def first_sina_fields(list_codes: Sequence[str]) -> Optional[List[str]]:
    for code in list_codes:
        parts = fetch_sina_fields(code)
        if parts:
            return parts
    return None


def parse_ashare(parts: List[str], fallback_time: str) -> Optional[SinaSlice]:
    last = _slot(parts, ASHARE_SLOTS, "last")
    prev = _slot(parts, ASHARE_SLOTS, "prev")
    if last <= 0.0 and prev > 0.0:
        last = prev
    if last <= 0.0:
        return None
    chg = round(((last - prev) / prev) * 100.0, 2) if prev > 0.0 else 0.0
    ttxt = parts[31] if len(parts) > 31 and ":" in parts[31] else fallback_time
    low_raw = _slot(parts, ASHARE_SLOTS, "low")
    return SinaSlice(
        name=parts[0] if parts else "", last=last,
        open=_slot(parts, ASHARE_SLOTS, "open") or last,
        high=max(_slot(parts, ASHARE_SLOTS, "high"), last),
        low=min(low_raw, last) if low_raw > 0.0 else last,
        volume=_slot(parts, ASHARE_SLOTS, "volume"),
        open_interest=0.0,
        amount=_slot(parts, ASHARE_SLOTS, "amount"),
        bid1=_slot(parts, ASHARE_SLOTS, "bid"),
        ask1=_slot(parts, ASHARE_SLOTS, "ask"),
        bid_vol1=_slot(parts, ASHARE_SLOTS, "bid_vol"),
        ask_vol1=_slot(parts, ASHARE_SLOTS, "ask_vol"),
        change_pct=chg, time_str=ttxt, source="SINA_LIVE_FEED",
    )


def _looks_cffex(parts: List[str]) -> bool:
    if not parts:
        return False
    return is_numeric_token(parts[0]) and safe_float(parts[0]) > 0.0


def _cjk_name(parts: List[str], fallback: str) -> str:
    for tok in reversed(parts):
        text = (tok or "").strip()
        if any("\u4e00" <= ch <= "\u9fff" for ch in text):
            return text
    return fallback


def _hhmmss(parts: List[str], fallback: str) -> str:
    for tok in parts:
        if (tok or "").count(":") == 2:
            return tok.strip()
    return fallback


def _parse_cffex_futures(
    parts: List[str], fallback_name: str, fallback_time: str,
) -> Optional[SinaSlice]:
    last = _slot(parts, CFFEX_SLOTS, "last")
    if last <= 0.0:
        return None
    prev = _slot(parts, CFFEX_SLOTS, "prev")
    chg = round(((last - prev) / prev) * 100.0, 2) if prev > 0.0 else 0.0
    high_px = _slot(parts, CFFEX_SLOTS, "high")
    low_px = _slot(parts, CFFEX_SLOTS, "low")
    return SinaSlice(
        name=_cjk_name(parts, fallback_name), last=last,
        open=last, high=high_px or last, low=low_px or last,
        volume=_slot(parts, CFFEX_SLOTS, "volume"),
        open_interest=_slot(parts, CFFEX_SLOTS, "hold"),
        amount=_slot(parts, CFFEX_SLOTS, "amount"),
        bid1=0.0, ask1=0.0, bid_vol1=0.0, ask_vol1=0.0,
        change_pct=chg, time_str=_hhmmss(parts, fallback_time),
        source="SINA_FUTURES_LIVE",
    )


def parse_futures(parts: List[str], fallback_name: str, fallback_time: str) -> Optional[SinaSlice]:
    if _looks_cffex(parts):
        return _parse_cffex_futures(parts, fallback_name, fallback_time)
    last = _slot(parts, FUTURES_SLOTS, "last")
    if last <= 0.0:
        last = _slot(parts, FUTURES_SLOTS, "bid")
    if last <= 0.0:
        return None
    open_px = _slot(parts, FUTURES_SLOTS, "open")
    high_px = _slot(parts, FUTURES_SLOTS, "high")
    low_px = _slot(parts, FUTURES_SLOTS, "low")
    name = parts[0] if parts and parts[0] else fallback_name
    ttxt = _clock_text(parts[1] if len(parts) > 1 else "", fallback_time)
    return SinaSlice(
        name=name, last=last, open=open_px or last, high=high_px or last,
        low=low_px or last,
        volume=_slot(parts, FUTURES_SLOTS, "volume"),
        open_interest=_slot(parts, FUTURES_SLOTS, "hold"),
        amount=0.0, bid1=_slot(parts, FUTURES_SLOTS, "bid"),
        ask1=_slot(parts, FUTURES_SLOTS, "ask"),
        bid_vol1=_slot(parts, FUTURES_SLOTS, "bid_vol"),
        ask_vol1=_slot(parts, FUTURES_SLOTS, "ask_vol"),
        change_pct=0.0, time_str=ttxt, source="SINA_FUTURES_LIVE",
    )


def parse_fx(parts: List[str], fallback_name: str, fallback_time: str) -> Optional[SinaSlice]:
    last = _slot(parts, FX_SLOTS, "last")
    if last <= 0.0:
        last = _slot(parts, FX_SLOTS, "bid")
    if last <= 0.0:
        return None
    name = parts[9] if len(parts) > 9 and parts[9] else fallback_name
    ttxt = parts[0] if parts and ":" in parts[0] else fallback_time
    return SinaSlice(
        name=name, last=last, open=last, high=last, low=last, volume=0.0,
        open_interest=0.0,
        amount=0.0, bid1=_slot(parts, FX_SLOTS, "bid"),
        ask1=_slot(parts, FX_SLOTS, "ask"), bid_vol1=0.0, ask_vol1=0.0,
        change_pct=0.0, time_str=ttxt, source="SINA_FX_LIVE",
    )
