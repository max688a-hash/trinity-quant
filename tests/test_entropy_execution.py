"""
tests.test_entropy_execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
对熵减执行内核 (动态防爆凯利、真实摩擦模型、组合风险守护、事件驱动回测)
进行严密单元测试，严格践行宪法禁止无摩擦回测与算术均值造假铁律。
包含熔断清仓、负势能防御与极端行情黑天鹅压力测试。
"""

import unittest
from truth_kernel.models import (
    BalanceSheet,
    IncomeStatement,
    CashFlowStatement,
    CompanyFinancialRecord
)
from entropy_execution.dynamic_kelly import DynamicKellyAllocator
from entropy_execution.friction_engine import FrictionEngine
from entropy_execution.portfolio_guardian import PortfolioGuardian
from entropy_execution.backtest_engine import EventDrivenBacktester


class TestEntropyExecution(unittest.TestCase):
    """熵减执行与风控核心测试套件"""

    def setUp(self) -> None:
        self.kelly = DynamicKellyAllocator(cvar_penalty_gamma=2.5, max_single_position=0.20)
        self.friction = FrictionEngine(
            stamp_duty_rate=0.0005,
            commission_rate=0.0002,
            min_commission=5.0,
            slippage_rate=0.0010
        )
        self.guardian = PortfolioGuardian(
            risk_free_rate=0.025,
            drawdown_warning=0.08,
            drawdown_severe=0.12,
            drawdown_breaker=0.15
        )
        self.backtester = EventDrivenBacktester(
            initial_cash=1_000_000.0,
            friction_engine=self.friction,
            kelly_allocator=self.kelly,
            portfolio_guardian=self.guardian
        )

    def test_dynamic_kelly_veto_and_constraints(self) -> None:
        """测试动态凯利公式对未通过排毒标的的零容忍与单标的 20% 硬上限"""
        # 1. 一票否决清仓
        res_veto = self.kelly.calculate_weight(
            symbol="BAD_STOCK", win_rate=0.7, payoff_ratio=2.0,
            cvar_alpha=0.05, is_firewall_admitted=False
        )
        self.assertEqual(res_veto.target_weight, 0.0)
        self.assertTrue(res_veto.is_vetoed)

        # 2. 期望为负
        res_neg = self.kelly.calculate_weight(
            symbol="NO_EDGE", win_rate=0.3, payoff_ratio=1.0,
            cvar_alpha=0.05, is_firewall_admitted=True
        )
        self.assertEqual(res_neg.target_weight, 0.0)

        # 3. 极佳参数下的单标的 20% 硬约束
        res_max = self.kelly.calculate_weight(
            symbol="PERFECT", win_rate=0.9, payoff_ratio=5.0,
            cvar_alpha=0.01, gravity_potential=0.8, is_firewall_admitted=True
        )
        self.assertLessEqual(res_max.target_weight, 0.20)
        self.assertGreater(res_max.target_weight, 0.05)

        # 4. 高 CVaR 尾部风险显著压低仓位
        res_high_cvar = self.kelly.calculate_weight(
            symbol="HIGH_RISK", win_rate=0.65, payoff_ratio=2.0,
            cvar_alpha=0.40, gravity_potential=0.5, is_firewall_admitted=True
        )
        res_low_cvar = self.kelly.calculate_weight(
            symbol="LOW_RISK", win_rate=0.65, payoff_ratio=2.0,
            cvar_alpha=0.05, gravity_potential=0.5, is_firewall_admitted=True
        )
        self.assertLess(res_high_cvar.target_weight, res_low_cvar.target_weight)

        # 5. 市价严重高估 (G_potential <= 0)，仓位强制归零防御
        res_overvalued = self.kelly.calculate_weight(
            symbol="OVERVALUED", win_rate=0.7, payoff_ratio=2.0,
            cvar_alpha=0.05, gravity_potential=-0.20, is_firewall_admitted=True
        )
        self.assertEqual(res_overvalued.target_weight, 0.0)
        self.assertIn("市价高于真值", res_overvalued.allocation_reason)

        # 6. 未提供势能时默认保守因子
        res_neutral = self.kelly.calculate_weight(
            symbol="NEUTRAL", win_rate=0.7, payoff_ratio=2.0,
            cvar_alpha=0.05, gravity_potential=None, is_firewall_admitted=True
        )
        self.assertGreater(res_neutral.target_weight, 0.0)

    def test_friction_engine_stamp_duty_and_slippage(self) -> None:
        """测试真实交易摩擦：买入无印花税但有滑点，卖出严格扣税与双向佣金"""
        price = 100.0
        shares = 1000

        # 买入撮合
        buy_res = self.friction.execute_buy("600519.SH", price, shares)
        self.assertEqual(buy_res.stamp_duty, 0.0, "A 股买入绝无印花税")
        self.assertGreater(buy_res.executed_price, price, "买入滑点必须向上恶化")
        self.assertAlmostEqual(buy_res.executed_price, 100.10)
        self.assertGreaterEqual(buy_res.commission, 5.0)

        # 卖出撮合
        sell_res = self.friction.execute_sell("600519.SH", price, shares)
        self.assertGreater(sell_res.stamp_duty, 0.0, "A 股卖出必须计提印花税")
        self.assertAlmostEqual(sell_res.stamp_duty, 100000.0 * 0.0005)
        self.assertLess(sell_res.executed_price, price, "卖出滑点必须向下恶化")
        self.assertAlmostEqual(sell_res.executed_price, 99.90)

        # 非法输入校验
        with self.assertRaises(ValueError):
            self.friction.execute_buy("TEST", -10.0, 100)
        with self.assertRaises(ValueError):
            self.friction.execute_sell("TEST", 10.0, 0)

    def test_portfolio_guardian_drawdown_and_drag(self) -> None:
        """测试波动性拖累公式 0.5*σ^2 与阶梯式熔断阈值"""
        nav_curve = [100.0, 110.0, 120.0, 100.8, 105.0]
        metrics = self.guardian.evaluate_returns(nav_curve, periods_per_year=12)

        self.assertGreater(metrics.volatility_drag, 0.0)
        self.assertAlmostEqual(metrics.max_drawdown, 0.16)
        self.assertTrue(metrics.circuit_breaker_active, "触碰 15% 回撤线必须启动绝对熔断")
        self.assertIn("极度危险熔断", metrics.status_summary)

        # 空或单元素序列保护
        empty_m = self.guardian.evaluate_returns([])
        self.assertEqual(empty_m.cagr, 0.0)

    def test_event_driven_backtest_with_friction(self) -> None:
        """测试事件驱动全仿真回测：必须有摩擦成本扣除且劣质标的不可买入"""
        bs_good = BalanceSheet(1e10, 2e9, 8e9, 4e9, receivables=1e8)
        inc_good = IncomeStatement(3e9, 1.5e9, 1.2e9)
        cf_good = CashFlowStatement(1.5e9, 2e8)
        rec_good = CompanyFinancialRecord("GOOD", "2023-12-31", "2024-04-20", bs_good, inc_good, cf_good)

        bs_bad = BalanceSheet(1e10, 9e9, 1e9, 2e8, short_term_debt=5e9, receivables=4e9)
        inc_bad = IncomeStatement(1e9, -2e8, -3e8)
        cf_bad = CashFlowStatement(-5e8, 1e8)
        rec_bad = CompanyFinancialRecord("BAD", "2023-12-31", "2024-04-20", bs_bad, inc_bad, cf_bad)

        snapshots = [
            {"GOOD": rec_good, "BAD": rec_bad},
            {"GOOD": rec_good, "BAD": rec_bad},
            {"GOOD": rec_good, "BAD": rec_bad}
        ]
        prices = [
            {"GOOD": 100.0, "BAD": 10.0},
            {"GOOD": 105.0, "BAD": 8.0},
            {"GOOD": 110.0, "BAD": 5.0}
        ]

        report = self.backtester.run_simulation(snapshots, prices)
        self.assertGreater(report.total_trades, 0)
        self.assertGreater(report.total_friction_cost, 0.0)
        self.assertEqual(len(report.equity_curve), 4)

    def test_backtest_circuit_breaker_liquidation(self) -> None:
        """测试极端行情黑天鹅熔断：暴跌触碰熔断线时自动强制清仓保本"""
        heavy_kelly = DynamicKellyAllocator(cvar_penalty_gamma=0.5, max_single_position=0.90)
        test_guardian = PortfolioGuardian(drawdown_breaker=0.06)
        test_backtester = EventDrivenBacktester(
            initial_cash=1_000_000.0,
            friction_engine=self.friction,
            kelly_allocator=heavy_kelly,
            portfolio_guardian=test_guardian
        )

        bs = BalanceSheet(1e10, 2e9, 8e9, 4e9)
        inc = IncomeStatement(3e9, 1.5e9, 1.2e9)
        cf = CashFlowStatement(1.5e9, 2e8)
        rec = CompanyFinancialRecord("CRASH_TEST", "2023-12-31", "2024-04-20", bs, inc, cf)

        # 5 步极端单边暴跌，确保第 5 步触发熔断清仓
        snapshots = [{"CRASH_TEST": rec} for _ in range(5)]
        prices = [
            {"CRASH_TEST": 100.0},
            {"CRASH_TEST": 110.0},
            {"CRASH_TEST": 65.0},
            {"CRASH_TEST": 50.0},
            {"CRASH_TEST": 40.0}
        ]

        # 用更早样本内窗口的已平仓收益热启动（p=0.8, b=4），使凯利达到重仓以检验熔断路径
        warm = [0.20] * 16 + [-0.05] * 4
        report = test_backtester.run_simulation(snapshots, prices, warm_start_returns=warm)
        self.assertGreater(report.total_trades, 1)
        self.assertEqual(report.cold_start_periods, 0)
        self.assertTrue(report.risk_metrics.circuit_breaker_active)

    def test_backtest_cold_start_caps_exposure(self) -> None:
        """无实证样本时严禁写死胜率重仓：单期暴跌 60% 对组合影响必须封顶在冷启动探仓以内"""
        bs = BalanceSheet(1e10, 2e9, 8e9, 4e9)
        inc = IncomeStatement(3e9, 1.5e9, 1.2e9)
        cf = CashFlowStatement(1.5e9, 2e8)
        rec = CompanyFinancialRecord("COLD", "2023-12-31", "2024-04-20", bs, inc, cf)
        report = EventDrivenBacktester(initial_cash=1_000_000.0, cold_start_weight=0.02).run_simulation(
            [{"COLD": rec}] * 2, [{"COLD": 100.0}, {"COLD": 40.0}]
        )
        self.assertEqual(report.cold_start_periods, 2)
        self.assertGreaterEqual(report.final_equity, 1_000_000.0 * (1 - 0.02 * 0.60 - 0.001))

    def test_backtest_pit_excludes_undisclosed_and_liquidates_delisted(self) -> None:
        """披露日晚于调仓日的报表不可见；退市标的按最后已知价强制清算"""
        from datetime import date
        bs = BalanceSheet(1e10, 2e9, 8e9, 4e9)
        inc = IncomeStatement(3e9, 1.5e9, 1.2e9)
        cf = CashFlowStatement(1.5e9, 2e8)
        late = CompanyFinancialRecord("LATE", "2024-03-31", "2024-04-28", bs, inc, cf)
        ok = CompanyFinancialRecord("OK", "2023-12-31", "2024-03-20", bs, inc, cf)
        snaps = [{"LATE": late, "OK": ok}, {"LATE": late, "OK": ok}]
        prices = [{"LATE": 10.0, "OK": 20.0}, {"LATE": 10.0}]
        report = EventDrivenBacktester(initial_cash=1_000_000.0).run_simulation(
            snaps, prices, rebalance_dates=[date(2024, 3, 31), date(2024, 6, 30)],
            last_known_prices=[{}, {"OK": 5.0}],
        )
        self.assertEqual(report.pit_excluded_records, 1)
        self.assertEqual(len(report.forced_liquidations), 1)
        self.assertIn("OK@2024-06-30:5.0", report.forced_liquidations[0])


if __name__ == "__main__":
    unittest.main()
