"""
tests/test_multi_asset_regime.py
================================
TRINITY QUANT 全资产分类、自适应波动空间与临界状态探测器测试套件。

严格验证：
1. 全资产规范（A股/港股/美股/期货）的微观制度解析
2. 消除绝对点数陷阱（玉米25点 vs 纯碱 vs 白银）的波动率归一化
3. 临界破位与状态机突变器对“逆势摸顶抄底”的一票否决
4. 大宗商品现货基差、升贴水结构与展期流血惩罚
5. 多市场全保真摩擦成本（印花税、佣金门槛、滑点与保证金）
"""

import unittest
from truth_kernel.asset_taxonomy import (
    AssetClass,
    CommissionType,
    InstrumentSpecification,
    MarketVenue,
    SettlementType,
    TaxonomyRegistry,
)
from gravity_brain.volatility_normalizer import (
    VolatilityNormalizer,
    VolatilityMetrics,
)
from immune_system.regime_detector import (
    MarketRegime,
    ProposedAction,
    RegimeBreakoutDetector,
)
from gravity_brain.commodity_basis_truth import (
    CommodityBasisEngine,
    TermStructureRegime,
)
from entropy_execution.multi_market_friction import (
    MultiMarketFrictionEngine,
)


class TestAssetTaxonomy(unittest.TestCase):
    """测试多资产分类与规范解析"""

    def test_pre_registered_specifications(self) -> None:
        corn = TaxonomyRegistry.get("C")
        self.assertEqual(corn.asset_class, AssetClass.COMMODITY_FUTURE)
        self.assertEqual(corn.contract_multiplier, 10.0)
        self.assertEqual(corn.commission_type, CommissionType.PER_CONTRACT)
        self.assertFalse(corn.allow_retail_delivery)

        soda = TaxonomyRegistry.get("SA")
        self.assertEqual(soda.contract_multiplier, 20.0)
        self.assertEqual(soda.price_tick, 1.0)

        moutai = TaxonomyRegistry.get("600519.SH")
        self.assertEqual(moutai.venue, MarketVenue.CN_EQUITY)
        self.assertEqual(moutai.settlement, SettlementType.T_PLUS_1)
        self.assertEqual(moutai.stamp_duty_sell, 0.0005)
        self.assertEqual(moutai.stamp_duty_buy, 0.0)

        tencent = TaxonomyRegistry.get("0700.HK")
        self.assertEqual(tencent.venue, MarketVenue.HK_EQUITY)
        self.assertEqual(tencent.stamp_duty_buy, 0.0010)
        self.assertEqual(tencent.stamp_duty_sell, 0.0010)

    def test_prefix_matching_for_futures(self) -> None:
        spec_c = TaxonomyRegistry.get("C2409")
        self.assertEqual(spec_c.symbol, "C")
        spec_sa = TaxonomyRegistry.get("SA2501")
        self.assertEqual(spec_sa.symbol, "SA")

    def test_invalid_spec_validation(self) -> None:
        with self.assertRaises(ValueError):
            InstrumentSpecification(
                symbol="ERR",
                name="Error",
                asset_class=AssetClass.EQUITY,
                venue=MarketVenue.CN_EQUITY,
                settlement=SettlementType.T_PLUS_1,
                contract_multiplier=0.0,  # 非法
                price_tick=1.0,
                lot_size=100,
                stamp_duty_buy=0.0,
                stamp_duty_sell=0.0,
                commission_rate=0.001,
                commission_type=CommissionType.PERCENTAGE,
                initial_margin_ratio=1.0
            )


class TestVolatilityNormalizer(unittest.TestCase):
    """测试自适应波动空间与无量纲归一化"""

    def setUp(self) -> None:
        self.normalizer = VolatilityNormalizer(window=20, band_multiplier=2.0)

    def test_corn_bounded_oscillation(self) -> None:
        # 模拟大连玉米围绕 2400 运行，日常振幅约 20~25 点
        closes = [
            2390.0, 2405.0, 2415.0, 2395.0, 2410.0,
            2420.0, 2400.0, 2385.0, 2410.0, 2415.0,
            2405.0, 2390.0, 2415.0, 2420.0, 2400.0,
            2395.0, 2410.0, 2415.0, 2405.0, 2408.0
        ]
        metrics = self.normalizer.compute("C", closes)
        self.assertTrue(metrics.is_within_normal_range)
        self.assertFalse(metrics.is_extreme_deviation)
        self.assertGreater(metrics.atr, 10.0)
        self.assertLess(metrics.atr, 35.0)

    def test_extreme_breakout_detection(self) -> None:
        # 模拟纯碱在 1800 运行，最后一根 K 线突然狂飙到 2100 (重大供需冲击)
        closes = [1800.0 + (i % 3) * 5.0 for i in range(19)]
        closes.append(2100.0)
        metrics = self.normalizer.compute("SA", closes)
        self.assertFalse(metrics.is_within_normal_range)
        self.assertTrue(metrics.is_extreme_deviation)
        self.assertGreater(metrics.z_score, 3.0)


class TestRegimeBreakoutDetector(unittest.TestCase):
    """测试状态机突变与逆势摸顶抄底一票否决"""

    def setUp(self) -> None:
        self.detector = RegimeBreakoutDetector(breakout_z_threshold=2.0, extreme_z_threshold=3.0)

    def test_veto_counter_trend_in_bull_breakout(self) -> None:
        # 处于多头突破态 (Z = 2.5)
        metrics = VolatilityMetrics(
            symbol="SA",
            current_price=2050.0,
            atr=40.0,
            atr_ratio=0.02,
            rolling_mean=1900.0,
            rolling_std=60.0,
            z_score=2.5,
            lower_band=1780.0,
            upper_band=2020.0
        )
        # 逆势摸顶做空：必须一票否决！
        result_short = self.detector.audit_order(metrics, ProposedAction.SELL_RALLY_MEAN_REVERT)
        self.assertFalse(result_short.is_permitted)
        self.assertIn("一票否决逆势摸顶做空", result_short.veto_reason or "")
        self.assertEqual(result_short.allowed_position_cap, 0.0)

        # 顺势做多：允许
        result_long = self.detector.audit_order(metrics, ProposedAction.BUY_LONG_TREND)
        self.assertTrue(result_long.is_permitted)
        self.assertEqual(result_long.allowed_position_cap, 0.60)

    def test_veto_counter_trend_in_bear_breakout(self) -> None:
        # 处于破位暴跌态 (Z = -2.6)
        metrics = VolatilityMetrics(
            symbol="C",
            current_price=2200.0,
            atr=25.0,
            atr_ratio=0.011,
            rolling_mean=2350.0,
            rolling_std=55.0,
            z_score=-2.7,
            lower_band=2240.0,
            upper_band=2460.0
        )
        # 逆势抄底做多：必须一票否决！
        result_dip = self.detector.audit_order(metrics, ProposedAction.BUY_DIP_MEAN_REVERT)
        self.assertFalse(result_dip.is_permitted)
        self.assertIn("一票否决逆势抄底做多", result_dip.veto_reason or "")

    def test_liquidity_dislocation_emergency_shutdown(self) -> None:
        # 极端跳空 8%
        metrics = VolatilityMetrics(
            symbol="AG",
            current_price=7000.0,
            atr=150.0,
            atr_ratio=0.021,
            rolling_mean=6900.0,
            rolling_std=50.0,
            z_score=2.0,
            lower_band=6800.0,
            upper_band=7000.0
        )
        result = self.detector.audit_order(metrics, ProposedAction.BUY_LONG_TREND, overnight_gap_ratio=0.08)
        self.assertEqual(result.regime, MarketRegime.LIQUIDITY_DISLOCATION)
        self.assertFalse(result.is_permitted)
        self.assertIn("触发全面熔断", result.veto_reason or "")


class TestCommodityBasisEngine(unittest.TestCase):
    """测试商品基差与期限结构"""

    def setUp(self) -> None:
        self.engine = CommodityBasisEngine(high_contango_drag_threshold=0.15)

    def test_backwardation_favorable_for_long(self) -> None:
        # 现货 2400, 主力 2300, 远月 2200 (Backwardation)
        metrics = self.engine.compute(
            symbol="C",
            spot_price=2400.0,
            near_price=2300.0,
            far_price=2200.0,
            days_between=60
        )
        self.assertEqual(metrics.structure, TermStructureRegime.BACKWARDATION)
        self.assertTrue(metrics.is_favorable_for_long)
        self.assertEqual(metrics.roll_drag_penalty, 0.0)

    def test_contango_roll_drag_penalty(self) -> None:
        # 现货 1800, 主力 2000, 远月 2200 (深度 Contango 远月升水流血)
        metrics = self.engine.compute(
            symbol="SA",
            spot_price=1800.0,
            near_price=2000.0,
            far_price=2200.0,
            days_between=60
        )
        self.assertEqual(metrics.structure, TermStructureRegime.CONTANGO)
        self.assertFalse(metrics.is_favorable_for_long)
        self.assertGreater(metrics.roll_drag_penalty, 0.20)


class TestMultiMarketFrictionEngine(unittest.TestCase):
    """测试跨市场摩擦成本精算"""

    def setUp(self) -> None:
        self.engine = MultiMarketFrictionEngine(default_slippage_ticks=1)

    def test_a_share_stamp_duty_asymmetry(self) -> None:
        # 茅台 100 股 @ 1500 元 = 150,000 元
        buy_res = self.engine.calculate_friction("600519.SH", 1500.0, 100, is_buy=True)
        sell_res = self.engine.calculate_friction("600519.SH", 1500.0, 100, is_buy=False)

        self.assertEqual(buy_res.stamp_duty, 0.0)
        self.assertAlmostEqual(sell_res.stamp_duty, 150000.0 * 0.0005, places=2)
        self.assertGreater(sell_res.total_friction, buy_res.total_friction)

    def test_hk_equity_dual_stamp_duty(self) -> None:
        # 腾讯 100 股 @ 380 港币 = 38,000 港币
        buy_res = self.engine.calculate_friction("0700.HK", 380.0, 100, is_buy=True)
        self.assertAlmostEqual(buy_res.stamp_duty, 38000.0 * 0.0010, places=2)
        self.assertEqual(buy_res.commission, 50.0)  # 50港币保底

    def test_future_multiplier_and_margin(self) -> None:
        # 玉米 10 手 @ 2400 元/吨 (每手10吨) -> 名义价值: 2400 * 10 * 10 = 240,000 元
        cost = self.engine.calculate_friction("C", 2400.0, 10, is_buy=True)
        self.assertEqual(cost.notional_value, 240000.0)
        self.assertEqual(cost.commission, 12.0)  # 1.20元/手 * 10手
        self.assertEqual(cost.margin_required, 240000.0 * 0.08)  # 8%保证金 = 19,200 元
        self.assertEqual(cost.slippage_cost, 1.0 * 10.0 * 10)  # 1跳 * 10吨 * 10手 = 100 元


if __name__ == "__main__":
    unittest.main()
