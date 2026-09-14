"""
truth_kernel/price_history_store.py
===================================
真实日线收盘价历史快照仓（含退市标的）。

- 数据来源：新浪财经日线 K 线接口，抓取时间与来源一并落盘作为溯源证据；
  接口未声明复权方式，本仓不做二次复权，字段 adjustment 如实标记为未核验；
- 严禁手写价格数组、严禁正弦波/随机游走伪造；
- 提供“截至某日最后一个可交易收盘价”与“是否已退市”查询，供 PIT 回测使用。
"""

import json
import os
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Tuple

SINA_KLINE_URL = (
    "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
    "CN_MarketData.getKLineData?symbol={sym}&scale=240&ma=no&datalen={n}"
)
DEFAULT_PRICE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "real_financials", "real_price_history.json"
)


@dataclass(frozen=True)
class DailyClose:
    trade_date: date
    close: float


PriceSeries = List[DailyClose]


def sina_symbol(symbol: str) -> str:
    """6 位 A 股代码 → 新浪代码 (sh/sz 前缀)"""
    code = symbol.split(".")[0].strip()
    if len(code) != 6 or not code.isdigit():
        raise ValueError(f"非法 A 股代码: {symbol}")
    return ("sh" if code.startswith(("6", "9")) else "sz") + code


def fetch_sina_daily_closes(symbol: str, datalen: int = 2300, timeout: float = 15.0) -> PriceSeries:
    """在线抓取未复权日线收盘价；网络失败直接抛错，严禁静默伪造"""
    url = SINA_KLINE_URL.format(sym=sina_symbol(symbol), n=max(1, min(datalen, 5000)))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{symbol}: 新浪返回非列表载荷")
    series: PriceSeries = []
    for row in raw:
        close = float(row["close"])
        if close <= 0:
            continue
        series.append(DailyClose(trade_date=date.fromisoformat(str(row["day"])[:10]), close=close))
    series.sort(key=lambda d: d.trade_date)
    return series


def build_price_history_file(symbols: List[str], out_path: str = DEFAULT_PRICE_FILE, datalen: int = 2300) -> Dict[str, int]:
    """抓取全部标的并落盘，附带来源与抓取时间戳"""
    payload: Dict[str, object] = {
        "source": "sina_finance_kline_scale240",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "adjustment": "AS_SERVED_BY_SOURCE_UNVERIFIED",
        "series": {},
    }
    counts: Dict[str, int] = {}
    series_map: Dict[str, List[List[object]]] = {}
    for sym in symbols:
        s = fetch_sina_daily_closes(sym, datalen=datalen)
        series_map[sym] = [[d.trade_date.isoformat(), d.close] for d in s]
        counts[sym] = len(s)
    payload["series"] = series_map
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return counts


def load_price_history(path: str = DEFAULT_PRICE_FILE) -> Dict[str, PriceSeries]:
    """加载落盘价格快照；文件缺失时抛 FileNotFoundError（调用方必须如实上报，不得回退常量）"""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"缺少真实价格快照 {path}；请运行 python3 -m truth_kernel.price_history_store 抓取"
        )
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    out: Dict[str, PriceSeries] = {}
    for sym, rows in payload.get("series", {}).items():
        series = [DailyClose(trade_date=date.fromisoformat(r[0]), close=float(r[1])) for r in rows if float(r[1]) > 0]
        series.sort(key=lambda d: d.trade_date)
        out[sym] = series
    return out


def close_on_or_before(series: PriceSeries, as_of: date, max_stale_days: int = 10) -> Optional[float]:
    """截至 as_of 最后一个收盘价；若最近价格早于 as_of 超过 max_stale_days（停牌/退市）则返回 None"""
    last: Optional[DailyClose] = None
    for d in series:
        if d.trade_date > as_of:
            break
        last = d
    if last is None or (as_of - last.trade_date).days > max_stale_days:
        return None
    return last.close


def last_known_close(series: PriceSeries, as_of: date) -> Optional[Tuple[date, float]]:
    """退市/长期停牌标的的最后已知收盘（用于强制清算标价）"""
    last: Optional[DailyClose] = None
    for d in series:
        if d.trade_date > as_of:
            break
        last = d
    return (last.trade_date, last.close) if last else None


def is_listed_by(series: PriceSeries, as_of: date) -> bool:
    return bool(series) and series[0].trade_date <= as_of


if __name__ == "__main__":
    universe_path = os.path.join(os.path.dirname(DEFAULT_PRICE_FILE), "real_market_universe.json")
    with open(universe_path, "r", encoding="utf-8") as fh:
        syms = list(json.load(fh).keys())
    print(build_price_history_file(syms))
