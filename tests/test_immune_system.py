"""
tests.test_immune_system
~~~~~~~~~~~~~~~~~~~~~~~~
对免疫排毒系统（Immune System）进行全方位极限压力测试。
注入历史著名造假、暴雷企业真实财务指纹（乐视网、康美药业、高杠杆债务到期墙企业），
并对照优质现金流真造血标的，验证：
1. 暴雷/假账样本拦截率必须达到 100%！
2. 优质健康标的 0 误杀！
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


class TestImmuneSystem(unittest.TestCase):
    """免疫排毒防火墙核心测试套件"""

    def setUp(self) -> None:
        self.purity_engine = CashPurityEngine()
        self.debt_engine = DebtWallEngine()
        self.firewall = PoisonFirewall(
            cash_purity_engine=self.purity_engine,
            debt_wall_engine=self.debt_engine
        )

    def test_case_letv_receivables_fraud(self) -> None:
        """
        【实证测试 1：乐视网（300104）2016 典型财务指纹】
        特征：账面净利润近 5 亿（假象繁盛），但应收账款高达近百亿（占营收 > 45%），
        经营现金流枯竭且为负，短期借款与一年内到期负债如泰山压顶。
        """
        bs = BalanceSheet(
            total_assets=3.2e10,
            total_liabilities=2.1e10,
            total_equity=1.1e10,
            cash_and_equivalents=3.6e9,
            restricted_cash=1.2e9,
            receivables=9.8e9,       # 应收账款巨胖
            goodwill=1.5e9,
            short_term_debt=6.5e9,   # 巨额短期负债
            long_term_debt_due_within_1y=3.2e9
        )
        inc = IncomeStatement(
            revenue=2.19e10,
            operating_profit=-3.3e8,
            net_profit=5.5e8,        # 账面做出的利润
            financial_expenses=5.2e8,
            ebitda=1.2e9
        )
        cf = CashFlowStatement(
            operating_cash_flow=-1.06e9, # 真实经营现金流失血逾 10 亿！
            capex=3.0e9,
            working_capital_change=1.2e9,
            depreciation_amortization=8.0e8
        )
        record = CompanyFinancialRecord(
            symbol="300104.SZ",
            period_end_date="2016-12-31",
            disclosure_date="2017-04-20",
            balance_sheet=bs,
            income_statement=inc,
            cash_flow_statement=cf
        )

        report = self.firewall.audit(record)
        # 必须触发一票否决！
        self.assertFalse(report.is_admitted, "乐视网样本必须被坚决一票否决！")
        self.assertTrue(report.cash_purity.is_veto, "必须击穿其造血纯度虚假神话！")
        self.assertTrue(report.debt_wall.is_veto, "必须识别其 1 年内到期债务挤兑毒性！")
        self.assertLess(report.cash_purity.phi_cp, 0.0, "经营净失血的企业 Φ_CP 必须为负！")

    def test_case_kangmei_deposit_loan_paradox(self) -> None:
        """
        【实证测试 2：康美药业（600518）典型“存贷双高”造假特征】
        特征：账面吹嘘 300 亿货币资金，实则 80% 受限/虚构，
        同时借入数百亿短期有息负债，财务利息支出侵蚀几乎全部利润。
        """
        bs = BalanceSheet(
            total_assets=7.4e10,
            total_liabilities=4.6e10,
            total_equity=2.8e10,
            cash_and_equivalents=3.4e10,  # 宣称 340 亿货币资金
            restricted_cash=2.8e10,       # 实质受限或虚构 280 亿！
            receivables=6.0e9,
            short_term_debt=1.5e10,       # 存贷双高，疯狂举借短期债
            long_term_debt_due_within_1y=8.0e9
        )
        inc = IncomeStatement(
            revenue=2.5e10,
            operating_profit=4.0e9,
            net_profit=3.5e9,
            financial_expenses=1.8e9,     # 巨额利息支出露出马脚
            ebitda=4.5e9
        )
        cf = CashFlowStatement(
            operating_cash_flow=1.8e9,
            capex=3.0e9,
            working_capital_change=2.0e9,
            depreciation_amortization=5.0e8
        )
        record = CompanyFinancialRecord(
            symbol="600518.SH",
            period_end_date="2017-12-31",
            disclosure_date="2018-04-26",
            balance_sheet=bs,
            income_statement=inc,
            cash_flow_statement=cf
        )

        report = self.firewall.audit(record)
        self.assertFalse(report.is_admitted, "康美药业存贷双高样本必须被一票否决！")
        # 检验受限资金超标否决
        has_cash_fraud_veto = any("资金虚假疑云" in reason for reason in report.veto_reasons)
        self.assertTrue(has_cash_fraud_veto, "必须检测出受限资金比例畸高疑云！")
        # 债务到期墙必须报警
        self.assertTrue(report.debt_wall.is_veto, "扣减受限资金后，债务毒性必须爆表！")

    def test_case_high_leverage_debt_wall(self) -> None:
        """
        【实证测试 3：某典型暴雷高杠杆房企 2020 债务到期墙】
        特征：总资产负债率 > 88%，一年内到期负债是现金的 8 倍，FCF 深度亏损。
        """
        bs = BalanceSheet(
            total_assets=1.5e11,
            total_liabilities=1.35e11,  # 负债率 90%
            total_equity=1.5e10,
            cash_and_equivalents=5.0e9,
            restricted_cash=2.0e9,
            receivables=1.0e10,
            short_term_debt=2.5e10,     # 一年内到期负债 350 亿
            long_term_debt_due_within_1y=1.0e10
        )
        inc = IncomeStatement(
            revenue=4.0e10,
            operating_profit=2.0e9,
            net_profit=1.0e9,
            financial_expenses=3.5e9,   # 财务利息彻底压死利润
            ebitda=3.0e9
        )
        cf = CashFlowStatement(
            operating_cash_flow=-5.0e9, # 严重现金失血
            capex=1.0e9
        )
        record = CompanyFinancialRecord(
            symbol="DEBT_COLLAPSE",
            period_end_date="2020-12-31",
            disclosure_date="2021-04-30",
            balance_sheet=bs,
            income_statement=inc,
            cash_flow_statement=cf
        )

        report = self.firewall.audit(record)
        self.assertFalse(report.is_admitted)
        self.assertTrue(report.debt_wall.is_veto)
        self.assertGreater(report.debt_wall.omega_debt, 5.0, "债务毒性指数必须远超警戒阈值！")

    def test_case_kweichow_moutai_pristine_cash(self) -> None:
        """
        【对照测试 1：贵州茅台（600519）优质印钞造血真值模型】
        特征：零有息负债，应收账款微乎其微，预收充沛，净利润 100% 对应真实现金流入。
        """
        bs = BalanceSheet(
            total_assets=2.5e11,
            total_liabilities=3.5e10,
            total_equity=2.15e11,
            cash_and_equivalents=1.8e11,
            restricted_cash=0.0,
            receivables=2.0e8,          # 应收账款占营收比例极低
            goodwill=0.0,
            short_term_debt=0.0,        # 零短期负债
            long_term_debt_due_within_1y=0.0
        )
        inc = IncomeStatement(
            revenue=1.4e11,
            operating_profit=9.5e10,
            net_profit=7.4e10,
            financial_expenses=-1.5e9,  # 利息收入为负（巨额净利息进账）
            ebitda=1.0e11
        )
        cf = CashFlowStatement(
            operating_cash_flow=7.8e10, # 经营现金流甚至大于净利润
            capex=4.0e9,
            working_capital_change=2.0e9,
            depreciation_amortization=2.5e9
        )
        record = CompanyFinancialRecord(
            symbol="600519.SH",
            period_end_date="2023-12-31",
            disclosure_date="2024-04-03",
            balance_sheet=bs,
            income_statement=inc,
            cash_flow_statement=cf
        )

        report = self.firewall.audit(record)
        self.assertTrue(report.is_admitted, "贵州茅台式真造血标的必须 100% 顺畅通过！")
        self.assertEqual(len(report.veto_reasons), 0, "不应产生任何否决意见")
        self.assertGreater(report.cash_purity.phi_cp, 0.70, "造血纯度 Φ_CP 应处于极高区间")
        self.assertAlmostEqual(report.debt_wall.omega_debt, 0.0, places=2, msg="零负债企业的 Ω_Debt 应为 0")

    def test_case_goodwill_bomb(self) -> None:
        """【测试 5：商誉雷区排毒】商誉占净资产超过 30% 必须被拦截"""
        bs = BalanceSheet(
            total_assets=1e10,
            total_liabilities=4e9,
            total_equity=6e9,
            cash_and_equivalents=2e9,
            goodwill=2.5e9  # 商誉占股东权益 41.7%
        )
        inc = IncomeStatement(revenue=5e9, operating_profit=8e8, net_profit=6e8)
        cf = CashFlowStatement(operating_cash_flow=7e8, capex=1e8)
        record = CompanyFinancialRecord("BOMB_GOODWILL", "2023-12-31", "2024-04-20", bs, inc, cf)

        report = self.firewall.audit(record)
        self.assertFalse(report.is_admitted)
        has_goodwill_veto = any("商誉减值炸弹" in r for r in report.veto_reasons)
        self.assertTrue(has_goodwill_veto)

    def test_batch_screening_100_percent_precision(self) -> None:
        """
        【全市场综合批处理测试】
        同时输入 3 个暴雷/假账标的 + 1 个健康标的，
        断言：排毒拦截率必须为 100%（拦截全部 3 个），健康标的 100% 存活！
        """
        letv = CompanyFinancialRecord(
            "300104.SZ", "2016-12-31", "2017-04-20",
            BalanceSheet(3.2e10, 2.1e10, 1.1e10, 3.6e9, 0, 9.8e9, 0, 0, 6.5e9, 3.2e9),
            IncomeStatement(2.19e10, -3.3e8, 5.5e8, 5.2e8, 1.2e9),
            CashFlowStatement(-1.06e9, 3.0e9)
        )
        moutai = CompanyFinancialRecord(
            "600519.SH", "2023-12-31", "2024-04-03",
            BalanceSheet(2.5e11, 3.5e10, 2.15e11, 1.8e11, 0, 2.0e8),
            IncomeStatement(1.4e11, 9.5e10, 7.4e10, 0, 1.0e11),
            CashFlowStatement(7.8e10, 4.0e9)
        )
        fake_cash = CompanyFinancialRecord(
            "FAKE_CASH", "2023-12-31", "2024-04-20",
            BalanceSheet(1e10, 4e9, 6e9, 3e9, 2.5e9), # 受限资金 83%
            IncomeStatement(5e9, 8e8, 6e8),
            CashFlowStatement(7e8, 1e8)
        )
        high_debt = CompanyFinancialRecord(
            "HIGH_DEBT", "2023-12-31", "2024-04-20",
            BalanceSheet(1e10, 9e9, 1e9, 5e8, 0, 0, 0, 0, 4e9, 2e9), # 1年到期 60亿，现金仅 5亿
            IncomeStatement(5e9, 8e8, 6e8, 5e8, 9e8),
            CashFlowStatement(1e8, 1e8)
        )

        universe = [letv, moutai, fake_cash, high_debt]
        clean_universe, reports = self.firewall.screen_universe(universe)

        # 断言纯净池中仅有且必须有 600519.SH
        self.assertEqual(len(clean_universe), 1)
        self.assertEqual(clean_universe[0].symbol, "600519.SH")

        # 断言其余 3 个全部被拒
        rejected = [r for r in reports if not r.is_admitted]
        self.assertEqual(len(rejected), 3)


if __name__ == "__main__":
    unittest.main()
