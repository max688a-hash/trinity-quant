"""
tests.test_truth_features
~~~~~~~~~~~~~~~~~~~~~~~~~
对真值内核的现金流特征工程与点时流水线进行严密单元测试。
确保 TTM 平滑与除零防御 100% 稳健。
"""

import unittest
from truth_kernel.models import (
    BalanceSheet,
    IncomeStatement,
    CashFlowStatement,
    CompanyFinancialRecord
)
from truth_kernel.pit_calendar import PITCalendar
from truth_kernel.cash_flow_engine import CashFlowEngine
from truth_kernel.feature_pipeline import TruthFeaturePipeline


def make_record(period: str, disc: str, rev: float, np: float, ocf: float, capex: float) -> CompanyFinancialRecord:
    bs = BalanceSheet(1e9, 4e8, 6e8, 2e8)
    inc = IncomeStatement(rev, np * 1.1, np)
    cf = CashFlowStatement(ocf, capex)
    return CompanyFinancialRecord("600519.SH", period, disc, bs, inc, cf)


class TestTruthFeatures(unittest.TestCase):
    """现金流特征引擎测试套件"""

    def setUp(self) -> None:
        self.engine = CashFlowEngine(smoothing_quarters=4)
        self.calendar = PITCalendar()
        # 4 个季度的真实历史序列
        self.r1 = make_record("2023-03-31", "2023-04-28", 1e8, 2e7, 3e7, 5e6)
        self.r2 = make_record("2023-06-30", "2023-08-28", 1.2e8, 2.5e7, 3.5e7, 6e6)
        self.r3 = make_record("2023-09-30", "2023-10-28", 1.1e8, 2.2e7, 3.2e7, 5e6)
        self.r4 = make_record("2023-12-31", "2024-04-20", 1.5e8, 3.5e7, 4.5e7, 8e6)

        for r in [self.r1, self.r2, self.r3, self.r4]:
            self.calendar.register_record(r)

        self.pipeline = TruthFeaturePipeline(self.calendar, self.engine)

    def test_ttm_rolling_calculation(self) -> None:
        """测试 4 季度完整历史的 TTM 滚动聚合数值精度"""
        records = [self.r1, self.r2, self.r3, self.r4]
        feat = self.engine.compute_features(records)
        self.assertIsNotNone(feat)

        expected_rev = 1e8 + 1.2e8 + 1.1e8 + 1.5e8
        expected_ocf = 3e7 + 3.5e7 + 3.2e7 + 4.5e7
        expected_capex = 5e6 + 6e6 + 5e6 + 8e6
        expected_fcf = expected_ocf - expected_capex

        self.assertAlmostEqual(feat.revenue_ttm, expected_rev)
        self.assertAlmostEqual(feat.ocf_ttm, expected_ocf)
        self.assertAlmostEqual(feat.fcf_ttm, expected_fcf)
        self.assertGreater(feat.cash_flow_to_revenue, 0.25)

    def test_short_history_scaling(self) -> None:
        """测试历史不足 4 季度的年化等比折算逻辑"""
        short_records = [self.r1, self.r2]  # 仅 2 个季度
        feat = self.engine.compute_features(short_records)
        self.assertIsNotNone(feat)
        # 两个季度之和乘以 2 (4/2)
        expected_rev = (1e8 + 1.2e8) * 2.0
        self.assertAlmostEqual(feat.revenue_ttm, expected_rev)

    def test_empty_record_handling(self) -> None:
        """测试空记录安全返回 None"""
        self.assertIsNone(self.engine.compute_features([]))

    def test_pipeline_point_in_time_extraction(self) -> None:
        """测试特征流水线在不同交易日截面的时点过滤"""
        # 在 2023-09-01 截面，只能看到 r1 和 r2
        feat_sep = self.pipeline.extract_features("600519.SH", "2023-09-01")
        self.assertIsNotNone(feat_sep)
        self.assertEqual(feat_sep.period_end_date, "2023-06-30")

        # 在 2024-05-01 截面，看到全部 4 季度
        feat_may = self.pipeline.extract_features("600519.SH", "2024-05-01")
        self.assertIsNotNone(feat_may)
        self.assertEqual(feat_may.period_end_date, "2023-12-31")

        # 批量接口测试
        batch = self.pipeline.extract_universe_features(["600519.SH", "UNKNOWN.SH"], "2024-05-01")
        self.assertIn("600519.SH", batch)
        self.assertNotIn("UNKNOWN.SH", batch)


if __name__ == "__main__":
    unittest.main()
