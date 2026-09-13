"""
immune_system.debt_wall
~~~~~~~~~~~~~~~~~~~~~~~
实现债务毒性与到期墙 (Debt Toxicity & Maturity Wall) 计算引擎。
度量未来 12 个月内刚性债务对企业自由流动资金的挤兑猝死风险。
"""

from dataclasses import dataclass
from truth_kernel.models import CompanyFinancialRecord


@dataclass(frozen=True)
class DebtWallAssessment:
    """债务毒性与到期墙评估审计结果"""
    symbol: str
    period_end_date: str
    omega_debt: float                 # 债务毒性综合指数 Ω_Debt
    total_due_1y: float               # 1年内到期刚性有息债务总额（元）
    liquid_coverage: float            # 真实流动储备 (真实货币资金 + max(0, FCF))
    interest_burden_factor: float     # 利息财务费用侵蚀放大倍数
    is_veto: bool                     # 是否触发一票否决
    is_warning: bool                  # 是否触发流动性预警
    diagnosis: str                    # 审计诊断报告


class DebtWallEngine:
    """
    债务到期墙与流动性猝死监控引擎
    数学公式：
    Ω_Debt = [Total_Due_1y / (Real_Liquid_Cash + max(0, FCF))] * [1 + Fin_Expense / max(1, EBITDA)]
    """

    def __init__(
        self,
        veto_threshold: float = 1.20,
        warning_threshold: float = 0.80,
        max_interest_to_ebitda: float = 0.40
    ) -> None:
        self.veto_threshold = veto_threshold
        self.warning_threshold = warning_threshold
        self.max_interest_to_ebitda = max_interest_to_ebitda

    def evaluate(self, record: CompanyFinancialRecord) -> DebtWallAssessment:
        """对单期财务记录执行债务到期墙压力测试"""
        bs = record.balance_sheet
        inc = record.income_statement
        cf = record.cash_flow_statement

        # 1. 计算 1 年内刚性有息负债总额
        total_due_1y = bs.total_due_1y

        # 2. 计算真实可用流动性兜底资金（真实未受限现金 + 自由现金流）
        fcf = cf.free_cash_flow
        positive_fcf = max(0.0, fcf)
        liquid_coverage = bs.real_liquid_cash + positive_fcf

        # 3. 计算基础债务覆盖倍数
        if total_due_1y <= 0:
            base_coverage_ratio = 0.0
        elif liquid_coverage > 0:
            base_coverage_ratio = total_due_1y / liquid_coverage
        else:
            # 真实流动资金枯竭且有到期硬负债：极度危险，直接封顶超标
            base_coverage_ratio = 50.0

        # 4. 计算利息费用吞噬放大倍数
        ebitda = inc.computed_ebitda
        fin_expense = max(0.0, inc.financial_expenses)
        interest_ratio = fin_expense / max(1.0, ebitda)
        interest_burden_factor = 1.0 + interest_ratio

        # 5. 计算综合债务毒性指数 Ω_Debt
        omega_debt = base_coverage_ratio * interest_burden_factor

        # 6. 判定否决与预警条件
        is_veto = False
        is_warning = False
        reasons = []

        if omega_debt > self.veto_threshold:
            is_veto = True
            reasons.append(
                f"债务毒性 Ω_Debt={omega_debt:.2f} 突破极限红线 {self.veto_threshold:.2f} "
                f"(1年内到期债务 {total_due_1y/1e8:.2f}亿 严重压垮流动性储备 {liquid_coverage/1e8:.2f}亿)"
            )

        if interest_ratio > self.max_interest_to_ebitda:
            # 财务费用吞噬 EBITDA 超过阈值
            reasons.append(
                f"财务利息侵蚀比例={interest_ratio*100:.1f}% 超过警戒 {self.max_interest_to_ebitda*100:.1f}%"
            )
            if interest_ratio >= 1.0:
                is_veto = True  # EBITDA 不足以支付利息，必然违约

        if not is_veto and omega_debt > self.warning_threshold:
            is_warning = True
            reasons.append(f"债务毒性 Ω_Debt={omega_debt:.2f} 处于预警关注区间 [{self.warning_threshold:.2f}, {self.veto_threshold:.2f}]")

        diagnosis = " | ".join(reasons) if reasons else "负债期限结构安全，现金流充足覆盖到期债务。"

        return DebtWallAssessment(
            symbol=record.symbol,
            period_end_date=record.period_end_date,
            omega_debt=round(omega_debt, 4),
            total_due_1y=round(total_due_1y, 2),
            liquid_coverage=round(liquid_coverage, 2),
            interest_burden_factor=round(interest_burden_factor, 4),
            is_veto=is_veto,
            is_warning=is_warning,
            diagnosis=diagnosis
        )
