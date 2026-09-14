"""K线多空：20日通道突破 + 放量；有持仓则必须增仓，减仓突破不得标进场。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ref: 海龟 S1 20日通道；量仓启发式 Kaufman 教材，非物理定律
_WINDOW = 20
_BUY_COLOR = "#e11d48"
_SELL_COLOR = "#10b981"


def _px(row: Dict[str, Any], key: str) -> float:
    try:
        num = float(row.get(key) or 0.0)
    except (TypeError, ValueError):
        return 0.0
    return num if num == num else 0.0


def _vol(row: Dict[str, Any]) -> float:
    value = _px(row, "volume")
    if value > 0.0:
        return value
    return _px(row, "vol")


def _oi_rising(curr: Dict[str, Any], prev: Dict[str, Any]) -> Optional[bool]:
    now = _px(curr, "hold")
    was = _px(prev, "hold")
    if now <= 0.0 or was <= 0.0:
        return None
    return now > was


def attach_breakout_signals(
    candles: List[Dict[str, Any]],
    allow_short: bool = True,
    window: int = _WINDOW,
) -> None:
    """原地标注 BUY/SELL。缩量或减仓突破保持无信号。"""
    if window <= 1:
        raise ValueError("突破窗口必须大于1")
    n_len = len(candles)
    if n_len < window + 1:
        return
    for i in range(window, n_len):
        prev_bars = candles[i - window:i]
        highs = [_px(row, "high") for row in prev_bars]
        lows = [_px(row, "low") for row in prev_bars]
        vols = [_vol(row) for row in prev_bars]
        avg_vol = sum(vols) / float(len(vols)) if vols else 0.0
        cur = candles[i]
        close = _px(cur, "close")
        vol = _vol(cur)
        if close <= 0.0 or avg_vol <= 0.0 or vol < avg_vol:
            continue
        oi_up = _oi_rising(cur, candles[i - 1])
        prior_high = max(highs)
        prior_low = min(lows)
        if close > prior_high:
            if oi_up is False:
                continue
            if allow_short:
                text = "🔴 放量增仓做多" if oi_up is True else "🔴 放量突破做多"
            else:
                text = "🔴 放量增仓买入" if oi_up is True else "🔴 放量突破买入"
            cur["signal"] = {"type": "BUY", "text": text, "color": _BUY_COLOR}
            continue
        if close < prior_low:
            if oi_up is False:
                continue
            if allow_short:
                text = "🟢 放量增仓做空" if oi_up is True else "🟢 放量破位做空"
            else:
                text = "🟢 放量破位卖出"
            cur["signal"] = {"type": "SELL", "text": text, "color": _SELL_COLOR}
