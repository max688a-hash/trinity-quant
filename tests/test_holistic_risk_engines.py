"""
tests/test_holistic_risk_engines.py
===================================
TRINITY QUANT 全维度深水区暗礁防御引擎测试套件。

严格检验：
1. 数据源实时探针、心跳停滞、脏数据过滤与无感秒级热切换 (DataProbeRouter)
2. 棉被企业去季节性 YoY 同比对齐与库存周期四阶段 (IndustryCycleEngine)
3. 涨跌停封死无法撮合物理阻断与 ADV 容量压制 (SignalSanityGate)
4. 危机时刻资产相关性坍塌与因子同质化踩踏熔断 (CrowdingMonitor)
"""

import unittest
from truth_kernel.data_probe_router import (
    DataProbeRouter,
    SourceStatus,
)
from truth_kernel.industry_cycle_engine import (
    IndustryCycleEngine,
    InventoryCyclePhase,
    MacroERPRegime,
)
from immune_system.signal_sanity_gate import (
    SignalSanityGate,
)
from immune_system.crowding_monitor import (
    CrowdingMonitor,
    CrowdingRegime,
)


class TestDataProbeRouter(unittest.TestCase):
    """测试数据源探针与热切换"""

    def setUp(self) -> None:
        self.router = DataProbeRouter(
            max_latency_ms=300.0,
            staleness_timeout_sec=2.0,
            spike_threshold_ratio=0.05
        )
        self.router.register_source("WIND_PRIMARY")
        self.router.register_source("EASTMONEY_BACKUP")

    def test_healthy_ingestion(self) -> None:
        frame = self.router.probe_and_ingest(
            source_name="WIND_PRIMARY",
            symbol="600519.SH",
            price=1500.0,
            volume=10000.0,
            quote_timestamp=100.0,
            rtt_latency_ms=25.0,
            system_time_now=100.5
        )
        self.assertIsNotNone(frame)
        self.assertEqual(frame.price, 1500.0)
        self.assertEqual(self.router.get_active_source(), "WIND_PRIMARY")

    def test_stale_data_triggers_failover(self) -> None:
        # 主源发生数据停滞 (当前时间 110.0，行情时间 100.0，超时 > 2s)
        stale_frame = self.router.probe_and_ingest(
            source_name="WIND_PRIMARY",
            symbol="600519.SH",
            price=1500.0,
            volume=10000.0,
            quote_timestamp=100.0,
            rtt_latency_ms=30.0,
            system_time_now=110.0
        )
        self.assertIsNone(stale_frame)

        # 备用源健康喂入
        backup_frame = self.router.probe_and_ingest(
            source_name="EASTMONEY_BACKUP",
            symbol="600519.SH",
            price=1500.0,
            volume=10000.0,
            quote_timestamp=110.0,
            rtt_latency_ms=45.0,
            system_time_now=110.1
        )
        self.assertIsNotNone(backup_frame)
        # 路由器应自动无感秒级切换到备用源
        self.assertEqual(self.router.get_active_source(), "EASTMONEY_BACKUP")

    def test_price_spike_corrupted_filter(self) -> None:
        # 先正常摄取 1500 元
        self.router.probe_and_ingest("WIND_PRIMARY", "600519.SH", 1500.0, 100.0, 100.0, 20.0, 100.1)
        # 突发推送错误数据 150.0 元 (少一位数，跌 90%)
        corrupt_frame = self.router.probe_and_ingest("WIND_PRIMARY", "600519.SH", 150.0, 100.0, 100.2, 20.0, 100.3)
        self.assertIsNone(corrupt_frame)


class TestIndustryCycleEngine(unittest.TestCase):
    """测试商业去季节性、宏观 ERP 与库存周期"""

    def test_cotton_quilt_seasonality_resolution(self) -> None:
        # 棉被企业：Q2(夏天)营收极低(2000万)，去年同期(1500万)；Q4(冬天)营收爆发(1亿)
        # 权重设置: [春 0.15, 夏 0.10, 秋 0.25, 冬 0.50]
        weights = [0.15, 0.10, 0.25, 0.50]
        report = IndustryCycleEngine.evaluate_seasonality(
            symbol="TEXTILE_01",
            current_quarter=2,  # 夏天
            current_rev=20.0,
            current_profit=-2.0,  # 夏天账面微亏
            prior_year_same_quarter_rev=15.0,
            prior_year_same_quarter_profit=-5.0,
            quarterly_weights=weights
        )
        # 验证同比增速为正 (20 vs 15 增长 33.3%)
        self.assertAlmostEqual(report.yoy_revenue_growth, 0.3333, places=3)
        # 验证去季节性归一化营收 = 20 / (4 * 0.10) = 50.0 亿元
        self.assertAlmostEqual(report.deseasonalized_revenue, 50.0, places=2)
        # 判定为淡季逆势突破
        self.assertTrue(report.is_counter_seasonal_breakthrough)

    def test_toxic_inventory_phase(self) -> None:
        # 营收同比下滑 -20%，存货同比激增 +40%
        metrics = IndustryCycleEngine.classify_inventory_cycle("SOLAR_01", -0.20, 0.40)
        self.assertEqual(metrics.phase, InventoryCyclePhase.PASSIVE_RESTOCKING)
        self.assertTrue(metrics.is_toxic_inventory_buildup)

    def test_macro_erp_valuation(self) -> None:
        # 大盘 PE = 12倍 (收益率 8.33%), 10年国债利率 2.3% -> ERP = 6.03% (极度便宜)
        erp, regime = IndustryCycleEngine.calculate_macro_erp(12.0, 0.023)
        self.assertGreater(erp, 0.055)
        self.assertEqual(regime, MacroERPRegime.EXTREME_CHEAP)


class TestSignalSanityGate(unittest.TestCase):
    """测试信号物理交叉核验门"""

    def setUp(self) -> None:
        self.gate = SignalSanityGate(
            max_adv_participation_rate=0.02,
            max_price_drift_ratio=0.015,
            max_quote_age_sec=3.0
        )

    def test_limit_down_locked_prohibits_fake_fills(self) -> None:
        # 跌停价 10.0 元，准备卖出 5000 股
        res = self.gate.verify_order(
            symbol="000001.SZ",
            is_buy=False,
            signal_price=10.0,
            current_market_price=10.0,
            proposed_quantity=5000,
            five_day_adv=1000000,
            limit_down_price=10.0
        )
        self.assertFalse(res.is_passed)
        self.assertTrue(res.is_limit_locked)
        self.assertIn("一字跌停封死", res.veto_reason or "")

    def test_adv_capacity_order_truncation(self) -> None:
        # 5日日均 1,000,000 股，2% 安全线为 20,000 股。若报单 50,000 股，自动压制至 20,000
        res = self.gate.verify_order(
            symbol="600519.SH",
            is_buy=True,
            signal_price=1500.0,
            current_market_price=1500.0,
            proposed_quantity=50000,
            five_day_adv=1000000
        )
        self.assertTrue(res.is_passed)
        self.assertEqual(res.adjusted_quantity, 20000.0)


class TestCrowdingMonitor(unittest.TestCase):
    """测试危机相关性坍塌与因子拥挤度"""

    def setUp(self) -> None:
        self.monitor = CrowdingMonitor(correlation_crisis_threshold=0.75, crowding_danger_score=80.0)

    def test_crisis_correlation_collapse_triggers_deleveraging(self) -> None:
        # 3个资产高度同涨同跌 (极端相关性接近 1.0)
        returns = [
            [-0.05, -0.04, -0.06, -0.03, -0.07],
            [-0.04, -0.05, -0.05, -0.02, -0.08],
            [-0.06, -0.04, -0.07, -0.03, -0.06]
        ]
        avg_corr = self.monitor.evaluate_correlation_collapse(returns)
        self.assertGreater(avg_corr, 0.75)

        report = self.monitor.audit_crowding(avg_corr, factor_turnover_heat=0.8, retail_sentiment_skew=0.7)
        self.assertEqual(report.regime, CrowdingRegime.CRITICAL_SQUEEZE)
        self.assertLessEqual(report.suggested_leverage_multiplier, 0.40)


if __name__ == "__main__":
    unittest.main()
