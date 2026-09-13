"""
最高开发宪法第八章：零放水自动化质量门禁 (Zero-Water Quality Gate) 物理断言测试
"""
import os
import re
import unittest
from typing import List, Tuple


class TestConstitutionStrict(unittest.TestCase):
    """最高开发宪法物理级严格断言门禁"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.html_path = os.path.join(cls.workspace_root, "trinity_dashboard.html")
        with open(cls.html_path, "r", encoding="utf-8") as fp:
            cls.html_content = fp.read()

    def test_code_files_line_count_strict(self) -> None:
        """宪法第3条第3款：全量Python文件行数必须严格<=300行"""
        violations: List[Tuple[str, int]] = []
        for root, _, files in os.walk(self.workspace_root):
            if any(x in root for x in (".venv", ".git", "__pycache__", ".chrome")):
                continue
            for f in files:
                if f.endswith(".py"):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                        count = len(fp.readlines())
                        if count > 300:
                            violations.append((os.path.relpath(fpath, self.workspace_root), count))
        self.assertEqual(
            len(violations), 0,
            f"宪法违背：发现单文件超过300行巨兽文件！清单: {violations}"
        )

    def test_mobile_anti_scroll_trapping(self) -> None:
        """宪法第7条第2款：严禁画布无差别preventDefault锁死移动端垂直滚动"""
        self.assertIn("Math.abs(deltaY) > Math.abs(curX - touchStartX)", self.html_content,
                      "移动端违宪：未实现垂直滚动向量差分流，存在触碰锁死陷阱！")
        self.assertIn("touchStartY", self.html_content, "移动端违宪：缺失垂直触控原点追踪！")

    def test_mobile_sticky_segmented_navigation(self) -> None:
        """宪法第7条第4款：深屏必须配备吸顶式快捷分段导航"""
        self.assertIn("scrollToPaperSection", self.html_content, "缺失吸顶快捷分段导航分流函数！")
        self.assertIn('id="sec-paper-sim"', self.html_content, "缺失模拟海龟锚点ID！")
        self.assertIn('id="sec-paper-combat"', self.html_content, "缺失真金实战锚点ID！")
        self.assertIn('id="sec-paper-daemon"', self.html_content, "缺失影子巡航锚点ID！")
        self.assertIn('id="sec-paper-stress"', self.html_content, "缺失黑天鹅压测锚点ID！")

    def test_financial_color_semantics_consistency(self) -> None:
        """宪法第12条：全站金融买卖色彩必须全局一致（红买绿卖），严禁同屏冲突"""
        # 严禁出现“绿买红卖”
        self.assertNotIn('option value="BUY">🟢', self.html_content,
                         "色彩违宪：买入方向赫然使用绿色，违背国内金融证券标准！")
        self.assertNotIn('option value="SELL">🔴', self.html_content,
                         "色彩违宪：卖出方向赫然使用红色，违背国内金融证券标准！")
        # 必须正确标记
        self.assertIn('option value="BUY">🔴', self.html_content, "买入必须标注红色！")
        self.assertIn('option value="SELL">🟢', self.html_content, "卖出必须标注绿色！")

    def test_multidevice_state_atomicity(self) -> None:
        """宪法第11条第1款：双端导航状态机必须通过data-tab原子对齐"""
        nav_match = re.search(r'<nav[^>]*>([\s\S]*?)</nav>', self.html_content)
        self.assertIsNotNone(nav_match, "缺失移动端底栏<nav>标签！")
        matches = re.findall(r'data-tab="([^"]+)"', nav_match.group(1))
        self.assertGreaterEqual(len(matches), 5, "移动端底栏必须完整挂载data-tab属性！")
        for tab in matches:
            self.assertTrue(
                tab in ("tab-backtest", "tab-screener", "tab-reflex", "tab-paper", "tab-multiasset"),
                f"未知非法底栏Tab挂载: {tab}"
            )

    def test_modal_backdrop_dismissal(self) -> None:
        """宪法第13条：弹窗遮罩层必须支持背景盲操点击即刻关闭"""
        self.assertIn('onclick="if(event.target===this) closeModal()"', self.html_content,
                      "移动端违宪：模态弹窗未实装遮罩层点击秒关！")

    def test_kline_redraw_on_tab_switch(self) -> None:
        """宪法第7条第3款：切Tab必须触发requestAnimationFrame重绘K线防模糊失真"""
        pattern = r"if\s*\(\s*tabId\s*===\s*['\"]tab-reflex['\"]\s*\)[\s\S]*?drawKlineChart"
        self.assertTrue(bool(re.search(pattern, self.html_content)),
                        "渲染违宪：切换至分形K线Tab时未触发drawKlineChart重绘！")

    def test_touchend_tooltip_decay(self) -> None:
        """宪法第7条第3款：触控浮层必须在touchend离开后自动淡出自愈"""
        self.assertIn("tooltipDismissTimer", self.html_content,
                      "交互违宪：缺失触屏离开后的Tooltip自动淡出定时器，存在霸屏遮挡缺陷！")

    def test_friction_cost_beginner_transparency(self) -> None:
        """认知人机工程：真实摩擦成本必须配备新手通俗大白话全息透视卡"""
        self.assertIn("新手白话透视", self.html_content, "认知缺陷：缺失摩擦成本新手大白话透视卡！")
        self.assertIn("1,000,000", self.html_content, "认知缺陷：缺失100万初始本金对照基准！")
        self.assertIn("59 笔", self.html_content, "认知缺陷：缺失59笔累计调仓笔数透明化！")
        self.assertIn("跌 50% 需要暴涨 100% 才能回本", self.html_content, "科普缺陷：缺失波动拖累大白话解释！")

    def test_kline_zero_visual_occlusion(self) -> None:
        """视觉人机工程：K线蜡烛图上方必须配备独立行情看板条，严禁遮挡蜡烛图主体"""
        self.assertIn('id="klineTopTickerBar"', self.html_content,
                      "视觉缺陷：缺失顶部独立行情看板条，存在蜡烛图被浮层遮挡的严重缺陷！")
        self.assertIn('id="tickerSymbolTag"', self.html_content, "缺失顶部看板标的代码标签！")
        self.assertIn('id="tickerChangeTag"', self.html_content, "缺失顶部看板涨跌幅标签！")

    def test_six_financial_market_sectors_completeness(self) -> None:
        """金融市场本体论：必须全量支持六大专属金融市场板块及大盘基准全谱系联动"""
        self.assertIn("switchMarketSector", self.html_content, "缺失市场大板块切换函数！")
        self.assertIn("MARKET_SECTORS", self.html_content, "缺失六大金融市场结构化数据集！")
        # 验证六大专属市场板块
        for sector in ("ashare", "futures", "hkstock", "usstock", "forex", "crypto"):
            self.assertIn(f"switchMarketSector('{sector}'", self.html_content,
                          f"市场残缺：缺失【{sector}】专属市场板块！")
        # 验证大盘基准指数
        for bm in ("上证指数", "南华商品综合指数", "恒生指数", "标普500指数", "美元指数", "全球加密总市值"):
            self.assertIn(bm, self.html_content, f"基准缺失：缺失【{bm}】大盘基准指数！")

    def test_dual_agent_hooks_and_cursor_rules(self) -> None:
        """宪法第11条：必须挂载 Antigravity 本地 Hooks 与 Cursor 规则双轨门禁"""
        # 1. Antigravity Hook 物理检验
        hook_path = os.path.join(self.workspace_root, ".agents", "hooks.json")
        self.assertTrue(os.path.exists(hook_path), "缺失 Antigravity 本地生命周期钩子: .agents/hooks.json！")
        import json
        with open(hook_path, "r", encoding="utf-8") as fp:
            hook_data = json.load(fp)
        self.assertIn("bionic-reflex-guard", hook_data, "缺失 bionic-reflex-guard 物理钩子配置！")
        guard_cfg = hook_data["bionic-reflex-guard"]
        self.assertIn("Stop", guard_cfg, "缺失 Stop 停机拦截物理钩子！")
        self.assertIn("PreToolUse", guard_cfg, "缺失 PreToolUse 写入物理守卫！")
        self.assertIn("PreInvocation", guard_cfg, "缺失 PreInvocation 仿生自激备忘钩子！")

        # 2. 守卫脚本物理检验
        script_path = os.path.join(self.workspace_root, "scripts", "reflex_guard_hook.py")
        self.assertTrue(os.path.exists(script_path), "缺失守卫脚本 scripts/reflex_guard_hook.py！")

        # 3. Cursor 规则物理检验
        cursor_path = os.path.join(self.workspace_root, ".cursorrules")
        self.assertTrue(os.path.exists(cursor_path), "缺失 Cursor 核心规则文件 .cursorrules！")
        with open(cursor_path, "r", encoding="utf-8") as fp:
            cr_content = fp.read()
        self.assertIn("Single-File <= 300 Lines Law", cr_content, "Cursor 规则缺失 300 行红线！")
        self.assertIn("Alimentary Digestive Autonomic Law", cr_content, "Cursor 规则缺失自律消化反射！")

        mdc_path = os.path.join(self.workspace_root, ".cursor", "rules", "trinity_bio_cybernetic.mdc")
        self.assertTrue(os.path.exists(mdc_path), "缺失 Cursor 现代 mdc 规则文件！")

        # 4. 宪法第十章、第十一章与第十二章检验
        agents_path = os.path.join(self.workspace_root, "AGENTS.md")
        with open(agents_path, "r", encoding="utf-8") as fp:
            agents_md = fp.read()
        self.assertIn("第十章 仿生跨学科多重神经突触反射与自律神经中枢最高立宪", agents_md)
        self.assertIn("第十一章 双轨本地智能体（Antigravity 与 Cursor）物理 Hook 与自愈闭环铁律", agents_md)
        self.assertIn("第十二章 跨学科知识裂变创新、防 AI 奖励造假与自发千问自激最高立宪", agents_md)
        self.assertIn("Anti-Reward Hacking & Anti-Model Deception Law", agents_md)

    def test_interdisciplinary_innovation_and_anti_deception(self) -> None:
        """宪法第12章：验证跨学科创新与对偶抗造假审查者一票否决门禁"""
        from gravity_brain.interdisciplinary_innovator import (
            InterdisciplinaryInnovator, DeceptionVerdict
        )
        engine = InterdisciplinaryInnovator()
        # 零摩擦伪量化必须被一票否决
        fraud_rep = engine.audit_strategy_authenticity(
            annualized_return=0.3, annualized_volatility=0.1, sharpe_ratio=2.0,
            total_friction_cost=0.0, max_drawdown=0.05, cvar_99=0.08
        )
        self.assertEqual(fraud_rep.verdict, DeceptionVerdict.ZERO_FRICTION_FRAUD)
        self.assertFalse(fraud_rep.is_authentic)

    def test_article_24_profit_integrity_and_monotonic_ratchet(self) -> None:
        """宪法第24条：严禁为迎合盈利而放宽风控参数（单向棘轮只严不宽）与外行毒蘑菇绝对阻断"""
        agents_path = os.path.join(self.workspace_root, "AGENTS.md")
        with open(agents_path, "r", encoding="utf-8") as fp:
            agents_md = fp.read()
        self.assertIn("第 24 条：严禁为迎合盈利目标而擅自放宽风控与拆除防线铁律", agents_md)
        self.assertIn("Monotonic Risk Ratchet Law", agents_md)

        from entropy_execution.profit_integrity_guard import (
            ProfitIntegrityGuard, RiskRelaxationForbiddenError, IntegrityVerdict
        )
        # 放宽单日回撤由2%至5%必须被阻断
        with self.assertRaises(RiskRelaxationForbiddenError):
            ProfitIntegrityGuard.validate_parameter_update("max_daily_drawdown", 0.02, 0.05)

        # 降低造血纯度门槛由0.30至0.10必须被阻断
        with self.assertRaises(RiskRelaxationForbiddenError):
            ProfitIntegrityGuard.validate_parameter_update("min_blood_purity", 0.30, 0.10)

        # 外行毒蘑菇标的一票否决
        is_safe, warn = ProfitIntegrityGuard.inspect_toddler_mushroom_safety(
            symbol="000999.SZ", blood_purity=0.15, debt_toxicity=0.50
        )
        self.assertFalse(is_safe)
        self.assertIn("剧毒蘑菇绝对拦截", warn)

    def test_article_25_universal_anti_goal_cheating(self) -> None:
        """宪法第25条：全领域严禁为迎合考核目标造假与拆除底线及1000问代码落地检验"""
        # 1. 宪法文本检验
        agents_path = os.path.join(self.workspace_root, "AGENTS.md")
        with open(agents_path, "r", encoding="utf-8") as fp:
            agents_md = fp.read()
        self.assertIn("第 25 条：全领域多学科严禁为迎合考核目标而造假与拆除底线总则", agents_md)
        self.assertIn("Universal Anti-Goal-Cheating & Environmental Grounding Law", agents_md)

        # 2. 全领域反目标作弊物理阻断检验
        from universal_quality_engine.universal_1000_synthesizer import (
            Universal1000Synthesizer, AntiGoalCheatingViolationError
        )
        with self.assertRaises(AntiGoalCheatingViolationError):
            Universal1000Synthesizer.audit_universal_goal_integrity(
                domain="education",
                goal_name="completion_rate",
                target_value=95.0,
                achieved_value=99.0,
                safety_invariants_relaxed=True,  # 试图拆除防线换取达标
                data_faked=False,
                full_environmental_friction_included=True
            )

        # 3. 1000 题代码落地检验机制
        rep = Universal1000Synthesizer.verify_1000_probes_implemented_in_code(
            domain="quantitative_finance",
            implemented_check_ids=list(range(1, 1001))
        )
        self.assertTrue(rep.is_fully_certified)
        self.assertEqual(rep.implementation_coverage_pct, 100.0)

    def test_article_26_anti_tofu_dreg_craftsmanship(self) -> None:
        """宪法第26条：工程落地实施防偷工减料与高标准施工防豆腐渣质检"""
        # 1. 宪法文本检验
        agents_path = os.path.join(self.workspace_root, "AGENTS.md")
        with open(agents_path, "r", encoding="utf-8") as fp:
            agents_md = fp.read()
        self.assertIn("第 26 条：工程落地实施防偷工减料与高标准施工千问立宪", agents_md)
        self.assertIn("Anti-Tofu-Dreg Construction & Craftsmanship Execution Law", agents_md)

        # 2. 全仓防豆腐渣施工质检扫描（要求 GRADE_AAA_FORTRESS）
        from universal_quality_engine.craftsmanship_execution_guard import (
            CraftsmanshipExecutionGuard, StructuralGrade
        )
        audit_rep = CraftsmanshipExecutionGuard.audit_workspace_craftsmanship(self.workspace_root)
        self.assertTrue(
            audit_rep.is_certified,
            f"施工违宪：全仓发现豆腐渣偷工减料隐患！清单: {audit_rep.tofu_dreg_violations}"
        )
        self.assertEqual(audit_rep.grade, StructuralGrade.GRADE_AAA_FORTRESS)

    def test_domestic_futures_universe_and_mobile_kline_jump(self) -> None:
        """宪法第25条：国内期货宇宙完整性（>=30标的、5大细分板块）与触控K线跳转微观契约看板"""
        for cat in ("🏛️ 金融国债", "🏗️ 黑色建材", "🥇 有色新能源", "🛢️ 能化能源", "🌾 农产品软商品"):
            self.assertIn(cat, self.html_content, f"期货板块残缺：缺失【{cat}】！")
        for sym in ("IF", "IC", "IM", "IH", "T", "TL", "RB", "HC", "I", "J", "JM", "CU", "AL", "ZN", "NI", "AU", "AG", "LC", "SC", "SA", "FG", "MA", "TA", "PP", "BU", "FU", "C", "M", "P", "Y", "SR", "CF", "LH", "AP"):
            self.assertIn(f"'{sym}'", self.html_content, f"缺失标的【{sym}】！")
        self.assertIn("scrollIntoView({ behavior: 'smooth', block: 'start' })", self.html_content)
        self.assertIn("ring-cyan-400", self.html_content)
        self.assertIn('id="tickerMicroSpecBar"', self.html_content)
        self.assertIn("自然人客户禁止进入交割月", self.html_content)

    def test_article_27_dynamic_pool_admission_traceability(self) -> None:
        """宪法第27条：标的动态深研入池、科学依据可追溯与严禁静态伪造标的池"""
        agents_path = os.path.join(self.workspace_root, "AGENTS.md")
        with open(agents_path, "r", encoding="utf-8") as fp:
            agents_md = fp.read()
        self.assertIn("第 27 条：标的动态深研入池、科学依据可追溯与严禁静态伪造池宪法", agents_md)
        self.assertIn("Dynamic Pool Admission & Epistemological Traceability Law", agents_md)

        from truth_kernel.pool_admission_auditor import PoolAdmissionAuditor
        # 审计核心主力标的入池法证完整性（杜绝拍脑袋与伪入池）
        ashare_syms = ["600519.SH", "300750.SZ", "600900.SH", "002594.SZ", "600036.SH", "601318.SH", "000858.SZ", "601899.SH"]
        is_valid, violations = PoolAdmissionAuditor.audit_pool_authenticity(ashare_syms)
        self.assertTrue(is_valid, f"标的入池法证违规: {violations}")

        # 前端全息看板与入池档案实装断言
        self.assertIn('id="admissionDocketModal"', self.html_content, "缺失入池法证研报弹窗！")
        self.assertIn("openAdmissionDocketModal", self.html_content, "缺失打开入池法证档案函数！")
        self.assertIn("ADMISSION_DOCKETS", self.html_content, "缺失标的入池深度研报数据集！")
        self.assertIn("入池深研依据", self.html_content, "缺失入池深研依据按钮！")

        # 双轨智能体规则（Cursor）对齐断言
        with open(os.path.join(self.workspace_root, ".cursorrules"), "r", encoding="utf-8") as f:
            self.assertIn("Article 27 Rules", f.read())
        with open(os.path.join(self.workspace_root, ".cursor", "rules", "trinity_bio_cybernetic.mdc"), "r", encoding="utf-8") as f:
            self.assertIn("Article 27", f.read())


if __name__ == "__main__":
    unittest.main()
