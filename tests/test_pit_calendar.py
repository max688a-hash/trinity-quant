"""
tests.test_pit_calendar
~~~~~~~~~~~~~~~~~~~~~~~
对真值内核的点时（Point-in-Time）时空防穿透机制与底层财务模型
进行严格边界与异常防御测试，确保时空物理隔离 0 瑕疵。
"""

import unittest
from truth_kernel.models import (
    BalanceSheet,
    IncomeStatement,
    CashFlowStatement,
    CompanyFinancialRecord
)
from truth_kernel.pit_calendar import PITCalendar, LookaheadBiasError


def create_dummy_record(
    symbol: str,
    period_end_date: str,
    disclosure_date: str
) -> CompanyFinancialRecord:
    """辅助工厂函数：生成轻量测试用财报记录"""
    bs = BalanceSheet(
        total_assets=1e9,
        total_liabilities=4e8,
        total_equity=6e8,
        cash_and_equivalents=2e8,
        restricted_cash=2e7,
        receivables=1e8,
        goodwill=5e7,
        short_term_debt=1e8,
        long_term_debt_due_within_1y=5e7,
        commercial_paper=1e7
    )
    inc = IncomeStatement(
        revenue=5e8,
        operating_profit=1e8,
        net_profit=8e7,
        financial_expenses=1e7,
        ebitda=1.2e8
    )
    cf = CashFlowStatement(
        operating_cash_flow=9e7,
        capex=2e7,
        working_capital_change=1e7,
        depreciation_amortization=2e7
    )
    return CompanyFinancialRecord(
        symbol=symbol,
        period_end_date=period_end_date,
        disclosure_date=disclosure_date,
        balance_sheet=bs,
        income_statement=inc,
        cash_flow_statement=cf
    )


class TestPITCalendar(unittest.TestCase):
    """点时日历时空穿透防线测试套件"""

    def setUp(self) -> None:
        self.calendar = PITCalendar(buffer_days=1)
        self.r_annual_2023 = create_dummy_record("600000.SH", "2023-12-31", "2024-04-20")
        self.r_q1_2024 = create_dummy_record("600000.SH", "2024-03-31", "2024-04-28")

        self.calendar.register_record(self.r_annual_2023)
        self.calendar.register_record(self.r_q1_2024)

    def test_time_barrier_before_disclosure(self) -> None:
        """测试：在法定披露日之前，任何查询均返回 None（绝无未来函数）"""
        record = self.calendar.get_latest_record("600000.SH", "2024-01-15")
        self.assertIsNone(record, "在披露日之前不应获取到任何未公开数据！")

        record_eve = self.calendar.get_latest_record("600000.SH", "2024-04-19")
        self.assertIsNone(record_eve, "披露日前夜仍不能偷窥数据！")

    def test_disclosure_day_availability(self) -> None:
        """测试：在法定披露日当天，数据正式对策略可见"""
        record = self.calendar.get_latest_record("600000.SH", "2024-04-20")
        self.assertIsNotNone(record)
        self.assertEqual(record.period_end_date, "2023-12-31")

    def test_multi_quarter_sequence(self) -> None:
        """测试：在 2024-04-25 截面，只能看到 2023 年报，看不到 2024 一季报"""
        mid_record = self.calendar.get_latest_record("600000.SH", "2024-04-25")
        self.assertIsNotNone(mid_record)
        self.assertEqual(mid_record.period_end_date, "2023-12-31")

        new_record = self.calendar.get_latest_record("600000.SH", "2024-04-29")
        self.assertIsNotNone(new_record)
        self.assertEqual(new_record.period_end_date, "2024-03-31")

    def test_historical_window_filtering(self) -> None:
        """测试：历史记录序列过滤严格遵守时点截面"""
        hist = self.calendar.get_historical_records("600000.SH", "2024-04-25")
        self.assertEqual(len(hist), 1)
        self.assertEqual(hist[0].period_end_date, "2023-12-31")

        hist_later = self.calendar.get_historical_records("600000.SH", "2024-05-01", limit=1)
        self.assertEqual(len(hist_later), 1)
        self.assertEqual(hist_later[0].period_end_date, "2024-03-31")

    def test_unregistered_symbol_queries(self) -> None:
        """测试：查询未注册股票代码安全返回空"""
        self.assertIsNone(self.calendar.get_latest_record("UNKNOWN.SH", "2024-05-01"))
        self.assertEqual(self.calendar.get_historical_records("UNKNOWN.SH", "2024-05-01"), [])
        # 未注册代码审计不抛异常
        self.calendar.check_lookahead_violation("UNKNOWN.SH", "2024-01-01", "2023-12-31")

    def test_lookahead_violation_trap(self) -> None:
        """测试：主动审查偷窥行为，必须抛出 LookaheadBiasError"""
        with self.assertRaises(LookaheadBiasError):
            self.calendar.check_lookahead_violation(
                symbol="600000.SH",
                query_date="2024-03-01",
                target_period_end="2023-12-31"
            )
        # 合法查询不抛异常
        self.calendar.check_lookahead_violation(
            symbol="600000.SH",
            query_date="2024-04-21",
            target_period_end="2023-12-31"
        )


class TestModelsDefense(unittest.TestCase):
    """财务数据结构防御性输入校验测试套件"""

    def test_balance_sheet_negative_assets(self) -> None:
        """测试：总资产为负必须报错"""
        with self.assertRaises(ValueError):
            BalanceSheet(total_assets=-100, total_liabilities=50, total_equity=50, cash_and_equivalents=10)

    def test_balance_sheet_negative_cash(self) -> None:
        """测试：货币资金为负必须报错"""
        with self.assertRaises(ValueError):
            BalanceSheet(total_assets=100, total_liabilities=50, total_equity=50, cash_and_equivalents=-10)

    def test_balance_sheet_invalid_restricted_cash(self) -> None:
        """测试：受限资金超过货币资金必须报错"""
        with self.assertRaises(ValueError):
            BalanceSheet(total_assets=100, total_liabilities=50, total_equity=50, cash_and_equivalents=10, restricted_cash=20)

    def test_income_statement_negative_revenue(self) -> None:
        """测试：营业收入为负必须报错"""
        with self.assertRaises(ValueError):
            IncomeStatement(revenue=-500, operating_profit=10, net_profit=5)

    def test_company_record_empty_symbol(self) -> None:
        """测试：股票代码为空必须报错"""
        bs = BalanceSheet(100, 50, 50, 20)
        inc = IncomeStatement(100, 10, 5)
        cf = CashFlowStatement(10, 2)
        with self.assertRaises(ValueError):
            CompanyFinancialRecord("", "2023-12-31", "2024-04-20", bs, inc, cf)

    def test_company_record_invalid_date_order(self) -> None:
        """测试：披露日早于报告截止日必须报错"""
        bs = BalanceSheet(100, 50, 50, 20)
        inc = IncomeStatement(100, 10, 5)
        cf = CashFlowStatement(10, 2)
        with self.assertRaises(ValueError):
            CompanyFinancialRecord("TEST", "2023-12-31", "2023-11-20", bs, inc, cf)

    def test_computed_properties(self) -> None:
        """测试计算衍生属性及资不抵债边界"""
        bs = BalanceSheet(100, 120, -20, 10, goodwill=10)
        self.assertEqual(bs.goodwill_to_equity, 1.0)
        self.assertAlmostEqual(bs.debt_to_assets, 1.2)

        inc_no_ebitda = IncomeStatement(100, 20, 15, financial_expenses=5)
        self.assertEqual(inc_no_ebitda.computed_ebitda, 25.0)


if __name__ == "__main__":
    unittest.main()
