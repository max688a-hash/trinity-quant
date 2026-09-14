"""
期货日K必须来自公开连续合约；多空信号必须用放量+持仓，禁止均线金叉冒充进场。
# ref: AGENTS.md 第1/10/33/38条；新浪 InnerFuturesNewService.getDailyKLine
"""

from __future__ import annotations

import os
import unittest


class TestFuturesKlineSignals(unittest.TestCase):
    """专业用户在分形K线与纸上工单上要看到可证伪的多空，不是金叉玩具。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _src(self, rel: str) -> str:
        with open(os.path.join(self.root, rel), encoding="utf-8") as fp:
            return fp.read()

    def test_frontend_must_not_use_ma_cross_as_entry(self) -> None:
        sig = self._src("web/src/lib/klineSignals.ts")
        self.assertIn("calculateDynamicSignals", sig)
        self.assertNotIn("均线金叉", sig)
        self.assertIn("type: 'BUY'", sig)
        self.assertIn("type: 'SELL'", sig)
        self.assertIn("做多", sig)
        self.assertIn("做空", sig)
        paper = self._src("web/src/pages/PaperPage.tsx")
        self.assertIn("fetchKline", paper)
        self.assertIn("系统信号", paper)
        chart = self._src("web/src/components/KlineChart.tsx")
        self.assertNotIn("均线金叉是真实K线上的动量标注", chart)
        self.assertIn("放量", chart)
        self.assertIn("klineSignalList", chart)
        self.assertIn("listedKlineSignals", chart)
        self.assertIn("paintKline", chart)
        self.assertIn("setCandles([])", chart)

    def test_kline_must_paint_real_ma_and_volume_not_dummy_switches(self) -> None:
        draw = self._src("web/src/lib/klineCanvasDraw.ts")
        self.assertIn("ma5", draw)
        self.assertIn("ma10", draw)
        self.assertIn("ma20", draw)
        self.assertIn("ma60", draw)
        self.assertIn("volume", draw)
        self.assertIn("overlays", draw)
        self.assertNotIn("均线金叉", draw)
        chart = self._src("web/src/components/KlineChart.tsx")
        self.assertNotIn("defaultChecked", chart)
        self.assertIn("setMa5", chart)
        self.assertIn("overlays", chart)
        sig = self._src("web/src/lib/klineSignals.ts")
        self.assertIn("ma10:", sig)
        self.assertIn("ma60:", sig)
        types = self._src("web/src/lib/types.ts")
        self.assertIn("ma10?:", types)
        self.assertIn("ma60?:", types)

    def test_breakout_engine_requires_volume_and_rejects_oi_fade(self) -> None:
        from gravity_brain.kline_breakout_signals import attach_breakout_signals

        bars = []
        for i in range(24):
            px = 100.0 + i
            bars.append({
                "date": f"d{i}",
                "open": px,
                "high": px + 1.0,
                "low": px - 1.0,
                "close": px,
                "volume": 1000.0,
                "hold": 5000.0 + i,
            })
        fade = list(bars)
        fade[-1]["close"] = 200.0
        fade[-1]["high"] = 201.0
        fade[-1]["volume"] = 5000.0
        fade[-1]["hold"] = 100.0
        attach_breakout_signals(fade, allow_short=True)
        self.assertIsNone(fade[-1].get("signal"))

        boom = list(bars)
        boom[-1]["close"] = 200.0
        boom[-1]["high"] = 201.0
        boom[-1]["volume"] = 5000.0
        boom[-1]["hold"] = 9000.0
        attach_breakout_signals(boom, allow_short=True)
        sig = boom[-1].get("signal")
        self.assertIsNotNone(sig)
        assert sig is not None
        self.assertEqual(sig["type"], "BUY")
        self.assertIn("做多", sig["text"])
        self.assertIn("#e11d48", sig["color"])

    def test_sa_daily_kline_is_live_or_unavailable(self) -> None:
        from truth_kernel.historical_kline_service import HistoricalKlineService
        from entropy_execution.battlefield_api_service import handle_get_kline

        bars = HistoricalKlineService.get_kline("SA", timeframe="D", count=60)
        self.assertGreater(
            len(bars), 20,
            "SA 连续日K公开源已通，空数组就是没接线",
        )
        last = bars[-1]
        self.assertGreater(float(last["close"]), 0.0)
        self.assertGreater(float(last["volume"]), 0.0)
        self.assertGreater(float(last.get("hold") or 0.0), 0.0)
        self.assertNotAlmostEqual(float(last["volume"]), float(last["hold"]))
        payload = handle_get_kline("SA", "D")
        self.assertGreater(int(payload["count"]), 20)
        texts = [
            str((row.get("signal") or {}).get("text") or "")
            for row in payload["candles"]
        ]
        self.assertNotIn("均线金叉", "".join(texts))
        self.assertTrue(
            any(("做多" in t) or ("做空" in t) for t in texts),
            msg="60根真实日K上至少应有一根放量突破多空标注",
        )

    def test_sa_intraday_stays_empty_until_source_exists(self) -> None:
        from entropy_execution.battlefield_api_service import handle_get_kline

        payload = handle_get_kline("SA", "5M")
        self.assertEqual(int(payload["count"]), 0)
        self.assertEqual(payload.get("candles") or [], [])

if __name__ == "__main__":
    unittest.main()
