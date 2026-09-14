"""
truth_kernel/market_session_clock.py
====================================
TRINITY QUANT 真实物理交易所交易时钟与休市防火墙。

最高宪法立宪铁律：
严禁脱离交易所物理开闭市时钟伪造成交！
1. A 股市场 (CN_EQUITY): 周一至周五 09:30-11:30, 13:00-15:00，法定节假日与周末闭市休盘;
2. 国内商品期货: 日盘 09:00-10:15 / 10:30-11:30 / 13:30-15:00，夜盘 21:00-02:30；
   中金所股指 09:30-11:30 / 13:00-15:00 无夜盘；国债 09:15-11:30 / 13:00-15:15 无夜盘;
3. 全球外汇 (FOREX): 周一 06:00 至周六 05:00 连续运转，周末闭市;
4. 全球加密资产 (CRYPTO): 7x24x365 全球无休物理实时开市;
5. 闭市时段若非显式开启【历史回放测试模式】，物理撮合引擎绝对禁止受理报单！
"""

from dataclasses import dataclass
from datetime import datetime, time as dtime, timezone, timedelta
from enum import Enum
from typing import Optional


class MarketSessionStatus(str, Enum):
    """市场开闭状态"""
    OPEN = "OPEN"                      # 正常连续竞价交易中
    CLOSED_WEEKEND = "CLOSED_WEEKEND"  # 周末法定休市
    CLOSED_NIGHT = "CLOSED_NIGHT"      # 夜间闭市时段
    CLOSED_NOON = "CLOSED_NOON"        # 午间休盘时段
    CLOSED_HOLIDAY = "CLOSED_HOLIDAY"  # 法定节假日休市


@dataclass(frozen=True)
class MarketClockCheckResult:
    """交易时钟裁决明细"""
    symbol: str
    venue: str
    is_open: bool
    status: MarketSessionStatus
    current_beijing_time: str
    reason: str
    can_execute_live: bool             # 是否允许实盘/实时模拟撮合


class MarketSessionClock:
    """物理交易所开闭市时钟判定引擎"""

    BEIJING_TZ = timezone(timedelta(hours=8))

    @classmethod
    def get_beijing_now(cls) -> datetime:
        return datetime.now(cls.BEIJING_TZ)

    @classmethod
    def evaluate_symbol(
        cls,
        symbol: str,
        simulated_dt: Optional[datetime] = None,
        is_replay_mode: bool = False
    ) -> MarketClockCheckResult:
        """
        评估标的当前是否处于合法交易时段
        """
        sym = symbol.strip().upper()
        now = simulated_dt if simulated_dt is not None else cls.get_beijing_now()
        time_str = now.strftime("%Y-%m-%d %H:%M:%S (UTC+8)")
        weekday = now.weekday()  # 0=周一, ..., 4=周五, 5=周六, 6=周日
        cur_t = now.time()

        # 1. 加密货币市场：7x24 全球连续实盘运行
        if any(c in sym for c in ("BTC", "ETH", "USDT", "SOL")):
            return MarketClockCheckResult(
                symbol=sym,
                venue="CRYPTO",
                is_open=True,
                status=MarketSessionStatus.OPEN,
                current_beijing_time=time_str,
                reason="全球加密资产 7x24x365 全天候实时开市撮合中",
                can_execute_live=True
            )

        # 回放模式特许豁免
        if is_replay_mode:
            return MarketClockCheckResult(
                symbol=sym,
                venue="REPLAY_SIM",
                is_open=True,
                status=MarketSessionStatus.OPEN,
                current_beijing_time=time_str,
                reason="用户已开启【历史回放测试模式】，特许沙盒推进",
                can_execute_live=True
            )

        # 2. 全球外汇市场 (FOREX)
        if any(fx in sym for fx in ("USDCNH", "EURUSD", "USDJPY", "GBPUSD", "DXY")):
            # 周六 05:00 至 周一 06:00 闭市
            is_fx_weekend = (weekday == 5 and cur_t >= dtime(5, 0)) or (weekday == 6) or (weekday == 0 and cur_t < dtime(6, 0))
            if is_fx_weekend:
                return MarketClockCheckResult(
                    symbol=sym,
                    venue="FOREX",
                    is_open=False,
                    status=MarketSessionStatus.CLOSED_WEEKEND,
                    current_beijing_time=time_str,
                    reason="全球外汇市场周末法定休市，周一早 06:00 开市",
                    can_execute_live=False
                )
            return MarketClockCheckResult(
                symbol=sym,
                venue="FOREX",
                is_open=True,
                status=MarketSessionStatus.OPEN,
                current_beijing_time=time_str,
                reason="全球外汇做市商交易中 (24小时连续)",
                can_execute_live=True
            )

        # 3. 国内期货：中金所股指/国债与商品时段分轨，禁止前缀硬编码串场
        from truth_kernel.cn_futures_session import evaluate_cn_future

        fut = evaluate_cn_future(sym, weekday, cur_t)
        if fut is not None:
            is_open, status_name, reason = fut
            return MarketClockCheckResult(
                symbol=sym,
                venue="CN_FUTURE",
                is_open=is_open,
                status=MarketSessionStatus[status_name],
                current_beijing_time=time_str,
                reason=reason,
                can_execute_live=is_open,
            )

        # 4. 美股股票市场 (US_EQUITY)
        is_us_stock = ".US" in sym or sym in ("AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META")
        if is_us_stock:
            if weekday == 6:
                return MarketClockCheckResult(sym, "US_EQUITY", False, MarketSessionStatus.CLOSED_WEEKEND, time_str, "美股市场周末休市", False)
            if weekday == 5 and cur_t > dtime(4, 0):
                return MarketClockCheckResult(sym, "US_EQUITY", False, MarketSessionStatus.CLOSED_WEEKEND, time_str, "美股周末休市中", False)
            if weekday == 0 and cur_t < dtime(21, 30):
                return MarketClockCheckResult(sym, "US_EQUITY", False, MarketSessionStatus.CLOSED_NIGHT, time_str, "美股未开市，开盘时间为北京时间 21:30", False)
            in_us = (cur_t >= dtime(21, 30) and weekday in (0, 1, 2, 3, 4)) or (cur_t <= dtime(4, 0) and weekday in (1, 2, 3, 4, 5))
            if in_us:
                return MarketClockCheckResult(sym, "US_EQUITY", True, MarketSessionStatus.OPEN, time_str, "美股连续竞价交易中 (纽约开盘)", True)
            else:
                return MarketClockCheckResult(sym, "US_EQUITY", False, MarketSessionStatus.CLOSED_NIGHT, time_str, "美股日间闭市中，开盘时间为北京时间 21:30", False)

        # 4. A 股股票市场 (CN_EQUITY) - 默认股票
        if weekday in (5, 6):  # 周六周日
            return MarketClockCheckResult(
                symbol=sym,
                venue="CN_EQUITY",
                is_open=False,
                status=MarketSessionStatus.CLOSED_WEEKEND,
                current_beijing_time=time_str,
                reason="中国 A 股市场周末法定休市！下周一 09:30 恢复开市交易",
                can_execute_live=False
            )

        in_am = dtime(9, 30) <= cur_t <= dtime(11, 30)
        in_pm = dtime(13, 0) <= cur_t <= dtime(15, 0)

        if in_am or in_pm:
            return MarketClockCheckResult(
                symbol=sym,
                venue="CN_EQUITY",
                is_open=True,
                status=MarketSessionStatus.OPEN,
                current_beijing_time=time_str,
                reason="A 股连续竞价交易中",
                can_execute_live=True
            )
        elif dtime(11, 30) < cur_t < dtime(13, 0):
            return MarketClockCheckResult(
                symbol=sym,
                venue="CN_EQUITY",
                is_open=False,
                status=MarketSessionStatus.CLOSED_NOON,
                current_beijing_time=time_str,
                reason="A 股午间休盘中，下午 13:00 重新开市",
                can_execute_live=False
            )
        else:
            return MarketClockCheckResult(
                symbol=sym,
                venue="CN_EQUITY",
                is_open=False,
                status=MarketSessionStatus.CLOSED_NIGHT,
                current_beijing_time=time_str,
                reason="A 股夜间闭市中，下个交易日 09:30 开盘",
                can_execute_live=False
            )
