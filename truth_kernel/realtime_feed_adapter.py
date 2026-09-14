"""
truth_kernel/realtime_feed_adapter.py
======================================
全市场实时行情适配器。
恪守最高宪法第 33 条：无新成交即零跳动，严禁高斯布朗伪造盘口。
"""

from dataclasses import dataclass
import json
import logging
import math
import threading
import time
from typing import Any, Dict, List, Optional
import urllib.request

_LOG = logging.getLogger(__name__)
# 开市连查无新观测即复用上一笔真实快照；禁止每次 HTTP 被当成随机心跳。
# ref: AGENTS.md 第 33 条 No-Trade Zero-Tick Invariant
_OPEN_SNAPSHOT_TTL_SEC = 0.35


@dataclass(frozen=True)
class MarketTick:
    """微观逐笔盘口切片数据规范"""
    symbol: str
    name: str
    timestamp: float
    time_str: str
    price: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    bid1: float
    ask1: float
    bid_vol1: float
    ask_vol1: float
    change_pct: float
    is_live: bool
    source: str
    is_closed: bool = False
    status_desc: str = ""
    open_interest: float = 0.0


class RealtimeFeedAdapter:
    """
    全市场实时行情统一适配网关。
    穿透公开行情；休市冻结真实最后收盘；拿不到行情则 DATA_UNAVAILABLE。
    """

    _ASSET_BASE_PARAMS: Dict[str, Dict[str, Any]] = {
        "600519.SH": {"name": "贵州茅台", "tick": 0.01},
        "600900.SH": {"name": "长江电力", "tick": 0.01},
        "002594.SZ": {"name": "比亚迪", "tick": 0.01},
        "000002.SZ": {"name": "万科A", "tick": 0.01},
        "SA": {"name": "纯碱主力期货", "tick": 1.0},
        "RB": {"name": "螺纹钢主力期货", "tick": 1.0},
        "AU": {"name": "沪金主力期货", "tick": 0.02},
        "BTCUSDT": {"name": "比特币现货", "tick": 0.1},
        "USDCNH": {"name": "美元离岸人民币", "tick": 0.0001},
        "DXY": {"name": "美元指数", "tick": 0.01},
    }

    def __init__(self) -> None:
        self._cache: Dict[str, MarketTick] = {}
        self._cache_lock = threading.Lock()

    def _tick_from_slice(self, symbol: str, now: float, slice_row: Any) -> MarketTick:
        return MarketTick(
            symbol=symbol, name=slice_row.name, timestamp=now, time_str=slice_row.time_str,
            price=slice_row.last, open=slice_row.open, high=slice_row.high, low=slice_row.low,
            close=slice_row.last, volume=slice_row.volume, amount=slice_row.amount,
            bid1=slice_row.bid1, ask1=slice_row.ask1,
            bid_vol1=slice_row.bid_vol1, ask_vol1=slice_row.ask_vol1,
            change_pct=slice_row.change_pct, is_live=True, source=slice_row.source,
            open_interest=float(getattr(slice_row, "open_interest", 0.0) or 0.0),
        )

    def _fetch_sina_live_quote(self, symbol: str) -> Optional[MarketTick]:
        """拉取 A 股/期货/外汇真实快照；连续合约走 nf_SA0/nf_IF0，外汇走 fx_susdcnh 与 DINIW。"""
        from truth_kernel.futures_kline_service import sina_continuous_symbol
        from truth_kernel.sina_public_quotes import (
            first_sina_fields, parse_ashare, parse_futures, parse_fx,
        )

        now = time.time()
        time_str = time.strftime("%H:%M:%S", time.localtime(now))
        cfg = self._ASSET_BASE_PARAMS.get(symbol, {"name": symbol})
        fallback_name = str(cfg.get("name") or symbol)
        if symbol.endswith(".SH") or symbol.endswith(".SZ"):
            code = symbol.split(".")[0]
            prefix = "sh" if symbol.endswith(".SH") else "sz"
            parts = first_sina_fields((f"{prefix}{code}",))
            parsed = parse_ashare(parts, time_str) if parts else None
            return self._tick_from_slice(symbol, now, parsed) if parsed else None
        cont = sina_continuous_symbol(symbol)
        if cont:
            parts = first_sina_fields((f"nf_{cont}",))
            parsed = parse_futures(parts, fallback_name, time_str) if parts else None
            return self._tick_from_slice(symbol, now, parsed) if parsed else None
        fx_lists = {
            "USDCNH": ("fx_susdcnh",),
            "DXY": ("DINIW",),
        }
        if symbol in fx_lists:
            parts = first_sina_fields(fx_lists[symbol])
            parsed = parse_fx(parts, fallback_name, time_str) if parts else None
            return self._tick_from_slice(symbol, now, parsed) if parsed else None
        return None

    def _fetch_binance_last(self, symbol: str) -> Optional[MarketTick]:
        """加密公开最新成交价。失败记日志并返回空，禁止写死 64800。"""
        if not symbol.endswith("USDT"):
            return None
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        req = urllib.request.Request(url, headers={"User-Agent": "TRINITY-QUANT/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
        except Exception as exc:
            _LOG.warning("Binance 现货价失败 symbol=%s err=%s", symbol, exc)
            return None
        try:
            px = float(payload.get("price") or 0.0)
        except (TypeError, ValueError) as exc:
            _LOG.warning("Binance 价格无法解析 symbol=%s err=%s", symbol, exc)
            return None
        if (not math.isfinite(px)) or px <= 0.0:
            return None
        now = time.time()
        time_str = time.strftime("%H:%M:%S", time.localtime(now))
        cfg = self._ASSET_BASE_PARAMS.get(symbol, {"name": symbol, "tick": 0.1})
        return MarketTick(
            symbol=symbol, name=str(cfg.get("name") or symbol), timestamp=now, time_str=time_str,
            price=px, open=px, high=px, low=px, close=px, volume=0.0, amount=0.0,
            bid1=px, ask1=px, bid_vol1=0.0, ask_vol1=0.0, change_pct=0.0,
            is_live=True, source="BINANCE_PUBLIC_TICKER"
        )

    def get_tick(self, symbol: str) -> MarketTick:
        """无成交即零跳动。拿不到行情不得写死底价。"""
        from truth_kernel.market_session_clock import MarketSessionClock
        clock = MarketSessionClock.evaluate_symbol(symbol)
        now = time.time()
        time_str = time.strftime("%H:%M:%S", time.localtime(now))

        if not clock.is_open:
            with self._cache_lock:
                cached = self._cache.get(symbol)
                if cached is not None and cached.is_closed and cached.price > 0:
                    return cached
        else:
            with self._cache_lock:
                cached = self._cache.get(symbol)
                if (
                    cached is not None
                    and cached.price > 0
                    and (now - cached.timestamp) <= _OPEN_SNAPSHOT_TTL_SEC
                ):
                    return cached

        live_tick = self._fetch_sina_live_quote(symbol)
        if live_tick is None or live_tick.price <= 0:
            live_tick = self._fetch_binance_last(symbol)
        if live_tick is not None and live_tick.price > 0:
            if not clock.is_open:
                closed_tick = MarketTick(
                    symbol=live_tick.symbol, name=live_tick.name,
                    timestamp=live_tick.timestamp, time_str=live_tick.time_str,
                    price=live_tick.price, open=live_tick.open, high=live_tick.high, low=live_tick.low,
                    close=live_tick.close, volume=live_tick.volume, amount=live_tick.amount,
                    bid1=live_tick.bid1, ask1=live_tick.ask1,
                    bid_vol1=live_tick.bid_vol1, ask_vol1=live_tick.ask_vol1,
                    change_pct=live_tick.change_pct, is_live=False, is_closed=True,
                    source="REAL_LAST_CLOSE_FROZEN",
                    status_desc=f"【交易所已休市】{clock.reason} · 真实最后收盘价已冻结",
                    open_interest=live_tick.open_interest,
                )
                with self._cache_lock:
                    self._cache[symbol] = closed_tick
                return closed_tick
            with self._cache_lock:
                self._cache[symbol] = live_tick
            return live_tick

        with self._cache_lock:
            cached = self._cache.get(symbol)
            if cached is not None and cached.price > 0:
                return MarketTick(
                    symbol=cached.symbol, name=cached.name, timestamp=now, time_str=time_str,
                    price=cached.price, open=cached.open, high=cached.high, low=cached.low,
                    close=cached.close, volume=cached.volume, amount=cached.amount,
                    bid1=cached.bid1, ask1=cached.ask1,
                    bid_vol1=cached.bid_vol1, ask_vol1=cached.ask_vol1,
                    change_pct=cached.change_pct, is_live=False, is_closed=not clock.is_open,
                    source="REAL_LAST_CLOSE_FROZEN" if not clock.is_open else "CACHE_STATIC_WAITING_TRADE",
                    status_desc="【缓存真实切片】外部网络断开，维持最后真实行情切片，零意淫跳动",
                    open_interest=cached.open_interest,
                )

        cfg = self._ASSET_BASE_PARAMS.get(symbol, {"name": symbol})
        return MarketTick(
            symbol=symbol, name=cfg.get("name", symbol), timestamp=now, time_str=time_str,
            price=0.0, open=0.0, high=0.0, low=0.0,
            close=0.0, volume=0.0, amount=0.0,
            bid1=0.0, ask1=0.0, bid_vol1=0.0, ask_vol1=0.0, change_pct=0.0,
            is_live=False, is_closed=not clock.is_open, source="DATA_UNAVAILABLE",
            status_desc="【数据源离线 DATA_UNAVAILABLE】未获取到交易所真实行情数据，严禁伪造价格"
        )

    def get_batch_ticks(self, symbols: Optional[List[str]] = None) -> List[MarketTick]:
        """批量获取指定标的或核心资产的最新 Tick"""
        target_symbols = symbols or list(self._ASSET_BASE_PARAMS.keys())
        return [self.get_tick(s) for s in target_symbols]
