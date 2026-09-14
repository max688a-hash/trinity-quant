"""
entropy_execution/system_quality_inspector.py
=============================================
TRINITY QUANT 系统启动验收套件（真验收，禁止假全绿）。

两类检查，分别汇报、分别判定：
1. 功能自检 (functional)：数据探针路由、审计财报汇总、陷阱识别、海龟引擎、模拟盘 T+1/印花税、
   反射中枢、分形引擎、PIT 回测汇总——任何一项失败 → is_passed=False。
2. 实盘就绪 (live_readiness)：商业数据源真实探活、实盘安全密钥配置、券商网关真实会话、
   回测跑赢基线——任何一项未达标 → is_live_ready=False，并逐条列出缺口；这些缺口不能被"功能自检通过"掩盖。

summary_verdict 由真实结果拼装，不存在任何无条件的 "100% 通过" 文案。
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from entropy_execution.gateway_connection_manager import ConnectionState, GatewayConnectionManager
from entropy_execution.live_safety_key import is_live_combat_safety_key_configured
from entropy_execution.paper_trading_engine import PaperTradingEngine
from gravity_brain.institutional_turtle import InstitutionalTurtleEngine, TurtleSignalType
from gravity_brain.multi_timeframe_fractal import MultiTimeframeFractalEngine, ResonanceGrade
from immune_system.reflex_system import BioReflexCentral, ReflexLevel
from immune_system.trap_detector import TrapDetector, TrapType
from truth_kernel.data_probe_router import DataProbeRouter
from truth_kernel.paid_data_bridge import PaidDataBridge


@dataclass(frozen=True)
class QualityInspectionReport:
    """系统质量验收正式报告"""
    timestamp: str
    is_passed: bool                      # 功能自检全部通过
    is_live_ready: bool                  # 实盘就绪项全部达标（缺任何外部条件即 False）
    functional_checks: Dict[str, bool]
    live_readiness_checks: Dict[str, bool]
    failed_functional: List[str]
    live_readiness_gaps: List[str]
    data_probe_status: str
    commercial_api_active: bool
    commercial_api_detail: str
    audit_total_statements: int
    audit_vetoed_count: int
    audit_admitted_count: int
    trap_detector_verified: bool
    turtle_engine_verified: bool
    paper_trading_verified: bool
    backtest_beats_baseline: bool
    backtest_detail: str
    summary_verdict: str
    notes: List[str] = field(default_factory=list)


class SystemQualityInspector:
    """全系统端到端质检验收器（结论 = 实测结果的函数）"""

    def __init__(self, workspace_root: str, gateway_manager: GatewayConnectionManager | None = None) -> None:
        self._root = workspace_root
        self._router = DataProbeRouter()
        self._bridge = PaidDataBridge()
        self._turtle = InstitutionalTurtleEngine()
        self._trap = TrapDetector()
        self._paper = PaperTradingEngine(initial_capital=10_000_000.0)
        self._gw_mgr = gateway_manager or GatewayConnectionManager()

    def _check_data_probe(self) -> Tuple[bool, str]:
        self._router.register_source("COMMERCIAL_API")
        self._router.register_source("LOCAL_AUDITED_STORE")
        frame = self._router.probe_and_ingest(
            source_name="COMMERCIAL_API", symbol="600519.SH", price=1500.0, volume=15000.0,
            quote_timestamp=time.time(), rtt_latency_ms=35.0,
        )
        active = self._router.get_active_source()
        ok = frame is not None and active == "COMMERCIAL_API"
        return ok, f"router_active={active} (合成探针帧，仅验证路由逻辑，不代表商业行情已接通)"

    def _load_json(self, *parts: str) -> Dict[str, Any]:
        path = os.path.join(self._root, "data", "real_financials", *parts)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}

    def _check_audit_summary(self) -> Tuple[bool, int, int, int]:
        summary = self._load_json("audit_summary.json").get("summary", {})
        total = int(summary.get("total_analyzed_reports", 0))
        veto = int(summary.get("total_vetoed", 0))
        admit = int(summary.get("total_admitted", 0))
        ok = total > 0 and veto + admit == total
        return ok, total, veto, admit

    def _check_backtest(self) -> Tuple[bool, bool, str]:
        """返回 (汇总文件可用, 跑赢基线, 说明)"""
        data = self._load_json("backtest_summary.json")
        if not data or "baseline_equal_weight_buy_hold" not in data:
            return False, False, "backtest_summary.json 缺失或未含基线对照（请先运行 entropy_execution.run_real_backtest）"
        beats = bool(data.get("beats_baseline", False))
        base = data["baseline_equal_weight_buy_hold"].get("total_net_return", 0.0)
        return True, beats, (
            f"策略净收益 {data.get('total_net_return', 0.0)*100:.2f}% vs 等权基线 {base*100:.2f}%；"
            f"凯利实证期 {data.get('kelly_empirical_periods', 0)}；{data.get('statistical_caveat', '')}"
        )

    def _check_paper_trading(self) -> bool:
        buy = self._paper.submit_order("600519.SH", is_buy=True, quantity=100, market_price=1500.0)
        same_day = self._paper.submit_order("600519.SH", is_buy=False, quantity=100, market_price=1510.0)
        t1_ok = (not same_day.is_success) and ("T+1" in (same_day.rejection_reason or ""))
        self._paper.rollover_trading_day()
        sell = self._paper.submit_order("600519.SH", is_buy=False, quantity=100, market_price=1520.0)
        return buy.is_success and buy.stamp_duty == 0.0 and t1_ok and sell.is_success and sell.stamp_duty > 0

    def _check_engines(self) -> Dict[str, bool]:
        trap = self._trap.audit_manipulator_traps(
            symbol="TEST_TRAP", price_change_pct=0.05, recent_avg_volume=50000.0, current_breakout_volume=12000.0,
            bid_volume_top3=1000.0, ask_volume_top3=1000.0, real_executed_sell_volume=100.0, real_executed_buy_volume=100.0,
        )
        closes = [100.0 + i for i in range(25)]
        turtle = self._turtle.evaluate_signals(
            symbol="C", current_price=130.0, closes_history=closes, highs_history=[c + 1.0 for c in closes],
            lows_history=[c - 1.0 for c in closes], equity=10_000_000.0, contract_multiplier=10.0,
        )
        reflex = BioReflexCentral().evaluate_primitive_reflex(
            "600519.SH", instant_price_drop_pct=-0.08, is_limit_down_locked=False, is_data_corrupted=False
        )
        frac = MultiTimeframeFractalEngine().evaluate_fractal_resonance(
            "600519.SH", closes, [120.0 + i for i in range(12)], 135.0, 130.0
        )
        return {
            "trap_detector": trap.trap_detected == TrapType.PUMP_AND_DUMP_BULL_TRAP,
            "turtle_engine": turtle.signal == TurtleSignalType.ENTRY_INIT_UNIT,
            "reflex_central": reflex is not None and reflex.level == ReflexLevel.PRIMITIVE_SPINAL,
            "fractal_engine": frac.resonance_grade == ResonanceGrade.FULL_BULL_RESONANCE,
        }

    def run_full_inspection(self) -> QualityInspectionReport:
        probe_ok, probe_detail = self._check_data_probe()
        audit_ok, total, veto, admit = self._check_audit_summary()
        bt_ok, bt_beats, bt_detail = self._check_backtest()
        paper_ok = self._check_paper_trading()
        engines = self._check_engines()

        functional: Dict[str, bool] = {
            "data_probe_router": probe_ok, "audit_summary_consistent": audit_ok,
            "paper_trading_t1_and_stamp_duty": paper_ok, "backtest_summary_with_baseline": bt_ok, **engines,
        }
        creds = self._bridge.probe_liveness()
        gw_states = {gw: self._gw_mgr.get_state(gw) for gw in ("QMT", "BINANCE")}
        readiness: Dict[str, bool] = {
            "commercial_data_active": bool(creds.is_active),
            "live_safety_key_configured": is_live_combat_safety_key_configured(),
            "broker_gateway_connected": any(s == ConnectionState.CONNECTED for s in gw_states.values()),
            "backtest_beats_baseline": bt_ok and bt_beats,
        }
        failed = [k for k, v in functional.items() if not v]
        gaps = [k for k, v in readiness.items() if not v]
        is_passed = not failed
        is_live_ready = is_passed and not gaps
        verdict = (
            f"功能自检 {len(functional) - len(failed)}/{len(functional)} 通过"
            + (f"，失败: {failed}" if failed else "")
            + f"；实盘就绪 {len(readiness) - len(gaps)}/{len(readiness)}"
            + (f"，缺口: {gaps}" if gaps else "，全部达标")
            + "。" + ("可进入影子跟单期" if is_live_ready else "禁止真金实盘")
        )
        return QualityInspectionReport(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            is_passed=is_passed, is_live_ready=is_live_ready,
            functional_checks=functional, live_readiness_checks=readiness,
            failed_functional=failed, live_readiness_gaps=gaps,
            data_probe_status=probe_detail,
            commercial_api_active=bool(creds.is_active), commercial_api_detail=creds.liveness_detail,
            audit_total_statements=total, audit_vetoed_count=veto, audit_admitted_count=admit,
            trap_detector_verified=engines["trap_detector"], turtle_engine_verified=engines["turtle_engine"],
            paper_trading_verified=paper_ok, backtest_beats_baseline=bt_ok and bt_beats, backtest_detail=bt_detail,
            summary_verdict=verdict,
            notes=[f"gateway_{k}={v.value}" for k, v in gw_states.items()],
        )
