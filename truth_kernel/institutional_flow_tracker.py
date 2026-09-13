"""
truth_kernel/institutional_flow_tracker.py
==========================================
主力资金真金穿透与散户噪音剥离器 (Institutional Flow Tracker)。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 严禁基于玄学资金指标，严格按逐笔成交金额分层切分资金性质;
2. 特大单/大单 (>=20万) 为机构真金主力，小单 (<4万) 为散户噪音;
3. 严格单文件不超过 300 行，强类型标注，零盲吞异常。
"""

from dataclasses import dataclass
import math
from typing import Dict, List


@dataclass(frozen=True)
class TickTradeItem:
    """逐笔物理成交快照"""
    price: float
    volume: int
    is_buyer_maker: bool          # True: 主动卖出(砸盘); False: 主动买入(吃单)


@dataclass(frozen=True)
class InstitutionalFlowReport:
    """主力资金真金穿透报告"""
    symbol: str
    super_large_net_inflow: float      # 超大单净流入 (>= 100万)
    large_net_inflow: float            # 大单净流入 (20万 - 100万)
    retail_net_inflow: float           # 散户小单净流入 (< 4万)
    main_force_ratio_pct: float        # 主力净流入占成交总额比例 [-100%, 100%]
    signal_judgment: str               # ACCUMULATION(吸筹) / DISTRIBUTION(出货) / NEUTRAL


class InstitutionalFlowTracker:
    """主力资金穿透追踪器"""

    SUPER_LARGE_THRESHOLD = 1_000_000.0   # 100万
    LARGE_THRESHOLD = 200_000.0           # 20万
    MEDIUM_THRESHOLD = 40_000.0           # 4万

    @classmethod
    def analyze_tick_trades(
        cls,
        symbol: str,
        trades: List[TickTradeItem]
    ) -> InstitutionalFlowReport:
        """切分并审计各层级资金真实流动"""
        super_in = 0.0
        large_in = 0.0
        retail_in = 0.0
        total_amount = 0.0

        for t in trades:
            if (
                t.price <= 0 or t.volume <= 0 or
                math.isnan(t.price) or math.isnan(t.volume) or
                math.isinf(t.price) or math.isinf(t.volume)
            ):
                continue
            amt = t.price * t.volume
            total_amount += amt
            # 主动买入为正 (+)，主动卖出为负 (-)
            direction = -1.0 if t.is_buyer_maker else 1.0
            flow = amt * direction

            if amt >= cls.SUPER_LARGE_THRESHOLD:
                super_in += flow
            elif amt >= cls.LARGE_THRESHOLD:
                large_in += flow
            elif amt < cls.MEDIUM_THRESHOLD:
                retail_in += flow

        main_force_net = super_in + large_in
        ratio = (main_force_net / total_amount * 100.0) if total_amount > 0 else 0.0

        if ratio > 15.0:
            judgment = "ACCUMULATION"        # 主力强力抢筹
        elif ratio < -15.0:
            judgment = "DISTRIBUTION"        # 主力暗中甩卖
        else:
            judgment = "NEUTRAL"

        return InstitutionalFlowReport(
            symbol=symbol,
            super_large_net_inflow=round(super_in, 2),
            large_net_inflow=round(large_in, 2),
            retail_net_inflow=round(retail_in, 2),
            main_force_ratio_pct=round(ratio, 2),
            signal_judgment=judgment
        )
