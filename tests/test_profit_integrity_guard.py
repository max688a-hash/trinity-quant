"""
tests/test_profit_integrity_guard.py
======================================
单元测试：盈利真实性守恒、单向棘轮风控与婴幼儿毒蘑菇绝对阻断防线。
"""

import unittest

from entropy_execution.profit_integrity_guard import (
    IntegrityVerdict,
    ProfitIntegrityGuard,
    RiskRelaxationForbiddenError,
)


class TestProfitIntegrityGuard(unittest.TestCase):
    """测试单向棘轮风控与反盈利造假网关"""

    def test_ratchet_drawdown_relaxation_forbidden(self) -> None:
        """验证严禁放宽单日最大回撤限额"""
        with self.assertRaises(RiskRelaxationForbiddenError):
            ProfitIntegrityGuard.validate_parameter_update(
                param_name="max_daily_drawdown",
                current_val=0.02,
                proposed_val=0.05
            )

    def test_ratchet_drawdown_tightening_allowed(self) -> None:
        """验证允许收紧单日最大回撤限额（从严）"""
        self.assertTrue(
            ProfitIntegrityGuard.validate_parameter_update(
                param_name="max_daily_drawdown",
                current_val=0.02,
                proposed_val=0.015
            )
        )

    def test_ratchet_blood_purity_relaxation_forbidden(self) -> None:
        """验证严禁降低造血纯度准入门槛"""
        with self.assertRaises(RiskRelaxationForbiddenError):
            ProfitIntegrityGuard.validate_parameter_update(
                param_name="min_blood_purity",
                current_val=0.30,
                proposed_val=0.15
            )

    def test_ratchet_friction_reduction_forbidden(self) -> None:
        """验证严禁为了纸面盈利而调低滑点费率"""
        with self.assertRaises(RiskRelaxationForbiddenError):
            ProfitIntegrityGuard.validate_parameter_update(
                param_name="min_slippage",
                current_val=0.0010,
                proposed_val=0.0001
            )

    def test_toddler_mushroom_toxic_veto(self) -> None:
        """验证外行毒蘑菇标的绝对物理阻断"""
        is_safe, warn = ProfitIntegrityGuard.inspect_toddler_mushroom_safety(
            symbol="000001.SZ",
            blood_purity=0.10,  # 严重造血不足
            debt_toxicity=0.65,  # 严重债务违约风险
            pledge_ratio=0.70   # 严重质押
        )
        self.assertFalse(is_safe)
        self.assertIn("剧毒蘑菇绝对拦截", warn)
        self.assertIn("一票否决", warn)

    def test_toddler_mushroom_clean_pass(self) -> None:
        """验证纯净造血标的正常准入"""
        is_safe, warn = ProfitIntegrityGuard.inspect_toddler_mushroom_safety(
            symbol="600519.SH",
            blood_purity=0.88,
            debt_toxicity=0.08,
            pledge_ratio=0.0
        )
        self.assertTrue(is_safe)
        self.assertIn("造血纯净", warn)

    def test_audit_toxic_mushroom_rejected(self) -> None:
        """验证策略掺杂毒蘑菇标的被一票否决"""
        rep = ProfitIntegrityGuard.audit_profit_claim(
            gross_profit=100_000.0,
            friction_paid=5_000.0,
            trades_count=20,
            max_drawdown=0.05,
            has_toxic_assets=True
        )
        self.assertFalse(rep.is_approved)
        self.assertEqual(rep.verdict, IntegrityVerdict.REJECT_TOXIC_MUSHROOM)

    def test_audit_moving_stop_loss_rejected(self) -> None:
        """验证策略推迟止损操纵胜率被当场熔断"""
        rep = ProfitIntegrityGuard.audit_profit_claim(
            gross_profit=100_000.0,
            friction_paid=5_000.0,
            trades_count=20,
            max_drawdown=0.05,
            stop_loss_loosened=True
        )
        self.assertFalse(rep.is_approved)
        self.assertEqual(rep.verdict, IntegrityVerdict.REJECT_MOVING_STOP_LOSS)

    def test_audit_zero_friction_rejected(self) -> None:
        """验证零摩擦假量化被拦截"""
        rep = ProfitIntegrityGuard.audit_profit_claim(
            gross_profit=100_000.0,
            friction_paid=0.0,
            trades_count=20,
            max_drawdown=0.05
        )
        self.assertFalse(rep.is_approved)
        self.assertEqual(rep.verdict, IntegrityVerdict.REJECT_ZERO_FRICTION)

    def test_audit_genuine_profit_verified(self) -> None:
        """验证全摩擦真实盈利获得合规认证"""
        rep = ProfitIntegrityGuard.audit_profit_claim(
            gross_profit=100_000.0,
            friction_paid=12_000.0,
            trades_count=30,
            max_drawdown=0.04
        )
        self.assertTrue(rep.is_approved)
        self.assertEqual(rep.verdict, IntegrityVerdict.VERIFIED_AUTHENTIC)
        self.assertEqual(rep.net_profit_after_friction, 88_000.0)


if __name__ == "__main__":
    unittest.main()
