"""
tests.test_gravity_brain
~~~~~~~~~~~~~~~~~~~~~~~~
对引力大脑核心组件（DCF引力估值、非对称凸性定价、复合 Alpha 引擎）
进行全方位单元测试与边界压力测试。
"""

import unittest
from truth_kernel.models import (
    BalanceSheet,
    IncomeStatement,
    CashFlowStatement,
    CompanyFinancialRecord
)
from gravity_brain.dcf_gravity import GravityValuationEngine
from gravity_brain.asymmetric_pricing import AsymmetricPricingEngine
from gravity_brain.alpha_engine import GravityAlphaEngine


class TestGravityBrain(unittest.TestCase):
    """真值引力大脑核心测试套件"""

    def setUp(self) -> None:
        self.val_engine = GravityValuationEngine()
        self.pricing_engine = AsymmetricPricingEngine()
        self.alpha_engine = GravityAlphaEngine(
            val_engine=self.val_engine,
            pricing_engine=self.pricing_engine
        )

        # 1. 强现金流印钞机模型 (如优质白马)
        bs_good = BalanceSheet(
            total_assets=1e11, total_liabilities=2e10, total_equity=8e10,
            cash_and_equivalents=5e10, receivables=2e9, goodwill=0
        )
        inc_good = IncomeStatement(revenue=5e10, operating_profit=3e10, net_profit=2.5e10)
        cf_good = CashFlowStatement(operating_cash_flow=2.8e10, capex=3e9)
        self.rec_good = CompanyFinancialRecord("PRISTINE.SH", "2023-12-31", "2024-04-20", bs_good, inc_good, cf_good)

        # 2. 负现金流/失血衰退模型
        bs_bad = BalanceSheet(
            total_assets=5e10, total_liabilities=4.5e10, total_equity=5e9,
            cash_and_equivalents=2e9, short_term_debt=2e10, receivables=1.5e10
        )
        inc_bad = IncomeStatement(revenue=2e10, operating_profit=-1e9, net_profit=-2e9, financial_expenses=1.5e9)
        cf_bad = CashFlowStatement(operating_cash_flow=-3e9, capex=1e9)
        self.rec_bad = CompanyFinancialRecord("BLEEDING.SZ", "2023-12-31", "2024-04-20", bs_bad, inc_bad, cf_bad)

    def test_dcf_gravity_valuation_cash_cow(self) -> None:
        """测试强造血标的的真值引力定价与安全边际"""
        # 假设当前市值为 3000 亿
        res = self.val_engine.compute_intrinsic_value(self.rec_good, market_cap=3e11)

        self.assertGreater(res.gravity_value, res.tangible_nav_floor)
        self.assertGreater(res.discounted_fcf_sum, 0.0)
        self.assertGreater(res.purity_penalty_factor, 0.8)
        self.assertIsNotNone(res.gravity_potential)

    def test_dcf_gravity_negative_cash_fallback(self) -> None:
        """测试负现金流标的自动回退至有形净资产清算底座"""
        res = self.val_engine.compute_intrinsic_value(self.rec_bad, market_cap=1e10)

        # 自由现金流为负，折现贡献额必须为 0
        self.assertEqual(res.discounted_fcf_sum, 0.0)
        # 估值严格等于有形净资产打折清算价
        self.assertAlmostEqual(res.gravity_value, res.tangible_nav_floor)

    def test_asymmetric_convexity_profiling(self) -> None:
        """测试非对称凸性与反脆弱得分评定"""
        val_good = self.val_engine.compute_intrinsic_value(self.rec_good, market_cap=3e11)
        audit_good = self.alpha_engine.firewall.audit(self.rec_good)
        convex_good = self.pricing_engine.evaluate_convexity(val_good, audit_good.debt_wall)

        # 优质标的应具备低尾部风险与高非对称赔率
        self.assertLess(convex_good.downside_tail_risk, 0.2)
        self.assertGreater(convex_good.convexity_score, 5.0)

        # 恶化标的下行风险拉满
        val_bad = self.val_engine.compute_intrinsic_value(self.rec_bad, market_cap=5e10)
        audit_bad = self.alpha_engine.firewall.audit(self.rec_bad)
        convex_bad = self.pricing_engine.evaluate_convexity(val_bad, audit_bad.debt_wall)

        self.assertGreater(convex_bad.downside_tail_risk, 0.8)
        self.assertFalse(convex_bad.is_convex)

    def test_alpha_engine_ranking_and_veto(self) -> None:
        """测试 Alpha 引擎对排毒淘汰标的一票清零与优质标的评级"""
        universe = [self.rec_good, self.rec_bad]
        ranked = self.alpha_engine.rank_universe(universe, market_caps={"PRISTINE.SH": 3e11, "BLEEDING.SZ": 5e10})

        self.assertEqual(len(ranked), 2)
        # 第一名必须是优质标的
        self.assertEqual(ranked[0].symbol, "PRISTINE.SH")
        self.assertTrue(ranked[0].is_firewall_admitted)
        self.assertIn(ranked[0].signal, ["STRONG_BUY", "BUY"])
        self.assertGreater(ranked[0].alpha_score, 0.0)

        # 第二名必须是被否决标的，Alpha 得分严格为 0
        self.assertEqual(ranked[1].symbol, "BLEEDING.SZ")
        self.assertFalse(ranked[1].is_firewall_admitted)
        self.assertEqual(ranked[1].signal, "VETO")
        self.assertEqual(ranked[1].alpha_score, 0.0)


if __name__ == "__main__":
    unittest.main()
