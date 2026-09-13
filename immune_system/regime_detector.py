"""
immune_system/regime_detector.py
================================
TRINITY QUANT 临界破位与状态机突变器。

针对金融物理状态跃迁：
在常态振荡空间内（如玉米~25点，|Z| <= 2.0），允许均值回归操作；
一旦突破临界边界，系统一票否决所有逆势摸顶抄底订单，防范逼仓与雪崩毁灭。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from gravity_brain.volatility_normalizer import VolatilityMetrics


class MarketRegime(str, Enum):
    """市场动力学状态分类"""
    MEAN_REVERTING = "MEAN_REVERTING"              # 常态阻尼振荡
    TREND_BREAKOUT_BULL = "TREND_BREAKOUT_BULL"    # 向上逃逸/多头逼空
    TREND_BREAKOUT_BEAR = "TREND_BREAKOUT_BEAR"    # 向下雪崩/破位暴跌
    LIQUIDITY_DISLOCATION = "LIQUIDITY_DISLOCATION"# 流动性断裂/跳空失衡


class ProposedAction(str, Enum):
    """拟执行交易动作"""
    BUY_DIP_MEAN_REVERT = "BUY_DIP_MEAN_REVERT"    # 逆势抄底 (在下跌时做多博反弹)
    SELL_RALLY_MEAN_REVERT = "SELL_RALLY_MEAN_REVERT"# 逆势摸顶 (在上涨时做空博回落)
    BUY_LONG_TREND = "BUY_LONG_TREND"              # 顺势做多 (跟随向上突破)
    SELL_SHORT_TREND = "SELL_SHORT_TREND"          # 顺势做空 (跟随向下破位)
    CLOSE_POSITION = "CLOSE_POSITION"              # 止损/止盈平仓
    HOLD = "HOLD"                                  # 观望持仓


@dataclass(frozen=True)
class RegimeAuditResult:
    """状态机审核决策"""
    symbol: str
    regime: MarketRegime
    action: ProposedAction
    is_permitted: bool
    veto_reason: Optional[str]
    allowed_position_cap: float


class RegimeBreakoutDetector:
    """临界破位与状态机突变探测器"""

    def __init__(
        self,
        breakout_z_threshold: float = 2.0,
        extreme_z_threshold: float = 3.0,
        max_gap_ratio: float = 0.05
    ) -> None:
        if breakout_z_threshold <= 0:
            raise ValueError("突破阈值必须大于0")
        if extreme_z_threshold <= breakout_z_threshold:
            raise ValueError("极端阈值必须大于突破阈值")
        if max_gap_ratio <= 0:
            raise ValueError("跳空阈值必须大于0")
        self._breakout_z = breakout_z_threshold
        self._extreme_z = extreme_z_threshold
        self._max_gap_ratio = max_gap_ratio

    def evaluate_regime(
        self,
        metrics: VolatilityMetrics,
        overnight_gap_ratio: float = 0.0
    ) -> MarketRegime:
        """
        评估标的当前所处的物理动力学状态
        
        :param metrics: 标的自适应波动指标
        :param overnight_gap_ratio: 隔夜或日内突发跳空幅度 abs(Open - PrevClose) / PrevClose
        :return: MarketRegime
        """
        if abs(overnight_gap_ratio) >= self._max_gap_ratio:
            return MarketRegime.LIQUIDITY_DISLOCATION

        if abs(metrics.z_score) > self._extreme_z:
            return MarketRegime.LIQUIDITY_DISLOCATION

        if metrics.z_score > self._breakout_z:
            return MarketRegime.TREND_BREAKOUT_BULL

        if metrics.z_score < -self._breakout_z:
            return MarketRegime.TREND_BREAKOUT_BEAR

        return MarketRegime.MEAN_REVERTING

    def audit_order(
        self,
        metrics: VolatilityMetrics,
        action: ProposedAction,
        overnight_gap_ratio: float = 0.0
    ) -> RegimeAuditResult:
        """
        排毒防火墙核验：严禁在突破逃逸态下进行逆势操作
        
        :param metrics: 标的自适应波动指标
        :param action: 策略计划执行的动作
        :param overnight_gap_ratio: 跳空比例
        :return: RegimeAuditResult
        """
        regime = self.evaluate_regime(metrics, overnight_gap_ratio)
        sym = metrics.symbol

        # 平仓与观望始终被允许
        if action in (ProposedAction.CLOSE_POSITION, ProposedAction.HOLD):
            return RegimeAuditResult(
                symbol=sym,
                regime=regime,
                action=action,
                is_permitted=True,
                veto_reason=None,
                allowed_position_cap=1.0
            )

        # 极端流动性断裂状态下，禁止任何新开仓，仅允许避险平仓
        if regime == MarketRegime.LIQUIDITY_DISLOCATION:
            return RegimeAuditResult(
                symbol=sym,
                regime=regime,
                action=action,
                is_permitted=False,
                veto_reason=f"标的处于流动性断裂/极值冲击态(|Z|={metrics.z_score:.2f})，触发全面熔断",
                allowed_position_cap=0.0
            )

        # 向上突破/逼空态：严禁摸顶做空
        if regime == MarketRegime.TREND_BREAKOUT_BULL:
            if action == ProposedAction.SELL_RALLY_MEAN_REVERT:
                return RegimeAuditResult(
                    symbol=sym,
                    regime=regime,
                    action=action,
                    is_permitted=False,
                    veto_reason=f"标的向上突破临界波动空间(Z={metrics.z_score:.2f}>{self._breakout_z})，一票否决逆势摸顶做空",
                    allowed_position_cap=0.0
                )
            # 顺势做多允许，但仓位受限防高位假突破
            return RegimeAuditResult(
                symbol=sym,
                regime=regime,
                action=action,
                is_permitted=True,
                veto_reason=None,
                allowed_position_cap=0.60
            )

        # 向下雪崩/破位态：严禁抄底做多
        if regime == MarketRegime.TREND_BREAKOUT_BEAR:
            if action == ProposedAction.BUY_DIP_MEAN_REVERT:
                return RegimeAuditResult(
                    symbol=sym,
                    regime=regime,
                    action=action,
                    is_permitted=False,
                    veto_reason=f"标的向下击穿临界波动空间(Z={metrics.z_score:.2f}<-{self._breakout_z})，一票否决逆势抄底做多",
                    allowed_position_cap=0.0
                )
            # 顺势做空允许
            return RegimeAuditResult(
                symbol=sym,
                regime=regime,
                action=action,
                is_permitted=True,
                veto_reason=None,
                allowed_position_cap=0.60
            )

        # 常态阻尼振荡态：均值回归与顺势均允许，全额可用
        return RegimeAuditResult(
            symbol=sym,
            regime=regime,
            action=action,
            is_permitted=True,
            veto_reason=None,
            allowed_position_cap=1.0
        )
