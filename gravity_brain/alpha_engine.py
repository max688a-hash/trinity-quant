"""
gravity_brain.alpha_engine
~~~~~~~~~~~~~~~~~~~~~~~~~~
引力真值复合 Alpha 引擎。
将造血纯度 Φ_CP、债务毒性 Ω_Debt、引力势能 G_potential 与非对称凸性得分
融合成兼顾确定性与安全边际的【真值引力 Alpha 矩阵】。
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from truth_kernel.models import CompanyFinancialRecord
from immune_system.poison_firewall import PoisonFirewall
from gravity_brain.dcf_gravity import GravityValuationEngine, GravityValuationResult
from gravity_brain.asymmetric_pricing import AsymmetricPricingEngine, ConvexityProfile


@dataclass(frozen=True)
class AlphaCandidate:
    """复合 Alpha 标的评估体征"""
    symbol: str
    period_end_date: str
    alpha_score: float                # 综合真值引力 Alpha 得分
    gravity_value: float              # 内在真值总量 (元)
    phi_cp: float                     # 造血纯度
    omega_debt: float                 # 债务毒性
    convexity_score: float            # 凸性得分
    is_firewall_admitted: bool        # 排毒准入标识
    signal: str                       # 投资决策信号: STRONG_BUY / BUY / NEUTRAL / VETO


class GravityAlphaEngine:
    """
    真值引力 Alpha 生成核心
    Alpha = max(0, G_potential) * Φ_CP * (Convexity / 10) * [1 / (1 + Ω_Debt)]
    """

    def __init__(
        self,
        firewall: Optional[PoisonFirewall] = None,
        val_engine: Optional[GravityValuationEngine] = None,
        pricing_engine: Optional[AsymmetricPricingEngine] = None
    ) -> None:
        self.firewall = firewall or PoisonFirewall()
        self.val_engine = val_engine or GravityValuationEngine()
        self.pricing_engine = pricing_engine or AsymmetricPricingEngine()

    def evaluate_candidate(
        self,
        record: CompanyFinancialRecord,
        market_cap: Optional[float] = None
    ) -> AlphaCandidate:
        """评估单只标的的 Alpha 得分与决策信号"""
        # 1. 免疫系统体检
        audit = self.firewall.audit(record)

        # 2. 真值引力定价
        val = self.val_engine.compute_intrinsic_value(record, market_cap=market_cap)

        # 3. 非对称凸性分析
        convexity = self.pricing_engine.evaluate_convexity(val, audit.debt_wall)

        # 4. 若未通过排毒防火墙，Alpha 得分直接置 0，给出 VETO
        if not audit.is_admitted:
            return AlphaCandidate(
                symbol=record.symbol,
                period_end_date=record.period_end_date,
                alpha_score=0.0,
                gravity_value=val.gravity_value,
                phi_cp=audit.cash_purity.phi_cp,
                omega_debt=audit.debt_wall.omega_debt,
                convexity_score=convexity.convexity_score,
                is_firewall_admitted=False,
                signal="VETO"
            )

        # 5. 准入标的综合 Alpha 计算
        # 基础潜力因子
        potential = max(0.1, val.gravity_potential) if val.gravity_potential is not None else 1.0
        purity = max(0.1, audit.cash_purity.phi_cp)
        conv_multiplier = max(0.1, convexity.convexity_score / 10.0)
        debt_penalty = 1.0 / (1.0 + audit.debt_wall.omega_debt)

        alpha_score = potential * purity * conv_multiplier * debt_penalty * 100.0

        # 信号分类
        if alpha_score >= 80.0 and convexity.is_convex:
            signal = "STRONG_BUY"
        elif alpha_score >= 40.0:
            signal = "BUY"
        else:
            signal = "NEUTRAL"

        return AlphaCandidate(
            symbol=record.symbol,
            period_end_date=record.period_end_date,
            alpha_score=round(alpha_score, 2),
            gravity_value=val.gravity_value,
            phi_cp=audit.cash_purity.phi_cp,
            omega_debt=audit.debt_wall.omega_debt,
            convexity_score=convexity.convexity_score,
            is_firewall_admitted=True,
            signal=signal
        )

    def rank_universe(
        self,
        records: List[CompanyFinancialRecord],
        market_caps: Optional[Dict[str, float]] = None
    ) -> List[AlphaCandidate]:
        """对全市场标的进行 Alpha 排序"""
        caps = market_caps or {}
        candidates = []
        for r in records:
            cap = caps.get(r.symbol)
            candidate = self.evaluate_candidate(r, market_cap=cap)
            candidates.append(candidate)

        # 按 Alpha 得分降序排列
        candidates.sort(key=lambda c: c.alpha_score, reverse=True)
        return candidates
