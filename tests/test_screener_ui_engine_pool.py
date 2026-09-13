"""
选股屏禁止本地玩具池冒充引擎结果。
主卡片必须来自 /api/screener；接口空/错阻断可买。
乐视/康美不得因本地表变成可买。
# ref: AGENTS.md 第 27 条 严禁静态伪造池
"""

from __future__ import annotations

import os
import unittest


class TestScreenerUiEnginePool(unittest.TestCase):
    """排毒大屏只渲染引擎池，禁止 STOCKS 本地表当可买。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        page = os.path.join(cls.root, "web", "src", "pages", "ScreenerPage.tsx")
        with open(page, encoding="utf-8") as fp:
            cls.page = fp.read()

    def test_screener_page_must_not_import_local_stock_table(self) -> None:
        self.assertNotIn(
            'from "../lib/stocks"',
            self.page,
            "选股屏仍引用本地 STOCKS，专业用户会把玩具池当法证准入",
        )
        self.assertNotIn("STOCKS.filter", self.page)
        self.assertNotIn("STOCKS.length", self.page)
        self.assertNotIn("STOCKS.map", self.page)

    def test_main_cards_must_come_from_screener_api(self) -> None:
        self.assertIn("fetchScreener", self.page)
        api_path = os.path.join(self.root, "web", "src", "lib", "api.ts")
        with open(api_path, encoding="utf-8") as fp:
            api_src = fp.read()
        self.assertIn("/api/screener", api_src)
        self.assertIn("is_qualified", self.page)

    def test_empty_or_error_must_block_buyable_fallback(self) -> None:
        self.assertNotIn("已审计本地法证池", self.page)
        self.assertNotIn("下方展示", self.page)
        self.assertIn("DATA_UNAVAILABLE", self.page)
        self.assertIn("禁止", self.page)

    def test_engine_payload_excludes_letv_kangmei(self) -> None:
        from entropy_execution.http_api_dispatcher import HttpApiDispatcher

        payload = HttpApiDispatcher.get_screener_results()
        self.assertGreaterEqual(payload["count"], 1)
        qualified = [item for item in payload["candidates"] if item.get("is_qualified")]
        self.assertGreaterEqual(len(qualified), 1)
        joined = " ".join(
            f"{item.get('symbol', '')} {item.get('name', '')}"
            for item in qualified
        )
        self.assertNotIn("300104", joined)
        self.assertNotIn("600518", joined)
        self.assertNotIn("乐视", joined)
        self.assertNotIn("康美", joined)
        for item in payload["candidates"]:
            blob = f"{item.get('symbol', '')} {item.get('name', '')}"
            if "300104" in blob or "600518" in blob or "乐视" in blob or "康美" in blob:
                self.assertFalse(item.get("is_qualified"))

    def test_letv_kangmei_remain_vetoed(self) -> None:
        from tests.test_immune_system import TestImmuneSystem

        immune = TestImmuneSystem()
        immune.setUp()
        immune.test_case_letv_receivables_fraud()
        immune.test_case_kangmei_deposit_loan_paradox()


if __name__ == "__main__":
    unittest.main()
