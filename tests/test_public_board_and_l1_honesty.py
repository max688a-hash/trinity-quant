"""
看板能接的公开源必须接；无买一量不得自称真实 L1 盘口。
# ref: AGENTS.md 第 33 / 38 条
"""

from __future__ import annotations

import os
import unittest


class TestPublicBoardAndL1Honesty(unittest.TestCase):
    """专业用户会把看板与微观流当成交依据，假 L1 与空看板即埋雷。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _src(self, rel: str) -> str:
        with open(os.path.join(self.root, rel), encoding="utf-8") as fp:
            return fp.read()

    def test_adapter_must_use_sina_continuous_and_fx_lists(self) -> None:
        src = self._src("truth_kernel/realtime_feed_adapter.py")
        self.assertIn("nf_SA0", src)
        self.assertIn("fx_susdcnh", src)
        self.assertIn("DINIW", src)
        self.assertNotIn("bid_vol1=10.0", src)
        self.assertNotIn("else 1000.0", src)

    def test_usdcnh_dxy_sa_quotes_are_live_or_unavailable(self) -> None:
        from truth_kernel.realtime_feed_adapter import RealtimeFeedAdapter
        from entropy_execution.board_quotes_service import handle_get_board_quotes

        adapter = RealtimeFeedAdapter()
        usdcnh = adapter.get_tick("USDCNH")
        self.assertNotAlmostEqual(usdcnh.price, 6.9, places=2)
        if usdcnh.price > 0.0:
            self.assertGreater(usdcnh.price, 5.0)
            self.assertLess(usdcnh.price, 10.0)
            blob = usdcnh.source.upper()
            self.assertTrue(
                any(token in blob for token in ("SINA", "FROZEN", "CACHE")),
                msg=f"USDCNH 有价却来源不明: {usdcnh.source}",
            )
            self.assertNotEqual(usdcnh.source, "DATA_UNAVAILABLE")
        else:
            self.assertEqual(usdcnh.source, "DATA_UNAVAILABLE")

        payload = handle_get_board_quotes("USDCNH,DXY,SA")
        by_sym = {row["symbol"]: row for row in payload["quotes"]}
        for sym in ("USDCNH", "DXY", "SA"):
            row = by_sym[sym]
            if not row.get("available"):
                self.assertIsNone(row.get("last"))
                self.assertEqual(row.get("status"), "DATA_UNAVAILABLE")
            else:
                self.assertGreater(float(row["last"]), 0.0)

    def test_microstructure_must_not_claim_l1_without_book(self) -> None:
        from entropy_execution.battlefield_api_service import handle_get_microstructure_flow

        dark = handle_get_microstructure_flow("NOPE.SH")
        self.assertEqual(dark["ofi"]["data_grade"], "DATA_UNAVAILABLE")
        self.assertNotIn("主力", dark["institutional_flow"]["signal_judgment"])

        btc = handle_get_microstructure_flow("BTCUSDT")
        self.assertNotEqual(btc["ofi"]["data_grade"], "REAL_EXCHANGE_L1")

        from truth_kernel.market_session_clock import MarketSessionClock

        sa = handle_get_microstructure_flow("SA")
        if not MarketSessionClock.evaluate_symbol("SA").is_open:
            self.assertNotEqual(sa["ofi"]["data_grade"], "REAL_EXCHANGE_L1")
            self.assertNotEqual(sa["institutional_flow"]["signal_judgment"], "主力温和吸筹")
            self.assertIn("休市", sa["institutional_flow"]["signal_judgment"])

    def test_gha_must_build_frontend(self) -> None:
        yml = self._src(".github/workflows/ci_quality_gate.yml")
        self.assertIn("npm run build", yml)
        self.assertIn("setup-node", yml)


if __name__ == "__main__":
    unittest.main()
