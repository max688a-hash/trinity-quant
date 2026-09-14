"""
tests/test_trade_statistics.py
==============================
滚动实证交易统计 → 凯利输入：冷启动无优势、样本充足后 p/b/CVaR 真实可复算、NaN 防御。
"""

import math
import unittest

from entropy_execution.live_pipeline_orchestrator import LivePipelineOrchestrator
from entropy_execution.paper_trading_engine import PaperTradingEngine
from entropy_execution.trade_statistics import (
    RollingTradeStatistics,
    kelly_inputs_from_returns,
    resolve_optional_market_cap,
)


class TestRollingTradeStatistics(unittest.TestCase):

    def test_cold_start_has_no_evidence(self) -> None:
        stats = RollingTradeStatistics(window=30, min_samples=10)
        k = stats.compute()
        self.assertEqual(k.sample_size, 0)
        self.assertFalse(k.has_sufficient_evidence)
        self.assertEqual(k.win_rate, 0.0)
        self.assertEqual(k.payoff_ratio, 0.0)

    def test_empirical_values_match_hand_calculation(self) -> None:
        rets = [0.04] * 6 + [-0.02] * 4  # p=0.6, b=2.0
        k = kelly_inputs_from_returns(rets, min_samples=10)
        self.assertTrue(k.has_sufficient_evidence)
        self.assertAlmostEqual(k.win_rate, 0.6, places=4)
        self.assertAlmostEqual(k.payoff_ratio, 2.0, places=4)
        # 5% 尾部 => floor(10*0.05)=0 -> 至少 1 笔 => 最差 -0.02
        self.assertAlmostEqual(k.cvar_alpha, 0.02, places=4)

    def test_window_evicts_old_samples(self) -> None:
        stats = RollingTradeStatistics(window=5, min_samples=3)
        stats.extend([-0.10] * 5)
        stats.extend([0.05] * 5)
        k = stats.compute()
        self.assertEqual(k.sample_size, 5)
        self.assertEqual(k.win_rate, 1.0)

    def test_nan_inf_ignored(self) -> None:
        stats = RollingTradeStatistics(window=10, min_samples=2)
        stats.extend([math.nan, math.inf, -math.inf, 0.01, -0.01])
        self.assertEqual(stats.sample_size, 2)

    def test_invalid_config_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RollingTradeStatistics(window=5, min_samples=6)
        with self.assertRaises(ValueError):
            RollingTradeStatistics(cvar_confidence=0.3)

    def test_market_cap_requires_real_shares(self) -> None:
        self.assertIsNone(resolve_optional_market_cap(10.0, None))
        self.assertIsNone(resolve_optional_market_cap(10.0, 0.0))
        self.assertIsNone(resolve_optional_market_cap(10.0, math.nan))
        self.assertEqual(resolve_optional_market_cap(10.0, 1e8), 1e9)


class TestOrchestratorKellyWiring(unittest.TestCase):

    def _bull_tick(self, orch: LivePipelineOrchestrator):
        return orch.execute_tick(
            symbol="600519.SH", current_price=150.0,
            macro_history=[100.0 + i for i in range(25)],
            meso_history=[120.0 + i for i in range(12)],
        )

    def test_cold_start_probe_then_empirical_kelly(self) -> None:
        paper = PaperTradingEngine(initial_capital=10_000_000.0)
        orch = LivePipelineOrchestrator(paper_engine=paper, cold_start_weight=0.02)
        res = self._bull_tick(orch)
        self.assertEqual(res.audit_trace["kelly"]["mode"], "COLD_START_PROBE")
        notional = res.receipt.executed_price * res.receipt.executed_quantity
        self.assertLessEqual(notional, 10_000_000.0 * 0.02)

        for r in [0.04] * 12 + [-0.02] * 8:
            orch.record_closed_trade(r)
        res2 = self._bull_tick(orch)
        self.assertEqual(res2.audit_trace["kelly"]["mode"], "EMPIRICAL")
        self.assertGreater(res2.audit_trace["kelly"]["weight"], 0.0)
        self.assertLessEqual(res2.audit_trace["kelly"]["weight"], 0.20)

    def test_negative_edge_stands_aside(self) -> None:
        orch = LivePipelineOrchestrator(paper_engine=PaperTradingEngine(initial_capital=10_000_000.0))
        for r in [0.01] * 5 + [-0.03] * 15:
            orch.record_closed_trade(r)
        res = self._bull_tick(orch)
        self.assertFalse(res.is_executed)
        self.assertEqual(res.action, "STAND_ASIDE")
        self.assertEqual(res.audit_trace["kelly"]["weight"], 0.0)

    def test_cold_start_weight_bounds(self) -> None:
        with self.assertRaises(ValueError):
            LivePipelineOrchestrator(cold_start_weight=0.10)


if __name__ == "__main__":
    unittest.main()
