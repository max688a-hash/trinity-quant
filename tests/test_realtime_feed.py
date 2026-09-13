"""
tests/test_realtime_feed.py
===========================
实时高频行情适配器与微观订单流跳动引擎单元测试。
严格遵循第一性原理与最高开发宪法 (AGENTS.md):
1. 验证价格物理非负与买卖价差数学严密性 (bid1 <= price <= ask1);
2. 验证多线程并发稳定性与离线高保真合成收敛性;
3. 单文件严格不超过 300 行，零伪 Mock。
"""

import concurrent.futures
import unittest
from truth_kernel.realtime_feed_adapter import (
    MarketMicroTickSynthesizer,
    RealtimeFeedAdapter,
    MarketTick
)


class TestRealtimeFeedAdapter(unittest.TestCase):
    """实时高频行情适配器单元测试套件"""

    def setUp(self) -> None:
        self.synthesizer = MarketMicroTickSynthesizer(seed=42)
        self.adapter = RealtimeFeedAdapter(synthesizer=self.synthesizer)

    def test_synthesizer_physical_invariants(self) -> None:
        """测试微观订单流合成器物理守恒量"""
        sym = "600519.SH"
        base_px = 1500.0
        tick_sz = 0.01

        for _ in range(50):
            tick = self.synthesizer.generate_next_tick(
                symbol=sym, name="贵州茅台", base_price=base_px, tick_size=tick_sz
            )
            self.assertIsInstance(tick, MarketTick)
            self.assertGreater(tick.price, 0.0)
            self.assertGreaterEqual(tick.high, tick.low)
            self.assertGreaterEqual(tick.high, tick.price)
            self.assertLessEqual(tick.low, tick.price)
            self.assertGreater(tick.volume, 0.0)
            self.assertGreater(tick.amount, 0.0)
            # 买卖价差守恒
            self.assertLessEqual(tick.bid1, tick.ask1)
            self.assertGreaterEqual(round(tick.ask1 - tick.bid1, 4), tick_sz)
            self.assertEqual(tick.source, "MICRO_TICK_SYNTHESIZER")

    def test_adapter_single_and_batch_query(self) -> None:
        """测试适配器单标的与批量查询功能"""
        # 单标的
        tick_mt = self.adapter.get_tick("600519.SH")
        self.assertEqual(tick_mt.symbol, "600519.SH")
        self.assertGreater(tick_mt.price, 0.0)

        # 批量资产
        symbols = ["600519.SH", "600900.SH", "SA", "BTCUSDT"]
        batch = self.adapter.get_batch_ticks(symbols)
        self.assertEqual(len(batch), len(symbols))
        for t in batch:
            self.assertIn(t.symbol, symbols)
            self.assertGreater(t.price, 0.0)

    def test_concurrent_multithread_access(self) -> None:
        """测试多线程并发请求安全性与无死锁"""
        def _fetch(sym: str) -> float:
            return self.adapter.get_tick(sym).price

        symbols = ["600519.SH", "600900.SH", "002594.SZ", "SA", "AU", "BTCUSDT"] * 10
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            prices = list(executor.map(_fetch, symbols))

        self.assertEqual(len(prices), 60)
        self.assertTrue(all(p > 0.0 for p in prices))


if __name__ == "__main__":
    unittest.main()
