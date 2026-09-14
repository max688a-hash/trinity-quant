"""
真金开关无安全密钥禁止点燃。乐视/康美不得因假真金开关变成可买。
# ref: AGENTS.md 第24条 外行用户否决权；unlock 同源密钥
"""

from __future__ import annotations

import os
import unittest

from entropy_execution.real_money_service import (
    _REAL_BROKER_ROUTER,
    get_real_money_status,
    handle_real_money_toggle,
)


class TestLiveCombatToggleKey(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["TRINITY_LIVE_COMBAT_SAFETY_KEY"] = "unit-test-safety-key-0123456789"
        handle_real_money_toggle({"enabled": False})  # 动尺理由: 熄火真金开关防用例泄漏点燃态，不是放宽风控

    def tearDown(self) -> None:
        handle_real_money_toggle({"enabled": False})  # 动尺理由: 用例收尾熄火，防止点燃态串到后续测试
        os.environ.pop("TRINITY_LIVE_COMBAT_SAFETY_KEY", None)

    def test_enable_without_key_stays_sandbox(self) -> None:
        res = handle_real_money_toggle({"enabled": True})
        self.assertFalse(res.get("success"))
        self.assertFalse(res["is_live_combat_mode"])
        self.assertFalse(_REAL_BROKER_ROUTER.is_live_combat)
        self.assertFalse(get_real_money_status()["is_live_combat_mode"])
        self.assertIn("密钥", res.get("message", ""))

    def test_wrong_key_cannot_ignite(self) -> None:
        res = handle_real_money_toggle({"enabled": True, "safety_key": "wrong-key"})
        self.assertFalse(res.get("success"))
        self.assertFalse(res["is_live_combat_mode"])

    def test_correct_key_can_set_flag_then_disable_without_key(self) -> None:
        on = handle_real_money_toggle({
            "enabled": True,
            "safety_key": "unit-test-safety-key-0123456789",
        })
        self.assertTrue(on.get("success"))
        self.assertTrue(on["is_live_combat_mode"])
        off = handle_real_money_toggle({"enabled": False})  # 动尺理由: 断言正确密钥点燃后可降级沙盒，不是拆除风控
        self.assertTrue(off.get("success"))
        self.assertFalse(off["is_live_combat_mode"])

    def test_unconfigured_key_cannot_ignite(self) -> None:
        os.environ.pop("TRINITY_LIVE_COMBAT_SAFETY_KEY", None)
        res = handle_real_money_toggle({"enabled": True, "safety_key": "unit-test-safety-key-0123456789"})
        self.assertFalse(res.get("success"))
        self.assertIn("未配置", res.get("message", ""))

    def test_letv_kangmei_remain_vetoed(self) -> None:
        from tests.test_immune_system import TestImmuneSystem
        immune = TestImmuneSystem()
        immune.setUp()
        immune.test_case_letv_receivables_fraud()
        immune.test_case_kangmei_deposit_loan_paradox()


if __name__ == "__main__":
    unittest.main()
