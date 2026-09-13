"""
gravity_brain/regime_multi_strategy_engine.py
=============================================
市场状态自适应多策略协同矩阵 (Regime-Switching Multi-Strategy Matrix)。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 严禁单一策略打天下导致震荡市反复抽耳光，基于市场物理状态动态切换;
2. 趋势突破 (Trend) + 均值回归 (Mean-Reversion) + 尾部对冲 (Tail-Risk) 互补协同;
3. 严格单文件不超过 300 行，强类型标注，零盲吞异常。
"""

from dataclasses import dataclass
from enum import Enum
import math
from typing import Dict, List, Optional

from gravity_brain.market_regime_classifier import MarketRegime, MarketRegimeClassifier


class StrategySignalAction(str, Enum):
    """策略决策动作"""
    BUY_LONG = "BUY_LONG"
    SELL_SHORT = "SELL_SHORT"
    CLOSE_POSITION = "CLOSE_POSITION"
    STAND_ASIDE = "STAND_ASIDE"


@dataclass(frozen=True)
class MultiStrategySignal:
    """多策略自适应决策信号"""
    symbol: str
    action: StrategySignalAction
    active_strategy: str
    market_regime: MarketRegime
    confidence_pct: float
    rationale: str
    target_price: float
    stop_loss_price: float


class RegimeMultiStrategyEngine:
    """市场状态自适应多策略协同矩阵调度器"""

    @classmethod
    def evaluate_symbol(
        cls,
        symbol: str,
        prices: List[float],
        current_price: float
    ) -> MultiStrategySignal:
        """根据当前价格序列计算状态并由对应策略产出决策"""
        if len(prices) < 20 or current_price <= 0:
            return MultiStrategySignal(
                symbol=symbol,
                action=StrategySignalAction.STAND_ASIDE,
                active_strategy="INSUFFICIENT_DATA",
                market_regime=MarketRegime.CHOPPY_OSCILLATING,
                confidence_pct=0.0,
                rationale="时序样本不足或价格异常，保持观望",
                target_price=current_price,
                stop_loss_price=current_price * 0.95
            )

        # 1. 判定当前市场状态
        regime_rep = MarketRegimeClassifier.classify_regime(prices)
        regime = regime_rep.regime

        # 2. 状态分发给对应策略
        if regime == MarketRegime.EXTREME_VOLATILE_CRISIS:
            # 激活尾部对冲与减仓策略
            return MultiStrategySignal(
                symbol=symbol,
                action=StrategySignalAction.CLOSE_POSITION,
                active_strategy="TailRiskHedgingStrategy",
                market_regime=regime,
                confidence_pct=95.0,
                rationale="触发 2008/2020 级极端黑天鹅波动防御：强制平仓锁定浮动亏损！",
                target_price=current_price,
                stop_loss_price=current_price * 0.98
            )

        elif regime == MarketRegime.BULL_TREND:
            # 激活单边趋势突破追踪策略 (唐奇安最高价突破)
            recent_high = max(prices[-20:])
            if current_price >= recent_high * 0.995:
                return MultiStrategySignal(
                    symbol=symbol,
                    action=StrategySignalAction.BUY_LONG,
                    active_strategy="TrendBreakoutStrategy",
                    market_regime=regime,
                    confidence_pct=85.0,
                    rationale=f"Hurst={regime_rep.hurst_exponent:.2f} 长记忆多头：突破20日新高 ¥{recent_high:.2f} 顺势追击！",
                    target_price=round(current_price * 1.15, 2),
                    stop_loss_price=round(current_price * 0.95, 2)
                )
            return MultiStrategySignal(
                symbol=symbol,
                action=StrategySignalAction.STAND_ASIDE,
                active_strategy="TrendBreakoutStrategy",
                market_regime=regime,
                confidence_pct=60.0,
                rationale="处于上升通道但未达到最高价突破阈值，持仓等待",
                target_price=current_price,
                stop_loss_price=round(current_price * 0.95, 2)
            )

        elif regime == MarketRegime.BEAR_TREND:
            # 激活单边空头保护
            return MultiStrategySignal(
                symbol=symbol,
                action=StrategySignalAction.SELL_SHORT,
                active_strategy="BearDefenseStrategy",
                market_regime=regime,
                confidence_pct=80.0,
                rationale=f"Hurst={regime_rep.hurst_exponent:.2f} 单边下行：执行顺势做空或防守出清",
                target_price=round(current_price * 0.88, 2),
                stop_loss_price=round(current_price * 1.05, 2)
            )

        else:
            # 激活统计套利与均值回归策略 (Bollinger Bands Z-Score)
            mean_p = sum(prices[-20:]) / 20.0
            variance = sum((p - mean_p) ** 2 for p in prices[-20:]) / 20.0
            std_p = math.sqrt(max(variance, 1e-9))
            z_score = (current_price - mean_p) / std_p

            if z_score < -1.8:
                # 触及下轨超卖，反弹低吸
                return MultiStrategySignal(
                    symbol=symbol,
                    action=StrategySignalAction.BUY_LONG,
                    active_strategy="MeanReversionPairsStrategy",
                    market_regime=regime,
                    confidence_pct=78.0,
                    rationale=f"震荡市 Z-Score={z_score:.2f} 跌破布林下轨：严重超卖，博弈物理均值回归！",
                    target_price=round(mean_p, 2),
                    stop_loss_price=round(current_price * 0.96, 2)
                )
            elif z_score > 1.8:
                # 触及上轨超买，逢高止盈
                return MultiStrategySignal(
                    symbol=symbol,
                    action=StrategySignalAction.SELL_SHORT,
                    active_strategy="MeanReversionPairsStrategy",
                    market_regime=regime,
                    confidence_pct=75.0,
                    rationale=f"震荡市 Z-Score={z_score:.2f} 突破布林上轨：严重超买，锁定波段利润！",
                    target_price=round(mean_p, 2),
                    stop_loss_price=round(current_price * 1.04, 2)
                )

            return MultiStrategySignal(
                symbol=symbol,
                action=StrategySignalAction.STAND_ASIDE,
                active_strategy="MeanReversionPairsStrategy",
                market_regime=regime,
                confidence_pct=50.0,
                rationale=f"震荡中轨 (Z={z_score:.2f})，未达均值回归边界，保持静默",
                target_price=round(mean_p, 2),
                stop_loss_price=round(current_price * 0.95, 2)
            )
