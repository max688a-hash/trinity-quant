"""
入池宗卷禁止把体检否决标的写成可买。
audit_summary 否决 600900 时，get_docket / 深研弹窗不得 is_buyable_now。
乐视/康美不得变成可买。
# ref: AGENTS.md 第 27 条
"""

from __future__ import annotations

import json
import os
import unittest


class TestDocketAuditRatchet(unittest.TestCase):
    """专业用户点入池深研会按 is_buyable_now 下手，禁止与体检相反。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        audit = os.path.join(cls.root, "data", "real_financials", "audit_summary.json")
        with open(audit, encoding="utf-8") as fp:
            cls.audit = json.load(fp)
        modal = os.path.join(cls.root, "web", "src", "components", "DocketModal.tsx")
        with open(modal, encoding="utf-8") as fp:
            cls.modal = fp.read()
        api_path = os.path.join(cls.root, "web", "src", "lib", "api.ts")
        with open(api_path, encoding="utf-8") as fp:
            cls.api = fp.read()

    def test_audit_still_vetoes_yangtze(self) -> None:
        stocks = self.audit.get("summary", {}).get("stocks", [])
        yangtze = [row for row in stocks if str(row.get("symbol", "")).startswith("600900")]
        self.assertTrue(yangtze)
        self.assertFalse(yangtze[0].get("is_admitted"))

    def test_get_docket_yangtze_must_not_be_buyable(self) -> None:
        from truth_kernel.pool_admission_auditor import PoolAdmissionAuditor

        docket = PoolAdmissionAuditor.get_docket("600900.SH")
        self.assertFalse(
            docket.is_buyable_now,
            "体检否决长江电力后宗卷仍 is_buyable_now，专业用户会当可买去手打",
        )
        self.assertGreater(docket.debt_toxicity, 0.40)

    def test_listed_dockets_include_yangtze_veto(self) -> None:
        from truth_kernel.pool_admission_auditor import PoolAdmissionAuditor

        listed = PoolAdmissionAuditor.list_all_dockets()
        yangtze = [row for row in listed if "600900" in row.symbol]
        self.assertTrue(yangtze)
        self.assertFalse(yangtze[0].is_buyable_now)

    def test_modal_must_read_dockets_api_not_local_buyable_table(self) -> None:
        self.assertIn("fetchPoolDockets", self.modal)
        self.assertIn("/api/pool/dockets", self.api)
        self.assertNotIn("ADMISSION_DOCKETS", self.modal)

    def test_letv_kangmei_remain_unbuyable(self) -> None:
        from tests.test_immune_system import TestImmuneSystem

        immune = TestImmuneSystem()
        immune.setUp()
        immune.test_case_letv_receivables_fraud()
        immune.test_case_kangmei_deposit_loan_paradox()


if __name__ == "__main__":
    unittest.main()
