"""
entropy_execution/dynamic_trailing_stop.py
==========================================
TRINITY QUANT 动态自适应跟踪止盈止损与高危仓位平仓引擎。

彻底摒弃“死固定点数止损”的业余做法：
1. 基于 ATR 动态波幅的吊灯追踪止损 (Chandelier Trailing Stop);
2. 单向向上锁利棘轮机制 (Ratchet: 止损线只升不降，锁定浮盈);
3. 浮盈阶梯动态收紧 (防利润大幅回撤);
4. 突发黑天鹅/高危毒性/庄家诱多一票即刻市价清仓 (Emergency Exit)。
"""

from dataclasses import dataclass
from enum import Enum
import math
from typing import Optional


class ExitTriggerType(str, Enum):
    """平仓触发原因"""
    NONE = "NONE"                                    # 正常持仓未触发出场
    DYNAMIC_TRAILING_STOP = "DYNAMIC_TRAILING_STOP"  # 触及动态跟踪止损线
    PROFIT_PROTECTION_TAKE = "PROFIT_PROTECTION"     # 锁利保护止盈出场
    EMERGENCY_TOXIC_EXIT = "EMERGENCY_TOXIC_EXIT"    # 突发基本面高危或庄家陷阱即刻平仓


@dataclass(frozen=True)
class TrailingStopVerdict:
    """动态跟踪出场决策"""
    symbol: str
    current_price: float
    entry_price: float
    highest_price: float
    current_stop_price: float
    floating_pnl_pct: float
    peak_pnl_pct: float
    should_close: bool
    trigger_type: ExitTriggerType
    explanation: str


class DynamicTrailingStopEngine:
    """动态自适应跟踪止盈止损器"""

    def __init__(
        self,
        base_atr_multiplier: float = 2.5,
        profit_lock_threshold_pct: float = 0.15,
        tightened_atr_multiplier: float = 1.5
    ) -> None:
        if base_atr_multiplier <= 0:
            raise ValueError("基础ATR倍数必须大于0")
        if tightened_atr_multiplier >= base_atr_multiplier:
            raise ValueError("收紧倍数必须小于基础倍数")
        self._base_mult = base_atr_multiplier
        self._tight_mult = tightened_atr_multiplier
        self._profit_lock_thresh = profit_lock_threshold_pct

    def evaluate_position(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        highest_price_since_entry: float,
        previous_stop_price: float,
        current_atr: float,
        is_emergency_toxic_flag: bool = False
    ) -> TrailingStopVerdict:
        """
        评估持仓风险与动态止损线计算
        
        :param symbol: 标的代码
        :param entry_price: 开仓建仓均价
        :param current_price: 当前最新市价
        :param highest_price_since_entry: 持仓期间达到的最高价
        :param previous_stop_price: 上一期已生效的动态止损价
        :param current_atr: 当前品种动态真实波幅 ATR
        :param is_emergency_toxic_flag: 是否检测到突发庄家陷阱或基本面债务暴雷
        """
        sym = symbol.upper()
        if (
            math.isnan(entry_price) or math.isnan(current_price) or math.isnan(current_atr) or
            math.isnan(highest_price_since_entry) or math.isnan(previous_stop_price) or
            math.isinf(entry_price) or math.isinf(current_price) or math.isinf(current_atr) or
            entry_price <= 0 or current_price <= 0 or current_atr <= 0
        ):
            raise ValueError("价格与ATR必须为大于0的有效实数")

        # 1. 突发高危紧急清仓 (Emergency Exit)
        if is_emergency_toxic_flag:
            return TrailingStopVerdict(
                symbol=sym,
                current_price=current_price,
                entry_price=entry_price,
                highest_price=highest_price_since_entry,
                current_stop_price=current_price,
                floating_pnl_pct=(current_price - entry_price) / entry_price,
                peak_pnl_pct=(highest_price_since_entry - entry_price) / entry_price,
                should_close=True,
                trigger_type=ExitTriggerType.EMERGENCY_TOXIC_EXIT,
                explanation="检测到突发庄家出货陷阱或基本面债务毒性爆雷，一票强制即刻平仓避险！"
            )

        # 2. 动态修正历史峰值与浮动盈亏
        effective_highest = max(highest_price_since_entry, current_price)
        floating_pnl = (current_price - entry_price) / entry_price
        peak_pnl = (effective_highest - entry_price) / entry_price

        # 3. 动态确定当前 ATR 缓冲带宽 (随着利润扩大动态收紧，锁定收益)
        if peak_pnl >= self._profit_lock_thresh:
            atr_mult = self._tight_mult
        else:
            atr_mult = self._base_mult

        # 4. 计算当前候选止损线 (吊灯出场价 = 峰值最高价 - k * ATR)
        candidate_stop = effective_highest - (atr_mult * current_atr)

        # 5. 单向向上锁利棘轮机制 (Ratchet: 绝不允许向下松动调低止损线)
        new_stop = max(previous_stop_price, candidate_stop)

        # 6. 检查市价是否击穿动态止损线
        if current_price <= new_stop:
            trigger = ExitTriggerType.PROFIT_PROTECTION_TAKE if floating_pnl > 0 else ExitTriggerType.DYNAMIC_TRAILING_STOP
            return TrailingStopVerdict(
                symbol=sym,
                current_price=current_price,
                entry_price=entry_price,
                highest_price=highest_price_since_entry,
                current_stop_price=new_stop,
                floating_pnl_pct=floating_pnl,
                peak_pnl_pct=peak_pnl,
                should_close=True,
                trigger_type=trigger,
                explanation=f"市价 ({current_price:.2f}) 击穿动态跟踪止损线 ({new_stop:.2f})，触发保护性平仓离场"
            )

        return TrailingStopVerdict(
            symbol=sym,
            current_price=current_price,
            entry_price=entry_price,
            highest_price=highest_price_since_entry,
            current_stop_price=new_stop,
            floating_pnl_pct=floating_pnl,
            peak_pnl_pct=peak_pnl,
            should_close=False,
            trigger_type=ExitTriggerType.NONE,
            explanation=f"持仓健康运行中，当前动态保护线下沿抬升至 {new_stop:.2f}"
        )
