"""
tests/test_physical_gateway_wiring.py
=====================================
真金路由器与物理驱动接线：无会话拒单、未点燃拒单、受理≠成交。
"""

import time
import unittest

from entropy_execution.binance_live_driver import BinanceLiveDriver
from entropy_execution.broker_gateway_adapter import (
    AbstractBrokerGateway,
    BrokerGatewayType,
    RealBrokerRouter,
    RealOrderRequest,
    RealOrderResponse,
    RealOrderStatus,
)
from entropy_execution.gateway_connection_manager import ConnectionState, GatewayConnectionManager
from entropy_execution.mini_qmt_driver import MiniQmtPhysicalDriver
from entropy_execution.physical_broker_gateways import BinancePhysicalGateway, QmtPhysicalGateway


class TestPhysicalGatewayWiring(unittest.TestCase):

    def test_router_binds_physical_gateways(self) -> None:
        router = RealBrokerRouter(is_live_combat=True)
        qmt = QmtPhysicalGateway(MiniQmtPhysicalDriver())
        binance = BinancePhysicalGateway(BinanceLiveDriver())
        router.bind_physical_gateway(qmt)
        router.bind_physical_gateway(binance)
        self.assertIs(router.get_gateway(BrokerGatewayType.QMT_STOCK), qmt)
        self.assertIs(router.get_gateway(BrokerGatewayType.BINANCE_CRYPTO), binance)

    def test_unconnected_physical_gateway_rejects(self) -> None:
        router = RealBrokerRouter(is_live_combat=True)
        router.bind_physical_gateway(QmtPhysicalGateway(MiniQmtPhysicalDriver()))
        res = router.route_and_execute("600519.SH", True, 100, 1500.0)
        self.assertEqual(res.status, RealOrderStatus.REJECTED)
        self.assertEqual(res.executed_quantity, 0.0)
        self.assertFalse(res.is_live_combat)

    def test_router_rejects_when_not_ignited(self) -> None:
        router = RealBrokerRouter(is_live_combat=False)
        res = router.route_and_execute("BTCUSDT", True, 0.1, 50000.0)
        self.assertEqual(res.status, RealOrderStatus.REJECTED)
        self.assertIn("未点燃", res.rejection_reason)

    def test_qmt_lot_size_guard(self) -> None:
        gw = QmtPhysicalGateway(MiniQmtPhysicalDriver())
        gw.driver.is_connected = True
        req = RealOrderRequest(cl_ord_id="X", symbol="600519.SH", is_buy=True, quantity=150, price=1500.0)
        res = gw.submit_order(req)
        self.assertEqual(res.status, RealOrderStatus.REJECTED)
        self.assertIn("100", res.rejection_reason)

    def test_manager_ignores_masked_view_and_stays_disconnected(self) -> None:
        mgr = GatewayConnectionManager()
        results = mgr.initialize_gateways({
            "QMT_STOCK": {"is_configured": True, "masked_info": {"account_id": "88...66"}, "fields_count": 2},
        })
        self.assertNotIn("QMT", results)
        self.assertEqual(mgr.get_state("QMT"), ConnectionState.DISCONNECTED)
        self.assertFalse(results["CTP"])

    def test_manager_real_creds_without_sdk_stay_disconnected(self) -> None:
        mgr = GatewayConnectionManager()
        results = mgr.initialize_gateways({"QMT_STOCK": {"account_id": "88886666", "mini_qmt_path": "/nonexistent"}})
        self.assertFalse(results["QMT"])
        self.assertEqual(mgr.get_state("QMT"), ConnectionState.DISCONNECTED)

    def test_submitted_ack_is_not_recorded_as_rejected(self) -> None:
        """柜台已受理 ≠ 成交，也 ≠ 本地拒绝。"""
        import os
        from entropy_execution.real_money_service import (
            _NETWORK_WATCHDOG,
            bind_physical_gateways_to_router,
            get_real_money_orders,
            handle_real_money_order,
            handle_real_money_toggle,
        )

        class _AckGw(AbstractBrokerGateway):
            def __init__(self) -> None:
                super().__init__(BrokerGatewayType.BINANCE_CRYPTO)
                self.is_connected = True

            def connect(self, credentials: dict) -> bool:
                self.is_connected = True
                return True

            def disconnect(self) -> None:
                self.is_connected = False

            def submit_order(self, req: RealOrderRequest) -> RealOrderResponse:
                return RealOrderResponse(
                    cl_ord_id=req.cl_ord_id, broker_order_id="ACK1",
                    status=RealOrderStatus.SUBMITTED, executed_price=0.0,
                    executed_quantity=0.0, friction_cost=0.0,
                    rejection_reason="", is_live_combat=True,
                )

            def cancel_order(self, cl_ord_id: str) -> bool:
                return False

            def query_account(self) -> dict:
                return {}

        os.environ["TRINITY_LIVE_COMBAT_SAFETY_KEY"] = "unit-test-safety-key-0123456789"
        try:
            handle_real_money_toggle({"enabled": False})  # 动尺理由: 先熄火再绑受理桩，避免无密钥误点燃
            _NETWORK_WATCHDOG.restore_connection()
            bind_physical_gateways_to_router([_AckGw()])
            on = handle_real_money_toggle({
                "enabled": True,
                "safety_key": "unit-test-safety-key-0123456789",
            })
            self.assertTrue(on.get("success"))
            _NETWORK_WATCHDOG.restore_connection()
            clid = f"CL_SUBMITTED_ACK_{int(time.time() * 1000)}"
            res = handle_real_money_order({
                "symbol": "ADAUSDT", "action": "BUY", "quantity": 0.031,
                "price": 88.0, "market_price": 88.0, "cl_ord_id": clid,
            })
            self.assertEqual(res.get("status"), "SUBMITTED", msg=str(res))
            self.assertFalse(res.get("success"))
            self.assertEqual(res.get("executed_quantity"), 0.0)
            hist = get_real_money_orders(20)["orders"]
            row = next((r for r in hist if r.get("cl_ord_id") == clid), None)
            self.assertIsNotNone(row)
            self.assertEqual(row["status"], "SUBMITTED")
            self.assertNotEqual(row["status"], "REJECTED")
        finally:
            handle_real_money_toggle({"enabled": False})  # 动尺理由: finally 熄火并卸桩，防止真金开关泄漏
            bind_physical_gateways_to_router([
                BinancePhysicalGateway(BinanceLiveDriver()),
            ])
            os.environ.pop("TRINITY_LIVE_COMBAT_SAFETY_KEY", None)


if __name__ == "__main__":
    unittest.main()
