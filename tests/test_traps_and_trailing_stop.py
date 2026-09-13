"""
tests/test_traps_and_trailing_stop.py
=====================================
TRINITY QUANT 陷阱识别与动态自适应跟踪止盈止损测试套件。

严格验证：
1. 庄家诱多无量拉升与虚假大单托盘出货识别 (TrapDetector)
2. 伪便宜价值陷阱 (低PE但现金流枯竭) 识别
3. 动态自适应跟踪止损单向棘轮机制 (锁定浮盈，防利润回吐)
4. 突发毒性与高危陷阱的一票即刻平仓 (Emergency Exit)
"""

import unittest
from immune_system.trap_detector import (
    TrapDetector,
    TrapType,
)
from entropy_execution.dynamic_trailing_stop import (
    DynamicTrailingStopEngine,
    ExitTriggerType,
)


class TestTrapDetector(unittest.TestCase):
    """测试庄家与市场陷阱识别"""

    def setUp(self) -> None:
        self.detector = TrapDetector(volume_divergence_threshold=0.50, spoofing_ratio_threshold=4.0)

    def test_pump_and_dump_trap(self) -> None:
        # 股价大涨 6%，但成交量仅有平时均量的 30% (典型无量诱多出货)
        report = self.detector.audit_manipulator_traps(
            symbol="TRAP_01",
            price_change_pct=0.06,
            recent_avg_volume=100000.0,
            current_breakout_volume=30000.0,
            bid_volume_top3=10000.0,
            ask_volume_top3=10000.0,
            real_executed_sell_volume=5000.0,
            real_executed_buy_volume=5000.0
        )
        self.assertEqual(report.trap_detected, TrapType.PUMP_AND_DUMP_BULL_TRAP)
        self.assertFalse(report.is_safe_to_enter)
        self.assertIn("无量诱多", report.evidence_details)

    def test_spoofing_phantom_bid_trap(self) -> None:
        # 买盘挂单高达 50,000，卖盘仅 10,000 (5倍悬殊假象)，但内盘主动砸盘 40,000 手
        report = self.detector.audit_manipulator_traps(
            symbol="SPOOF_01",
            price_change_pct=0.01,
            recent_avg_volume=100000.0,
            current_breakout_volume=80000.0,
            bid_volume_top3=50000.0,
            ask_volume_top3=10000.0,
            real_executed_sell_volume=40000.0,
            real_executed_buy_volume=15000.0
        )
        self.assertEqual(report.trap_detected, TrapType.SPOOFING_PHANTOM_BID)
        self.assertFalse(report.is_safe_to_enter)
        self.assertIn("虚假大单托盘", report.evidence_details)

    def test_value_trap(self) -> None:
        # PE = 5.0, PB = 0.8 (表面极度便宜), 但经营现金流占净利润仅 10%，主业近3年复合下滑 15%
        report = self.detector.audit_value_trap(
            symbol="CHEAP_TRAP",
            pe_ratio=5.0,
            pb_ratio=0.8,
            ocf_to_net_profit_ratio=0.10,
            revenue_3y_cagr=-0.15
        )
        self.assertEqual(report.trap_detected, TrapType.VALUE_TRAP)
        self.assertFalse(report.is_safe_to_enter)


class TestDynamicTrailingStopEngine(unittest.TestCase):
    """测试动态自适应跟踪止损止盈"""

    def setUp(self) -> None:
        self.engine = DynamicTrailingStopEngine(
            base_atr_multiplier=2.5,
            profit_lock_threshold_pct=0.15,
            tightened_atr_multiplier=1.5
        )

    def test_dynamic_ratchet_locks_in_profit(self) -> None:
        # 1. 开仓建仓: 100元买入, ATR=2.0, 初始止损 = 100 - 2.5*2 = 95.0
        v1 = self.engine.evaluate_position(
            symbol="600519.SH",
            entry_price=100.0,
            current_price=100.0,
            highest_price_since_entry=100.0,
            previous_stop_price=95.0,
            current_atr=2.0
        )
        self.assertFalse(v1.should_close)
        self.assertEqual(v1.current_stop_price, 95.0)

        # 2. 股价上涨到 125元 (浮盈25% > 15%锁利阈值，ATR倍数收紧至 1.5)
        # 候选止损 = 125 - 1.5 * 2 = 122.0 元
        v2 = self.engine.evaluate_position(
            symbol="600519.SH",
            entry_price=100.0,
            current_price=124.0,
            highest_price_since_entry=125.0,
            previous_stop_price=95.0,
            current_atr=2.0
        )
        self.assertFalse(v2.should_close)
        # 验证止损线从 95 自动向上抬升至 122.0，成功锁定 22% 真实利润！
        self.assertEqual(v2.current_stop_price, 122.0)

        # 3. 股价自高位回撤至 121.0 (击穿动态止损线 122.0)
        v3 = self.engine.evaluate_position(
            symbol="600519.SH",
            entry_price=100.0,
            current_price=121.0,
            highest_price_since_entry=125.0,
            previous_stop_price=122.0,
            current_atr=2.0
        )
        self.assertTrue(v3.should_close)
        self.assertEqual(v3.trigger_type, ExitTriggerType.PROFIT_PROTECTION_TAKE)
        self.assertIn("击穿动态跟踪止损线", v3.explanation)

    def test_emergency_toxic_exit(self) -> None:
        # 处于持仓中，突然突发庄家出货或财报暴雷
        v_exit = self.engine.evaluate_position(
            symbol="600519.SH",
            entry_price=100.0,
            current_price=105.0,
            highest_price_since_entry=108.0,
            previous_stop_price=98.0,
            current_atr=2.0,
            is_emergency_toxic_flag=True
        )
        self.assertTrue(v_exit.should_close)
        self.assertEqual(v_exit.trigger_type, ExitTriggerType.EMERGENCY_TOXIC_EXIT)
        self.assertIn("强制即刻平仓避险", v_exit.explanation)


if __name__ == "__main__":
    unittest.main()
