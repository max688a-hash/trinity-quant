"""
tests/test_real_money_execution.py
==================================
TRINITY QUANT 真实真金级实盘交易全套系统单元测试。
严格遵守最高宪法立宪铁律：真实边界数值校验，绝无伪 Mock，单文件不超过 300 行。
"""

import os
import shutil
import tempfile
import time
import unittest

from entropy_execution.algorithmic_order_slicer import (
    ChildOrderSlice,
    IcebergOrderSlicer,
    MarketImpactModel,
    SlicerAlgorithm,
    TWAPOrderSlicer,
)
from entropy_execution.broker_gateway_adapter import (
    BrokerGatewayType,
    CTPFuturesGateway,
    CryptoBinanceGateway,
    QMTStockGateway,
    RealBrokerRouter,
    RealOrderRequest,
    RealOrderStatus,
)
from entropy_execution.real_money_risk_gateway import (
    PreTradeRiskResult,
    RealMoneyRiskGateway,
    RiskVerdict,
)
from entropy_execution.real_order_ledger import RealOrderLedger


class TestRealMoneyRiskGateway(unittest.TestCase):
    """真金实战事前硬风控网关测试"""

    def setUp(self) -> None:
        self.gw = RealMoneyRiskGateway(
            max_single_notional=500_000.0,
            max_price_deviation_pct=0.02,
            max_concentration_ratio=0.20,
            daily_loss_circuit_breaker_pct=0.02,
            max_orders_per_sec=5,
            max_cancels_per_day=400
        )
        self.gw.set_day_start_equity(10_000_000.0)

    def test_pre_trade_pass(self) -> None:
        res = self.gw.check_pre_trade_risk(
            symbol="600519.SH", is_buy=True, quantity=100.0,
            order_price=1550.0, market_price=1550.0,
            current_position_value=0.0, account_total_equity=10_000_000.0
        )
        self.assertTrue(res.is_allowed)
        self.assertEqual(res.verdict, RiskVerdict.PASS)
        self.assertFalse(res.kill_switch_active)

    def test_fat_finger_rejection(self) -> None:
        # 偏离最新市价 > 2.0%
        res = self.gw.check_pre_trade_risk(
            symbol="600519.SH", is_buy=True, quantity=100.0,
            order_price=1600.0, market_price=1550.0,  # 偏离 3.2%
            current_position_value=0.0, account_total_equity=10_000_000.0
        )
        self.assertFalse(res.is_allowed)
        self.assertEqual(res.verdict, RiskVerdict.REJECT_FAT_FINGER)

    def test_notional_limit_rejection(self) -> None:
        # 单笔委托 > 500,000 元
        res = self.gw.check_pre_trade_risk(
            symbol="600519.SH", is_buy=True, quantity=400.0,
            order_price=1550.0, market_price=1550.0,  # 620,000 元
            current_position_value=0.0, account_total_equity=10_000_000.0
        )
        self.assertFalse(res.is_allowed)
        self.assertEqual(res.verdict, RiskVerdict.REJECT_NOTIONAL_LIMIT)

    def test_concentration_rejection(self) -> None:
        # 单标的持仓超过 20%
        res = self.gw.check_pre_trade_risk(
            symbol="600519.SH", is_buy=True, quantity=200.0,
            order_price=1550.0, market_price=1550.0,  # 310,000 元
            current_position_value=1_800_000.0, account_total_equity=10_000_000.0  # 合计 21.1%
        )
        self.assertFalse(res.is_allowed)
        self.assertEqual(res.verdict, RiskVerdict.REJECT_CONCENTRATION)

    def test_self_trade_rejection(self) -> None:
        # 存在未结卖单时挂买单
        self.gw.register_active_order("600519.SH", is_buy=False, qty=100.0, px=1550.0)
        res = self.gw.check_pre_trade_risk(
            symbol="600519.SH", is_buy=True, quantity=100.0,
            order_price=1550.0, market_price=1550.0,
            current_position_value=0.0, account_total_equity=10_000_000.0
        )
        self.assertFalse(res.is_allowed)
        self.assertEqual(res.verdict, RiskVerdict.REJECT_SELF_TRADE)

    def test_daily_loss_circuit_breaker(self) -> None:
        # 日亏达到 2.0% 触发硬件级拔插头
        self.gw.update_equity(9_790_000.0)  # 亏损 2.1%
        self.assertTrue(self.gw.is_kill_switch_active)

        # 尝试发单应被绝对熔断锁定
        res = self.gw.check_pre_trade_risk(
            symbol="600519.SH", is_buy=True, quantity=100.0,
            order_price=1550.0, market_price=1550.0,
            current_position_value=0.0, account_total_equity=9_790_000.0
        )
        self.assertFalse(res.is_allowed)
        self.assertEqual(res.verdict, RiskVerdict.EMERGENCY_LOCKDOWN)

        # 管理员密码解锁
        self.assertTrue(self.gw.unlock_emergency_kill_switch("TRINITY_MASTER_OVERRIDE_SAFETY_KEY_2026"))
        self.assertFalse(self.gw.is_kill_switch_active)


class TestBrokerGateways(unittest.TestCase):
    """实盘交易网关与智能路由测试"""

    def test_qmt_stock_gateway(self) -> None:
        gw = QMTStockGateway()
        self.assertFalse(gw.connect({}))
        req = RealOrderRequest("ORD_QMT_1", "600519.SH", is_buy=False, quantity=100.0, price=1550.0)
        resp = gw.submit_order(req)
        self.assertEqual(resp.status, RealOrderStatus.REJECTED)
        self.assertEqual(resp.executed_quantity, 0.0)
        self.assertIn("会话", resp.rejection_reason)

    def test_ctp_futures_gateway(self) -> None:
        gw = CTPFuturesGateway()
        self.assertFalse(gw.connect({}))
        req = RealOrderRequest("ORD_CTP_1", "SA2409", is_buy=True, quantity=10.0, price=1800.0)
        resp = gw.submit_order(req)
        self.assertEqual(resp.status, RealOrderStatus.REJECTED)
        self.assertEqual(resp.friction_cost, 0.0)

    def test_binance_crypto_gateway(self) -> None:
        gw = CryptoBinanceGateway()
        self.assertFalse(gw.connect({}))
        req = RealOrderRequest("ORD_BIN_1", "BTCUSDT", is_buy=True, quantity=0.5, price=65000.0)
        resp = gw.submit_order(req)
        self.assertEqual(resp.status, RealOrderStatus.REJECTED)
        self.assertEqual(resp.executed_quantity, 0.0)

    def test_real_broker_router(self) -> None:
        router = RealBrokerRouter(is_live_combat=True)
        self.assertEqual(router.resolve_gateway_type("600519.SH"), BrokerGatewayType.QMT_STOCK)
        self.assertEqual(router.resolve_gateway_type("000001.SZ"), BrokerGatewayType.QMT_STOCK)
        self.assertEqual(router.resolve_gateway_type("BTCUSDT"), BrokerGatewayType.BINANCE_CRYPTO)
        self.assertEqual(router.resolve_gateway_type("ETHUSDT"), BrokerGatewayType.BINANCE_CRYPTO)
        self.assertEqual(router.resolve_gateway_type("SA2409"), BrokerGatewayType.CTP_FUTURES)

        resp = router.route_and_execute("600519.SH", is_buy=True, quantity=100.0, price=1550.0)
        self.assertEqual(resp.status, RealOrderStatus.REJECTED)
        self.assertFalse(resp.is_live_combat)


class TestAlgorithmicOrderSlicer(unittest.TestCase):
    """TWAP 与冰山算法拆单测试"""

    def test_market_impact_model(self) -> None:
        model = MarketImpactModel()
        est_small = model.estimate_impact("600519.SH", notional=20_000.0)
        self.assertEqual(est_small.recommended_algo, SlicerAlgorithm.DIRECT)
        self.assertEqual(est_small.recommended_slices, 1)

        est_mid = model.estimate_impact("600519.SH", notional=200_000.0)
        self.assertEqual(est_mid.recommended_algo, SlicerAlgorithm.ICEBERG)
        self.assertGreater(est_mid.recommended_slices, 1)

        est_large = model.estimate_impact("600519.SH", notional=1_000_000.0)
        self.assertEqual(est_large.recommended_algo, SlicerAlgorithm.TWAP)
        self.assertGreaterEqual(est_large.recommended_slices, 5)

    def test_twap_slicer(self) -> None:
        slicer = TWAPOrderSlicer()
        slices = slicer.slice_order("600519.SH", is_buy=True, total_quantity=500.0, base_price=1550.0)
        self.assertGreater(len(slices), 1)
        tot = sum(s.quantity for s in slices)
        self.assertEqual(tot, 500.0)
        for s in slices:
            self.assertGreater(s.quantity, 0)
            self.assertLessEqual(s.price_limit, 1550.0 * 1.01)

    def test_iceberg_slicer(self) -> None:
        slicer = IcebergOrderSlicer(visible_ratio=0.20)
        slices = slicer.slice_order("600519.SH", is_buy=True, total_quantity=1000.0, price=1550.0)
        self.assertGreater(len(slices), 1)
        # 第一笔应显式露出
        self.assertTrue(slices[0].is_visible)
        self.assertEqual(slices[0].quantity, 200.0)
        # 后续暗池隐藏
        self.assertFalse(slices[1].is_visible)


class TestRealOrderLedger(unittest.TestCase):
    """真实订单事务型 WAL 账本测试"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_ledger.db")
        self.ledger = RealOrderLedger(db_path=self.db_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_order_lifecycle_and_reconciliation(self) -> None:
        # 1. 提交新订单 (幂等测试)
        self.assertTrue(self.ledger.record_order_submitted("CL_001", "600519.SH", is_buy=True, quantity=100.0, price=1550.0))
        self.assertFalse(self.ledger.record_order_submitted("CL_001", "600519.SH", is_buy=True, quantity=100.0, price=1550.0))

        # 2. 模拟真实成交回报
        self.ledger.record_order_filled("CL_001", "BK_999", 1550.0, 100.0, friction_cost=35.0)

        # 3. 检查持仓与历史
        hist = self.ledger.get_order_history(10)
        self.assertEqual(len(hist), 1)
        self.assertEqual(hist[0]["status"], "FILLED")

        pos = self.ledger.get_positions()
        self.assertIn("600519.SH", pos)
        self.assertEqual(pos["600519.SH"]["quantity"], 100.0)
        self.assertEqual(pos["600519.SH"]["shares_frozen_t1"], 100.0)

        # 4. 券商核对对齐: 正常匹配
        matched, mismatches = self.ledger.reconcile_positions({"600519.SH": 100.0})
        self.assertTrue(matched)
        self.assertEqual(len(mismatches), 0)

        # 5. 券商核对对齐: 账实不符
        matched_err, mismatches_err = self.ledger.reconcile_positions({"600519.SH": 80.0})
        self.assertFalse(matched_err)
        self.assertEqual(len(mismatches_err), 1)


if __name__ == "__main__":
    unittest.main()
