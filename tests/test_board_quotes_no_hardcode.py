"""
看板禁止硬编码上证假报价。
看板价必须来自 /api/market/quotes；缺 K 线必须 DATA_UNAVAILABLE。
乐视/康美不得因假报价变成可买。
# ref: AGENTS.md 第 33 条 无真实成交即零跳动
"""

from __future__ import annotations

import os
import unittest

from tests.ui_corpus import load_ui_corpus


_FAKE_BOARD_TOKENS = (
    "3,042.88",
    "3042.88",
    "2,280.45",
    "64,200",
    "上证 3,042",
    "BTC 64200",
    "茅台 1550",
)


class TestBoardQuotesNoHardcode(unittest.TestCase):
    """专业用户会把看板数字当成交价，写死点位即欺诈。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.ui = load_ui_corpus(cls.root)

    def test_web_src_must_not_hardcode_board_last_prices(self) -> None:
        for token in _FAKE_BOARD_TOKENS:
            self.assertNotIn(
                token,
                self.ui,
                f"看板/基准仍写死假报价 {token}，专业用户会当成交价去买",
            )

    def test_frontend_must_fetch_market_quotes_api(self) -> None:
        api_path = os.path.join(self.root, "web", "src", "lib", "api.ts")
        with open(api_path, encoding="utf-8") as fp:
            api_src = fp.read()
        self.assertIn("/api/market/quotes", api_src)
        self.assertIn("fetchBoardQuotes", api_src)
        with open(os.path.join(self.root, "main.py"), encoding="utf-8") as fp:
            main_src = fp.read()
        self.assertIn("/api/market/quotes", main_src)

    def test_empty_candles_block_quote_not_fallback_3042(self) -> None:
        from entropy_execution.board_quotes_service import quote_from_candles

        q = quote_from_candles("000001.SH", [])
        self.assertFalse(q["available"])
        self.assertIsNone(q["last"])
        self.assertEqual(q["status"], "DATA_UNAVAILABLE")
        self.assertNotEqual(q.get("last"), 3042.88)
        self.assertNotEqual(q.get("last"), 3042.0)

    def test_last_close_comes_from_owned_candles_only(self) -> None:
        from entropy_execution.board_quotes_service import quote_from_candles

        q = quote_from_candles(
            "000001.SH",
            [
                {"date": "2024-06-03", "close": 3010.0},
                {"date": "2024-06-04", "close": 3025.5},
            ],
        )
        self.assertTrue(q["available"])
        self.assertEqual(q["last"], 3025.5)
        self.assertAlmostEqual(float(q["change_pct"] or 0.0), (3025.5 - 3010.0) / 3010.0 * 100.0)

    def test_sse_must_not_borrow_moutai_history(self) -> None:
        from entropy_execution.board_quotes_service import fetch_owned_kline

        moutai = fetch_owned_kline("600519.SH")
        self.assertGreaterEqual(len(moutai), 10)
        sse = fetch_owned_kline("000001.SH")
        if sse:
            last_sse = float(sse[-1]["close"])
            last_mt = float(moutai[-1]["close"])
            self.assertNotEqual(
                last_sse,
                last_mt,
                "上证借用茅台收盘价冒充指数点位",
            )
        else:
            from entropy_execution.board_quotes_service import quote_from_candles

            blocked = quote_from_candles("000001.SH", sse)
            self.assertFalse(blocked["available"])

    def test_handler_missing_kline_does_not_invent_board_print(self) -> None:
        from entropy_execution.board_quotes_service import handle_get_board_quotes

        payload = handle_get_board_quotes("NHCI,DXY")
        self.assertIn("quotes", payload)
        for item in payload["quotes"]:
            if not item.get("available"):
                self.assertIsNone(item.get("last"))
                self.assertEqual(item.get("status"), "DATA_UNAVAILABLE")
            self.assertNotEqual(item.get("last"), 3042.88)
            self.assertNotEqual(item.get("last"), 2280.45)

    def test_letv_kangmei_remain_vetoed_despite_board_quotes(self) -> None:
        from tests.test_immune_system import TestImmuneSystem

        immune = TestImmuneSystem()
        immune.setUp()
        immune.test_case_letv_receivables_fraud()
        immune.test_case_kangmei_deposit_loan_paradox()
        from entropy_execution.board_quotes_service import quote_from_candles

        fake = quote_from_candles(
            "300104.SZ",
            [{"date": "2016-12-30", "close": 3042.88}],
        )
        self.assertTrue(fake["available"])
        self.assertEqual(fake["last"], 3042.88)
        immune.test_case_letv_receivables_fraud()


if __name__ == "__main__":
    unittest.main()
