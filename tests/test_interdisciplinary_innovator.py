"""
tests/test_interdisciplinary_innovator.py
=========================================
验证跨学科知识创新与对偶抗欺骗审计引擎。
单文件严格控制在 300 行以内，零伪 Mock，全真实数值断言。
"""

import unittest

from gravity_brain.interdisciplinary_innovator import (
    DeceptionVerdict,
    InterdisciplinaryInnovator,
)


class TestInterdisciplinaryInnovator(unittest.TestCase):
    """跨学科创新与对偶抗欺骗单元测试"""

    def setUp(self) -> None:
        self.engine = InterdisciplinaryInnovator(max_allowed_sharpe=3.5)

    def test_zero_friction_fraud_rejected(self) -> None:
        """测试零摩擦伪量化欺骗被对偶审查者一票否决"""
        report = self.engine.audit_strategy_authenticity(
            annualized_return=0.35,
            annualized_volatility=0.15,
            sharpe_ratio=2.1,
            total_friction_cost=0.0,  # 零摩擦！
            max_drawdown=0.08,
            cvar_99=0.12,
            has_pit_alignment=True
        )
        self.assertFalse(report.is_authentic)
        self.assertEqual(report.verdict, DeceptionVerdict.ZERO_FRICTION_FRAUD)
        self.assertIn("毒蘑菇警告", report.toddler_friendly_warning)

    def test_lookahead_bias_rejected(self) -> None:
        """测试未来函数时点穿越被对偶审查者一票否决"""
        report = self.engine.audit_strategy_authenticity(
            annualized_return=0.25,
            annualized_volatility=0.12,
            sharpe_ratio=1.8,
            total_friction_cost=15000.0,
            max_drawdown=0.06,
            cvar_99=0.10,
            has_pit_alignment=False  # 缺乏真实披露日对齐！
        )
        self.assertFalse(report.is_authentic)
        self.assertEqual(report.verdict, DeceptionVerdict.LOOKAHEAD_BIAS)
        self.assertIn("偷看答案", report.toddler_friendly_warning)

    def test_overfitting_sharpe_rejected(self) -> None:
        """测试虚高夏普比率过拟合被对偶审查者一票否决"""
        report = self.engine.audit_strategy_authenticity(
            annualized_return=1.20,
            annualized_volatility=0.10,
            sharpe_ratio=4.8,  # 畸高夏普！
            total_friction_cost=25000.0,
            max_drawdown=0.04,
            cvar_99=0.08,
            has_pit_alignment=True
        )
        self.assertFalse(report.is_authentic)
        self.assertEqual(report.verdict, DeceptionVerdict.OVERFITTING_SNOOPING)
        self.assertIn("镜花水月", report.toddler_friendly_warning)

    def test_authentic_passed(self) -> None:
        """测试全摩擦、时点对齐、真实尾部风险的健康策略通过审查"""
        report = self.engine.audit_strategy_authenticity(
            annualized_return=0.22,
            annualized_volatility=0.14,
            sharpe_ratio=1.45,
            total_friction_cost=67614.9,  # 计提真实税费
            max_drawdown=0.095,
            cvar_99=0.14,
            has_pit_alignment=True
        )
        self.assertTrue(report.is_authentic)
        self.assertEqual(report.verdict, DeceptionVerdict.AUTHENTIC_PASSED)
        self.assertEqual(report.risk_score_penalty, 0.0)
        self.assertIn("纯净营养", report.toddler_friendly_warning)

    def test_interdisciplinary_asset_evaluation(self) -> None:
        """测试跨学科资产融合定价与蘑菇验毒"""
        # 1. 茅台型健康资产
        synth_good = self.engine.evaluate_interdisciplinary_asset(
            symbol="600519.SH",
            current_price=1550.0,
            dcf_value=2200.0,
            phi_cp=1.54,
            omega_debt=0.0,
            recent_price_change_pct=0.05,
            market_sentiment_bias=0.2,
            historical_volatility=0.18
        )
        self.assertTrue(synth_good.is_safe_to_consume)
        self.assertGreater(synth_good.cybernetic_kelly_fraction, 0.0)
        self.assertIn("金种子", synth_good.toddler_verdict_card)

        # 2. 康美/万科型造血坏疽毒蘑菇
        synth_poison = self.engine.evaluate_interdisciplinary_asset(
            symbol="BAD_CORP",
            current_price=20.0,
            dcf_value=15.0,
            phi_cp=0.08,  # 造血严重坏死
            omega_debt=3.5,
            recent_price_change_pct=-0.15,
            market_sentiment_bias=-0.8,
            historical_volatility=0.45
        )
        self.assertFalse(synth_poison.is_safe_to_consume)
        self.assertEqual(synth_poison.cybernetic_kelly_fraction, 0.0)
        self.assertIn("毒蘑菇", synth_poison.toddler_verdict_card)


if __name__ == "__main__":
    unittest.main()
