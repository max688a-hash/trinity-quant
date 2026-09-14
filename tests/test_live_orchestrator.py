"""
tests/test_live_orchestrator.py
===============================
TRINITY QUANT 四层实时全链路编排、极限流动性跌停防御与持久化 REST 服务测试套件。

严格验证：
1. 极端一字涨停/跌停板流动性枯竭防御 (submit_order liquidity lock)
2. 四层端到端实时管线编排调度 (LivePipelineOrchestrator: 脊髓反射/排毒/分形/凯利撮合)
3. main.py 生产级 REST 服务持久化与状态同步 (消解形神分离与隐形 bug)
"""

import json
import unittest
from entropy_execution.live_pipeline_orchestrator import LivePipelineOrchestrator
from entropy_execution.paper_trading_engine import PaperTradingEngine
from main import TrinityRequestHandler, _GLOBAL_PAPER_ENGINE, _GLOBAL_PAPER_LOCK


class TestLiquidityDefenseAndOrchestrator(unittest.TestCase):
    """测试极端流动性拦截与全链路编排"""

    def setUp(self) -> None:
        self.paper = PaperTradingEngine(initial_capital=5_000_000.0)
        self.orchestrator = LivePipelineOrchestrator(paper_engine=self.paper)

    def test_limit_up_down_liquidity_defense(self) -> None:
        # 1. 一字涨停无筹码拦截
        buy_rcpt = self.paper.submit_order(
            "600519.SH", is_buy=True, quantity=100, market_price=1500.0, is_limit_up_locked=True
        )
        self.assertFalse(buy_rcpt.is_success)
        self.assertIn("一字涨停", buy_rcpt.rejection_reason or "")

        # 正常买入
        normal_buy = self.paper.submit_order(
            "600519.SH", is_buy=True, quantity=100, market_price=1500.0
        )
        self.assertTrue(normal_buy.is_success)

        # 解冻 T+1
        self.paper.rollover_trading_day()

        # 2. 一字跌停无接盘流动性拦截
        sell_rcpt = self.paper.submit_order(
            "600519.SH", is_buy=False, quantity=100, market_price=1350.0, is_limit_down_locked=True
        )
        self.assertFalse(sell_rcpt.is_success)
        self.assertIn("一字跌停", sell_rcpt.rejection_reason or "")

    def test_orchestrator_spinal_panic_freeze(self) -> None:
        # 触发脊髓触火反射
        res = self.orchestrator.execute_tick(
            symbol="600519.SH",
            current_price=1400.0,
            macro_history=[100.0 + i for i in range(25)],
            meso_history=[120.0 + i for i in range(12)],
            instant_price_drop_pct=-0.08
        )
        self.assertFalse(res.is_executed)
        self.assertEqual(res.action, "EMERGENCY_FREEZE")
        self.assertEqual(res.alert_type, "CRISIS_ALARM")
        self.assertIn("触火即缩", res.veto_reason or "")

    def test_orchestrator_insider_dump_veto(self) -> None:
        # 触发大股东集中套现出逃
        res = self.orchestrator.execute_tick(
            symbol="TEST_DUMP",
            current_price=50.0,
            macro_history=[10.0 + i for i in range(25)],
            meso_history=[20.0 + i for i in range(12)],
            insider_dump_ratio_adv=0.20
        )
        self.assertFalse(res.is_executed)
        self.assertEqual(res.action, "VETO_INSIDER_DUMP")
        self.assertEqual(res.alert_type, "CRISIS_ALARM")

    def test_orchestrator_full_bull_execution(self) -> None:
        # 多头共振标的触发全链路顺畅买入
        res = self.orchestrator.execute_tick(
            symbol="600519.SH",
            current_price=150.0,
            macro_history=[100.0 + i for i in range(25)],
            meso_history=[120.0 + i for i in range(12)]
        )
        self.assertTrue(res.is_executed, msg=str(res.veto_reason))
        self.assertEqual(res.audit_trace["kelly"]["mode"], "COLD_START_PROBE")
        self.assertLessEqual(res.receipt.executed_price * res.receipt.executed_quantity, 5_000_000.0 * 0.02)
        self.assertEqual(res.action, "BUY_EXECUTED")
        self.assertEqual(res.alert_type, "ENTRY_PING")
        self.assertIsNotNone(res.receipt)
        self.assertTrue(res.receipt.is_success)

    def test_zero_price_does_not_crash_or_fill(self) -> None:
        res = self.orchestrator.execute_tick(
            symbol="600519.SH",
            current_price=0.0,
            macro_history=[100.0 + i for i in range(25)],
            meso_history=[120.0 + i for i in range(12)],
        )
        self.assertFalse(res.is_executed)
        self.assertIn("DATA_UNAVAILABLE", res.veto_reason or res.action)


class TestMainServerPersistence(unittest.TestCase):
    """测试 main.py 的状态持久化与 REST API 响应"""

    def test_paper_state_persistence_across_trades(self) -> None:
        with _GLOBAL_PAPER_LOCK:
            init_cash = _GLOBAL_PAPER_ENGINE.cash

        # 模拟通过 _handle_paper_trade 下单
        handler = TrinityRequestHandler.__new__(TrinityRequestHandler)
        trade_res = handler._handle_paper_trade({
            "symbol": "600519.SH",
            "action": "BUY",
            "quantity": 100,
            "price": 1500.0,
            "is_replay_mode": True
        })
        self.assertTrue(trade_res["success"])

        # 检验后续 _get_paper_state 获取到的是持久化后的状态
        state = handler._get_paper_state()
        self.assertLess(state["cash"], init_cash)
        self.assertGreaterEqual(state["positions_count"], 1)
        self.assertTrue(any(p["symbol"] == "600519.SH" for p in state["positions"]))

        # 模拟跨日解冻
        rollover_res = handler._handle_paper_rollover()
        self.assertTrue(rollover_res["success"])

        # 检验智能选股接口
        screener_res = handler._get_screener_results()
        self.assertGreaterEqual(screener_res["count"], 1)

        # 检验端到端管线接口
        pipe_res = handler._handle_pipeline_run({
            "symbol": "600519.SH",
            "price": 1550.0
        })
        self.assertIn("stage_immune_passed", pipe_res)


if __name__ == "__main__":
    unittest.main()
