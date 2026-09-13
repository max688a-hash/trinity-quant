"""
tests/test_autopilot_daemon.py
==============================
TRINITY QUANT 影子巡航自学习守护进程单元测试。
"""

import time
import unittest

from entropy_execution.autonomous_learning_sandbox import AutonomousLearningSandbox
from entropy_execution.autopilot_learning_daemon import (
    AutoPilotHeartbeat,
    AutoPilotLearningDaemon,
)
from entropy_execution.paper_trading_engine import PaperTradingEngine


class TestAutoPilotDaemon(unittest.TestCase):
    """测试后台自巡航守护进程生命周期与任务调度"""

    def setUp(self) -> None:
        paper = PaperTradingEngine(initial_capital=10_000_000.0, enforce_trading_hours=False)
        sandbox = AutonomousLearningSandbox(paper_engine=paper)
        self.daemon = AutoPilotLearningDaemon(sandbox=sandbox, poll_interval_seconds=0.1)

    def tearDown(self) -> None:
        self.daemon.stop()

    def test_daemon_lifecycle(self) -> None:
        """测试启动与停止生命周期"""
        self.assertFalse(self.daemon.is_running)
        self.assertTrue(self.daemon.start())
        self.assertTrue(self.daemon.is_running)
        time.sleep(0.3)
        self.assertTrue(self.daemon.stop())
        self.assertFalse(self.daemon.is_running)

    def test_process_next_asset_tick(self) -> None:
        """测试单步调度轮询执行"""
        res = self.daemon.process_next_asset_tick()
        hb: AutoPilotHeartbeat = self.daemon.get_heartbeat()
        self.assertEqual(hb.total_ticks_processed, 1)
        self.assertNotEqual(hb.last_scanned_symbol, "NONE")
        self.assertIn("BTCUSDT", hb.active_monitored_assets)


if __name__ == "__main__":
    unittest.main()
