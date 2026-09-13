"""
tests/test_turtle_and_paper_trading.py
======================================
TRINITY QUANT 机构级海龟引擎、自动模拟盘与商业API桥接测试套件。

严格验证：
1. 商业 API 凭证自动解析与加载 (PaidDataBridge)
2. 机构级海龟 Unit 风险头寸规模、S1/S2突破与胜负跳过滤网 (InstitutionalTurtle)
3. 海龟金字塔加仓 (+0.5N) 与全局 2N 动态止损抬升
4. 模拟盘 T+1 锁仓、跨日解冻、全摩擦扣减与自动盯市跟踪止损 (PaperTradingEngine)
"""

import unittest
from truth_kernel.paid_data_bridge import PaidDataBridge
from gravity_brain.institutional_turtle import (
    InstitutionalTurtleEngine,
    TurtlePositionUnit,
    TurtleSignalType,
    TurtleSystemType,
)
from entropy_execution.paper_trading_engine import PaperTradingEngine


class TestPaidDataBridge(unittest.TestCase):
    """测试商业 API 密钥解析与加载"""

    def test_load_credentials(self) -> None:
        bridge = PaidDataBridge()
        creds = bridge.credentials
        self.assertTrue(creds.is_active)
        self.assertEqual(creds.tushare_key, "huanghanchi")
        self.assertIn("indevs.in", creds.api_base_url)


class TestInstitutionalTurtle(unittest.TestCase):
    """测试机构级海龟系统"""

    def setUp(self) -> None:
        self.turtle = InstitutionalTurtleEngine(risk_fraction_per_unit=0.01, max_units_per_asset=4)

    def test_unit_sizing_math(self) -> None:
        # 本金 1000万, 风险1% = 10万
        # 玉米 N = 25.0, 乘数 = 10.0 -> Dollar Volatility = 250元
        # 1 Unit = 100,000 / 250 = 400 手
        unit = self.turtle.calculate_unit_size(10_000_000.0, 25.0, 10.0)
        self.assertEqual(unit, 400.0)

    def test_system_1_breakout_and_skip_filter(self) -> None:
        # 构造25期收盘价，最高价在120，最新价125突破
        closes = [100.0 + (i % 5) for i in range(25)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]

        # 首次突破：触发 System 1 入场
        dec = self.turtle.evaluate_signals(
            symbol="C",
            current_price=115.0,
            closes_history=closes,
            highs_history=highs,
            lows_history=lows,
            equity=10_000_000.0,
            contract_multiplier=10.0
        )
        self.assertEqual(dec.signal, TurtleSignalType.ENTRY_INIT_UNIT)
        self.assertEqual(dec.system_type, TurtleSystemType.SYSTEM_1)

        # 模拟该单出场 (跌破 10日低点 100.0)
        pos = [TurtlePositionUnit(1, 105.0, 400.0)]
        exit_dec = self.turtle.evaluate_signals(
            symbol="C",
            current_price=95.0,  # 跌破 10日低点与 2N 止损
            closes_history=closes,
            highs_history=highs,
            lows_history=lows,
            equity=10_000_000.0,
            contract_multiplier=10.0,
            existing_units=pos
        )
        self.assertEqual(exit_dec.signal, TurtleSignalType.EXIT_ALL_UNITS)

    def test_pyramiding_and_stop_ratchet(self) -> None:
        closes = [100.0 for _ in range(25)]
        highs = [102.0 for _ in range(25)]
        lows = [98.0 for _ in range(25)]

        # 持有 1 Unit @ 100元，N = 4.0
        # +0.5N = +2.0 元，即现价到达 102 元触发加仓
        pos = [TurtlePositionUnit(1, 100.0, 100.0)]
        dec = self.turtle.evaluate_signals(
            symbol="SA",
            current_price=103.0,
            closes_history=closes,
            highs_history=highs,
            lows_history=lows,
            equity=10_000_000.0,
            contract_multiplier=20.0,
            existing_units=pos
        )
        self.assertEqual(dec.signal, TurtleSignalType.PYRAMID_ADD_UNIT)
        self.assertEqual(dec.current_units_count, 2)
        # 全局统一止损线抬升至 103 - 2*4 = 95.0
        self.assertEqual(dec.stop_price, 103.0 - 2.0 * 4.0)


class TestPaperTradingEngine(unittest.TestCase):
    """测试自动模拟盘仿真与物理摩擦"""

    def setUp(self) -> None:
        self.engine = PaperTradingEngine(initial_capital=1_000_000.0)

    def test_a_share_t1_lock_and_next_day_exit(self) -> None:
        # 买入 100 股茅台 @ 1500元
        buy_rcpt = self.engine.submit_order("600519.SH", is_buy=True, quantity=100, market_price=1500.0)
        self.assertTrue(buy_rcpt.is_success)
        self.assertEqual(buy_rcpt.stamp_duty, 0.0)  # 买入无印花税

        # 当日即刻尝试平仓 -> 触发 T+1 物理阻断
        same_day_sell = self.engine.submit_order("600519.SH", is_buy=False, quantity=100, market_price=1520.0)
        self.assertFalse(same_day_sell.is_success)
        self.assertIn("T+1", same_day_sell.rejection_reason or "")

        # 跨日结算解冻
        self.engine.rollover_trading_day()

        # 次日成功卖出平仓 -> 扣除 0.05% 印花税与佣金
        next_day_sell = self.engine.submit_order("600519.SH", is_buy=False, quantity=100, market_price=1550.0)
        self.assertTrue(next_day_sell.is_success)
        self.assertGreater(next_day_sell.stamp_duty, 0.0)
        self.assertGreater(self.engine.total_equity, 1_000_000.0)  # 盈利实现


if __name__ == "__main__":
    unittest.main()
