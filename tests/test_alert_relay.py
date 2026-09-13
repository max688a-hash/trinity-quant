"""
tests/test_alert_relay.py
=========================
跨端多通道主动外呼与战地紧急手机推送单元测试。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 验证拔插头、刚性止损与排毒一票否决外呼报文构造;
2. 验证防风暴轰炸频率抑制 (Rate Limiter);
3. 单文件严格不超过 300 行，零伪 Mock。
"""

import time
import unittest
from entropy_execution.alert_relay_gateway import (
    AlertLevel,
    AlertMessage,
    AlertRelayGateway
)


class TestAlertRelayGateway(unittest.TestCase):
    """测试外呼告警网关"""

    def setUp(self) -> None:
        self.gateway = AlertRelayGateway(throttle_seconds=1.0)

    def test_circuit_breaker_alert_construction(self) -> None:
        """测试日内 2% 拔插头告警生成与本地缓冲"""
        res = self.gateway.trigger_circuit_breaker(
            drawdown_pct=0.0215, reason="流动性瞬间枯竭触发事前风控"
        )
        self.assertTrue(res.get("LOCAL_BUFFER"))

        alerts = self.gateway.get_recent_alerts(5)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["level"], AlertLevel.CRITICAL_CIRCUIT_BREAKER.value)
        self.assertIn("2.0%", alerts[0]["title"])

    def test_stop_loss_and_poison_veto_alerts(self) -> None:
        """测试单笔 5% 止损与排毒熔断告警"""
        self.gateway.trigger_stop_loss(
            symbol="600519.SH", entry_px=1600.0, exit_px=1520.0, loss_pct=0.05
        )
        self.gateway.trigger_poison_veto(
            symbol="000002.SZ", reason="债务毒性超标", phi_cp=0.15, omega_debt=0.65
        )

        recent = self.gateway.get_recent_alerts(10)
        self.assertEqual(len(recent), 2)
        symbols = [a["symbol"] for a in recent]
        self.assertIn("600519.SH", symbols)
        self.assertIn("000002.SZ", symbols)

    def test_alert_throttling_suppression(self) -> None:
        """测试同标的高频警报抑制防轰炸"""
        # 第一次触发
        self.gateway.trigger_stop_loss("600519.SH", 100.0, 95.0, 0.05)
        # 紧接着第二次触发相同告警
        second_res = self.gateway.trigger_stop_loss("600519.SH", 100.0, 95.0, 0.05)
        self.assertTrue(second_res.get("THROTTLED"))


if __name__ == "__main__":
    unittest.main()
