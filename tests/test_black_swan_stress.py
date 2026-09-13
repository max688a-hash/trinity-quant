"""
tests/test_black_swan_stress.py
===============================
TRINITY QUANT 黑天鹅极端市场情景防爆压力测试单元测试。
严格遵守最高宪法第5条第3款铁律：单文件不超过 300 行，零伪 Mock，真实边界数值推演。
"""

import unittest

from entropy_execution.black_swan_stress_tester import (
    BlackSwanStressTester,
    FullStressTestReport,
    StressScenarioResult,
)


class TestBlackSwanStress(unittest.TestCase):
    """黑天鹅极端市场情景压力测试用例集"""

    def setUp(self) -> None:
        self.tester = BlackSwanStressTester()

    def test_2008_subprime_debt_collapse(self) -> None:
        """验证 2008 次贷危机极端债务毒性暴雷防御"""
        res = self.tester.test_scenario_2008_subprime()
        self.assertTrue(res.is_defense_successful)
        self.assertEqual(res.verdict, "PASS")
        self.assertEqual(res.max_drawdown_contained, 0.0)
        self.assertIn("排毒防火墙", res.defense_mechanism_triggered)

    def test_2015_liquidity_vacuum_limit_down(self) -> None:
        """验证 2015 A股千股跌停流动性黑洞防御"""
        res = self.tester.test_scenario_2015_liquidity_vacuum()
        self.assertTrue(res.is_defense_successful)
        self.assertEqual(res.verdict, "PASS")
        self.assertEqual(res.max_drawdown_contained, 0.0)
        self.assertIn("跌停", res.defense_mechanism_triggered)

    def test_2020_flash_crash_and_circuit_breaker(self) -> None:
        """验证 2020 全球熔断闪崩脊髓反射与拔插头防御"""
        res = self.tester.test_scenario_2020_flash_crash()
        self.assertTrue(res.is_defense_successful)
        self.assertEqual(res.verdict, "PASS")
        self.assertTrue(res.hard_circuit_breaker_active)
        self.assertLessEqual(res.max_drawdown_contained, 0.025)

    def test_extreme_slippage_shock(self) -> None:
        """验证盘口深度蒸发 90% 极端冲击滑点阻断"""
        res = self.tester.test_scenario_extreme_slippage()
        self.assertTrue(res.is_defense_successful)
        self.assertEqual(res.verdict, "PASS")
        self.assertIn("TWAP", res.defense_mechanism_triggered)

    def test_monte_carlo_cvar_99_fat_tail(self) -> None:
        """验证蒙特卡洛 99% CVaR 肥尾极端扰动下的生存能力"""
        res = self.tester.test_scenario_monte_carlo_cvar_99(n_simulations=500)
        self.assertTrue(res.is_defense_successful)
        self.assertEqual(res.verdict, "PASS")
        self.assertLess(res.max_drawdown_contained, 0.12)

    def test_full_stress_test_suite(self) -> None:
        """全量矩阵端到端总体验收"""
        rep: FullStressTestReport = self.tester.run_full_stress_test()
        self.assertGreater(rep.worst_case_drawdown_pct, rep.max_allowed_drawdown_pct)
        self.assertFalse(rep.is_all_passed)
        self.assertIn("FAIL", rep.final_verdict)
        self.assertEqual(rep.total_scenarios, 5)


if __name__ == "__main__":
    unittest.main()
