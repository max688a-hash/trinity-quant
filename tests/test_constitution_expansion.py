"""
tests/test_constitution_expansion.py
====================================
最高开发宪法拓展法条 (第21条至第32条) 物理断言测试套件：
涵盖防AI奖励造假、单向棘轮风控、客观现实实证调研、反谄媚迎合、全息披露、时间复杂度与双模态智力解缚。
严格遵守单文件 <= 300 行红线与真实无 Mock 原则。
"""
import os
import unittest
from typing import List


class TestConstitutionExpansion(unittest.TestCase):
    """最高宪法拓展章节（第21-32条）断言门禁"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        with open(os.path.join(cls.workspace_root, "AGENTS.md"), "r", encoding="utf-8") as fp:
            cls.agents_md = fp.read()
        with open(os.path.join(cls.workspace_root, ".cursorrules"), "r", encoding="utf-8") as fp:
            cls.cursorrules = fp.read()
        with open(os.path.join(cls.workspace_root, ".cursor", "rules", "trinity_bio_cybernetic.mdc"), "r", encoding="utf-8") as fp:
            cls.cursor_mdc = fp.read()

    def test_articles_21_to_26_invariants(self) -> None:
        """断言第21-26条：防奖励造假、跨学科创新、千问自激、单向棘轮风控、环境守恒、防豆腐渣"""
        self.assertIn("第 21 条：严禁 AI 盈利指标造假与奖励欺骗", self.agents_md)
        self.assertIn("第 22 条：跨学科物理破壁与第一性原理守恒创新法则", self.agents_md)
        self.assertIn("第 23 条：全生命周期常态化千问自激中枢法则", self.agents_md)
        self.assertIn("第 24 条：严禁为迎合盈利目标而擅自放宽风控与拆除防线铁律", self.agents_md)
        self.assertIn("第 25 条：全领域多学科严禁为迎合考核目标而造假与拆除底线总则", self.agents_md)
        self.assertIn("第 26 条：工程落地实施防偷工减料与高标准施工千问立宪", self.agents_md)

    def test_article_27_pool_admission_traceability(self) -> None:
        """断言第27条：标的动态深研入池依据与排毒门禁"""
        self.assertIn("第 27 条：标的动态深研入池、科学依据可追溯与严禁静态伪造池宪法", self.agents_md)
        from truth_kernel.pool_admission_auditor import PoolAdmissionAuditor
        dockets = PoolAdmissionAuditor.list_all_dockets()
        self.assertGreaterEqual(len(dockets), 5)
        for d in dockets:
            self.assertGreaterEqual(len(d.admission_reasons), 2)
            self.assertGreaterEqual(len(d.expulsion_triggers), 1)

    def test_article_28_empirical_due_diligence(self) -> None:
        """断言第28条：依据客观现实、未经实证调研严禁妄下结论"""
        self.assertIn("第 28 条：依据客观现实、未经实证调研严禁妄下结论宪法", self.agents_md)
        self.assertIn("Article 28 Rules", self.cursorrules)

    def test_article_29_anti_sycophancy(self) -> None:
        """断言第29条：独立客观求真与反谄媚迎合宪法"""
        self.assertIn("第 29 条：独立客观求真与反谄媚迎合宪法", self.agents_md)
        self.assertIn("Anti-Sycophancy", self.agents_md)
        self.assertIn("反谄媚求真", self.cursorrules)

    def test_article_30_symmetrical_disclosure(self) -> None:
        """断言第30条：全息对称披露与零美化披露宪法"""
        self.assertIn("第 30 条：全息对称披露与零美化披露宪法", self.agents_md)
        self.assertIn("Full-Spectrum Symmetrical Disclosure", self.agents_md)
        self.assertIn("全息对称披露", self.cursorrules)

    def test_article_31_algorithmic_scalability(self) -> None:
        """断言第31条：算法渐近复杂度与大数据量生存宪法"""
        self.assertIn("第 31 条：算法渐近复杂度与大数据量生存宪法", self.agents_md)
        self.assertIn("O(N \\log N)", self.agents_md)
        self.assertIn("渐近时间复杂度", self.cursorrules)

    def test_article_32_dual_mode_creative_autonomy(self) -> None:
        """断言第32条：双模态研发与智力解缚立宪（沙盒探索无限自由，生产准入绝对刚性）"""
        self.assertIn("第 32 条：双模态研发与智力解缚立宪", self.agents_md)
        self.assertIn("Dual-Mode Bounded Creative Autonomy Law", self.agents_md)
        self.assertIn("沙盒内探索无限自由", self.cursorrules)
        self.assertIn("Articles 29-32", self.cursor_mdc)

    def test_article_33_absolute_truth_grounding_anti_fabrication(self) -> None:
        """断言第33条：绝对真值数据锚定、反伪造心跳与零假演播铁律"""
        self.assertIn("第 33 条：绝对真值数据锚定、反伪造心跳与零假演播铁律", self.agents_md)
        self.assertIn("No-Trade Zero-Tick Invariant", self.agents_md)
        self.assertIn("Zero-Random-Jitter Law", self.agents_md)

        # 1. 物理断言：连续查询实时行情，无新成交时价格与成交量必须绝对保持恒定 (零随机伪跳动)
        from truth_kernel.realtime_feed_adapter import RealtimeFeedAdapter
        adapter = RealtimeFeedAdapter()
        t1 = adapter.get_tick("600519.SH")
        t2 = adapter.get_tick("600519.SH")
        self.assertEqual(t1.price, t2.price, "违宪：无新成交时价格发生漂移随机跳动！")
        self.assertEqual(t1.volume, t2.volume, "违宪：无新成交时成交量发生随机漂移！")

        # 2. 物理断言：真实历史 K 线服务必须返回客观历史记录，严禁正弦波造假
        from truth_kernel.historical_kline_service import HistoricalKlineService
        candles = HistoricalKlineService.get_kline("600519.SH", timeframe="D", count=30)
        self.assertGreaterEqual(len(candles), 10)
        self.assertTrue(any(yr in candles[0]["date"] for yr in ("2023-", "2024-", "2025-", "2026-")), f"非法历史日期: {candles[0]['date']}")

        # 3. 物理断言：前端代码静态排查，绝对禁止正弦波捏造蜡烛与写死买卖点索引
        with open(os.path.join(self.workspace_root, "trinity_dashboard.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertNotIn("Math.sin(i * 0.55)", html, "违宪：前端仍在使用正弦波伪造K线！")
        self.assertNotIn("candles[10].signal = { type: 'BUY'", html, "违宪：前端仍在使用固定索引硬编码信号点！")
        self.assertIn("loadRealKlineData", html, "缺失真实K线加载器！")
        self.assertIn("calculateDynamicSignals", html, "缺失动态数学算法信号推导器！")


if __name__ == "__main__":
    unittest.main()
