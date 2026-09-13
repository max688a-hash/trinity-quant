"""
选股引擎禁止用写死造血/债务数覆盖真实财报体检。
audit_summary 否决 600900 时，/api/screener 不得把长江电力标可买。
乐视/康美不得变成可买。
# ref: AGENTS.md 第 27 条 / 第 33 条
"""

from __future__ import annotations

import json
import os
import unittest


class TestScreenerAuditTruth(unittest.TestCase):
    """专业用户会按选股数字下单，写死 Φ/Ω 即伪造准入。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        engine = os.path.join(cls.root, "gravity_brain", "auto_screener_engine.py")
        with open(engine, encoding="utf-8") as fp:
            cls.engine_src = fp.read()
        audit = os.path.join(cls.root, "data", "real_financials", "audit_summary.json")
        with open(audit, encoding="utf-8") as fp:
            cls.audit = json.load(fp)

    def test_default_universe_must_not_hardcode_moutai_phi_or_yangtze_omega(self) -> None:
        self.assertNotIn(
            '"phi_cp": 1.05',
            self.engine_src,
            "选股默认宇宙仍写死茅台 Φ=1.05，专业用户会当法证造血",
        )
        self.assertNotIn(
            '"omega_debt": 0.42',
            self.engine_src,
            "选股默认宇宙仍写死长江电力 Ω=0.42，覆盖真实体检否决",
        )

    def test_audit_marks_yangtze_vetoed(self) -> None:
        stocks = self.audit.get("summary", {}).get("stocks", [])
        yangtze = [row for row in stocks if str(row.get("symbol", "")).startswith("600900")]
        self.assertTrue(yangtze, "体检档案必须仍覆盖长江电力，否则本刀无法对齐")
        self.assertFalse(
            yangtze[0].get("is_admitted"),
            "真实体检仍否决长江电力；引擎不得把它标可买",
        )

    def test_screener_must_not_qualify_yangtze_when_audit_vetoes(self) -> None:
        from entropy_execution.http_api_dispatcher import HttpApiDispatcher

        payload = HttpApiDispatcher.get_screener_results()
        qualified = [
            item
            for item in payload.get("candidates", [])
            if item.get("is_qualified")
            and (
                "600900" in str(item.get("symbol", ""))
                or "长江" in str(item.get("name", ""))
            )
        ]
        self.assertEqual(
            qualified,
            [],
            "audit 否决 600900 时 /api/screener 仍 is_qualified=True，专业用户会当可买",
        )

    def test_letv_kangmei_remain_unbuyable(self) -> None:
        from entropy_execution.http_api_dispatcher import HttpApiDispatcher
        from tests.test_immune_system import TestImmuneSystem

        immune = TestImmuneSystem()
        immune.setUp()
        immune.test_case_letv_receivables_fraud()
        immune.test_case_kangmei_deposit_loan_paradox()

        payload = HttpApiDispatcher.get_screener_results()
        for item in payload.get("candidates", []):
            blob = f"{item.get('symbol', '')} {item.get('name', '')}"
            if "300104" in blob or "600518" in blob or "乐视" in blob or "康美" in blob:
                self.assertFalse(
                    item.get("is_qualified"),
                    f"{blob} 被标可买，毒资产上桌",
                )


if __name__ == "__main__":
    unittest.main()
