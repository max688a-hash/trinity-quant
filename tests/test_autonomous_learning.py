"""
tests/test_autonomous_learning.py
=================================
TRINITY QUANT 自动模拟盘影子巡航与系统自主学习进化引擎单元测试。
遵守宪法第一性原理：真实数值边界验证，单文件不超过 300 行。
"""

import unittest

from entropy_execution.autonomous_learning_sandbox import (
    AutonomousLearningSandbox,
    AutopsyVerdict,
    SelfLearningReport,
)
from entropy_execution.paper_trading_engine import PaperTradingEngine


class TestAutonomousLearningSandbox(unittest.TestCase):
    """测试系统自主学习与影子巡航"""

    def setUp(self) -> None:
        self.paper = PaperTradingEngine(initial_capital=10_000_000.0, enforce_trading_hours=False)
        self.sandbox = AutonomousLearningSandbox(paper_engine=self.paper)

    def test_initial_learning_report(self) -> None:
        """测试初始自主学习实证报告结构：真实零假样本冷启动"""
        rep = self.sandbox.generate_learning_report()
        self.assertEqual(rep.total_auto_trades, 0)
        self.assertEqual(rep.empirical_win_rate, 0.0)
        self.assertGreater(rep.calibrated_kelly_f, 0.05)
        self.assertFalse(rep.is_cooling_down)
        self.assertIn("系统自学习中枢已就绪", rep.learning_synthesis)

    def test_shadow_tick_execution(self) -> None:
        """测试影子自动巡航 Tick 执行与决策"""
        res = self.sandbox.run_autonomous_tick(
            symbol="BTCUSDT",
            current_price=65000.0,
            is_replay_mode=True
        )
        self.assertIn("executed", res)
        if res.get("action"):
            return
        self.assertFalse(res["executed"])
        why = str(res.get("reason") or res.get("veto_reason") or "")
        self.assertTrue(why, msg=f"拒绝成交必须写明原因: {res}")

    def test_trade_autopsy_and_parameter_calibration(self) -> None:
        """测试逐笔复盘归因与贝叶斯参数在线迭代"""
        init_rep = self.sandbox.generate_learning_report()
        init_trades = init_rep.total_auto_trades
        init_kelly = init_rep.calibrated_kelly_f

        # 模拟一笔盈利交易归因
        self.sandbox._record_autopsy_and_learn(
            symbol="600519.SH",
            entry_price=1500.0,
            exit_price=1580.0,
            quantity=100.0,
            friction=105.0,
            is_trailing_stop=False
        )

        new_rep = self.sandbox.generate_learning_report()
        self.assertEqual(new_rep.total_auto_trades, init_trades + 1)
        self.assertEqual(new_rep.recent_autopsies[0]["verdict"], AutopsyVerdict.ALPHA_EXPANSION_WIN.value)
        self.assertGreaterEqual(new_rep.calibrated_kelly_f, 0.05)

        # 模拟一笔棘轮止盈归因
        self.sandbox._record_autopsy_and_learn(
            symbol="BTCUSDT",
            entry_price=64000.0,
            exit_price=65000.0,
            quantity=0.5,
            friction=25.0,
            is_trailing_stop=True
        )
        rep3 = self.sandbox.generate_learning_report()
        self.assertEqual(rep3.recent_autopsies[0]["verdict"], AutopsyVerdict.TRAILING_STOP_PROFIT.value)

    def test_cooling_down_protection(self) -> None:
        """测试极端回撤下触发模型自冷却保护"""
        # 强制制造大回撤
        self.paper._max_drawdown = 0.04  # 4% 回撤
        self.sandbox._calibrate_parameters()
        rep = self.sandbox.generate_learning_report()
        self.assertTrue(rep.is_cooling_down)


if __name__ == "__main__":
    unittest.main()
