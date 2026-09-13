"""
tests/test_microstructure_alpha.py
==================================
单元测试：微观高频盘口 OFI 因子、冰山吸筹嗅探与主力资金穿透。
"""

import unittest
from truth_kernel.iceberg_detector import IcebergDetector, IcebergType
from truth_kernel.institutional_flow_tracker import InstitutionalFlowTracker, TickTradeItem
from truth_kernel.order_flow_imbalance import Level2DepthSnapshot, OrderFlowImbalanceEngine


class TestMicrostructureAlpha(unittest.TestCase):
    """测试微观盘口高频因子与资金流工厂"""

    def test_order_flow_imbalance_ofi(self) -> None:
        """测试 OFI 订单流不平衡冲量计算"""
        # 前一 Tick 盘口
        snap_t0 = Level2DepthSnapshot(
            symbol="600519.SH",
            timestamp=1600000000.0,
            bid_prices=[1550.0, 1549.0, 1548.0, 1547.0, 1546.0],
            bid_volumes=[100, 200, 300, 400, 500],
            ask_prices=[1551.0, 1552.0, 1553.0, 1554.0, 1555.0],
            ask_volumes=[150, 250, 350, 450, 550]
        )

        # 当前 Tick 盘口：买一价上升到 1551.0 (多头吃掉卖一)，挂单 800 手
        snap_t1 = Level2DepthSnapshot(
            symbol="600519.SH",
            timestamp=1600000001.0,
            bid_prices=[1551.0, 1550.0, 1549.0, 1548.0, 1547.0],
            bid_volumes=[800, 100, 200, 300, 400],
            ask_prices=[1552.0, 1553.0, 1554.0, 1555.0, 1556.0],
            ask_volumes=[120, 220, 320, 420, 520]
        )

        ofi_delta = OrderFlowImbalanceEngine.compute_ofi_delta(snap_t0, snap_t1)
        self.assertGreater(ofi_delta, 0)
        self.assertEqual(ofi_delta, 800.0)

        # 全量指标评估
        metrics = OrderFlowImbalanceEngine.evaluate_depth_flow(snap_t0, snap_t1)
        self.assertEqual(metrics.symbol, "600519.SH")
        self.assertEqual(metrics.next_tick_momentum, "UPWARD_PRESSURE")

    def test_iceberg_detector(self) -> None:
        """测试盘口冰山隐形挂单吸筹嗅探"""
        # 初始显式挂单 100 手，成交 1000 手后，盘口依然剩余 50 手 (说明有 950 手隐形补单)
        rep = IcebergDetector.inspect_price_level(
            symbol="002594.SZ",
            price_level=250.0,
            is_bid=True,
            initial_visible_vol=100,
            executed_trade_vol=1000,
            remaining_visible_vol=50
        )
        self.assertEqual(rep.detected_type, IcebergType.BUY_ACCUMULATION)
        self.assertEqual(rep.estimated_hidden_volume, 950)
        self.assertGreater(rep.confidence_score, 0.70)

        # 正常无冰山情况
        normal_rep = IcebergDetector.inspect_price_level(
            symbol="002594.SZ",
            price_level=250.0,
            is_bid=True,
            initial_visible_vol=100,
            executed_trade_vol=40,
            remaining_visible_vol=60
        )
        self.assertEqual(normal_rep.detected_type, IcebergType.NONE)
        self.assertEqual(normal_rep.estimated_hidden_volume, 0)

    def test_institutional_flow_tracker(self) -> None:
        """测试主力机构真金穿透与散户噪音切分"""
        trades = [
            # 特大单主动买入 (1550 * 1000 = 155万)
            TickTradeItem(price=1550.0, volume=1000, is_buyer_maker=False),
            # 大单主动买入 (1550 * 200 = 31万)
            TickTradeItem(price=1550.0, volume=200, is_buyer_maker=False),
            # 散户小单主动卖出 (1550 * 10 = 1.55万)
            TickTradeItem(price=1550.0, volume=10, is_buyer_maker=True),
        ]
        rep = InstitutionalFlowTracker.analyze_tick_trades("600519.SH", trades)
        self.assertGreater(rep.super_large_net_inflow, 1_000_000.0)
        self.assertGreater(rep.large_net_inflow, 300_000.0)
        self.assertLess(rep.retail_net_inflow, 0.0)
        self.assertEqual(rep.signal_judgment, "ACCUMULATION")


if __name__ == "__main__":
    unittest.main()
