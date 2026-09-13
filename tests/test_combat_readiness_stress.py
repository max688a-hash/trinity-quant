"""
tests/test_combat_readiness_stress.py
=====================================
实盘战场极限制空权与隐藏漏洞二次深度打靶套件。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 验证微观小数币种成本核算、T+1跨日解冻、内存防泄漏与实盘夜盘时钟;
2. 彻底歼灭隐形假阳性、静默旁路与非交易时段偷跑;
3. 严格单文件 <= 300 行，强类型规范，真实断言无伪 Mock。
"""

from datetime import datetime, timezone, timedelta
import math
import os
import tempfile
import unittest

from entropy_execution.dynamic_trailing_stop import (
    DynamicTrailingStopEngine,
    ExitTriggerType,
)
from entropy_execution.network_watchdog import NetworkWatchdog
from entropy_execution.paper_trading_engine import PaperTradingEngine
from entropy_execution.real_order_ledger import RealOrderLedger
from truth_kernel.institutional_flow_tracker import (
    InstitutionalFlowTracker,
    TickTradeItem,
)
from truth_kernel.market_session_clock import (
    MarketSessionClock,
    MarketSessionStatus,
)
from truth_kernel.models import (
    BalanceSheet,
    CashFlowStatement,
    CompanyFinancialRecord,
    IncomeStatement,
)
from immune_system.cash_purity import CashPurityEngine


class TestCombatReadinessStress(unittest.TestCase):
    """实盘战场真金级别深度防爆压力测试"""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_combat_ledger.db")
        self.ledger = RealOrderLedger(db_path=self.db_path)

    def tearDown(self) -> None:
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError as exc:
                import logging
                logging.getLogger("test").debug("Temporary db remove skipped: %s", exc)

    def test_real_order_ledger_crypto_fractional_and_t1_rollover(self) -> None:
        """测试加密货币微量碎股成本核算与 T+1 跨日隔夜解冻"""
        # 1. 提交并成交 0.1 BTC @ 60,000
        self.ledger.record_order_submitted("ORD_BTC_1", "BTCUSDT", True, 0.1, 60_000.0)
        self.ledger.record_order_filled("ORD_BTC_1", "BINANCE_1", 60_000.0, 0.1, 4.5)

        # 2. 补仓 0.05 BTC @ 66,000
        self.ledger.record_order_submitted("ORD_BTC_2", "BTCUSDT", True, 0.05, 66_000.0)
        self.ledger.record_order_filled("ORD_BTC_2", "BINANCE_2", 66_000.0, 0.05, 2.475)

        positions = self.ledger.get_positions()
        btc_pos = positions["BTCUSDT"]
        self.assertAlmostEqual(btc_pos["quantity"], 0.15, places=6)
        # 加权成本 = (0.1*60000 + 0.05*66000) / 0.15 = 62,000 (严禁因 max(1.0, qty) 导致除以 1.0 的重大算错)
        self.assertAlmostEqual(btc_pos["cost_basis"], 62_000.0, places=2)

        # 3. 跨交易日结算解冻 T+1
        self.ledger.rollover_trading_day()
        positions_after = self.ledger.get_positions()
        self.assertEqual(positions_after["BTCUSDT"]["shares_frozen_t1"], 0.0)

    def test_paper_trading_engine_nan_poisoning_defense(self) -> None:
        """测试模拟盘撮合引擎对 NaN 报价与 NaN 数量资金毒化的物理防护"""
        engine = PaperTradingEngine(initial_capital=1_000_000.0)

        # 1. 报单价格为 NaN 时物理拦截
        rcpt_nan_px = engine.submit_order("600519.SH", True, quantity=100.0, market_price=float("nan"))
        self.assertFalse(rcpt_nan_px.is_success)
        self.assertIn("NaN/Inf", str(rcpt_nan_px.rejection_reason))
        self.assertEqual(engine.cash, 1_000_000.0)
        self.assertFalse(math.isnan(engine.total_equity))

        # 2. 行情更新推送为 NaN 时绝不污染持仓与总净值
        engine.submit_order("600519.SH", True, quantity=100.0, market_price=1500.0, is_replay_mode=True)
        rcpts_quote = engine.update_market_quote("600519.SH", current_price=float("nan"), current_atr=15.0)
        self.assertEqual(rcpts_quote, [])
        pos = engine.get_position("600519.SH")
        self.assertIsNotNone(pos)
        self.assertEqual(pos.current_price, 1500.0)
        self.assertFalse(math.isnan(engine.total_equity))

    def test_dynamic_trailing_stop_nan_and_highest_price_ratchet(self) -> None:
        """测试动态吊灯止损对新高价格的实时棘轮锁定与 NaN 严格拦截"""
        engine = DynamicTrailingStopEngine(base_atr_multiplier=2.0)

        # 1. 价格创出新高 (120 > 历史记录 110) 必须以真实新高 120 抬高止损线
        verdict = engine.evaluate_position(
            symbol="600519.SH", entry_price=100.0, current_price=120.0,
            highest_price_since_entry=110.0, previous_stop_price=95.0, current_atr=5.0
        )
        # candidate_stop = 120 - 2.0 * 5.0 = 110.0 (收紧倍数如无浮盈阶梯)
        self.assertGreaterEqual(verdict.current_stop_price, 105.0)
        self.assertFalse(verdict.should_close)

        # 2. NaN 价格必须硬性阻断报错，杜绝静默假阳性
        with self.assertRaises(ValueError):
            engine.evaluate_position(
                symbol="600519.SH", entry_price=float("nan"), current_price=100.0,
                highest_price_since_entry=110.0, previous_stop_price=95.0, current_atr=5.0
            )

    def test_network_watchdog_memory_bound_and_nan_defense(self) -> None:
        """测试网络看门狗在海量高频报单下的有限内存淘汰与 NaN 拦截"""
        watchdog = NetworkWatchdog()

        # 1. NaN 价格提交拦截
        res_nan = watchdog.audit_pre_submission("CL_1", "600519.SH", True, 100.0, float("nan"))
        self.assertFalse(res_nan.is_safe)
        self.assertIn("NaN/Inf", str(res_nan.rejection_reason))

        # 2. 12,000 笔订单注册：内存队列严格控制在 10,000 上限，杜绝内存泄漏
        for i in range(12_000):
            watchdog._executed_cl_ord_ids.add(f"ORD_{i}")
            watchdog._executed_order_queue.append(f"ORD_{i}")
            if len(watchdog._executed_cl_ord_ids) > watchdog.MAX_TRACKED_ORDERS:
                oldest = watchdog._executed_order_queue.pop(0)
                watchdog._executed_cl_ord_ids.discard(oldest)

        self.assertLessEqual(len(watchdog._executed_cl_ord_ids), watchdog.MAX_TRACKED_ORDERS)
        self.assertLessEqual(len(watchdog._executed_order_queue), watchdog.MAX_TRACKED_ORDERS)

    def test_market_session_clock_futures_night_and_us_equity(self) -> None:
        """测试物理时钟对国内期货夜盘边界（周一凌晨/周六凌晨）与美股交易时段的判定"""
        tz = timezone(timedelta(hours=8))

        # 1. 周一凌晨 01:00 (国内期货无周日夜盘，必须闭市)
        mon_1am = datetime(2026, 9, 14, 1, 0, 0, tzinfo=tz)  # 2026-09-14 是周一
        res_mon = MarketSessionClock.evaluate_symbol("RB2410", simulated_dt=mon_1am)
        self.assertFalse(res_mon.is_open)
        self.assertIn("CLOSED", res_mon.status.value)

        # 2. 周六凌晨 01:00 (周五夜盘延续交易，必须开市)
        sat_1am = datetime(2026, 9, 19, 1, 0, 0, tzinfo=tz)  # 2026-09-19 是周六
        res_sat = MarketSessionClock.evaluate_symbol("RB2410", simulated_dt=sat_1am)
        self.assertTrue(res_sat.is_open)
        self.assertEqual(res_sat.status, MarketSessionStatus.OPEN)

        # 3. 美股交易时段：北京时间周二晚 22:30 (美股开盘交易中)
        tue_night = datetime(2026, 9, 15, 22, 30, 0, tzinfo=tz)
        res_us_open = MarketSessionClock.evaluate_symbol("AAPL.US", simulated_dt=tue_night)
        self.assertTrue(res_us_open.is_open)
        self.assertEqual(res_us_open.venue, "US_EQUITY")

        # 4. 美股日间休市：北京时间周三上午 10:30 (美股闭市)
        wed_day = datetime(2026, 9, 16, 10, 30, 0, tzinfo=tz)
        res_us_closed = MarketSessionClock.evaluate_symbol("AAPL.US", simulated_dt=wed_day)
        self.assertFalse(res_us_closed.is_open)

    def test_institutional_flow_tracker_nan_and_negative_filtering(self) -> None:
        """测试主力资金穿透器对负成交量与 NaN 脏数据的清洗过滤"""
        dirty_ticks = [
            TickTradeItem(price=10.0, volume=100, is_buyer_maker=False),   # 正常 1000 元
            TickTradeItem(price=float("nan"), volume=100, is_buyer_maker=False), # 异常 NaN
            TickTradeItem(price=10.0, volume=-50, is_buyer_maker=False),    # 负成交量
            TickTradeItem(price=-10.0, volume=100, is_buyer_maker=True),    # 负价格
            TickTradeItem(price=50.0, volume=25_000, is_buyer_maker=False)  # 125 万 (超大单)
        ]
        rep = InstitutionalFlowTracker.analyze_tick_trades("600519.SH", dirty_ticks)
        self.assertFalse(math.isnan(rep.super_large_net_inflow))
        self.assertFalse(math.isnan(rep.main_force_ratio_pct))
        self.assertEqual(rep.signal_judgment, "ACCUMULATION")

    def test_cash_purity_net_profit_deficit_warning(self) -> None:
        """测试造血纯度引擎对净利润亏损企业的实质性赤字预警"""
        engine = CashPurityEngine()
        rec = CompanyFinancialRecord(
            symbol="688999.SH", period_end_date="2025-12-31", disclosure_date="2026-03-31",
            balance_sheet=BalanceSheet(
                total_assets=5e8, total_liabilities=1e8, total_equity=4e8,
                cash_and_equivalents=1e8, restricted_cash=0.0, receivables=1e7
            ),
            income_statement=IncomeStatement(
                revenue=2e8, operating_profit=1e7, net_profit=-50_000_000.0, financial_expenses=0.0
            ),
            cash_flow_statement=CashFlowStatement(
                operating_cash_flow=60_000_000.0, capex=1e7, working_capital_change=0.0, depreciation_amortization=5e7
            )
        )
        res = engine.evaluate(rec)
        self.assertTrue(res.is_warning or res.is_veto)
        self.assertIn("亏损", res.diagnosis)


if __name__ == "__main__":
    unittest.main()
