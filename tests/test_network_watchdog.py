"""
tests/test_network_watchdog.py
==============================
测试网络物理断网侦测、心跳看门狗、幂等去重与下单死循环防爆机制。
单文件严格控制在 300 行以内，零伪 Mock，全真实数值断言。
"""

import time
import unittest

from entropy_execution.network_watchdog import (
    NetworkLinkStatus,
    NetworkWatchdog,
)
from entropy_execution.real_money_service import (
    _NETWORK_WATCHDOG,
    get_real_money_status,
    handle_real_money_order,
)


class TestNetworkWatchdog(unittest.TestCase):
    """网络物理看门狗与死循环防爆单元测试"""

    def setUp(self) -> None:
        self.wd = NetworkWatchdog(
            max_latency_ms=500.0,
            heartbeat_timeout_sec=1.5,
            duplicate_window_sec=1.0
        )

    def test_healthy_heartbeat_and_audit(self) -> None:
        """测试正常心跳下放行安全报单"""
        self.wd.record_heartbeat(latency_ms=25.0)
        res = self.wd.audit_pre_submission(
            cl_ord_id="CL_TEST_001",
            symbol="600519.SH",
            is_buy=True,
            quantity=100.0,
            price=1550.0
        )
        self.assertTrue(res.is_safe)
        self.assertEqual(res.status, NetworkLinkStatus.HEALTHY)
        self.assertIsNone(res.rejection_reason)

    def test_severed_network_freeze(self) -> None:
        """测试物理断网或心跳超时时硬性冻结报单"""
        self.wd.force_simulate_severed()
        res = self.wd.audit_pre_submission(
            cl_ord_id="CL_TEST_002",
            symbol="600519.SH",
            is_buy=True,
            quantity=100.0,
            price=1550.0
        )
        self.assertFalse(res.is_safe)
        self.assertEqual(res.status, NetworkLinkStatus.SEVERED)
        self.assertIn("物理网络中断", res.rejection_reason or "")

    def test_idempotent_duplicate_order_id(self) -> None:
        """测试幂等性拦截重复单号"""
        self.wd.record_heartbeat(latency_ms=10.0)
        res1 = self.wd.audit_pre_submission("CL_UNIQUE_999", "000001.SZ", True, 200, 10.5)
        self.assertTrue(res1.is_safe)

        # 重复单号立即提交
        res2 = self.wd.audit_pre_submission("CL_UNIQUE_999", "000001.SZ", True, 200, 10.5)
        self.assertFalse(res2.is_safe)
        self.assertIn("已在在途或完成列表中", res2.rejection_reason or "")

    def test_rapid_retry_loop_storm_interception(self) -> None:
        """测试拦截重试风暴与死循环高频报单（防无限下单/平仓循环）"""
        self.wd.record_heartbeat(latency_ms=15.0)
        res1 = self.wd.audit_pre_submission("CL_A1", "RB2410", True, 10, 3600.0)
        self.assertTrue(res1.is_safe)

        # 毫秒级重发相同特征报单（模拟断网重试循环 bug）
        res2 = self.wd.audit_pre_submission("CL_A2", "RB2410", True, 10, 3600.0)
        self.assertFalse(res2.is_safe)
        self.assertIn("重复报单指纹", res2.rejection_reason or "")

    def test_real_money_service_integration(self) -> None:
        """测试实战服务聚合层在断网状态下的真实物理阻断"""
        _NETWORK_WATCHDOG.restore_connection()
        status = get_real_money_status()
        self.assertIn("network_watchdog", status)
        self.assertTrue(status["network_watchdog"]["is_network_alive"])

        # 仿真断网
        _NETWORK_WATCHDOG.force_simulate_severed()
        order_res = handle_real_money_order({
            "symbol": "600519.SH",
            "action": "BUY",
            "quantity": 100,
            "price": 1550.0
        })
        self.assertFalse(order_res["success"])
        self.assertEqual(order_res["verdict"], "NETWORK_WATCHDOG_FREEZE")
        self.assertIn("物理网络", order_res["reason"])

        # 恢复网络，提交不同标的报单
        _NETWORK_WATCHDOG.restore_connection()
        order_res2 = handle_real_money_order({
            "symbol": "000001.SZ",
            "action": "BUY",
            "quantity": 500,
            "price": 10.50
        })
        # 看门狗已放行，但无真实柜台会话仍必须拒单，禁止本地伪成交
        self.assertFalse(order_res2["success"])
        self.assertNotEqual(order_res2.get("verdict"), "NETWORK_WATCHDOG_FREEZE")
        self.assertEqual(order_res2.get("status"), "REJECTED")
        self.assertIn("会话", str(order_res2.get("rejection_reason") or ""))

    def tearDown(self) -> None:
        _NETWORK_WATCHDOG.restore_connection()


if __name__ == "__main__":
    unittest.main()
