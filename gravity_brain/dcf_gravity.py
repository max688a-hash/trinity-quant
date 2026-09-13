"""
gravity_brain.dcf_gravity
~~~~~~~~~~~~~~~~~~~~~~~~~
实现真值引力估值模型 V_G (Gravity Valuation Model)。
数学公式：
V_G = ∑ [FCFE_t * min(1.0, Φ_CP) / (1 + r_e)^t] + [NAV_tangible * (1 - δ_impair) / (1 + r_e)^N]
结合造血纯度加权的现金流折现（DCF）与有形净资产清算价值，
构成股票价格围绕摆动的“真值质量中心”。
"""

from dataclasses import dataclass
from typing import Optional
from truth_kernel.models import CompanyFinancialRecord
from immune_system.cash_purity import CashPurityEngine


@dataclass(frozen=True)
class GravityValuationResult:
    """真值引力估值审计结果"""
    symbol: str
    period_end_date: str
    gravity_value: float              # 内在真值引力总量 V_G (元)
    discounted_fcf_sum: float         # 纯造血现金流折现贡献额 (元)
    tangible_nav_floor: float         # 有形净资产清算底座 (元)
    purity_penalty_factor: float      # 造血纯度折价因子 min(1.0, max(0.0, Φ_CP))
    cost_of_equity: float             # 股权资本折现率 r_e
    gravity_potential: Optional[float]# 引力势能比率 (V_G - MarketCap) / MarketCap
    margin_of_safety: float           # 安全边际百分比 (V_G - MarketCap) / V_G
    is_undervalued: bool              # 是否处于真值引力洼地 (具备非对称上行收益)


class GravityValuationEngine:
    """
    真值引力定价核心引擎
    """

    def __init__(
        self,
        risk_free_rate: float = 0.025,   # 无风险基准利率 (如 10 年期国债 2.5%)
        equity_risk_premium: float = 0.05,# 股权风险溢价 ERP 5.0%
        terminal_growth_rate: float = 0.02,# 永续保守增长率 2.0%
        projection_years: int = 5,       # 明确预测期 N=5 年
        impairment_discount: float = 0.15,# 有形资产减值安全缓冲折价 15%
        purity_engine: Optional[CashPurityEngine] = None
    ) -> None:
        self.r_f = risk_free_rate
        self.erp = equity_risk_premium
        self.g_term = terminal_growth_rate
        self.n_years = projection_years
        self.delta_impair = impairment_discount
        self.purity_engine = purity_engine or CashPurityEngine()

    def compute_intrinsic_value(
        self,
        record: CompanyFinancialRecord,
        market_cap: Optional[float] = None,
        conservative_fcf: Optional[float] = None
    ) -> GravityValuationResult:
        """
        计算单只标的的真值引力定价
        :param record: 最新可见财务记录
        :param market_cap: 当前总市值 (元)，若提供则计算引力势能与安全边际
        :param conservative_fcf: 可选外部平滑后的 TTM FCF，未提供则使用单期 FCF 年化
        """
        bs = record.balance_sheet
        cf = record.cash_flow_statement

        # 1. 资本成本 r_e
        r_e = self.r_f + self.erp  # 基准 7.5%

        # 2. 获取基准自由现金流 FCF
        base_fcf = conservative_fcf if conservative_fcf is not None else cf.free_cash_flow

        # 3. 评估造血纯度 Φ_CP
        purity_res = self.purity_engine.evaluate(record)
        phi_cp = purity_res.phi_cp
        purity_factor = max(0.0, min(1.0, phi_cp))

        # 4. 预测期折现现金流
        discounted_fcf_sum = 0.0
        # 稳健成长假设：若 FCF 为负，则预测现金流折现为 0 (完全依赖净资产清算底座)
        if base_fcf > 0 and purity_factor > 0:
            effective_fcf = base_fcf * purity_factor
            for t in range(1, self.n_years + 1):
                # 保守假定现金流按 3% 缓慢内生扩张
                fcf_t = effective_fcf * ((1.0 + self.g_term) ** (t - 1))
                df = (1.0 + r_e) ** t
                discounted_fcf_sum += (fcf_t / df)
            
            # 永续终值折现 (Gordon Growth Model)
            terminal_fcf = effective_fcf * ((1.0 + self.g_term) ** self.n_years)
            terminal_value = terminal_fcf / max(0.01, r_e - self.g_term)
            discounted_terminal = terminal_value / ((1.0 + r_e) ** self.n_years)
            discounted_fcf_sum += discounted_terminal

        # 5. 有形净资产清算价值 NAV_tangible (总资产 - 负债 - 商誉)
        tangible_equity = max(0.0, bs.total_equity - bs.goodwill)
        # 扣除安全减值缓冲
        tangible_nav_floor = tangible_equity * (1.0 - self.delta_impair)

        # 6. 综合真值引力 V_G = 现金流价值 + 资产安全底座的折现折旧保护
        # 为防止双重计算，当存在强现金流折现时，资产底座作为安全边际下限支撑
        gravity_value = max(tangible_nav_floor, discounted_fcf_sum + (tangible_nav_floor * 0.3))

        # 7. 测算引力势能与安全边际
        gravity_potential = None
        margin_of_safety = 0.0
        is_undervalued = False

        if market_cap is not None and market_cap > 0:
            gravity_potential = (gravity_value - market_cap) / market_cap
            margin_of_safety = (gravity_value - market_cap) / max(1.0, gravity_value)
            # 安全边际 > 25% 判定为引力洼地
            is_undervalued = (gravity_potential > 0.25)

        return GravityValuationResult(
            symbol=record.symbol,
            period_end_date=record.period_end_date,
            gravity_value=round(gravity_value, 2),
            discounted_fcf_sum=round(discounted_fcf_sum, 2),
            tangible_nav_floor=round(tangible_nav_floor, 2),
            purity_penalty_factor=round(purity_factor, 4),
            cost_of_equity=round(r_e, 4),
            gravity_potential=round(gravity_potential, 4) if gravity_potential is not None else None,
            margin_of_safety=round(margin_of_safety, 4),
            is_undervalued=is_undervalued
        )
