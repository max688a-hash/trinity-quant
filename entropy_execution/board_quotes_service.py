"""
看板报价：只输出标的自有 K 线最后收盘价。
无蜡烛则 DATA_UNAVAILABLE，严禁写死 3042.88 或借用茅台历史冒充上证。
"""

from __future__ import annotations

from dataclasses import asdict
import json
import logging
import math
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Sequence

_LOG = logging.getLogger(__name__)

BOARD_DEFAULT_SYMBOLS: Sequence[str] = (
    "000001.SH",
    "NHCI",
    "DXY",
    "BTCUSDT",
    "600519.SH",
    "SA",
    "USDCNH",
)

_UNAVAILABLE: str = "DATA_UNAVAILABLE"


def _finite_positive(value: Any) -> Optional[float]:
    """防御 NaN/Inf/非数字；看板禁止把垃圾点位当成交价。"""
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        _LOG.warning("看板收盘价无法解析: %s", exc)
        return None
    if not math.isfinite(num) or num <= 0.0:
        return None
    return num


def _blocked(symbol: str) -> Dict[str, Any]:
    return {
        "symbol": symbol,
        "available": False,
        "last": None,
        "prev": None,
        "change_pct": None,
        "status": _UNAVAILABLE,
    }


def quote_from_candles(symbol: str, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    由自有蜡烛推导最后成交参考价。
    缺值阻断：空序列或非法收盘 → available=False，last=None。
    """
    sym = (symbol or "").strip().upper()
    if not candles:
        return _blocked(sym)
    last = _finite_positive(candles[-1].get("close"))
    if last is None:
        return _blocked(sym)
    prev = last
    if len(candles) >= 2:
        parsed_prev = _finite_positive(candles[-2].get("close"))
        if parsed_prev is not None:
            prev = parsed_prev
    change_pct = None
    if prev > 0.0:
        change_pct = (last - prev) / prev * 100.0
    return {
        "symbol": sym,
        "available": True,
        "last": last,
        "prev": prev,
        "change_pct": change_pct,
        "status": "OK",
    }


def _bars_from_kline_objects(raw: Any) -> List[Dict[str, Any]]:
    bars: List[Dict[str, Any]] = []
    if not raw:
        return bars
    for item in raw:
        if isinstance(item, dict):
            bars.append(item)
        else:
            bars.append(asdict(item))
    return bars


def _fetch_binance_daily(symbol: str) -> List[Dict[str, Any]]:
    """公开日 K，不是交易会话；失败则空列表，禁止合成心跳。"""
    url = (
        "https://api.binance.com/api/v3/klines"
        f"?symbol={symbol}&interval=1d&limit=5"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "TRINITY-QUANT/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        _LOG.warning("Binance 日K拉取失败 %s: %s", symbol, exc)
        return []
    if not isinstance(payload, list):
        return []
    bars: List[Dict[str, Any]] = []
    for row in payload:
        if not isinstance(row, list) or len(row) < 5:
            continue
        close_px = _finite_positive(row[4])
        if close_px is None:
            continue
        bars.append({"date": str(row[0]), "close": close_px})
    return bars


def _live_tick_bars(symbol: str) -> List[Dict[str, Any]]:
    """仅接受新浪或 Binance 公开快照；禁止走冻结基准价伪报价。"""
    from truth_kernel.realtime_feed_adapter import RealtimeFeedAdapter

    adapter = RealtimeFeedAdapter()
    try:
        tick = adapter._fetch_sina_live_quote(symbol)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        _LOG.warning("看板实时快照失败 %s: %s", symbol, exc)
        tick = None
    if tick is None:
        tick = adapter._fetch_binance_last(symbol)
    if tick is None:
        return []
    last = _finite_positive(tick.price)
    if last is None:
        return []
    prev = last
    chg = getattr(tick, "change_pct", None)
    if isinstance(chg, (int, float)) and math.isfinite(float(chg)) and abs(float(chg)) > 1e-12:
        denom = 1.0 + float(chg) / 100.0
        if denom > 0.0:
            prev = last / denom
    return [
        {"date": "prev", "close": prev},
        {"date": tick.time_str, "close": last},
    ]


def fetch_owned_kline(symbol: str) -> List[Dict[str, Any]]:
    """
    只返回该标的自己的历史。
    不得借用任何离线手写样本；无源则空列表。
    """
    from truth_kernel.historical_kline_service import HistoricalKlineService

    sym = (symbol or "").strip().upper()
    if not sym:
        return []
    live = HistoricalKlineService._fetch_sina_kline(sym, scale=240, datalen=60)
    if live:
        return _bars_from_kline_objects(live)
    if sym.endswith("USDT") and sym.isalnum():
        crypto_bars = _fetch_binance_daily(sym)
        if crypto_bars:
            return crypto_bars
    return _live_tick_bars(sym)


def handle_get_board_quotes(symbols: Optional[str] = None) -> Dict[str, Any]:
    """GET /api/market/quotes — 看板专用，缺值阻断，O(N) 标的数。"""
    raw = (symbols or ",".join(BOARD_DEFAULT_SYMBOLS)).strip()
    parts = [item.strip().upper() for item in raw.split(",") if item.strip()]
    if not parts:
        parts = list(BOARD_DEFAULT_SYMBOLS)
    quotes = [quote_from_candles(sym, fetch_owned_kline(sym)) for sym in parts]
    return {"quotes": quotes, "count": len(quotes)}
