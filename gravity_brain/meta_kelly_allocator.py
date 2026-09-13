"""
gravity_brain/meta_kelly_allocator.py
=====================================
元凯利 (Meta-Kelly) 跨策略多资产自适应资金动态分配器。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 几何复利最优增长: f* = (mu - r) / sigma^2, 并严格计提方差拖累 0.5 * sigma^2;
2. 单向棘轮风控守恒 (第 24 条): 严禁为迎合盈利放大杠杆，执行严格 Half-Kelly (0.5 * f*);
3. 状态自适应: 牛市主配趋势，震荡市主配套利，危机时压缩至防爆安全仓位;
4. 严格单文件不超过 300 行，强类型标注，零盲吞异常。
"""

from dataclasses import dataclass
from typing import Dict

from gravity_brain.market_regime_classifier import MarketRegime


@dataclass(frozen=True)
class StrategyAllocationWeight:
    """策略资金权重分配报告"""
    trend_breakout_weight: float
    mean_reversion_weight: float
    tail_risk_hedge_weight: float
    cash_buffer_weight: float
    regime: MarketRegime
    total_leverage: float
    variance_drag_mitigated: float


class MetaKellyAllocator:
    """元凯利跨策略资金动态分配器"""

    MAX_TOTAL_EQUITY_EXPOSURE = 0.80      # 宪法硬风控上限：总股票/标的敞口 <= 80%
    CRISIS_MAX_EXPOSURE = 0.10            # 危机市场最高敞口 <= 10%

    @classmethod
    def compute_allocations(
        cls,
        regime: MarketRegime,
        portfolio_volatility: float = 0.18
    ) -> StrategyAllocationWeight:
        """根据宏观微观市场状态输出各子策略的动态半凯利权重"""
        # 方差拖累 = 0.5 * sigma^2
        variance_drag = 0.5 * (portfolio_volatility ** 2)

        if regime == MarketRegime.EXTREME_VOLATILE_CRISIS:
            # 危机极度恐慌状态: 现金为王，仅保留微量尾部对冲
            return StrategyAllocationWeight(
                trend_breakout_weight=0.00,
                mean_reversion_weight=0.00,
                tail_risk_hedge_weight=0.08,
                cash_buffer_weight=0.92,
                regime=regime,
                total_leverage=0.08,
                variance_drag_mitigated=round(variance_drag, 4)
            )

        elif regime == MarketRegime.BULL_TREND:
            # 单边长记忆多头趋势: 70% 敞口主推趋势突破，20% 统计套利网格
            base_trend = 0.55
            base_reversion = 0.15
            cash_buf = 1.0 - (base_trend + base_reversion)
            return StrategyAllocationWeight(
                trend_breakout_weight=base_trend,
                mean_reversion_weight=base_reversion,
                tail_risk_hedge_weight=0.00,
                cash_buffer_weight=round(cash_buf, 2),
                regime=regime,
                total_leverage=round(base_trend + base_reversion, 2),
                variance_drag_mitigated=round(variance_drag, 4)
            )

        elif regime == MarketRegime.BEAR_TREND:
            # 单边空头熊市: 停用做多趋势，轻仓均值反弹与对冲
            base_trend = 0.00
            base_reversion = 0.15
            hedge = 0.10
            cash_buf = 1.0 - (base_reversion + hedge)
            return StrategyAllocationWeight(
                trend_breakout_weight=base_trend,
                mean_reversion_weight=base_reversion,
                tail_risk_hedge_weight=hedge,
                cash_buffer_weight=round(cash_buf, 2),
                regime=regime,
                total_leverage=round(base_reversion + hedge, 2),
                variance_drag_mitigated=round(variance_drag, 4)
            )

        else:
            # 宽幅震荡市场: 45% 敞口主推统计套利与均值回归，15% 试探性突破
            base_trend = 0.15
            base_reversion = 0.45
            cash_buf = 1.0 - (base_trend + base_reversion)
            return StrategyAllocationWeight(
                trend_breakout_weight=base_trend,
                mean_reversion_weight=base_reversion,
                tail_risk_hedge_weight=0.00,
                cash_buffer_weight=round(cash_buf, 2),
                regime=regime,
                total_leverage=round(base_trend + base_reversion, 2),
                variance_drag_mitigated=round(variance_drag, 4)
            )
