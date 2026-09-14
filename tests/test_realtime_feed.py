"""
tests/test_realtime_feed.py
===========================
实时行情统一适配器真实性与防伪造测试套件。
严格遵循最高开发宪法第 33 条 (绝对真值数据锚定与反伪造心跳):
1. 真实行情离线或不存在时，必须诚实返回 DATA_UNAVAILABLE (price=0.0)，严禁伪造价格；
2. 严禁生产适配器依赖微观高斯布朗合成器；
3. 休市与无新成交时价格必须保持物理绝对恒定 (零随机伪跳动)；
4. 单文件严格不超过 300 行，零伪 Mock。
"""

import concurrent.futures
import unittest
from truth_kernel.realtime_feed_adapter import (
    RealtimeFeedAdapter,
    MarketTick
)


class TestRealtimeFeedAdapter(unittest.TestCase):
    """实时高频行情适配器真值与防伪测试套件"""

    def setUp(self) -> None:
        self.adapter = RealtimeFeedAdapter()

    def test_unknown_or_offline_symbol_returns_data_unavailable(self) -> None:
        """测试未知或离线标的必须返回 DATA_UNAVAILABLE，严禁伪造底价与假收盘"""
        tick = self.adapter.get_tick("NOPE.SH")
        self.assertIsInstance(tick, MarketTick)
        self.assertEqual(tick.price, 0.0, "违宪：离线/未知标的伪造了非零价格！")
        self.assertEqual(tick.source, "DATA_UNAVAILABLE", "违宪：离线标的未标定 DATA_UNAVAILABLE！")
        self.assertFalse(tick.is_live)
        self.assertNotIn("REAL_LAST_CLOSE_FROZEN", tick.source, "违宪：未获取行情却谎报真实收盘已冻结！")
        self.assertNotIn("MICRO_TICK_SYNTHESIZER", tick.source, "违宪：生产适配器调用了伪造合成器！")

    def test_adapter_has_no_synthesizer_dependency(self) -> None:
        """测试生产行情适配器绝不搭载微观布朗合成器"""
        self.assertFalse(
            hasattr(self.adapter, "synthesizer"),
            "违宪：RealtimeFeedAdapter 仍搭载了伪造合成器实例！"
        )

    def test_zero_random_jitter_deterministic(self) -> None:
        """测试连续查询行情在休市或无成交时绝对恒定（零随机漂移）"""
        sym = "600519.SH"
        t1 = self.adapter.get_tick(sym)
        t2 = self.adapter.get_tick(sym)
        self.assertEqual(t1.price, t2.price, "违宪：无成交时价格发生随机变动！")
        self.assertEqual(t1.volume, t2.volume, "违宪：无成交时成交量发生漂移！")
        self.assertEqual(t1.source, t2.source)

    def test_batch_query_physical_integrity(self) -> None:
        """测试批量查询物理返回完整性"""
        symbols = ["600519.SH", "600900.SH", "SA", "BTCUSDT"]
        batch = self.adapter.get_batch_ticks(symbols)
        self.assertEqual(len(batch), len(symbols))
        for t in batch:
            self.assertIn(t.symbol, symbols)
            self.assertIn(
                t.source,
                (
                    "DATA_UNAVAILABLE",
                    "REAL_LAST_CLOSE_FROZEN",
                    "SINA_LIVE_FEED",
                    "SINA_FUTURES_LIVE",
                    "SINA_FX_LIVE",
                    "CACHE_STATIC_WAITING_TRADE",
                    "BINANCE_PUBLIC_TICKER",
                ),
            )
            self.assertNotEqual(t.source, "MICRO_TICK_SYNTHESIZER")

    def test_concurrent_multithread_access(self) -> None:
        """测试多线程并发请求安全性与无死锁"""
        def _fetch(sym: str) -> float:
            return self.adapter.get_tick(sym).price

        symbols = ["600519.SH", "600900.SH", "002594.SZ", "SA", "AU", "BTCUSDT"] * 10
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            prices = list(executor.map(_fetch, symbols))

        self.assertEqual(len(prices), 60)
        self.assertTrue(all(p >= 0.0 for p in prices))


if __name__ == "__main__":
    unittest.main()

