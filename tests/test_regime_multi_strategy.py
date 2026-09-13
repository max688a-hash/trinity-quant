"""
tests/test_regime_multi_strategy.py
===================================
单元测试：市场状态机、多策略矩阵调度与元凯利资金分配器。
"""

import unittest
from gravity_brain.market_regime_classifier import MarketRegime, MarketRegimeClassifier
from gravity_brain.meta_kelly_allocator import MetaKellyAllocator
from gravity_brain.regime_multi_strategy_engine import RegimeMultiStrategyEngine, StrategySignalAction


class TestRegimeMultiStrategy(unittest.TestCase):
    """测试多策略矩阵与状态机协同"""

    def test_hurst_and_classification(self) -> None:
        """验证分形 Hurst 计算与状态判定"""
        # 强单边上涨序列
        bull_prices = [100.0 * (1.008 ** i) for i in range(40)]
        res_bull = MarketRegimeClassifier.classify_regime(bull_prices)
        self.assertEqual(res_bull.regime, MarketRegime.BULL_TREND)
        self.assertGreaterEqual(res_bull.hurst_exponent, 0.50)

        # 宽幅震荡序列
        choppy_prices = [100.0 + 3.0 * (-1 if i % 2 == 0 else 1) for i in range(40)]
        res_choppy = MarketRegimeClassifier.classify_regime(choppy_prices)
        self.assertEqual(res_choppy.regime, MarketRegime.CHOPPY_OSCILLATING)

        # 极端暴跌闪崩序列
        crash_prices = [100.0] * 10 + [100.0 * (0.90 ** i) for i in range(1, 15)]
        res_crash = MarketRegimeClassifier.classify_regime(crash_prices)
        self.assertEqual(res_crash.regime, MarketRegime.EXTREME_VOLATILE_CRISIS)

    def test_multi_strategy_engine_signals(self) -> None:
        """验证多策略自适应决策输出"""
        # 1. 牛市创新高触发突破买入
        bull_prices = [100.0 + i * 1.5 for i in range(30)]
        sig_bull = RegimeMultiStrategyEngine.evaluate_symbol("600519.SH", bull_prices, bull_prices[-1])
        self.assertEqual(sig_bull.active_strategy, "TrendBreakoutStrategy")
        self.assertEqual(sig_bull.action, StrategySignalAction.BUY_LONG)

        # 2. 震荡市超卖触发均值回归
        osc_prices = [100.0] * 25
        # 现价跌破下轨
        sig_osc = RegimeMultiStrategyEngine.evaluate_symbol("002594.SZ", osc_prices, 90.0)
        self.assertEqual(sig_osc.active_strategy, "MeanReversionPairsStrategy")
        self.assertEqual(sig_osc.action, StrategySignalAction.BUY_LONG)

        # 3. 极端黑天鹅强制防爆
        crash_prices = [100.0] * 10 + [100.0 * (0.85 ** i) for i in range(1, 15)]
        sig_crash = RegimeMultiStrategyEngine.evaluate_symbol("BTCUSDT", crash_prices, 50.0)
        self.assertEqual(sig_crash.active_strategy, "TailRiskHedgingStrategy")
        self.assertEqual(sig_crash.action, StrategySignalAction.CLOSE_POSITION)

    def test_meta_kelly_allocations(self) -> None:
        """验证元凯利分配权重约束与单向棘轮"""
        # 牛市权重
        w_bull = MetaKellyAllocator.compute_allocations(MarketRegime.BULL_TREND)
        self.assertGreater(w_bull.trend_breakout_weight, w_bull.mean_reversion_weight)
        self.assertLessEqual(w_bull.total_leverage, 0.80)

        # 震荡市权重
        w_choppy = MetaKellyAllocator.compute_allocations(MarketRegime.CHOPPY_OSCILLATING)
        self.assertGreater(w_choppy.mean_reversion_weight, w_choppy.trend_breakout_weight)
        self.assertLessEqual(w_choppy.total_leverage, 0.80)

        # 危机市场权重
        w_crisis = MetaKellyAllocator.compute_allocations(MarketRegime.EXTREME_VOLATILE_CRISIS)
        self.assertEqual(w_crisis.trend_breakout_weight, 0.0)
        self.assertEqual(w_crisis.mean_reversion_weight, 0.0)
        self.assertLessEqual(w_crisis.total_leverage, 0.10)
        self.assertGreaterEqual(w_crisis.cash_buffer_weight, 0.90)


if __name__ == "__main__":
    unittest.main()
