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

        # 2. 物理断言：未获取到真实行情时严禁写死底价伪造，必须报告 DATA_UNAVAILABLE (price=0.0)
        nope_tick = adapter.get_tick("NOPE.SH")
        self.assertEqual(nope_tick.price, 0.0, "违宪：离线/未知标的伪造了非零底价！")
        self.assertEqual(nope_tick.source, "DATA_UNAVAILABLE", "违宪：离线未报告 DATA_UNAVAILABLE！")

        # 3. 物理断言：真实历史 K 线服务必须返回客观历史记录，严禁正弦波造假
        from truth_kernel.historical_kline_service import HistoricalKlineService
        candles = HistoricalKlineService.get_kline("600519.SH", timeframe="D", count=30)
        self.assertGreaterEqual(len(candles), 10)
        self.assertTrue(any(yr in candles[0]["date"] for yr in ("2023-", "2024-", "2025-", "2026-")), f"非法历史日期: {candles[0]['date']}")

        # 4. 物理断言：自学习沙盒严禁虚构种子盈利历史 (AUTO_001 pnl +3000)
        from entropy_execution.autonomous_learning_sandbox import AutonomousLearningSandbox
        sandbox = AutonomousLearningSandbox()
        rep = sandbox.generate_learning_report()
        self.assertEqual(rep.total_auto_trades, 0, "违宪：自学习沙盒存在伪造的初始赢钱历史！")
        self.assertEqual(rep.empirical_win_rate, 0.0, "违宪：冷启动报告伪造了胜率！")

        # 5. 物理断言：前端与HTTP路由严禁后门伪造跳动或硬编码回放
        with open(os.path.join(self.workspace_root, "web", "src", "pages", "PaperPage.tsx"), "r", encoding="utf-8") as fp:
            paper_tsx = fp.read()
        self.assertNotIn("is_replay_mode: true", paper_tsx, "违宪：前端硬编码了 is_replay_mode: true 导致休市偷跑！")
        self.assertIn("is_replay_mode: isReplayMode", paper_tsx)

        with open(os.path.join(self.workspace_root, "main.py"), "r", encoding="utf-8") as fp:
            main_py = fp.read()
        self.assertNotIn("allow_sim_on_closed", main_py, "违宪：生产 HTTP 路由仍保留 allow_sim_on_closed 伪造后门！")

        # 6. 物理断言：前端代码静态排查，绝对禁止正弦波捏造蜡烛与写死买卖点索引
        from tests.ui_corpus import load_ui_corpus
        html = load_ui_corpus(self.workspace_root)
        self.assertNotIn("Math.sin(i * 0.55)", html, "违宪：前端仍在使用正弦波伪造K线！")
        self.assertNotIn("candles[10].signal = { type: 'BUY'", html, "违宪：前端仍在使用固定索引硬编码信号点！")
        self.assertIn("loadRealKlineData", html, "缺失真实K线加载器！")
        self.assertIn("calculateDynamicSignals", html, "缺失动态数学算法信号推导器！")

    def test_article_34_mobile_viewport_ownership(self) -> None:
        """断言第34条：移动端物理视口所有权与真实人机工程排障宪法"""
        self.assertIn("第 34 条：移动端物理视口所有权与真实人机工程排障宪法", self.agents_md)
        self.assertIn("Mobile Viewport Ownership", self.agents_md)
        from tests.test_mobile_nav_viewport import TestMobileNavViewport
        from io import StringIO
        suite = unittest.TestLoader().loadTestsFromTestCase(TestMobileNavViewport)
        res = unittest.TextTestRunner(stream=StringIO(), verbosity=0).run(suite)
        self.assertTrue(res.wasSuccessful(), "移动端视口所有权测试未通过！")

    def test_article_35_mechanical_closeout_clean_handoff(self) -> None:
        """断言第35条：机械收尾闸机与工作区纯净交接宪法"""
        self.assertIn("第 35 条：机械收尾闸机与工作区纯净交接宪法", self.agents_md)
        self.assertIn("Mechanical Closeout Enforcer", self.agents_md)
        with open(os.path.join(self.workspace_root, ".gitignore"), "r", encoding="utf-8") as fp:
            gitignore = fp.read()
        self.assertIn("web/dist/", gitignore, "构建产物 web/dist/ 必须写入 .gitignore！")
        self.assertIn(".kiro/gates/state/", gitignore, "运行态 .kiro/gates/state/ 必须写入 .gitignore！")

    def test_article_36_purpose_driven_verification(self) -> None:
        """断言第36条：目的牵引物理质检与反浅层验收宪法"""
        self.assertIn("第 36 条：目的牵引物理质检与反浅层验收宪法", self.agents_md)
        self.assertIn("Purpose-Driven Physical Verification", self.agents_md)
        self.assertIn("目的牵引物理质检", self.cursorrules)
        # 验证 .kiro/purpose.json 的真实性与物理可执行性
        purpose_file = os.path.join(self.workspace_root, ".kiro", "purpose.json")
        self.assertTrue(os.path.exists(purpose_file), "缺失 .kiro/purpose.json 目的指标定义！")
        import json
        with open(purpose_file, "r", encoding="utf-8") as fp:
            purpose_data = json.load(fp)
        self.assertIn("软件目的", purpose_data)
        self.assertIn("目的指标", purpose_data)
        for item in purpose_data["目的指标"]:
            self.assertIsNotNone(item.get("measure_cmd"))

    def test_article_37_modal_anti_deadlock_and_visual_proximity(self) -> None:
        """断言第37条：浮层弹窗防死锁与组件视觉邻近铁律"""
        self.assertIn("第 37 条：浮层弹窗防死锁与组件视觉邻近铁律", self.agents_md)
        self.assertIn("Backdrop Tap Dismissal", self.agents_md)
        self.assertIn("Visual Proximity Law", self.agents_md)
        self.assertIn("浮层弹窗防死锁", self.cursorrules)
        self.assertIn("组件视觉邻近", self.cursorrules)
        # 验证技能库中已固化防死锁与视觉邻近规范
        ui_skill_path = os.path.join(self.workspace_root, ".agents", "skills", "superpowers-universal-ui-ux", "SKILL.md")
        with open(ui_skill_path, "r", encoding="utf-8") as fp:
            ui_skill = fp.read()
        self.assertIn("弹窗与浮层防死锁", ui_skill)
        self.assertIn("组件视觉邻近律", ui_skill)


if __name__ == "__main__":
    unittest.main()


