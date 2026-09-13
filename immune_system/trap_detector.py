"""
immune_system/trap_detector.py
==============================
TRINITY QUANT 庄家诱多、假突破与价值陷阱多维识别引擎。

识别市场看不见的致命陷阱：
1. 庄家诱多出货陷阱 (量价严重背离、高位缩量拉升出货、假突破);
2. 假大单托盘陷阱 (Phantom Spoofing: 买一巨量挂单掩护小单出货);
3. 伪便宜价值陷阱 (Value Trap: 低市盈率掩盖现金流枯竭与主业衰退)。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TrapType(str, Enum):
    """陷阱类型分类"""
    NONE = "NONE"                                    # 无异常陷阱
    PUMP_AND_DUMP_BULL_TRAP = "PUMP_AND_DUMP"        # 诱多拉高出货陷阱
    SPOOFING_PHANTOM_BID = "SPOOFING_PHANTOM_BID"    # 虚假大单托盘出货
    VALUE_TRAP = "VALUE_TRAP"                        # 伪便宜价值陷阱


@dataclass(frozen=True)
class TrapAuditReport:
    """陷阱审计决策"""
    symbol: str
    trap_detected: TrapType
    is_safe_to_enter: bool
    confidence_score: float                          # 0.0 ~ 1.0
    evidence_details: str


class TrapDetector:
    """多维投资与庄家操盘陷阱识别器"""

    def __init__(
        self,
        volume_divergence_threshold: float = 0.50,
        spoofing_ratio_threshold: float = 4.0
    ) -> None:
        if volume_divergence_threshold <= 0:
            raise ValueError("背离阈值必须大于0")
        if spoofing_ratio_threshold <= 1.0:
            raise ValueError("假托单比例必须大于1.0")
        self._vol_div_thresh = volume_divergence_threshold
        self._spoof_thresh = spoofing_ratio_threshold

    def audit_manipulator_traps(
        self,
        symbol: str,
        price_change_pct: float,
        recent_avg_volume: float,
        current_breakout_volume: float,
        bid_volume_top3: float,
        ask_volume_top3: float,
        real_executed_sell_volume: float,
        real_executed_buy_volume: float
    ) -> TrapAuditReport:
        """
        审计庄家对倒、诱多出货与假大单托盘
        
        :param price_change_pct: 盘中或当期涨幅 (如 +0.06 为上涨6%)
        :param recent_avg_volume: 过去20期均量
        :param current_breakout_volume: 当期突破成交量
        :param bid_volume_top3: 买一至买三挂单总量
        :param ask_volume_top3: 卖一至卖三挂单总量
        :param real_executed_sell_volume: 实际主动主动抛盘成交量 (主卖)
        :param real_executed_buy_volume: 实际主动买盘成交量 (主买)
        """
        sym = symbol.upper()

        # 1. 诱多出货 (Pump & Dump): 价格冲高但量能严重萎缩 (无量假突破诱多)
        if price_change_pct > 0.04:
            if current_breakout_volume < recent_avg_volume * self._vol_div_thresh:
                return TrapAuditReport(
                    symbol=sym,
                    trap_detected=TrapType.PUMP_AND_DUMP_BULL_TRAP,
                    is_safe_to_enter=False,
                    confidence_score=0.90,
                    evidence_details="价格异常冲高但成交量急剧萎缩50%以上，呈现典型无量诱多拉高出货特征"
                )

        # 2. 假大单托盘 (Spoofing): 买盘挂单堆积如山，但实际成交全是主动砸盘
        if ask_volume_top3 > 0:
            bid_ask_ratio = bid_volume_top3 / ask_volume_top3
            if bid_ask_ratio >= self._spoof_thresh:
                # 若主动卖盘明显大于主动买盘
                if real_executed_sell_volume > real_executed_buy_volume * 1.5:
                    return TrapAuditReport(
                        symbol=sym,
                        trap_detected=TrapType.SPOOFING_PHANTOM_BID,
                        is_safe_to_enter=False,
                        confidence_score=0.85,
                        evidence_details=f"买盘挂单高达卖盘 {bid_ask_ratio:.1f} 倍，但内盘主动砸盘成交异常活跃，判定为虚假大单托盘出货"
                    )

        return TrapAuditReport(
            symbol=sym,
            trap_detected=TrapType.NONE,
            is_safe_to_enter=True,
            confidence_score=0.10,
            evidence_details="未检测到异常庄家操盘与量价诱多迹象"
        )

    def audit_value_trap(
        self,
        symbol: str,
        pe_ratio: float,
        pb_ratio: float,
        ocf_to_net_profit_ratio: float,
        revenue_3y_cagr: float
    ) -> TrapAuditReport:
        """
        审计低估值伪便宜价值陷阱 (Value Trap)
        """
        sym = symbol.upper()

        # 表面 PE/PB 极低，但现金流严重背离且主业持续萎缩
        if (0 < pe_ratio < 8.0) and (pb_ratio < 1.0):
            if ocf_to_net_profit_ratio < 0.30 or revenue_3y_cagr < -0.10:
                return TrapAuditReport(
                    symbol=sym,
                    trap_detected=TrapType.VALUE_TRAP,
                    is_safe_to_enter=False,
                    confidence_score=0.92,
                    evidence_details="低市盈率与破净假象：经营现金流枯竭且主业持续负增长，属于典型价值毁灭型陷阱"
                )

        return TrapAuditReport(
            symbol=sym,
            trap_detected=TrapType.NONE,
            is_safe_to_enter=True,
            confidence_score=0.10,
            evidence_details="基本面造血与估值匹配正常"
        )
