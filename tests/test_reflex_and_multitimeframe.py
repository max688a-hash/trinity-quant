"""
tests/test_reflex_and_multitimeframe.py
=======================================
TRINITY QUANT 仿生神经反射与多时间尺度分形共振测试套件。

严格验证：
1. 脊髓原始本能反射：闪崩与数据破坏瞬间切断与清仓 (BioReflexCentral)
2. 自主神经内稳态：高波收缩敞口与利润回撤阶梯锁利
3. 多周期分形三位一体：大周期定趋势、中周期看结构、小周期看触发
4. 逆势诱多假反弹物理拦截：大周期下跌时日内反弹一票观望
"""

import unittest
from immune_system.reflex_system import (
    BioReflexCentral,
    ReflexLevel,
)
from gravity_brain.multi_timeframe_fractal import (
    MultiTimeframeFractalEngine,
    ResonanceGrade,
    StructuralPattern,
    TrendDirection,
)


class TestBioReflexCentral(unittest.TestCase):
    """测试仿生神经反射中枢"""

    def setUp(self) -> None:
        self.reflex = BioReflexCentral(panic_gap_threshold=0.07)

    def test_primitive_spinal_flash_crash(self) -> None:
        # 突发闪崩 -9% -> 脊髓弧零思考瞬间熔断
        cmd = self.reflex.evaluate_primitive_reflex(
            symbol="FLASH_01",
            instant_price_drop_pct=-0.09,
            is_limit_down_locked=False,
            is_data_corrupted=False
        )
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.level, ReflexLevel.PRIMITIVE_SPINAL)
        self.assertEqual(cmd.action_type, "PANIC_EMERGENCY_EXIT")
        self.assertTrue(cmd.bypass_deliberation)

    def test_primitive_data_corruption(self) -> None:
        cmd = self.reflex.evaluate_primitive_reflex(
            symbol="FEED_01",
            instant_price_drop_pct=0.0,
            is_limit_down_locked=False,
            is_data_corrupted=True
        )
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.action_type, "EMERGENCY_FREEZE_GATE")

    def test_autonomic_profit_ratchet(self) -> None:
        # 利润高位回撤 10% -> 自主神经锁利
        cmd = self.reflex.evaluate_autonomic_reflex("POS_01", current_volatility_z=1.0, profit_drawdown_from_peak=0.10)
        self.assertEqual(cmd.action_type, "RATCHET_LOCK_PROFIT")


class TestMultiTimeframeFractalEngine(unittest.TestCase):
    """测试多时间尺度分形共振动力学"""

    def setUp(self) -> None:
        self.engine = MultiTimeframeFractalEngine()

    def test_bull_resonance(self) -> None:
        # 大周期日线多头 (均线上行)
        macro = [100.0 + i * 2.0 for i in range(25)]
        # 中周期小时线上行
        meso = [140.0 + i for i in range(12)]
        # 小周期分时走强 (现价 152 > 开盘 150)
        verdict = self.engine.evaluate_fractal_resonance("600519.SH", macro, meso, 152.0, 150.0)
        self.assertEqual(verdict.resonance_grade, ResonanceGrade.FULL_BULL_RESONANCE)
        self.assertEqual(verdict.allowed_direction, "BUY")
        self.assertEqual(verdict.confidence_multiplier, 1.0)

    def test_bearish_divergence_protects_against_bull_trap(self) -> None:
        # 大周期日线下跌通道
        macro = [200.0 - i * 2.0 for i in range(25)]
        # 中周期小时线破位
        meso = [160.0 - i for i in range(12)]
        # 但日内分时突发逆势上涨 (现价 148 > 开盘 145)
        verdict = self.engine.evaluate_fractal_resonance("TRAP_STOCK", macro, meso, 148.0, 145.0)
        self.assertEqual(verdict.resonance_grade, ResonanceGrade.DIVERGENT_CONFLICT)
        self.assertEqual(verdict.allowed_direction, "STAND_ASIDE")
        self.assertEqual(verdict.confidence_multiplier, 0.0)
        self.assertNotIn("诱多", verdict.detailed_thesis)
        self.assertIn("无量仓", verdict.detailed_thesis)


if __name__ == "__main__":
    unittest.main()
