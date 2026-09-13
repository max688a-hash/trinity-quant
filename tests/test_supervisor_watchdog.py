"""
tests/test_supervisor_watchdog.py
=================================
进程看门狗与自愈中枢单元测试。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 验证组件心跳注册、打卡与停顿检测;
2. 验证内存常驻统计与故障自愈回调;
3. 单文件严格不超过 300 行，零伪 Mock。
"""

import unittest
from entropy_execution.supervisor_watchdog import SupervisorWatchdog


class TestSupervisorWatchdog(unittest.TestCase):
    """测试看门狗健康与自愈逻辑"""

    def setUp(self) -> None:
        self.watchdog = SupervisorWatchdog(max_memory_mb=2000.0, timeout_seconds=0.1)

    def test_heartbeat_and_patrol_healthy(self) -> None:
        """测试正常心跳打卡与巡检通过"""
        self.watchdog.register_component("CTP_GATEWAY")
        self.watchdog.beat("CTP_GATEWAY")

        report = self.watchdog.patrol_and_heal()
        self.assertTrue(report["all_healthy"])
        self.assertFalse(report["memory_alarm"])
        self.assertEqual(len(report["components"]), 1)
        self.assertTrue(report["components"][0]["is_alive"])

    def test_stalled_component_self_healing(self) -> None:
        """测试组件心跳超时触发自愈函数"""
        healed_flag = False

        def _recover() -> bool:
            nonlocal healed_flag
            healed_flag = True
            return True

        self.watchdog.register_component("AUTOPILOT_DAEMON", healer_fn=_recover)
        # 人工使心跳过期
        self.watchdog._heartbeats["AUTOPILOT_DAEMON"]["last_pulse"] -= 1.0

        report = self.watchdog.patrol_and_heal()
        self.assertTrue(healed_flag)
        self.assertTrue(report["all_healthy"])
        self.assertEqual(report["components"][0]["restarts_count"], 1)

    def test_memory_rss_reading(self) -> None:
        """测试物理内存度量非空且大于0"""
        mem = self.watchdog.get_memory_usage_mb()
        self.assertGreater(mem, 0.0)


if __name__ == "__main__":
    unittest.main()
