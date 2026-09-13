"""
无 xtquant / 无真实 Binance 握手时禁止点亮 is_connected。
乐视/康美不得因假连接变成可买。
# ref: AGENTS.md 第 33 条 无真实成交即零跳动
"""

from __future__ import annotations

import unittest

from entropy_execution.binance_live_driver import BinanceLiveDriver
from entropy_execution.gateway_connection_manager import (
    ConnectionState,
    GatewayConnectionManager,
)
from entropy_execution.mini_qmt_driver import MiniQmtPhysicalDriver


class TestLiveDriverNoSdk(unittest.TestCase):
    """物理驱动在无 SDK 会话时必须保持断开。"""

    def test_mini_qmt_without_terminal_stays_offline(self) -> None:
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

    def test_binance_without_real_handshake_stays_offline(self) -> None:
        driver = BinanceLiveDriver(api_key="test_key_123", api_secret="test_secret_456")
        ok, msg = driver.connect()
        self.assertFalse(ok)
        self.assertFalse(driver.is_connected)
        self.assertTrue("握手" in msg or "失败" in msg or "Key" in msg)
        with self.assertRaises(RuntimeError):
            driver.query_balances()
        b_ok, ord_id, _ = driver.place_order("BTCUSDT", "BUY", 0.01, 65000.0, "LIMIT")
        self.assertFalse(b_ok)
        self.assertEqual(ord_id, "")

    def test_hmac_sign_still_deterministic_offline(self) -> None:
        driver = BinanceLiveDriver(api_key="test_key_123", api_secret="test_secret_456")
        sig1 = driver._sign("symbol=BTCUSDT&timestamp=1600000000000")
        sig2 = driver._sign("symbol=BTCUSDT&timestamp=1600000000000")
        self.assertEqual(sig1, sig2)
        self.assertEqual(len(sig1), 64)
        self.assertFalse(driver.is_connected)

    def test_manager_does_not_mark_fake_credentials_connected(self) -> None:
        mgr = GatewayConnectionManager()
        init_res = mgr.initialize_gateways({
            "QMT": {"account_id": "88886666", "mini_path": ""},
            "BINANCE": {"api_key": "k", "api_secret": "s"},
        })
        self.assertFalse(init_res.get("QMT", False))
        self.assertFalse(init_res.get("BINANCE", False))
        self.assertFalse(init_res.get("CTP", False))
        for t in mgr.heartbeat_patrol():
            self.assertEqual(t.state, ConnectionState.DISCONNECTED)
            self.assertFalse(t.is_healthy)
        self.assertFalse(mgr.force_reconnect("QMT"))
        self.assertEqual(mgr._states["QMT"], ConnectionState.DISCONNECTED)

    def test_letv_kangmei_remain_vetoed_and_unfilled(self) -> None:
        from tests.test_immune_system import TestImmuneSystem
        immune = TestImmuneSystem()
        immune.setUp()
        immune.test_case_letv_receivables_fraud()
        immune.test_case_kangmei_deposit_loan_paradox()
        qmt = MiniQmtPhysicalDriver(account_id="poison", mini_path="/no/such/qmt")
        qmt.connect_terminal()
        for poison in ("300104.SZ", "600518.SH"):
            ok, _, _ = qmt.place_order(poison, True, 100, 10.0)
            self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
