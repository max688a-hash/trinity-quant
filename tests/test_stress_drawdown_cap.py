"""
黑天鹅总报告必须把回撤上限当硬闸：超 2% 不得 is_all_passed。
乐视/康美不得因假全绿变成可买。
# ref: AGENTS.md 第 24 条 单日最大亏损 2%；第 21 条 禁止粉饰 CVaR
"""

from __future__ import annotations

import unittest

from entropy_execution.black_swan_stress_tester import BlackSwanStressTester


class TestStressDrawdownCap(unittest.TestCase):
    """回撤硬上限必须能一票否决全绿。"""

    def test_live_suite_fails_when_worst_dd_exceeds_cap(self) -> None:
        rep = BlackSwanStressTester().run_full_stress_test()
        self.assertEqual(rep.max_allowed_drawdown_pct, 0.02)
        self.assertGreater(rep.worst_case_drawdown_pct, rep.max_allowed_drawdown_pct)
        self.assertFalse(rep.is_all_passed)
        self.assertIn("FAIL", rep.final_verdict)

    def test_monte_carlo_cvar_over_cap_is_fail(self) -> None:
        res = BlackSwanStressTester().test_scenario_monte_carlo_cvar_99(n_simulations=500)
        self.assertGreater(res.max_drawdown_contained, 0.02)
        self.assertFalse(res.is_defense_successful)
        self.assertEqual(res.verdict, "FAIL")
        self.assertIn("FAIL", res.details)

    def test_letv_kangmei_remain_vetoed(self) -> None:
        from tests.test_immune_system import TestImmuneSystem
        immune = TestImmuneSystem()
        immune.setUp()
        immune.test_case_letv_receivables_fraud()
        immune.test_case_kangmei_deposit_loan_paradox()


if __name__ == "__main__":
    unittest.main()
