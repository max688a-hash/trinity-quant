"""
tests/test_universal_1000_synthesizer.py
=========================================
单元测试：全领域 1000 问自激生成与全领域反目标造假最高宪法门禁。
"""

import unittest

from universal_quality_engine.universal_1000_synthesizer import (
    AntiGoalCheatingViolationError,
    Universal1000Synthesizer,
    UniversalProbeCategory,
)


class TestUniversal1000Synthesizer(unittest.TestCase):
    """测试通用 1000 问生成器与全领域反作弊引擎"""

    def test_synthesize_1000_probes_structure(self) -> None:
        """验证能为任意领域完整生成 10 大维度共 1,000 道深度质询"""
        probes = Universal1000Synthesizer.synthesize_1000_probes_for_domain("education")
        self.assertEqual(len(probes), 1000)
        categories = {p.category for p in probes}
        self.assertEqual(len(categories), 10)
        # 验证包含目标与守恒维度
        self.assertIn(UniversalProbeCategory.GOAL_VS_INVARIANT, categories)
        self.assertIn(UniversalProbeCategory.SOCIOTECHNICAL_ENV, categories)

    def test_anti_goal_cheating_relaxation_veto(self) -> None:
        """验证严禁为了迎合任何目标而放宽安全守恒防线（全领域一票否决）"""
        with self.assertRaises(AntiGoalCheatingViolationError):
            Universal1000Synthesizer.audit_universal_goal_integrity(
                domain="healthcare",
                goal_name="battery_saving",
                target_value=95.0,
                achieved_value=98.0,
                safety_invariants_relaxed=True,  # 试图为省电而关掉心跳骤停监测
                data_faked=False,
                full_environmental_friction_included=True
            )

    def test_anti_goal_cheating_faked_data_veto(self) -> None:
        """验证严禁为了迎合考核目标而伪造数据"""
        with self.assertRaises(AntiGoalCheatingViolationError):
            Universal1000Synthesizer.audit_universal_goal_integrity(
                domain="education",
                goal_name="student_passing_rate",
                target_value=90.0,
                achieved_value=92.0,
                safety_invariants_relaxed=False,
                data_faked=True,  # 伪造及格率
                full_environmental_friction_included=True
            )

    def test_anti_goal_cheating_friction_required(self) -> None:
        """验证必须计提真实环境摩擦损耗"""
        passed, msg = Universal1000Synthesizer.audit_universal_goal_integrity(
            domain="ecommerce",
            goal_name="order_fulfillment_speed",
            target_value=100.0,
            achieved_value=120.0,
            safety_invariants_relaxed=False,
            data_faked=False,
            full_environmental_friction_included=False  # 未计提真实网络延迟和物流丢件
        )
        self.assertFalse(passed)
        self.assertIn("未全额计提真实物理与人类社会环境摩擦", msg)

    def test_verify_1000_probes_full_certification(self) -> None:
        """验证 1000 题全部落实到代码与测试时的完整认证"""
        all_ids = list(range(1, 1001))
        rep = Universal1000Synthesizer.verify_1000_probes_implemented_in_code(
            domain="quantitative_finance",
            implemented_check_ids=all_ids
        )
        self.assertTrue(rep.is_fully_certified)
        self.assertEqual(rep.implementation_coverage_pct, 100.0)
        self.assertEqual(len(rep.violations), 0)

    def test_verify_1000_probes_gap_detection(self) -> None:
        """验证当 1000 问中存在未落实到代码的缺口时拒绝认证"""
        partial_ids = list(range(1, 801))  # 仅实现了 800 题
        rep = Universal1000Synthesizer.verify_1000_probes_implemented_in_code(
            domain="new_app",
            implemented_check_ids=partial_ids
        )
        self.assertFalse(rep.is_fully_certified)
        self.assertEqual(rep.implementation_coverage_pct, 80.0)
        self.assertIn("尚有 200 项未在目标程序代码与测试中断言", rep.violations[0])


if __name__ == "__main__":
    unittest.main()
