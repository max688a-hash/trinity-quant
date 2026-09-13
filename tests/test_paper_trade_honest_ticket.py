"""
纸上成交禁止写死茅台 1550；否决标的禁止纸上成交。
盈利必须带全摩擦从账本长出，禁止为绿而放宽或假成交。
乐视/康美不得变成可买。
# ref: AGENTS.md 第 21 / 24 / 33 条
"""

from __future__ import annotations

import os
import unittest


class TestPaperTradeHonestTicket(unittest.TestCase):
    """手打工单必须用行情价；写死 1550 会让纸上盈亏与盘口脱节。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        page = os.path.join(cls.root, "web", "src", "pages", "PaperPage.tsx")
        with open(page, encoding="utf-8") as fp:
            cls.page = fp.read()

    def test_paper_page_must_not_hardcode_moutai_1550(self) -> None:
        self.assertNotIn("price: 1550", self.page)
        self.assertNotIn("price:1550", self.page)
        self.assertIn("fetchBoardQuotes", self.page)
        self.assertIn("fetchScreener", self.page)

    def test_missing_price_is_rejected_not_defaulted(self) -> None:
        from entropy_execution.http_api_dispatcher import HttpApiDispatcher
        from entropy_execution.paper_trading_engine import PaperTradingEngine
        import threading

        engine = PaperTradingEngine(initial_capital=1_000_000.0)
        lock = threading.Lock()
        res = HttpApiDispatcher.handle_paper_trade(
            engine,
            lock,
            {"symbol": "600519.SH", "action": "BUY", "quantity": 100, "is_replay_mode": True},
        )
        self.assertFalse(res.get("success"))
        self.assertIn("DATA_UNAVAILABLE", str(res.get("rejection_reason") or ""))

    def test_yangtze_paper_buy_rejected_when_audit_vetoes(self) -> None:
        from entropy_execution.http_api_dispatcher import HttpApiDispatcher
        from entropy_execution.paper_trading_engine import PaperTradingEngine
        import threading

        engine = PaperTradingEngine(initial_capital=1_000_000.0)
        lock = threading.Lock()
        res = HttpApiDispatcher.handle_paper_trade(
            engine,
            lock,
            {
                "symbol": "600900.SH",
                "action": "BUY",
                "quantity": 100,
                "price": 30.0,
                "is_replay_mode": True,
            },
        )
        self.assertFalse(res.get("success"))
        self.assertEqual(engine.cash, 1_000_000.0)

    def test_letv_kangmei_paper_buy_rejected(self) -> None:
        from entropy_execution.http_api_dispatcher import HttpApiDispatcher
        from entropy_execution.paper_trading_engine import PaperTradingEngine
        import threading
        from tests.test_immune_system import TestImmuneSystem

        immune = TestImmuneSystem()
        immune.setUp()
        immune.test_case_letv_receivables_fraud()
        immune.test_case_kangmei_deposit_loan_paradox()

        engine = PaperTradingEngine(initial_capital=1_000_000.0)
        lock = threading.Lock()
        for symbol in ("300104.SZ", "600518.SH"):
            res = HttpApiDispatcher.handle_paper_trade(
                engine,
                lock,
                {
                    "symbol": symbol,
                    "action": "BUY",
                    "quantity": 100,
                    "price": 2.0,
                    "is_replay_mode": True,
                },
            )
            self.assertFalse(res.get("success"), f"{symbol} 纸上成交等于毒资产上桌")
        self.assertEqual(engine.cash, 1_000_000.0)


if __name__ == "__main__":
    unittest.main()
