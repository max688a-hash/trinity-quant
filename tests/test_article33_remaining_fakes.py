"""
第 33 / 26 / 34 条剩余假货回归：合成器、休市偷跑、默 1550、盲吞异常、隐藏页签。
# ref: AGENTS.md 第 26 / 33 / 34 / 37 条
"""

from __future__ import annotations

import os
import unittest


class TestArticle33RemainingFakes(unittest.TestCase):
    """发现即修复：生产路径不得再留反重力假货。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _src(self, rel: str) -> str:
        with open(os.path.join(self.root, rel), encoding="utf-8") as fp:
            return fp.read()

    def test_production_feed_must_not_ship_synthesizer(self) -> None:
        import truth_kernel.realtime_feed_adapter as feed

        self.assertFalse(
            hasattr(feed, "MarketMicroTickSynthesizer"),
            "生产行情模块仍导出高斯合成器",
        )
        src = self._src("truth_kernel/realtime_feed_adapter.py")
        self.assertNotIn("random.gauss", src)
        self.assertNotIn("MICRO_TICK_SYNTHESIZER", src)
        self.assertNotIn("allow_sim_on_closed", src)

    def test_sina_failures_must_be_logged(self) -> None:
        src = self._src("truth_kernel/realtime_feed_adapter.py")
        self.assertNotIn("except Exception:\n                return None", src)
        self.assertIn("_LOG", src)

    def test_closed_ashare_without_replay_is_rejected(self) -> None:
        from entropy_execution.paper_trade_gate import evaluate_paper_ticket
        from truth_kernel.market_session_clock import MarketSessionClock

        admitted, _, _, _, _, _ = evaluate_paper_ticket(
            {
                "symbol": "600519.SH",
                "action": "BUY",
                "quantity": 100,
                "price": 1275.16,
                "is_replay_mode": True,
            }
        )
        if not admitted:
            self.skipTest("茅台未准入，无法单独打休市门")
        clock = MarketSessionClock.evaluate_symbol("600519.SH")
        if clock.is_open:
            self.skipTest("A 股开市中")
        ok, reason, _, _, _, _ = evaluate_paper_ticket(
            {
                "symbol": "600519.SH",
                "action": "BUY",
                "quantity": 100,
                "price": 1275.16,
                "is_replay_mode": False,
            }
        )
        self.assertFalse(ok)
        self.assertIn("休市", reason)

    def test_real_money_missing_price_is_not_1550(self) -> None:
        from entropy_execution.real_money_service import handle_real_money_order

        res = handle_real_money_order(
            {"symbol": "600519.SH", "action": "BUY", "quantity": 100}
        )
        self.assertFalse(res.get("success"))
        blob = " ".join(str(res.get(k) or "") for k in ("reason", "rejection_reason", "message", "verdict"))
        self.assertIn("DATA_UNAVAILABLE", blob)

    def test_health_latency_is_not_hardcoded_35(self) -> None:
        src = self._src("entropy_execution/http_api_dispatcher.py")
        self.assertNotIn('"latency_ms": 35.0', src)
        self.assertNotIn("latency_ms\": 35.0", src)

    def test_hidden_tabs_must_not_mount_screener_autopsy(self) -> None:
        app = self._src("web/src/App.tsx")
        self.assertIn('{tab === "tab-screener" ? <ScreenerPage /> : null}', app)
        self.assertIn('{tab === "tab-autopsy" ? <AutopsyPanel /> : null}', app)
        self.assertNotIn('<ScreenerPage />\n          </div>', app)

    def test_paper_replay_requires_explicit_checkbox(self) -> None:
        page = self._src("web/src/pages/PaperPage.tsx")
        self.assertNotIn("is_replay_mode: true", page)
        self.assertIn('id="paper-replay"', page)
        self.assertIn("历史回放", page)

    def test_old_dashboard_must_not_advertise_brownian_ticks(self) -> None:
        html = self._src("trinity_dashboard.html")
        self.assertNotIn("高保真微观布朗流", html)

    def test_pipeline_must_not_default_linear_fake_kline(self) -> None:
        src = self._src("entropy_execution/http_api_dispatcher.py")
        self.assertNotIn("[100.0 + i for i in range(25)]", src)
        self.assertNotIn("[120.0 + i for i in range(12)]", src)

    def test_shadow_tick_must_not_fill_minutes_with_daily(self) -> None:
        src = self._src("entropy_execution/autonomous_learning_sandbox.py")
        self.assertNotIn("macro[:12]", src)

    def test_buy_fill_hud_must_be_rose_not_emerald(self) -> None:
        src = self._src("entropy_execution/live_pipeline_orchestrator.py")
        self.assertNotIn('alert_color="emerald-pulse" if rcpt.is_success', src)
        self.assertIn("rose-pulse", src)


if __name__ == "__main__":
    unittest.main()
