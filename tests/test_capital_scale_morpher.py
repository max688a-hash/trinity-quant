"""
tests/test_capital_scale_morpher.py
===================================
资金体量自适应形态变形器 (CapitalScaleMorpher) 单元测试。
确保个人微型资金 (1~10万) 到机构巨鲸资金 (1000万+) 的全自适应平滑演进。
"""

import unittest
from entropy_execution.capital_scale_morpher import (
    CapitalScaleMorpher,
    CapitalScaleTier,
)


class TestCapitalScaleMorpher(unittest.TestCase):

    def test_micro_guerrilla_tier(self) -> None:
        """测试 2万元 个人极小资金：集中优势兵力，严禁算法拆单防吃5元最低佣金"""
        profile = CapitalScaleMorpher.resolve_profile(equity=20_000.0)
        self.assertEqual(profile.tier, CapitalScaleTier.MICRO_GUERRILLA)
        self.assertEqual(profile.max_concentration_ratio, 0.60)
        self.assertFalse(profile.enable_algorithmic_slicing)
        self.assertTrue(profile.min_commission_defense)
        self.assertEqual(profile.target_asset_count, 2)
        self.assertEqual(profile.daily_drawdown_circuit_breaker_pct, 0.04)
        self.assertIn("游击狙击", profile.display_title)

    def test_tactical_cruiser_tier(self) -> None:
        """测试 50万元 个人成长/进阶大户资金：攻守平衡"""
        profile = CapitalScaleMorpher.resolve_profile(equity=500_000.0)
        self.assertEqual(profile.tier, CapitalScaleTier.TACTICAL_CRUISER)
        self.assertEqual(profile.max_concentration_ratio, 0.35)
        self.assertFalse(profile.enable_algorithmic_slicing)
        self.assertEqual(profile.target_asset_count, 4)
        self.assertEqual(profile.daily_drawdown_circuit_breaker_pct, 0.03)

    def test_dreadnought_fleet_tier(self) -> None:
        """测试 200万元 高净值/准机构资金：冰山拆单，方差拖累压制"""
        profile = CapitalScaleMorpher.resolve_profile(equity=2_000_000.0)
        self.assertEqual(profile.tier, CapitalScaleTier.DREADNOUGHT_FLEET)
        self.assertEqual(profile.max_concentration_ratio, 0.20)
        self.assertTrue(profile.enable_algorithmic_slicing)
        self.assertEqual(profile.target_asset_count, 7)
        self.assertEqual(profile.daily_drawdown_circuit_breaker_pct, 0.02)

    def test_whale_carrier_tier(self) -> None:
        """测试 1000万元 机构级巨鲸资金：容量优先，冲击滑点最小化，极严日内1.5%熔断"""
        profile = CapitalScaleMorpher.resolve_profile(equity=10_000_000.0)
        self.assertEqual(profile.tier, CapitalScaleTier.WHALE_CARRIER)
        self.assertEqual(profile.max_concentration_ratio, 0.12)
        self.assertTrue(profile.enable_algorithmic_slicing)
        self.assertEqual(profile.target_asset_count, 15)
        self.assertEqual(profile.daily_drawdown_circuit_breaker_pct, 0.015)
        self.assertIn("航母巨鲸", profile.display_title)

    def test_boundary_and_zero_protection(self) -> None:
        """测试临界值与零净值防御"""
        p_zero = CapitalScaleMorpher.resolve_profile(equity=0.0)
        self.assertEqual(p_zero.tier, CapitalScaleTier.MICRO_GUERRILLA)

        p_neg = CapitalScaleMorpher.resolve_profile(equity=-5000.0)
        self.assertEqual(p_neg.tier, CapitalScaleTier.MICRO_GUERRILLA)


if __name__ == "__main__":
    unittest.main()
