"""
尸检/引力榜禁止与选股引擎自相矛盾。
DesktopPanels 不得再用本地 STOCKS 把长江电力写成债务否决；
乐视/康美不得变成可买。
# ref: AGENTS.md 第 27 条 严禁静态伪造池
"""

from __future__ import annotations

import os
import unittest


class TestDesktopPanelsSingleTruth(unittest.TestCase):
    """专业用户同一次会话只允许一套准入判决。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        panels = os.path.join(cls.root, "web", "src", "pages", "DesktopPanels.tsx")
        with open(panels, encoding="utf-8") as fp:
            cls.panels = fp.read()
        api_path = os.path.join(cls.root, "web", "src", "lib", "api.ts")
        with open(api_path, encoding="utf-8") as fp:
            cls.api = fp.read()
        main_path = os.path.join(cls.root, "main.py")
        with open(main_path, encoding="utf-8") as fp:
            cls.main = fp.read()

    def test_panels_must_not_import_local_stock_table(self) -> None:
        self.assertNotIn(
            'from "../lib/stocks"',
            self.panels,
            "引力/尸检仍引用本地 STOCKS，会把长江电力写成与选股引擎相反的否决",
        )
        self.assertNotIn("STOCKS.filter", self.panels)
        self.assertNotIn("STOCKS.map", self.panels)
        self.assertNotIn("STOCKS.length", self.panels)

    def test_valuation_must_read_screener_api(self) -> None:
        self.assertIn("fetchScreener", self.panels)
        self.assertIn("/api/screener", self.api)
        self.assertIn("gravity_value", self.panels)

    def test_autopsy_must_read_forensic_api_not_hardcoded_yangtze_veto(self) -> None:
        self.assertIn("fetchForensicAutopsy", self.panels)
        self.assertIn("/api/pool/autopsy", self.api)
        self.assertIn("/api/pool/autopsy", self.main)
        self.assertNotIn("Ω_Debt=2.96", self.panels)
        self.assertNotIn("债务猝死否决", self.panels)
        self.assertIn("DATA_UNAVAILABLE", self.panels)

    def test_yangtze_screener_and_autopsy_share_audit_veto(self) -> None:
        from entropy_execution.http_api_dispatcher import HttpApiDispatcher
        from entropy_execution.forensic_autopsy_service import list_forensic_autopsy

        screener = HttpApiDispatcher.get_screener_results()
        yangtze = [
            item
            for item in screener["candidates"]
            if "600900" in str(item.get("symbol", "")) or "长江" in str(item.get("name", ""))
        ]
        qualified_yangtze = [item for item in yangtze if item.get("is_qualified")]
        self.assertEqual(qualified_yangtze, [], "体检否决后引力/选股不得再把长江电力标可买")

        autopsy = list_forensic_autopsy()
        self.assertEqual(autopsy.get("status"), "OK")
        joined = " ".join(
            f"{case.get('symbol', '')} {case.get('name', '')}"
            for case in autopsy.get("cases", [])
        )
        self.assertIn("600900", joined)
        self.assertIn("长江电力", joined)
        self.assertIn("300104", joined)
        self.assertIn("600518", joined)
        self.assertIn("乐视", joined)
        self.assertIn("康美", joined)
        for case in autopsy.get("cases", []):
            self.assertFalse(case.get("is_admitted"))
            self.assertFalse(case.get("is_buyable"))
            self.assertTrue(case.get("veto_reasons"))

    def test_letv_kangmei_remain_unbuyable(self) -> None:
        from tests.test_immune_system import TestImmuneSystem

        immune = TestImmuneSystem()
        immune.setUp()
        immune.test_case_letv_receivables_fraud()
        immune.test_case_kangmei_deposit_loan_paradox()


if __name__ == "__main__":
    unittest.main()
