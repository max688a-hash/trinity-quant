"""
标的动态入池法证审计中枢单元测试
严格落实最高开发宪法第27条：Dynamic Pool Admission & Epistemological Traceability Law
"""
import unittest
from truth_kernel.pool_admission_auditor import (
    PoolAdmissionAuditor,
    AdmissionDocket,
    AdmissionGrade,
    InvestmentHorizon
)


class TestPoolAdmissionAuditor(unittest.TestCase):
    """标的入池法证审计测试用例"""

    def test_core_ashare_assets_dockets_complete(self) -> None:
        """验证核心A股标的入池法证档案的严密性与第一性原理守恒"""
        ashare_symbols = [
            "600519.SH", "300750.SZ", "600900.SH", "002594.SZ",
            "600036.SH", "601318.SH", "000858.SZ", "601899.SH"
        ]
        for s in ashare_symbols:
            docket = PoolAdmissionAuditor.get_docket(s)
            self.assertEqual(docket.symbol, s)
            self.assertGreaterEqual(len(docket.admission_reasons), 3, f"{s} 必须至少具备3条入池客观科学依据")
            self.assertGreaterEqual(len(docket.expulsion_triggers), 2, f"{s} 必须至少具备2条硬性排毒剔除条件")
            self.assertGreaterEqual(docket.blood_purity, 0.30, f"{s} 入池标的造血纯度必须不低于0.30")
            self.assertIn(docket.horizon, (InvestmentHorizon.LONG_TERM_CORE, InvestmentHorizon.MEDIUM_TERM_CYCLE, InvestmentHorizon.SHORT_TERM_TACTICAL))
            if not docket.is_buyable_now:
                self.assertEqual(docket.grade, AdmissionGrade.WATCHLIST)
                self.assertTrue(
                    docket.debt_toxicity > 0.40 or "否决" in docket.current_action_advice,
                    f"{s} 不可买时必须有体检否决或债务超阈",
                )
                continue
            self.assertLessEqual(docket.debt_toxicity, 0.40, f"{s} 入池标的债务毒性必须不高于0.40")
            self.assertIn(docket.grade, (AdmissionGrade.AAA_FORTRESS, AdmissionGrade.AA_CYCLICAL, AdmissionGrade.A_TACTICAL))
            self.assertTrue(docket.is_buyable_now)

    def test_horizon_categorization_logic(self) -> None:
        """验证标的投资久期分类定位（长期价值堡垒 vs 中期周期 vs 短期战术）"""
        moutai = PoolAdmissionAuditor.get_docket("600519.SH")
        self.assertEqual(moutai.horizon, InvestmentHorizon.LONG_TERM_CORE)
        self.assertEqual(moutai.grade, AdmissionGrade.AAA_FORTRESS)

        catl = PoolAdmissionAuditor.get_docket("300750.SZ")
        self.assertEqual(catl.horizon, InvestmentHorizon.MEDIUM_TERM_CYCLE)
        self.assertEqual(catl.grade, AdmissionGrade.AA_CYCLICAL)

        zijin = PoolAdmissionAuditor.get_docket("601899.SH")
        self.assertEqual(zijin.horizon, InvestmentHorizon.SHORT_TERM_TACTICAL)
        self.assertEqual(zijin.grade, AdmissionGrade.A_TACTICAL)

    def test_futures_dockets_and_expulsion(self) -> None:
        """验证期货合约入池法证具备交割月禁入等排毒风控条款"""
        rb = PoolAdmissionAuditor.get_docket("RB")
        self.assertEqual(rb.market, "futures")
        has_delivery_expulsion = any("交割" in trig for trig in rb.expulsion_triggers)
        self.assertTrue(has_delivery_expulsion, "期货标的必须包含交割月强平排毒条件")

        cffex_if = PoolAdmissionAuditor.get_docket("IF")
        self.assertEqual(cffex_if.market, "futures")
        self.assertEqual(cffex_if.grade, AdmissionGrade.AAA_FORTRESS)

    def test_pool_authenticity_audit(self) -> None:
        """验证池真实性全量法证审计机制"""
        valid_symbols = ["600519.SH", "600900.SH", "RB", "IF"]
        is_ok, violations = PoolAdmissionAuditor.audit_pool_authenticity(valid_symbols)
        self.assertTrue(is_ok)
        self.assertEqual(len(violations), 0)


if __name__ == "__main__":
    unittest.main()
