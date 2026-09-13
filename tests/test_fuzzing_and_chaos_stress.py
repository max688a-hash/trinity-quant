"""
tests/test_fuzzing_and_chaos_stress.py
======================================
系统全维度零盲区混沌模糊打靶 (Chaos Fuzzing Stress Test)。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 验证极端边界: 负数价格、NaN、Inf、零成交量、空盘口、越界异常;
2. 杜绝隐形 bug 与静默假阳性 (Zero Silent False Positives);
3. 严格单文件 <= 300 行，强类型规范，真实断言无伪 Mock。
"""

import math
import unittest
from typing import List

from gravity_brain.market_regime_classifier import (
    MarketRegimeClassifier,
    MarketRegime,
)
from entropy_execution.dynamic_kelly import DynamicKellyAllocator
from entropy_execution.algorithmic_order_slicer import (
    MarketImpactModel,
    TWAPOrderSlicer,
    IcebergOrderSlicer,
)
from truth_kernel.order_flow_imbalance import (
    OrderFlowImbalanceEngine,
    Level2DepthSnapshot,
)
from truth_kernel.iceberg_detector import IcebergDetector, IcebergType
from entropy_execution.broker_gateway_adapter import (
    RealBrokerRouter,
    RealOrderStatus,
)
from entropy_execution.real_money_risk_gateway import (
    RealMoneyRiskGateway,
    RiskVerdict,
)
from entropy_execution.reconciliation_engine import ReconciliationEngine
from immune_system.signal_sanity_gate import SignalSanityGate


class TestFuzzingAndChaosStress(unittest.TestCase):
    """全系统零死角混沌边界打靶测试用例集"""

    def test_market_regime_classifier_fuzzing(self) -> None:
        """测试市场状态机对极端异常、负数、零与 NaN/Inf 价格的自愈与防御能力"""
        # 1. 空输入与极短序列
        self.assertEqual(MarketRegimeClassifier.calculate_hurst_exponent([]), 0.50)
        self.assertEqual(MarketRegimeClassifier.calculate_hurst_exponent([10.0]), 0.50)
        self.assertEqual(MarketRegimeClassifier.calculate_hurst_exponent([10.0] * 5), 0.50)

        # 2. 包含负价格（如 2020 原油期货负值）与零价格
        chaotic_prices = [10.0, 0.0, -5.0, 12.0, -1.0, 15.0, 0.0, 18.0] * 5
        hurst = MarketRegimeClassifier.calculate_hurst_exponent(chaotic_prices)
        self.assertTrue(0.05 <= hurst <= 0.95)

        # 3. 包含 NaN 与 Inf 毒化输入
        poisoned_prices = [10.0, float("nan"), 12.0, float("inf"), float("-inf"), 14.0] * 6
        res = MarketRegimeClassifier.classify_regime(poisoned_prices)
        self.assertIn(res.regime, [MarketRegime.CHOPPY_OSCILLATING, MarketRegime.EXTREME_VOLATILE_CRISIS])
        self.assertFalse(math.isnan(res.hurst_exponent))
        self.assertFalse(math.isnan(res.volatility_atr_pct))

    def test_dynamic_kelly_allocator_fuzzing(self) -> None:
        """测试动态凯利分配器面对 NaN/Inf/负胜率等毒化输入的数学防爆熔断"""
        allocator = DynamicKellyAllocator()

        # 1. NaN 胜率输入
        res_nan_p = allocator.calculate_weight("600519.SH", float("nan"), 2.0, 0.05)
        self.assertEqual(res_nan_p.target_weight, 0.0)
        self.assertTrue(res_nan_p.is_vetoed)
        self.assertIn("NaN 或 Inf", res_nan_p.allocation_reason)

        # 2. Inf 盈亏比输入
        res_inf_b = allocator.calculate_weight("600519.SH", 0.60, float("inf"), 0.05)
        self.assertEqual(res_inf_b.target_weight, 0.0)
        self.assertTrue(res_inf_b.is_vetoed)

        # 3. NaN CVaR 输入
        res_nan_cvar = allocator.calculate_weight("600519.SH", 0.60, 2.0, float("nan"))
        self.assertEqual(res_nan_cvar.target_weight, 0.0)
        self.assertTrue(res_nan_cvar.is_vetoed)

        # 4. 负引力势能输入 (高估资产)
        res_neg_gp = allocator.calculate_weight("600519.SH", 0.70, 3.0, 0.03, gravity_potential=-0.2)
        self.assertEqual(res_neg_gp.target_weight, 0.0)
        self.assertFalse(res_neg_gp.is_vetoed)

    def test_algorithmic_order_slicer_fuzzing(self) -> None:
        """测试算法拆单器面对负数金额、零手数及 NaN 冲击的物理防御"""
        impact_model = MarketImpactModel()
        twap_slicer = TWAPOrderSlicer(impact_model)
        iceberg_slicer = IcebergOrderSlicer()

        # 1. 负数与 NaN 名义本金
        impact_neg = impact_model.estimate_impact("600519.SH", notional=-1000.0)
        self.assertEqual(impact_neg.estimated_slippage_pct, 0.0)
        self.assertEqual(impact_neg.expected_impact_cost_yuan, 0.0)

        impact_nan = impact_model.estimate_impact("600519.SH", notional=float("nan"))
        self.assertEqual(impact_nan.estimated_slippage_pct, 0.0)

        # 2. 非法报单量与非法价格
        self.assertEqual(twap_slicer.slice_order("600519.SH", True, total_quantity=-50.0, base_price=100.0), [])
        self.assertEqual(twap_slicer.slice_order("600519.SH", True, total_quantity=50.0, base_price=float("nan")), [])
        self.assertEqual(iceberg_slicer.slice_order("600519.SH", True, total_quantity=0.0, price=100.0), [])
        self.assertEqual(iceberg_slicer.slice_order("600519.SH", True, total_quantity=100.0, price=-10.0), [])

    def test_order_flow_imbalance_chaos(self) -> None:
        """测试盘口微观高频 OFI 引擎对空五档与异常数据长度的防御"""
        empty_snap = Level2DepthSnapshot(
            symbol="000001.SZ", timestamp=1000.0,
            bid_prices=[], bid_volumes=[], ask_prices=[], ask_volumes=[]
        )
        valid_snap = Level2DepthSnapshot(
            symbol="000001.SZ", timestamp=1001.0,
            bid_prices=[10.0], bid_volumes=[100], ask_prices=[10.1], ask_volumes=[200]
        )

        # 1. 连续盘口空盘防御
        delta_0 = OrderFlowImbalanceEngine.compute_ofi_delta(empty_snap, valid_snap)
        self.assertEqual(delta_0, 0.0)
        delta_1 = OrderFlowImbalanceEngine.compute_ofi_delta(valid_snap, empty_snap)
        self.assertEqual(delta_1, 0.0)

        # 2. 评估空盘推力
        metrics = OrderFlowImbalanceEngine.evaluate_depth_flow(None, empty_snap)
        self.assertEqual(metrics.ofi_net_value, 0.0)
        self.assertEqual(metrics.depth_imbalance_ratio, 0.0)
        self.assertEqual(metrics.next_tick_momentum, "BALANCED")

    def test_iceberg_detector_fuzzing(self) -> None:
        """测试冰山吸筹嗅探器面对负成交量及异常盘口变化的稳定性"""
        # 1. 负数成交量防御
        rep_neg = IcebergDetector.inspect_price_level(
            symbol="RB2410", price_level=3500.0, is_bid=True,
            initial_visible_vol=-100, executed_trade_vol=-50, remaining_visible_vol=-80
        )
        self.assertEqual(rep_neg.detected_type, IcebergType.NONE)
        self.assertEqual(rep_neg.estimated_hidden_volume, 0)

        # 2. 正常冰山大单触发
        rep_ice = IcebergDetector.inspect_price_level(
            symbol="RB2410", price_level=3500.0, is_bid=True,
            initial_visible_vol=500, executed_trade_vol=1500, remaining_visible_vol=400
        )
        self.assertEqual(rep_ice.detected_type, IcebergType.BUY_ACCUMULATION)
        self.assertGreater(rep_ice.estimated_hidden_volume, 1000)
        self.assertGreater(rep_ice.confidence_score, 0.60)

    def test_broker_router_chaos_rejection(self) -> None:
        """测试实盘交易路由器对负价格、负手数、NaN/Inf 非法委托的刚性拒绝"""
        router = RealBrokerRouter(is_live_combat=False)

        # 1. 负数量委托
        resp_neg_qty = router.route_and_execute("600519.SH", True, quantity=-100.0, price=1700.0)
        self.assertEqual(resp_neg_qty.status, RealOrderStatus.REJECTED)
        self.assertIn("非法报单参数拦截", resp_neg_qty.rejection_reason)

        # 2. NaN 价格委托
        resp_nan_px = router.route_and_execute("600519.SH", True, quantity=100.0, price=float("nan"))
        self.assertEqual(resp_nan_px.status, RealOrderStatus.REJECTED)

        # 3. 0 价格委托
        resp_zero_px = router.route_and_execute("BTCUSDT", False, quantity=1.0, price=0.0)
        self.assertEqual(resp_zero_px.status, RealOrderStatus.REJECTED)

    def test_real_money_risk_gateway_fuzzing(self) -> None:
        """测试事前硬风控网关面对 NaN 价格/数量渗透的防爆拦截 (修复历史静默漏洞)"""
        gateway = RealMoneyRiskGateway()
        gateway.set_day_start_equity(1_000_000.0)

        # 1. NaN 价格委托尝试渗透 (历史漏洞检测)
        res_nan = gateway.check_pre_trade_risk(
            symbol="600519.SH", is_buy=True, quantity=100.0,
            order_price=float("nan"), market_price=1700.0,
            current_position_value=0.0, account_total_equity=1_000_000.0
        )
        self.assertFalse(res_nan.is_allowed)
        self.assertEqual(res_nan.verdict, RiskVerdict.REJECT_FAT_FINGER)

        # 2. 负数量委托拦截
        res_neg = gateway.check_pre_trade_risk(
            symbol="600519.SH", is_buy=True, quantity=-50.0,
            order_price=1700.0, market_price=1700.0,
            current_position_value=0.0, account_total_equity=1_000_000.0
        )
        self.assertFalse(res_neg.is_allowed)
        self.assertEqual(res_neg.verdict, RiskVerdict.REJECT_FAT_FINGER)

        # 3. 正常委托合规通过
        res_valid = gateway.check_pre_trade_risk(
            symbol="600519.SH", is_buy=True, quantity=100.0,
            order_price=1700.0, market_price=1700.0,
            current_position_value=0.0, account_total_equity=1_000_000.0
        )
        self.assertTrue(res_valid.is_allowed)
        self.assertEqual(res_valid.verdict, RiskVerdict.PASS)

    def test_signal_sanity_gate_fuzzing(self) -> None:
        """测试信号多维物理核验门对 NaN/负价格/过期信号的拦截"""
        gate = SignalSanityGate()

        # 1. NaN 信号价格
        res_nan = gate.verify_order(
            symbol="600519.SH", is_buy=True, signal_price=float("nan"),
            current_market_price=1700.0, proposed_quantity=100.0, five_day_adv=10_000.0
        )
        self.assertFalse(res_nan.is_passed)
        self.assertEqual(res_nan.adjusted_quantity, 0.0)

        # 2. 价格漂移超过 1.5% 拦截
        res_drift = gate.verify_order(
            symbol="600519.SH", is_buy=True, signal_price=1700.0,
            current_market_price=1740.0, proposed_quantity=100.0, five_day_adv=10_000.0
        )
        self.assertFalse(res_drift.is_passed)
        self.assertIn("盘口漂移过大", str(res_drift.veto_reason))

        # 3. ADV 容量压缩
        res_adv = gate.verify_order(
            symbol="600519.SH", is_buy=True, signal_price=1700.0,
            current_market_price=1701.0, proposed_quantity=500.0, five_day_adv=10_000.0
        )
        self.assertTrue(res_adv.is_passed)
        self.assertEqual(res_adv.adjusted_quantity, 200.0)  # 10000 * 2% = 200

    def test_reconciliation_engine_chaos(self) -> None:
        """测试账实平账引擎面对极端严重账实不一致时的紧急硬锁死"""
        engine = ReconciliationEngine()

        # 1. 账实完全一致
        rep_bal = engine.audit_and_reconcile(
            {"600519.SH": 100.0, "000001.SZ": 500.0},
            {"600519.SH": 100.0, "000001.SZ": 500.0}
        )
        self.assertTrue(rep_bal.is_balanced)
        self.assertFalse(rep_bal.emergency_lockout)

        # 2. 遭遇飞单/漏单 (柜台 200 股，本地 100 股)
        rep_dis = engine.audit_and_reconcile(
            {"600519.SH": 100.0},
            {"600519.SH": 200.0}
        )
        self.assertFalse(rep_dis.is_balanced)
        self.assertTrue(rep_dis.emergency_lockout)
        self.assertEqual(rep_dis.disparities_count, 1)


if __name__ == "__main__":
    unittest.main()
