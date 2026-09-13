"""
tests/test_industry_chain_graph.py
==================================
AI 产业链深度图谱与机构级万字穿透研报大脑单元测试。
严格遵循第一性原理与最高开发宪法 (AGENTS.md):
1. 验证上中下游拓扑完整性与毛利定价权分配;
2. 验证机构研报对于造血纯度、债务到期墙与极端压力测试的法证严肃性;
3. 单文件严格不超过 300 行，零伪 Mock。
"""

import unittest
from truth_kernel.industry_chain_graph import (
    ChainSegment,
    PricingPower,
    IndustryChainGraphRegistry
)
from truth_kernel.institutional_report_generator import (
    InstitutionalReportGenerator,
    InstitutionalReport
)


class TestIndustryChainAndReport(unittest.TestCase):
    """产业链图谱与机构研报生成器单元测试"""

    def test_industry_chain_topology_and_margins(self) -> None:
        """测试产业链知识图谱上中下游拓扑与毛利定价权完整性"""
        chains = IndustryChainGraphRegistry.list_chains()
        self.assertGreaterEqual(len(chains), 6)

        # 检验贵州茅台产业链
        chain_mt = IndustryChainGraphRegistry.get_chain("600519.SH")
        self.assertIsNotNone(chain_mt)
        self.assertEqual(chain_mt.sector_id, "baijiu_consumer")
        self.assertTrue(len(chain_mt.upstream_nodes) >= 1)
        self.assertTrue(len(chain_mt.midstream_nodes) >= 1)
        self.assertTrue(len(chain_mt.downstream_nodes) >= 1)

        # 验证中游坤沙固态发酵高毛利
        mid_node = chain_mt.midstream_nodes[0]
        self.assertGreaterEqual(mid_node.gross_margin_pct, 85.0)
        self.assertEqual(mid_node.pricing_power, PricingPower.DOMINANT)

    def test_chain_lookup_flexibility(self) -> None:
        """测试按带后缀或纯代码检索产业链"""
        c1 = IndustryChainGraphRegistry.get_chain("002594.SZ")
        c2 = IndustryChainGraphRegistry.get_chain("002594")
        self.assertIsNotNone(c1)
        self.assertEqual(c1, c2)
        self.assertEqual(c1.representative_name, "比亚迪")

    def test_institutional_report_healthy_asset(self) -> None:
        """测试健康造血标的机构研报生成"""
        report = InstitutionalReportGenerator.generate_report("600519.SH")
        self.assertIsInstance(report, InstitutionalReport)
        self.assertIn("GRADE_AAA", report.rating)
        self.assertGreater(report.target_gravity_price, 0.0)
        self.assertIn("600519", report.symbol)
        self.assertTrue(len(report.black_swan_stress_tests) >= 3)
        self.assertFalse(report.regulatory_verdict_and_kelly["is_vetoed"])

    def test_institutional_report_vetoed_debt_asset(self) -> None:
        """测试债务承压与排毒标的机构研报硬阻断与零头寸"""
        report = InstitutionalReportGenerator.generate_report("000002.SZ")
        self.assertIsInstance(report, InstitutionalReport)
        # 债务毒性应被严格审查
        self.assertIn("VETO", report.rating)
        self.assertTrue(report.regulatory_verdict_and_kelly["is_vetoed"])
        self.assertEqual(report.regulatory_verdict_and_kelly["recommended_kelly_position"], "0.0% 组合总资产")


if __name__ == "__main__":
    unittest.main()
