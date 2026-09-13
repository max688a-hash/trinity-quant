"""
gravity_brain.asymmetric_pricing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
非对称凸性定价与反脆弱性 (Asymmetric Convexity & Antifragility) 测算引擎。
数学核心：
追求具有正向偏度 (Positive Skewness) 的收益分布：
下行风险被有形净资产底座与真实货币资金硬性封死（Downside Capped），
上行收益享有价值均值回归与现金流内生复利的开放式期权（Upside Uncapped）。
"""

from dataclasses import dataclass
from typing import Optional
from gravity_brain.dcf_gravity import GravityValuationResult
from immune_system.debt_wall import DebtWallAssessment


@dataclass(frozen=True)
class ConvexityProfile:
    """标的非对称凸性体征"""
    symbol: str
    period_end_date: str
    convexity_score: float            # 综合凸性得分 (0 ~ 10 分，越高越具备反脆弱性)
    downside_tail_risk: float         # 下行尾部风险代理指标 (0.0 极安全 ~ 1.0 极高危)
    upside_leverage: float            # 上行势能释放乘数
    payoff_asymmetry_ratio: float     # 期望盈亏非对称比 (Upside / max(0.01, Downside))
    is_convex: bool                   # 是否具备非对称凸性优势


class AsymmetricPricingEngine:
    """
    非对称凸性定价引擎
    结合引力定价与债务毒性，定量评估资产的反脆弱度。
    """

    def evaluate_convexity(
        self,
        valuation: GravityValuationResult,
        debt_wall: DebtWallAssessment
    ) -> ConvexityProfile:
        """评估资产的收益非对称性分布"""
        # 1. 测算下行尾部风险 Downside Risk
        # 债务毒性越高，资产流动性猝死概率越大，下行风险越高
        omega = debt_wall.omega_debt
        base_downside = min(1.0, max(0.05, omega * 0.4))
        # 若造血纯度过低，进一步放大下行预期损失
        purity_discount = 1.0 - valuation.purity_penalty_factor
        downside_tail = min(1.0, base_downside + (purity_discount * 0.3))

        # 2. 测算上行势能 Upside Potential
        # 基于引力势能比率 (若未输入市值，默认使用内在现金流折现与资产底座比例)
        if valuation.gravity_potential is not None:
            upside = max(0.0, valuation.gravity_potential)
        else:
            # 内在价值相对资产底座的倍数
            upside = max(0.0, (valuation.gravity_value - valuation.tangible_nav_floor) / max(1.0, valuation.tangible_nav_floor))

        # 3. 计算非对称赔率
        asymmetry_ratio = upside / max(0.05, downside_tail)

        # 4. 综合凸性得分 (0-10分)
        # 具备高安全边际且低债务毒性时，得分高
        raw_score = (asymmetry_ratio * 2.0) + (valuation.purity_penalty_factor * 3.0) - (omega * 2.5)
        convexity_score = max(0.0, min(10.0, raw_score))

        # 判定：得分 >= 6.0 且债务毒性处于安全区判定为具备非对称凸性
        is_convex = (convexity_score >= 6.0 and omega <= 0.80)

        return ConvexityProfile(
            symbol=valuation.symbol,
            period_end_date=valuation.period_end_date,
            convexity_score=round(convexity_score, 2),
            downside_tail_risk=round(downside_tail, 4),
            upside_leverage=round(upside, 4),
            payoff_asymmetry_ratio=round(asymmetry_ratio, 2),
            is_convex=is_convex
        )
