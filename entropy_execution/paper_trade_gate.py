"""
纸上工单门禁：无行情价不得默 1550；选股未准入不得成交。
盈利只能带全摩擦从账本长出，禁止为绿而放宽。
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, Optional, Tuple

from gravity_brain.auto_screener_engine import AutoScreenerEngine

_LOG = logging.getLogger(__name__)


def _root(symbol: str) -> str:
    return str(symbol or "").split(".")[0].strip().upper()


def _finite_positive(value: Any) -> Optional[float]:
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        _LOG.warning("纸上工单数值无法解析: %s", exc)
        return None
    if not math.isfinite(num) or num <= 0.0:
        return None
    return num


def _qualified_roots() -> set[str]:
    return {
        _root(item.symbol)
        for item in AutoScreenerEngine().run_screening()
        if item.is_qualified
    }


def _listed_symbol(symbol: str) -> str:
    raw = str(symbol or "").strip().upper()
    if not raw or "." in raw:
        return raw
    if raw[:1] in ("6", "9"):
        return f"{raw}.SH"
    if raw[:1] in ("0", "3"):
        return f"{raw}.SZ"
    return raw


def _buy_is_admitted(symbol: str) -> bool:
    if _root(symbol) not in _qualified_roots():
        return False
    from truth_kernel.pool_admission_auditor import PoolAdmissionAuditor
    docket = PoolAdmissionAuditor.get_docket(_listed_symbol(symbol))
    return bool(docket.is_buyable_now)


def evaluate_paper_ticket(payload: Dict[str, Any]) -> Tuple[bool, str, str, str, float, float]:
    """
    返回 (ok, reason, symbol, action, qty, price)。
    失败时 qty/price 为 0，调用方不得送入撮合器。
    """
    if not isinstance(payload, dict):
        return False, "DATA_UNAVAILABLE。工单不是合法对象。", "", "BUY", 0.0, 0.0
    if "price" not in payload or payload.get("price") is None or payload.get("price") == "":
        return False, "DATA_UNAVAILABLE。禁止默用 1550 冒充成交价。", "", "BUY", 0.0, 0.0
    px = _finite_positive(payload.get("price"))
    if px is None:
        return False, "DATA_UNAVAILABLE。成交价缺失或非法。", "", "BUY", 0.0, 0.0
    qty = _finite_positive(payload.get("quantity", 100.0))
    if qty is None:
        return False, "DATA_UNAVAILABLE。数量缺失或非法。", "", "BUY", 0.0, 0.0
    sym = str(payload.get("symbol", "")).strip().upper()
    if not _root(sym):
        return False, "DATA_UNAVAILABLE。标的缺失。", "", "BUY", 0.0, 0.0
    act = str(payload.get("action", "BUY")).strip().upper()
    if act not in ("BUY", "SELL"):
        return False, "DATA_UNAVAILABLE。方向非法。", sym, "BUY", 0.0, 0.0
    if act == "BUY" and not _buy_is_admitted(sym):
        return False, "法证否决或未准入，禁止纸上成交，禁止手打。", sym, act, 0.0, 0.0
    return True, "", sym, act, qty, px
