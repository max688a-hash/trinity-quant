"""
tests/test_live_broker_drivers.py
=================================
单元测试：MiniQMT / Binance 无 SDK 时禁止伪 CONNECTED。
"""

import unittest
from entropy_execution.binance_live_driver import BinanceLiveDriver
from entropy_execution.gateway_connection_manager import GatewayConnectionManager, ConnectionState
from entropy_execution.mini_qmt_driver import MiniQmtPhysicalDriver


class TestLiveBrokerDrivers(unittest.TestCase):
    """测试真实券商与加密资产物理驱动器的诚实离线行为"""

    def test_mini_qmt_driver(self) -> None:
        driver = MiniQmtPhysicalDriver(account_id="66668888", mini_path="", token="")
        ok, msg = driver.connect_terminal()
        self.assertFalse(ok)
        self.assertFalse(driver.is_connected)
        self.assertIn("会话", msg)
        with self.assertRaises(RuntimeError):
            driver.query_account_assets()
        p_ok, ord_id, _ = driver.place_order("600519.SH", True, 100, 1550.0)
        self.assertFalse(p_ok)
        self.assertEqual(ord_id, "")
        c_ok, _ = driver.cancel_order("QMT_GHOST")
        self.assertFalse(c_ok)
        driver.disconnect_terminal()
        self.assertFalse(driver.is_connected)

    def test_binance_live_driver(self) -> None:
        driver = BinanceLiveDriver(api_key="test_key_123", api_secret="test_secret_456")
        ok, msg = driver.connect()
        self.assertFalse(ok)
        self.assertFalse(driver.is_connected)
        self.assertIn("握手", msg)
        sig1 = driver._sign("symbol=BTCUSDT&timestamp=1600000000000")
        sig2 = driver._sign("symbol=BTCUSDT&timestamp=1600000000000")
        self.assertEqual(sig1, sig2)
        self.assertEqual(len(sig1), 64)
        with self.assertRaises(RuntimeError):
            driver.query_balances()
        b_ok, ord_id, _ = driver.place_order("BTCUSDT", "BUY", 0.01, 65000.0, "LIMIT")
        self.assertFalse(b_ok)
        self.assertEqual(ord_id, "")
        c_ok, _ = driver.cancel_order("BTCUSDT", "BIN_GHOST")
        self.assertFalse(c_ok)

    def test_gateway_connection_manager(self) -> None:
        reconcile_called: list[bool] = []

        def dummy_reconcile() -> None:
            reconcile_called.append(True)

        mgr = GatewayConnectionManager(on_reconnected_reconcile=dummy_reconcile)
        init_res = mgr.initialize_gateways({
            "QMT": {"account_id": "88886666", "mini_path": ""},
            "BINANCE": {"api_key": "k", "api_secret": "s"}
        })
        self.assertFalse(init_res["QMT"])
        self.assertFalse(init_res["BINANCE"])
        self.assertFalse(init_res["CTP"])
        telemetries = mgr.heartbeat_patrol()
        self.assertEqual(len(telemetries), 3)
        for t in telemetries:
            self.assertEqual(t.state, ConnectionState.DISCONNECTED)
            self.assertFalse(t.is_healthy)
        r_ok = mgr.force_reconnect("QMT")
        self.assertFalse(r_ok)
        self.assertEqual(len(reconcile_called), 0)


if __name__ == "__main__":
    unittest.main()
