"""
tests/test_reconciliation_engine.py
===================================
柜台双向平账与对账中枢单元测试。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 验证本地账本与真实券商持仓完全一致判定;
2. 验证差异飞单漏单捕获与紧急硬锁死机制;
3. 单文件严格不超过 300 行，零伪 Mock。
"""

import unittest
from entropy_execution.reconciliation_engine import (
    ReconciliationEngine,
    ReconciliationReport
)


class TestReconciliationEngine(unittest.TestCase):
    """测试平账对账引擎"""

    def setUp(self) -> None:
        self.engine = ReconciliationEngine()

    def test_perfect_reconciliation(self) -> None:
        """测试账实完全吻合情景"""
        local_pos = {"600519.SH": 100.0, "600900.SH": 1000.0}
        broker_pos = {"600519.SH": 100.0, "600900.SH": 1000.0}

        report = self.engine.audit_and_reconcile(local_pos, broker_pos)
        self.assertTrue(report.is_balanced)
        self.assertEqual(report.disparities_count, 0)
        self.assertFalse(report.emergency_lockout)
        self.assertIn("账实绝对守恒", report.summary_verdict)

    def test_critical_disparity_triggers_lockout(self) -> None:
        """测试柜台飞单导致超标差异，触发物理硬锁死"""
        local_pos = {"600519.SH": 100.0, "SA": 2.0}
        # 券商端 SA 只有 0 手（可能遭遇柜台撤单或漏单）
        broker_pos = {"600519.SH": 100.0, "SA": 0.0}

        report = self.engine.audit_and_reconcile(local_pos, broker_pos)
        self.assertFalse(report.is_balanced)
        self.assertEqual(report.disparities_count, 1)
        self.assertTrue(report.emergency_lockout)
        self.assertIn("紧急锁死", report.summary_verdict)

        disp = report.disparities[0]
        self.assertEqual(disp.symbol, "SA")
        self.assertEqual(disp.disparity_qty, -2.0)
        self.assertTrue(disp.is_critical)


if __name__ == "__main__":
    unittest.main()
