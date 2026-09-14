"""国内期货开休窗口。中金所与商品时段不得混用。"""

from __future__ import annotations

from datetime import time as dtime
from typing import Optional, Tuple

from truth_kernel.futures_kline_service import sina_continuous_symbol

CFFEX_INDEX = frozenset({"IF", "IC", "IH", "IM"})
CFFEX_BOND = frozenset({"T", "TF", "TS", "TL"})
_Status = str
_OpenReason = Tuple[bool, _Status, str]


def futures_root(symbol: str) -> Optional[str]:
    """连续码或合约月 → 品种根。A股/加密/南华返回 None。"""
    raw = (symbol or "").strip().upper().split(".")[0]
    if not raw or raw.endswith("USDT"):
        return None
    cont = sina_continuous_symbol(raw)
    if cont:
        if cont.endswith("0") and cont[:-1].isalpha():
            return cont[:-1]
        return cont
    letters = "".join(ch for ch in raw if ch.isalpha())
    digits = "".join(ch for ch in raw if ch.isdigit())
    if 1 <= len(letters) <= 2 and len(digits) >= 3:
        return letters
    return None


def session_kind(symbol: str) -> Optional[str]:
    root = futures_root(symbol)
    if root is None:
        return None
    if root in CFFEX_INDEX:
        return "CFFEX_INDEX"
    if root in CFFEX_BOND:
        return "CFFEX_BOND"
    return "COMMODITY"


def _inside(cur: dtime, start: dtime, end: dtime) -> bool:
    return start <= cur <= end


def evaluate_cn_future(symbol: str, weekday: int, cur_t: dtime) -> Optional[_OpenReason]:
    """None=非国内期货。status 为 MarketSessionStatus 名。"""
    kind = session_kind(symbol)
    if kind is None:
        return None
    if weekday == 6:
        return (
            False,
            "CLOSED_WEEKEND",
            "国内期货市场周日全天休市！严禁在休盘时段产生虚假成交！",
        )
    if weekday == 5:
        if kind == "COMMODITY" and cur_t <= dtime(2, 30):
            return True, "OPEN", "国内商品期货夜盘连续竞价撮合中"
        return False, "CLOSED_WEEKEND", "国内期货市场周末休市，下周一开盘"
    if kind == "CFFEX_INDEX":
        if _inside(cur_t, dtime(9, 30), dtime(11, 30)) or _inside(
            cur_t, dtime(13, 0), dtime(15, 0)
        ):
            return True, "OPEN", "中金所股指期货连续竞价撮合中"
        if dtime(11, 30) < cur_t < dtime(13, 0):
            return False, "CLOSED_NOON", "中金所股指午间休盘，13:00 开市"
        return False, "CLOSED_NIGHT", "中金所股指无夜盘，开市 09:30-11:30 / 13:00-15:00"
    if kind == "CFFEX_BOND":
        if _inside(cur_t, dtime(9, 15), dtime(11, 30)) or _inside(
            cur_t, dtime(13, 0), dtime(15, 15)
        ):
            return True, "OPEN", "中金所国债期货连续竞价撮合中"
        if dtime(11, 30) < cur_t < dtime(13, 0):
            return False, "CLOSED_NOON", "中金所国债午间休盘，13:00 开市"
        return False, "CLOSED_NIGHT", "中金所国债无夜盘，开市 09:15-11:30 / 13:00-15:15"
    if weekday == 0 and cur_t < dtime(9, 0):
        return False, "CLOSED_NIGHT", "国内期货周一早盘未开市，开盘时间为 09:00"
    in_day = (
        _inside(cur_t, dtime(9, 0), dtime(10, 15))
        or _inside(cur_t, dtime(10, 30), dtime(11, 30))
        or _inside(cur_t, dtime(13, 30), dtime(15, 0))
    )
    in_night = (
        cur_t >= dtime(21, 0) and weekday in (0, 1, 2, 3, 4)
    ) or (cur_t <= dtime(2, 30) and weekday in (1, 2, 3, 4, 5))
    if in_day or in_night:
        return True, "OPEN", "国内商品期货连续竞价撮合中"
    return False, "CLOSED_NIGHT", "国内期货非交易时段 (休盘中)，开市时间: 09:00 / 21:00"
