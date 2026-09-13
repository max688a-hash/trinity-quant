"""
tests/test_time_bomb_defuser.py
===============================
全天候隐形定时炸弹排查与物理拆除中枢 (TimeBombDefuserCentral) 单元测试。
100% 覆盖率验证除权假暴跌、期货交割陷阱、周末跳空、假死看门狗与停牌流动性黑洞。
"""

import unittest
from immune_system.time_bomb_defuser import (
    BombHazardType,
    TimeBombDefuserCentral,
)


class TestTimeBombDefuser(unittest.TestCase):

    def test_ex_dividend_false_panic_calibrator(self) -> None:
        """测试 10送10 导致股价折半：系统成功识别假暴跌，物理阻止误杀割肉"""
        rep = TimeBombDefuserCentral.calibrate_ex_dividend_drop(
            symbol="600519.SH",
            current_price=100.0,
            raw_pre_close=200.0,
            cash_dividend_per_share=0.0,
            split_ratio=1.0  # 10送10除权
        )
        self.assertTrue(rep.is_hazard_active)
        self.assertEqual(rep.risk_severity, "CRITICAL")
        self.assertTrue(rep.auto_defused)
        self.assertIn("表面跌幅 -50.0%", rep.diagnosis_detail)
        self.assertIn("真实涨跌幅 +0.00%", rep.diagnosis_detail)
        self.assertIn("拦截脊髓原始避险反射", rep.defuse_action)

    def test_ex_dividend_real_market_drop(self) -> None:
        """测试无除权的真实盘口暴跌：系统放行避险逻辑"""
        rep = TimeBombDefuserCentral.calibrate_ex_dividend_drop(
            symbol="600519.SH",
            current_price=180.0,
            raw_pre_close=200.0,
            cash_dividend_per_share=0.0,
            split_ratio=0.0
        )
        self.assertFalse(rep.is_hazard_active)
        self.assertEqual(rep.risk_severity, "SAFE")

    def test_futures_delivery_month_guard(self) -> None:
        """测试期货交割月临界防强平"""
        # 临近交割仅剩 5 天 -> 危险，触发自动移仓
        rep_danger = TimeBombDefuserCentral.check_futures_delivery_month("SA2409", days_to_delivery=5)
        self.assertTrue(rep_danger.is_hazard_active)
        self.assertEqual(rep_danger.risk_severity, "CRITICAL")
        self.assertTrue(rep_danger.auto_defused)
        self.assertIn("自动移仓激活", rep_danger.defuse_action)

        # 远月合约 30 天 -> 安全
        rep_safe = TimeBombDefuserCentral.check_futures_delivery_month("SA2501", days_to_delivery=30)
        self.assertFalse(rep_safe.is_hazard_active)
        self.assertEqual(rep_safe.risk_severity, "SAFE")

    def test_weekend_gap_deleveraging(self) -> None:
        """测试周五尾盘跨周末降杠杆防周一跳空爆仓"""
        # 周五 14:50，杠杆 68% -> 触发周末降杠杆
        rep = TimeBombDefuserCentral.evaluate_weekend_gap_deleveraging(
            weekday=4,
            current_time_str="14:50:00",
            margin_utilization_ratio=0.68,
            is_leveraged_venue=True
        )
        self.assertTrue(rep.is_hazard_active)
        self.assertEqual(rep.risk_severity, "CRITICAL")
        self.assertTrue(rep.auto_defused)
        self.assertIn("压缩至 30.0% 以下", rep.defuse_action)

        # 周三正常盘中 -> 安全
        rep_wed = TimeBombDefuserCentral.evaluate_weekend_gap_deleveraging(
            weekday=2,
            current_time_str="14:50:00",
            margin_utilization_ratio=0.68,
            is_leveraged_venue=True
        )
        self.assertFalse(rep_wed.is_hazard_active)

    def test_market_data_zombie_watchdog(self) -> None:
        """测试盘中超过 15 秒无行情报文触发假死看门狗"""
        rep_dead = TimeBombDefuserCentral.check_data_stream_watchdog(
            last_tick_epoch=1000.0,
            current_epoch=1020.0,  # 过去 20 秒无数据
            is_market_open=True
        )
        self.assertTrue(rep_dead.is_hazard_active)
        self.assertEqual(rep_dead.risk_severity, "CRITICAL")
        self.assertTrue(rep_dead.auto_defused)
        self.assertIn("死人开关触发", rep_dead.defuse_action)

        # 正常 2 秒内 -> 安全
        rep_live = TimeBombDefuserCentral.check_data_stream_watchdog(
            last_tick_epoch=1000.0,
            current_epoch=1002.0,
            is_market_open=True
        )
        self.assertFalse(rep_live.is_hazard_active)

    def test_suspension_liquidity_enclave(self) -> None:
        """测试股票停牌资产流动性隔离仓与打折计提"""
        rep_sus = TimeBombDefuserCentral.evaluate_suspension_liquidity_enclave(
            symbol="000001.SZ",
            is_suspended=True,
            nominal_position_value=100_000.0,
            haircut_ratio=0.30
        )
        self.assertTrue(rep_sus.is_hazard_active)
        self.assertEqual(rep_sus.risk_severity, "CRITICAL")
        self.assertTrue(rep_sus.auto_defused)
        self.assertIn("计提 30% 折扣", rep_sus.defuse_action)
        self.assertIn("30,000.00", rep_sus.defuse_action)

    def test_sweep_all_hazards(self) -> None:
        """测试一键全景排查"""
        reports = TimeBombDefuserCentral.sweep_all_hazards()
        self.assertEqual(len(reports), 5)
        hazards = [r.hazard_type for r in reports]
        self.assertIn(BombHazardType.EX_DIVIDEND_FALSE_PANIC, hazards)
        self.assertIn(BombHazardType.FUTURES_DELIVERY_TRAP, hazards)
        self.assertIn(BombHazardType.WEEKEND_GAP_RISK, hazards)
        self.assertIn(BombHazardType.ZOMBIE_DATA_STREAM, hazards)
        self.assertIn(BombHazardType.SUSPENSION_LIQUIDITY_LOCK, hazards)


if __name__ == "__main__":
    unittest.main()
