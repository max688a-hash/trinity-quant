"""
tests/test_physical_gateway_wiring.py
=====================================
真金路由器与物理驱动接线：无会话拒单、未点燃拒单、受理≠成交。
"""

import unittest

from entropy_execution.binance_live_driver import BinanceLiveDriver
from entropy_execution.broker_gateway_adapter import (
    BrokerGatewayType,
    RealBrokerRouter,
    RealOrderRequest,
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


if __name__ == "__main__":
    unittest.main()
