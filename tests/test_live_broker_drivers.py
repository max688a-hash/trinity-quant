"""
tests/test_live_broker_drivers.py
=================================
单元测试：MiniQMT 物理驱动、Binance 实盘驱动与长连接自愈状态机。
"""

import unittest
from entropy_execution.binance_live_driver import BinanceLiveDriver
from entropy_execution.gateway_connection_manager import GatewayConnectionManager, ConnectionState
from entropy_execution.mini_qmt_driver import MiniQmtPhysicalDriver


class TestLiveBrokerDrivers(unittest.TestCase):
    """测试真实券商与加密资产物理驱动器"""

    def test_mini_qmt_driver(self) -> None:
        """测试 MiniQMT 物理驱动生命周期"""
        driver = MiniQmtPhysicalDriver(account_id="66668888", mini_path="", token="")
        ok, msg = driver.connect_terminal()
        self.assertTrue(ok)
        self.assertTrue(driver.is_connected)

        # 资金资产快照测试
        assets = driver.query_account_assets()
        self.assertEqual(assets.account_id, "66668888")
        self.assertGreater(assets.total_asset, 0)
        self.assertGreater(assets.cash_available, 0)

        # 持仓测试
        pos = driver.query_positions()
        self.assertIsInstance(pos, list)

        # 报单与撤单测试
        p_ok, ord_id, _ = driver.place_order("600519.SH", True, 100, 1550.0)
        self.assertTrue(p_ok)
        self.assertTrue(ord_id.startswith("QMT_"))

        c_ok, _ = driver.cancel_order(ord_id)
        self.assertTrue(c_ok)

        # 断开测试
        driver.disconnect_terminal()
        self.assertFalse(driver.is_connected)

    def test_binance_live_driver(self) -> None:
        """测试 Binance 物理签名与交易驱动"""
        driver = BinanceLiveDriver(api_key="test_key_123", api_secret="test_secret_456")
        ok, _ = driver.connect()
        self.assertTrue(ok)

        # 签名一致性测试
        sig1 = driver._sign("symbol=BTCUSDT&timestamp=1600000000000")
        sig2 = driver._sign("symbol=BTCUSDT&timestamp=1600000000000")
        self.assertEqual(sig1, sig2)
        self.assertEqual(len(sig1), 64)

        # 资产查询测试 (沙盒降级或真实网络)
        balances = driver.query_balances()
        self.assertGreater(len(balances), 0)
        usdt_bal = next((b for b in balances if b.asset == "USDT"), None)
        self.assertIsNotNone(usdt_bal)

        # 下单与撤单测试
        b_ok, ord_id, _ = driver.place_order("BTCUSDT", "BUY", 0.01, 65000.0, "LIMIT")
        self.assertTrue(b_ok)
        self.assertTrue(len(ord_id) > 0)

        c_ok, _ = driver.cancel_order("BTCUSDT", ord_id)
        self.assertTrue(c_ok)

    def test_gateway_connection_manager(self) -> None:
        """测试网关长连接自愈与级联平账"""
        reconcile_called = []

        def dummy_reconcile() -> None:
            reconcile_called.append(True)

        mgr = GatewayConnectionManager(on_reconnected_reconcile=dummy_reconcile)
        init_res = mgr.initialize_gateways({
            "QMT": {"account_id": "88886666", "mini_path": ""},
            "BINANCE": {"api_key": "k", "api_secret": "s"}
        })
        self.assertTrue(init_res["QMT"])
        self.assertTrue(init_res["BINANCE"])

        # 巡检测试
        telemetries = mgr.heartbeat_patrol()
        self.assertEqual(len(telemetries), 3)
        for t in telemetries:
            self.assertEqual(t.state, ConnectionState.CONNECTED)
            self.assertTrue(t.is_healthy)

        # 人工强制重连测试
        r_ok = mgr.force_reconnect("QMT")
        self.assertTrue(r_ok)
        self.assertGreaterEqual(len(reconcile_called), 1)


if __name__ == "__main__":
    unittest.main()
