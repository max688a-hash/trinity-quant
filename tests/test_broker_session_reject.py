"""
未真实柜台会话时禁止本地伪成交（宪法第 33 条）。
空 connect / 纯字符串账号 ≠ 会话；乐视/康美不得因假 FILLED 变成可买。
"""

from __future__ import annotations

import unittest

from entropy_execution.broker_gateway_adapter import (
    BrokerGatewayType,
    CTPFuturesGateway,
    CryptoBinanceGateway,
    QMTStockGateway,
    RealBrokerRouter,
    NO_LIVE_SESSION_REASON,
    RealOrderRequest,
    RealOrderStatus,
)
# ref: AGENTS.md 第 33 条 无真实成交即零跳动；禁止本地伪 FILLED


def _order(symbol: str, cl_ord_id: str = "CL_NO_SESSION") -> RealOrderRequest:
    return RealOrderRequest(
        cl_ord_id=cl_ord_id,
        symbol=symbol,
        is_buy=True,
        quantity=100.0,
        price=1550.0,
    )


class TestBrokerSessionReject(unittest.TestCase):
    """CTP / QMT / Binance 适配器在无 SDK 会话时必须拒单。"""

    def test_empty_connect_stays_offline(self) -> None:
        for gw in (CTPFuturesGateway(), QMTStockGateway(), CryptoBinanceGateway()):
            self.assertFalse(gw.connect({}))
            self.assertFalse(gw.is_connected)

    def test_string_credentials_are_not_a_live_session(self) -> None:
        fake_creds = {
            "BrokerID": "9999",
            "InvestorID": "demo",
            "Password": "demo",
            "API_KEY": "k",
            "API_SECRET": "s",
            "mini_qmt": "/tmp/fake_qmt",
        }
        samples = (
            (CTPFuturesGateway(), "SA2409"),
            (QMTStockGateway(), "600519.SH"),
            (CryptoBinanceGateway(), "BTCUSDT"),
        )
        for gw, symbol in samples:
            self.assertFalse(gw.connect(fake_creds))
            resp = gw.submit_order(_order(symbol))
            self.assertEqual(resp.status, RealOrderStatus.REJECTED)
            self.assertNotEqual(resp.status, RealOrderStatus.FILLED)
            self.assertEqual(resp.executed_quantity, 0.0)
            self.assertEqual(resp.rejection_reason, NO_LIVE_SESSION_REASON)

    def test_router_defaults_offline_and_never_fills(self) -> None:
        router = RealBrokerRouter(is_live_combat=True)
        health = router.get_system_health()
        self.assertEqual(
            health["gateways"][BrokerGatewayType.CTP_FUTURES.value]["status"],
            "OFFLINE",
        )
        self.assertEqual(health["gateways"][BrokerGatewayType.QMT_STOCK.value]["status"], "OFFLINE")
        self.assertEqual(
            health["gateways"][BrokerGatewayType.BINANCE_CRYPTO.value]["status"],
            "OFFLINE",
        )
        for symbol in ("600519.SH", "SA2409", "BTCUSDT"):
            resp = router.route_and_execute(symbol, True, 1.0, 100.0)
            self.assertEqual(resp.status, RealOrderStatus.REJECTED)
            self.assertNotEqual(resp.broker_order_id[:3], "QMT")
            self.assertTrue(
                ("会话" in resp.rejection_reason) or ("未连接" in resp.rejection_reason),
                msg=resp.rejection_reason,
            )

    def test_disconnected_account_query_is_not_ten_million_theatre(self) -> None:
        gw = QMTStockGateway()
        snap = gw.query_account()
        cash = float(snap.get("cash") or snap.get("available") or 0.0)
        self.assertEqual(cash, 0.0)
        self.assertFalse(gw.cancel_order("CL_GHOST"))

    def test_letv_kangmei_remain_vetoed_and_unfilled(self) -> None:
        from tests.test_immune_system import TestImmuneSystem
        immune = TestImmuneSystem()
        immune.setUp()
        immune.test_case_letv_receivables_fraud()
        immune.test_case_kangmei_deposit_loan_paradox()
        router = RealBrokerRouter(is_live_combat=True)
        for poison in ("300104.SZ", "600518.SH"):
            resp = router.route_and_execute(poison, True, 100.0, 10.0)
            self.assertEqual(resp.status, RealOrderStatus.REJECTED)
            self.assertNotEqual(resp.status, RealOrderStatus.FILLED)


if __name__ == "__main__":
    unittest.main()
