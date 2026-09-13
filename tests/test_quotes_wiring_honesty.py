"""
公开行情接得上就必须接；接不上才标 DATA_UNAVAILABLE。
禁止把三项缺陷当遗留挂着：BTC 空 tick、Z 滑条死基准、K 线金叉冒充入池。
# ref: AGENTS.md 第 28 / 33 条
"""

from __future__ import annotations

import os
import unittest


class TestQuotesWiringHonesty(unittest.TestCase):
    """能接的公开源必须接线；未知标的不得借茅台或写死 ATR。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _src(self, rel: str) -> str:
        with open(os.path.join(self.root, rel), encoding="utf-8") as fp:
            return fp.read()

    def test_tick_adapter_must_wire_binance_public_ticker(self) -> None:
        src = self._src("truth_kernel/realtime_feed_adapter.py")
        self.assertIn("api.binance.com", src)
        from truth_kernel.realtime_feed_adapter import RealtimeFeedAdapter

        tick = RealtimeFeedAdapter().get_tick("BTCUSDT")
        self.assertNotEqual(tick.price, 64800.0)
        if tick.price > 0.0:
            self.assertIn("BINANCE", tick.source.upper())
            self.assertGreater(tick.price, 1000.0)
        else:
            self.assertEqual(tick.source, "DATA_UNAVAILABLE")

    def test_multiasset_must_read_quotes_api(self) -> None:
        page = self._src("web/src/pages/MultiAssetPage.tsx")
        self.assertIn("fetchBoardQuotes", page)
        self.assertIn("fetchKline", page)
        self.assertIn("BTCUSDT", page)
        self.assertIn("DATA_UNAVAILABLE", page)
        self.assertNotIn("asset?.base ?? 2400", page)
        self.assertNotIn("22.5", page)
        self.assertNotIn(".base ??", page)

    def test_kline_ma_cross_is_overlay_not_admission(self) -> None:
        chart = self._src("web/src/components/KlineChart.tsx")
        self.assertIn("不是入池", chart)
        self.assertIn("loadRealKlineData", chart)
        paper = self._src("web/src/pages/PaperPage.tsx")
        self.assertNotIn("calculateDynamicSignals", paper)

    def test_btc_kline_must_not_borrow_moutai(self) -> None:
        from truth_kernel.historical_kline_service import HistoricalKlineService

        moutai_last = float(HistoricalKlineService._REAL_MOUTAI_DAILY[-1]["close"])
        bars = HistoricalKlineService.get_kline("BTCUSDT", timeframe="D", count=30)
        if bars:
            last = float(bars[-1]["close"])
            self.assertNotEqual(last, moutai_last)
            self.assertGreater(last, 1000.0)
        else:
            self.assertEqual(bars, [])
        nope = HistoricalKlineService.get_kline("NOPE.SH", timeframe="D", count=10)
        self.assertEqual(nope, [])
        closes = HistoricalKlineService.get_recent_closes("NOPE.SH", window=30)
        self.assertEqual(closes, [])


if __name__ == "__main__":
    unittest.main()
