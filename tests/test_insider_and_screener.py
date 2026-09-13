"""
tests/test_insider_and_screener.py
==================================
测试大股东减持抛售探针与一键真值智能选股引擎。
"""

import unittest

from gravity_brain.auto_screener_engine import (
    AutoScreenerEngine,
    AutoScreeningCandidate,
    CompanyDeepDossier,
)
from immune_system.insider_dump_monitor import (
    AlertSeverity,
    AudioAlertTone,
    InsiderDumpMonitor,
)


class TestInsiderAndScreener(unittest.TestCase):
    """验证大股东抛售监测与自动选股"""

    def setUp(self) -> None:
        self.insider_monitor = InsiderDumpMonitor(
            max_dumping_ratio=0.05,
            max_pledge_ratio=0.50,
            max_discount_pct=0.08
        )
        self.screener = AutoScreenerEngine(
            min_phi_cp=0.80,
            max_omega_debt=1.00,
            min_alpha=1.0
        )

    def test_insider_normal_case(self) -> None:
        """测试正常持股状态标的"""
        res = self.insider_monitor.evaluate_insider_risk(
            symbol="600519",
            insider_sell_volume=500.0,
            adv_20=50000.0, # 1% 减持
            pledged_shares_ratio=0.0,
            block_discount_pct=0.02
        )
        self.assertEqual(res.severity, AlertSeverity.NORMAL)
        self.assertFalse(res.is_vetoed)
        self.assertEqual(res.audio_tone, AudioAlertTone.NONE)

    def test_insider_critical_dumping_veto(self) -> None:
        """测试大股东恶性集中抛售一票否决"""
        res = self.insider_monitor.evaluate_insider_risk(
            symbol="300104",
            insider_sell_volume=12000.0,
            adv_20=50000.0, # 24% 恶性挤兑抛售
            pledged_shares_ratio=0.75,
            block_discount_pct=0.12
        )
        self.assertEqual(res.severity, AlertSeverity.CRITICAL_DUMP)
        self.assertTrue(res.is_vetoed)
        self.assertEqual(res.audio_tone, AudioAlertTone.CRISIS_ALARM)
        self.assertEqual(res.ui_theme_class, "badge-glow-red")
        self.assertIn("疯狂甩卖危机", res.warning_message)

    def test_auto_screener_filtering(self) -> None:
        """测试一键真值智能选股与深研报告装载"""
        mock_universe = [
            {
                "symbol": "600519", "name": "贵州茅台",
                "phi_cp": 1.54, "omega_debt": 0.00, "alpha": 4.6, "gravity_val": 13342.3
            },
            {
                "symbol": "002594", "name": "比亚迪",
                "phi_cp": 2.59, "omega_debt": 0.88, "alpha": 1.4, "gravity_val": 2179.3
            },
            {
                "symbol": "300104", "name": "乐视网",
                "phi_cp": 0.02, "omega_debt": 4.50, "alpha": -8.0, "gravity_val": 12.0
            }
        ]
        candidates = self.screener.run_screening(mock_universe)
        # 茅台与比亚迪应入选，乐视网必须被淘汰
        qualified = [c for c in candidates if c.is_qualified]
        symbols = [c.symbol for c in qualified]
        self.assertIn("600519", symbols)
        self.assertIn("002594", symbols)
        self.assertNotIn("300104", symbols)

        # 检查茅台深研档案完整性
        moutai = next(c for c in qualified if c.symbol == "600519")
        self.assertEqual(moutai.audio_chime, "ENTRY_PING")
        self.assertEqual(moutai.color_indicator, "badge-glow-green")
        self.assertIn("飞天茅台", moutai.deep_dossier.core_business)
        self.assertTrue(moutai.deep_dossier.anti_cycle_grade.startswith("AAA"))


if __name__ == "__main__":
    unittest.main()
