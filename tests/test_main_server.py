"""
tests/test_main_server.py
=========================
单元测试：main.py 服务端点与全链路质检执行。
"""

import json
import unittest

from entropy_execution.real_money_service import (
    get_real_money_orders,
    get_real_money_status,
    handle_real_money_order,
    handle_real_money_toggle,
)
from main import TrinityRequestHandler, run_full_verification


class TestMainServer(unittest.TestCase):
    """测试主服务与 REST API 响应逻辑"""

    def setUp(self) -> None:
        self.handler = TrinityRequestHandler.__new__(TrinityRequestHandler)
        self.handler.workspace_root = "/Volumes/tianyou-168/顶级量化"

    def test_health_status(self) -> None:
        """验证健康监测端点返回数据完整性"""
        status = self.handler._get_health_status()
        self.assertEqual(status["status"], "HEALTHY")
        self.assertIn("active_source", status)
        self.assertIn("latency_ms", status)
        self.assertIn("four_pillars", status)
        self.assertIn("truth_kernel", status["four_pillars"])

    def test_paper_state(self) -> None:
        """验证模拟盘状态端点"""
        state = self.handler._get_paper_state()
        self.assertGreater(state["cash"], 0)
        self.assertTrue(state["t_plus_1_enforced"])
        self.assertTrue(state["ratchet_enabled"])

    def test_market_status(self) -> None:
        """验证跨市场物理时钟状态获取"""
        mkt = self.handler._get_market_status()
        self.assertIn("CN_EQUITY", mkt)
        self.assertIn("CN_FUTURE", mkt)
        self.assertIn("FOREX", mkt)
        self.assertIn("CRYPTO", mkt)
        self.assertTrue(mkt["CRYPTO"]["is_market_open"])

    def test_paper_trade_buy(self) -> None:
        """验证真实模拟报单买入与摩擦反馈"""
        res = self.handler._handle_paper_trade({
            "symbol": "600519.SH",
            "action": "BUY",
            "quantity": 100,
            "price": 1550.0,
            "is_replay_mode": True
        })
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "BUY")
        self.assertGreater(res["friction_total"], 0)

    def test_reflex_probe(self) -> None:
        """验证仿生神经反射紧急熔断探针"""
        res = self.handler._handle_reflex_probe({
            "symbol": "600519.SH",
            "price_drop_pct": -0.095,
            "corrupted": True
        })
        self.assertEqual(res["level"], "PRIMITIVE_SPINAL")
        self.assertTrue(res["bypass_deliberation"])

    def test_real_money_service_endpoints(self) -> None:
        """验证真金实盘服务 API 端点逻辑"""
        status = get_real_money_status()
        self.assertIn("gateways", status)
        self.assertIn("is_live_combat_mode", status)
        self.assertIn("circuit_breaker_limit_pct", status)

        # 切换实战模式测试
        t_res = handle_real_money_toggle({"enabled": True})
        self.assertTrue(t_res["is_live_combat_mode"])
        t_res_off = handle_real_money_toggle({"enabled": False})
        self.assertFalse(t_res_off["is_live_combat_mode"])

        # 真实报单与账本查询测试 (使用微量加密资产避免多次运行后触发20%集中度硬风控)
        o_res = handle_real_money_order({
            "symbol": "BTCUSDT", "action": "BUY", "quantity": 0.01, "price": 65000.0, "market_price": 65000.0
        })
        self.assertTrue(o_res["success"])
        orders = get_real_money_orders(10)
        self.assertGreaterEqual(orders["count"], 1)

    def test_autonomous_learning_endpoints(self) -> None:
        """验证系统自学习与影子巡航端点"""
        from main import _GLOBAL_LEARNING_SANDBOX
        rep = _GLOBAL_LEARNING_SANDBOX.generate_learning_report()
        self.assertGreater(rep.total_auto_trades, 0)
        self.assertIn("系统自学习总结", rep.learning_synthesis)

    def test_realtime_ticks_endpoint(self) -> None:
        """验证实时高频行情跳动端点"""
        from entropy_execution.http_api_dispatcher import HttpApiDispatcher
        res = HttpApiDispatcher.get_realtime_ticks("600519.SH")
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["ticks"][0]["symbol"], "600519.SH")
        self.assertGreater(res["ticks"][0]["price"], 0.0)

    def test_industry_chain_and_report_endpoints(self) -> None:
        """验证产业链图谱与机构研报端点"""
        from entropy_execution.http_api_dispatcher import HttpApiDispatcher
        chain_res = HttpApiDispatcher.get_industry_chain("600519.SH")
        self.assertTrue(chain_res["found"])
        self.assertEqual(chain_res["chain"]["sector_id"], "baijiu_consumer")

        rep_res = HttpApiDispatcher.get_institutional_report("600519.SH")
        self.assertIn("report", rep_res)
        self.assertEqual(rep_res["report"]["symbol"], "600519.SH")
        self.assertGreater(rep_res["report"]["target_gravity_price"], 0.0)

    def test_battlefield_service_endpoints(self) -> None:
        """验证战地发射台、告警与平账端点"""
        from entropy_execution.battlefield_api_service import (
            handle_get_vault_status, handle_save_vault_credentials,
            handle_get_alert_history, handle_trigger_test_alert,
            handle_get_supervisor_telemetry
        )
        vault_res = handle_get_vault_status()
        self.assertIn("gateways", vault_res)

        save_res = handle_save_vault_credentials({
            "gateway": "BINANCE_CRYPTO",
            "credentials": {"api_key": "abc123456", "api_secret": "sec987654"}
        })
        self.assertTrue(save_res["success"])

        alert_res = handle_trigger_test_alert({"channel": "WECHAT", "webhook_url": ""})
        self.assertTrue(alert_res["dispatched"])

        history = handle_get_alert_history()
        self.assertIn("alerts", history)

        telemetry = handle_get_supervisor_telemetry()
        self.assertIn("memory_rss_mb", telemetry)

    def test_run_full_verification(self) -> None:
        """验证主检验脚本返回码为0"""
        ret = run_full_verification()
        self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
