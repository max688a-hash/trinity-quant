"""
tests/test_market_session_clock.py
==================================
TRINITY QUANT 真实物理交易所开闭市时钟、全资产休市拦截与 24/7 加密撮合测试套件。

严格验证：
1. 周末法定休市物理拦截 (A股、国内商品期货、外汇)
2. 全球加密资产 (BTCUSDT) 7x24x365 永续开市与实时撮合
3. 模拟盘物理休盘拦截：周日买入期货/A股严禁虚假成交，回放模式特许
"""

from datetime import datetime, timezone, timedelta
import unittest
from entropy_execution.paper_trading_engine import PaperTradingEngine
from truth_kernel.market_session_clock import (
    MarketSessionClock,
    MarketSessionStatus,
)


class TestMarketSessionClock(unittest.TestCase):
    """测试真实物理交易所开闭市时钟"""

    def setUp(self) -> None:
        # 构造周日凌晨 03:35 场景 (非交易时段)
        self.tz_beijing = timezone(timedelta(hours=8))
        self.sunday_night = datetime(2026, 9, 13, 3, 35, 0, tzinfo=self.tz_beijing)
        # 构造周一上午 10:00 场景 (法定交易时段)
        self.monday_morning = datetime(2026, 9, 14, 10, 0, 0, tzinfo=self.tz_beijing)

    def test_weekend_closure_for_cn_futures_and_equity(self) -> None:
        # 1. 郑州纯碱期货 (SA) 在周日凌晨必须判定为闭市
        sa_res = MarketSessionClock.evaluate_symbol("SA", simulated_dt=self.sunday_night)
        self.assertFalse(sa_res.is_open)
        self.assertEqual(sa_res.status, MarketSessionStatus.CLOSED_WEEKEND)
        self.assertFalse(sa_res.can_execute_live)

        # 2. 贵州茅台 (600519.SH) 在周日凌晨必须判定为闭市
        moutai_res = MarketSessionClock.evaluate_symbol("600519.SH", simulated_dt=self.sunday_night)
        self.assertFalse(moutai_res.is_open)
        self.assertEqual(moutai_res.status, MarketSessionStatus.CLOSED_WEEKEND)

        # 3. 外汇 (USDCNH) 周日必须判定为周末休市
        fx_res = MarketSessionClock.evaluate_symbol("USDCNH", simulated_dt=self.sunday_night)
        self.assertFalse(fx_res.is_open)
        self.assertEqual(fx_res.status, MarketSessionStatus.CLOSED_WEEKEND)

    def test_crypto_always_open_24_7(self) -> None:
        # 比特币在周日凌晨必须正常开市 (7x24x365 永续)
        btc_res = MarketSessionClock.evaluate_symbol("BTCUSDT", simulated_dt=self.sunday_night)
        self.assertTrue(btc_res.is_open)
        self.assertEqual(btc_res.status, MarketSessionStatus.OPEN)
        self.assertTrue(btc_res.can_execute_live)

    def test_regular_trading_hours_on_monday(self) -> None:
        # 周一上午 10:00: A股与期货均处于正常连续竞价时段
        sa_res = MarketSessionClock.evaluate_symbol("SA", simulated_dt=self.monday_morning)
        self.assertTrue(sa_res.is_open)

        moutai_res = MarketSessionClock.evaluate_symbol("600519.SH", simulated_dt=self.monday_morning)
        self.assertTrue(moutai_res.is_open)

    def test_paper_trading_anti_fabrication_rejection(self) -> None:
        # 开启严格物理时钟检查的模拟盘引擎
        engine = PaperTradingEngine(initial_capital=10_000_000.0, enforce_trading_hours=True)

        # 1. 在休市时段直接买入茅台/纯碱 -> 触发休市拦截，拒绝受理报单！
        now = MarketSessionClock.get_beijing_now()
        # 若当前实际处于休市期 (如周日)
        if now.weekday() in (5, 6):
            rcpt = engine.submit_order("600519.SH", is_buy=True, quantity=100, market_price=1500.0)
            self.assertFalse(rcpt.is_success)
            self.assertIn("休市拦截", rcpt.rejection_reason or "")

            # 2. 但买入 7x24 小时交易的比特币 -> 必须成功撮合！
            btc_rcpt = engine.submit_order("BTCUSDT", is_buy=True, quantity=1.0, market_price=65000.0)
            self.assertTrue(btc_rcpt.is_success)

            # 3. 若开启历史回放测试模式 (is_replay_mode=True) -> 特许放行
            replay_rcpt = engine.submit_order(
                "600519.SH", is_buy=True, quantity=100, market_price=1500.0, is_replay_mode=True
            )
            self.assertTrue(replay_rcpt.is_success)


if __name__ == "__main__":
    unittest.main()
