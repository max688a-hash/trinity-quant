"""
truth_kernel/historical_kline_service.py
========================================
真实历史 K 线数据服务。
遵循最高宪法第 1 条与第 33 条：
1. 真实数据源优先 (新浪/腾讯/Binance 真实历史公开接口)；
2. 无在线数据源时返回空列表（fail-closed），严禁离线手写数组或首值填充伪造历史；
3. 单文件严格不超过 300 行，强类型规范。
"""

from dataclasses import dataclass, asdict
import json
import logging
import math
import threading
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request

_LOG = logging.getLogger(__name__)
_BINANCE_TF = {
    "D": "1d",
    "1H": "1h",
    "60m": "1h",
    "15M": "15m",
    "5M": "5m",
    "Tick": "1m",
}


@dataclass(frozen=True)
class KlineCandle:
    """真实单根 K 线蜡烛数据模型"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_up: bool
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    hold: float = 0.0


class HistoricalKlineService:
    """真实历史 K 线数据引擎（在线源 + 会话缓存，无离线伪造）"""

    _CACHE: Dict[str, List[KlineCandle]] = {}
    _CACHE_LOCK = threading.Lock()

    @classmethod
    def _fetch_sina_kline(cls, symbol: str, scale: int = 240, datalen: int = 60) -> Optional[List[KlineCandle]]:
        """从新浪真实公开行情接口获取真实历史 K 线"""
        if not (symbol.endswith(".SH") or symbol.endswith(".SZ")):
            return None
        code = symbol.split(".")[0]
        prefix = "sh" if symbol.endswith(".SH") else "sz"
        url = f"https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol={prefix}{code}&scale={scale}&ma=no&datalen={datalen}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"}
        )
        try:
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                if not isinstance(data, list) or len(data) == 0:
                    return None
                raw_candles = []
                for item in data:
                    day = item.get("day", "")
                    o = float(item.get("open", 0))
                    h = float(item.get("high", 0))
                    l = float(item.get("low", 0))
                    c = float(item.get("close", 0))
                    v = float(item.get("volume", 0))
                    if o > 0 and c > 0:
                        raw_candles.append({
                            "date": day, "open": o, "high": h, "low": l, "close": c, "vol": v
                        })
                return cls._build_candles_with_ma(raw_candles)
        except Exception as exc:
            _LOG.warning("新浪K线拉取失败 symbol=%s err=%s", symbol, exc)
            return None

    @classmethod
    def _fetch_binance_kline(
        cls, symbol: str, timeframe: str, count: int
    ) -> Optional[List[KlineCandle]]:
        """Binance 公开 K 线。失败返回空，禁止借茅台日K冒充 BTC。"""
        if not symbol.endswith("USDT"):
            return None
        interval = _BINANCE_TF.get(timeframe, "1d")
        limit = max(5, min(int(count), 500))
        url = (
            "https://api.binance.com/api/v3/klines"
            f"?symbol={symbol}&interval={interval}&limit={limit}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "TRINITY-QUANT/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            _LOG.warning("Binance K线拉取失败 symbol=%s err=%s", symbol, exc)
            return None
        if not isinstance(payload, list) or not payload:
            return None
        raw_candles: List[Dict[str, Any]] = []
        for row in payload:
            if not isinstance(row, list) or len(row) < 6:
                continue
            try:
                o = float(row[1])
                h = float(row[2])
                l = float(row[3])
                c = float(row[4])
                v = float(row[5])
            except (TypeError, ValueError) as exc:
                _LOG.warning("Binance K线无法解析 symbol=%s err=%s", symbol, exc)
                continue
            if (not math.isfinite(c)) or c <= 0.0:
                continue
            raw_candles.append({
                "date": str(row[0]),
                "open": o if math.isfinite(o) and o > 0.0 else c,
                "high": h if math.isfinite(h) and h > 0.0 else c,
                "low": l if math.isfinite(l) and l > 0.0 else c,
                "close": c,
                "vol": v if math.isfinite(v) and v >= 0.0 else 0.0,
            })
        if not raw_candles:
            return None
        return cls._build_candles_with_ma(raw_candles)

    @classmethod
    def _build_candles_with_ma(cls, raw_list: List[Dict[str, Any]]) -> List[KlineCandle]:
        """为真实蜡烛数据计算客观移动平均线 MA5/10/20/60"""
        candles: List[KlineCandle] = []
        closes: List[float] = []

        for i, item in enumerate(raw_list):
            c = float(item["close"])
            closes.append(c)

            def get_ma(period: int) -> Optional[float]:
                if len(closes) < period:
                    return None
                return round(sum(closes[-period:]) / period, 2)

            candles.append(KlineCandle(
                date=item["date"],
                open=float(item["open"]),
                high=float(item["high"]),
                low=float(item["low"]),
                close=c,
                volume=float(item["vol"]),
                is_up=(c >= float(item["open"])),
                ma5=get_ma(5),
                ma10=get_ma(10),
                ma20=get_ma(20),
                ma60=get_ma(60),
                hold=float(item.get("hold") or 0.0),
            ))
        return candles

    @classmethod
    def get_kline(cls, symbol: str, timeframe: str = "D", count: int = 60) -> List[Dict[str, Any]]:
        """
        获取标的真实 K 线历史。
        仅在线接口 + 会话内缓存；离线返回空列表，绝对杜绝手写数组/正弦波伪造。
        """
        sym = (symbol or "600519.SH").strip().upper()
        scale_map = {"D": 240, "1H": 60, "15M": 15, "5M": 5}
        scale = scale_map.get(timeframe, 240)

        if timeframe == "D":
            from truth_kernel.futures_kline_service import fetch_futures_daily
            fut_raw = fetch_futures_daily(sym, count)
            if fut_raw:
                live_fut = cls._build_candles_with_ma(fut_raw)
                with cls._CACHE_LOCK:
                    cls._CACHE[f"{sym}_{timeframe}"] = live_fut
                return [asdict(c) for c in live_fut]

        # 1. 尝试网络真实行情历史
        live_candles = cls._fetch_sina_kline(sym, scale=scale, datalen=count)
        if live_candles and len(live_candles) > 0:
            with cls._CACHE_LOCK:
                cls._CACHE[f"{sym}_{timeframe}"] = live_candles
            return [asdict(c) for c in live_candles]

        # 2. 尝试本地缓存
        cache_key = f"{sym}_{timeframe}"
        with cls._CACHE_LOCK:
            if cache_key in cls._CACHE:
                return [asdict(c) for c in cls._CACHE[cache_key]]

        crypto = cls._fetch_binance_kline(sym, timeframe, count)
        if crypto:
            with cls._CACHE_LOCK:
                cls._CACHE[f"{sym}_{timeframe}"] = crypto
            return [asdict(c) for c in crypto]

        return []

    @classmethod
    def get_recent_closes(cls, symbol: str, window: int = 30) -> List[float]:
        """获取标的真实客观收盘价序列，用于状态机与策略输入"""
        klines = cls.get_kline(symbol, timeframe="D", count=window)
        if not klines:
            return []
        closes = [float(k["close"]) for k in klines]
        return closes[-window:]
