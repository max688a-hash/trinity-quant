"""
tests.test_immune_edge_cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
对免疫排毒系统的边界数值、预警黄线与异常防线进行精细化覆盖测试。
包含零营收、零流动性现金、资不抵债、利息负担过高与预警状态转化。
"""

import unittest
from truth_kernel.models import (
    BalanceSheet,
    IncomeStatement,
    CashFlowStatement,
    CompanyFinancialRecord
)
from immune_system.cash_purity import CashPurityEngine
from immune_system.debt_wall import DebtWallEngine
from immune_system.poison_firewall import PoisonFirewall


class TestImmuneEdgeCases(unittest.TestCase):
    """免疫系统边缘边界与预警测试套件"""

    def setUp(self) -> None:
        self.purity_engine = CashPurityEngine()
        self.debt_engine = DebtWallEngine()
        self.firewall = PoisonFirewall(
            cash_purity_engine=self.purity_engine,
            debt_wall_engine=self.debt_engine
        )

    def test_warning_zones_purity_and_debt(self) -> None:
        """测试：标的落入预警黄线区间 (0.30 <= Φ_CP < 0.60, 0.80 < Ω_Debt <= 1.20)"""
        # 设计一个刚好在黄线范围的公司
        bs = BalanceSheet(
            total_assets=1e9,
            total_liabilities=5e8,
            total_equity=5e8,
            cash_and_equivalents=1e8,
            receivables=1e8,  # 占营收 20%
            short_term_debt=8.5e7  # 8500万债务，流动性1亿，base=0.85
        )
        inc = IncomeStatement(
            revenue=5e8,
            operating_profit=5e7,
            net_profit=4e7,
            financial_expenses=5e6, # 500万，ebitda 5500万，利息比 < 10%
            ebitda=5.5e7
        )
        # OCF 2500万，净利润 4000万，Φ_CP 约在 0.40 ~ 0.50 之间
        cf = CashFlowStatement(operating_cash_flow=2.5e7, capex=1e7)
        rec = CompanyFinancialRecord("WARN_CO", "2023-12-31", "2024-04-20", bs, inc, cf)

        report = self.firewall.audit(rec)
        # 虽然通过一票否决准入，但产生了预警意见
        self.assertTrue(report.is_admitted)
        self.assertTrue(report.cash_purity.is_warning)
        self.assertTrue(report.debt_wall.is_warning)
        self.assertGreater(len(report.warning_reasons), 0)

    def test_zero_revenue_and_receivables(self) -> None:
        """测试：零营业收入边界情况"""
        bs_no_rec = BalanceSheet(1e8, 2e7, 8e7, 3e7, receivables=0)
        inc_zero = IncomeStatement(revenue=0, operating_profit=-1e6, net_profit=-1e6)
        cf = CashFlowStatement(operating_cash_flow=-1e6, capex=0)
        rec_zero = CompanyFinancialRecord("ZERO_REV", "2023-12-31", "2024-04-20", bs_no_rec, inc_zero, cf)

        res = self.purity_engine.evaluate(rec_zero)
        self.assertTrue(res.is_veto)

        # 零营收但账上有应收账款（荒谬假象）
        bs_with_rec = BalanceSheet(1e8, 2e7, 8e7, 3e7, receivables=5e6)
        rec_fake = CompanyFinancialRecord("ZERO_REV_REC", "2023-12-31", "2024-04-20", bs_with_rec, inc_zero, cf)
        res_fake = self.purity_engine.evaluate(rec_fake)
        self.assertTrue(res_fake.is_veto)

    def test_zero_liquid_reserves_with_debt(self) -> None:
        """测试：真实流动现金枯竭，且伴有刚性债务"""
        bs = BalanceSheet(
            total_assets=1e8,
            total_liabilities=8e7,
            total_equity=2e7,
            cash_and_equivalents=1e6,
            restricted_cash=1e6, # 现金全部受限
            short_term_debt=2e7  # 刚性负债 2000 万
        )
        inc = IncomeStatement(1e8, 5e6, 3e6, financial_expenses=2e6, ebitda=7e6)
        cf = CashFlowStatement(operating_cash_flow=-5e6, capex=2e6) # FCF 为负
        rec = CompanyFinancialRecord("DRY_CASH", "2023-12-31", "2024-04-20", bs, inc, cf)

        debt_res = self.debt_engine.evaluate(rec)
        self.assertTrue(debt_res.is_veto)
        self.assertGreater(debt_res.omega_debt, 10.0)

    def test_interest_burden_thresholds(self) -> None:
        """测试：财务费用吞噬 EBITDA 的两个梯度（预警与违约否决）"""
        # 梯度 1：利息占 EBITDA 50%（> 40%，未达 100%）
        bs = BalanceSheet(1e8, 2e7, 8e7, 5e7, short_term_debt=1e7)
        inc_high_interest = IncomeStatement(5e7, 1e7, 5e6, financial_expenses=6e6, ebitda=1.2e7)
        cf = CashFlowStatement(1e7, 2e6)
        rec1 = CompanyFinancialRecord("INTEREST_WARN", "2023-12-31", "2024-04-20", bs, inc_high_interest, cf)
        res1 = self.debt_engine.evaluate(rec1)
        self.assertTrue(any("财务利息侵蚀比例" in reason for reason in [res1.diagnosis]))

        # 梯度 2：利息占 EBITDA 110%（>= 100%，必然违约）
        inc_insolvent = IncomeStatement(5e7, 2e6, -5e6, financial_expenses=1.1e7, ebitda=1e7)
        rec2 = CompanyFinancialRecord("INSOLVENT", "2023-12-31", "2024-04-20", bs, inc_insolvent, cf)
        res2 = self.debt_engine.evaluate(rec2)
        self.assertTrue(res2.is_veto)


if __name__ == "__main__":
    unittest.main()
