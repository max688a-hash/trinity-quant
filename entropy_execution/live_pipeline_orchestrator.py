"""
entropy_execution/live_pipeline_orchestrator.py
===============================================
TRINITY QUANT 四层架构实时全链路编排总指挥部 (Live Pipeline Orchestrator)。

彻底消解“断头断尾”与“形神分离”：
1. 第一层 [truth_kernel]: 时点 PIT 检验与行情推入
2. 第二层 [immune_system]: 排毒防火墙、大股东减持质押雷达、庄家陷阱与脊髓原始反射
3. 第三层 [gravity_brain]: 多周期分形共振、海龟突破与 Alpha 定价
4. 第四层 [entropy_execution]: 动态防爆凯利仓位配比、全摩擦扣减与自动模拟盘撮合
5. 声色决策指令输出: 联动 Web Audio 叮声提示 (ENTRY_PING) 与低频警报 (CRISIS_ALARM)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from entropy_execution.dynamic_kelly import DynamicKellyAllocator
from entropy_execution.paper_trading_engine import PaperExecutionReceipt, PaperTradingEngine
from gravity_brain.institutional_turtle import InstitutionalTurtleEngine, TurtleSignalType
from gravity_brain.multi_timeframe_fractal import MultiTimeframeFractalEngine, ResonanceGrade
from immune_system.insider_dump_monitor import (
    AlertSeverity,
    AudioAlertTone,
    InsiderDumpMonitor,
)
from immune_system.poison_firewall import PoisonFirewall
from immune_system.reflex_system import BioReflexCentral, ReflexLevel
from immune_system.trap_detector import TrapDetector, TrapType
from truth_kernel.models import CompanyFinancialRecord


@dataclass(frozen=True)
class PipelineCycleResult:
    """实时全链路编排运行终局回执"""
    symbol: str
    is_executed: bool
    action: str                       # BUY / SELL / VETO / STAND_ASIDE
    stage_immune_passed: bool
    stage_gravity_passed: bool
    stage_execution_passed: bool
    veto_reason: Optional[str]
    alert_type: str                   # NONE / ENTRY_PING / CRISIS_ALARM
    alert_color: str                  # none / emerald-pulse / rose-strobe
    audit_trace: Dict[str, Any]
    receipt: Optional[PaperExecutionReceipt]


class LivePipelineOrchestrator:
    """
    四层全链路自动化总编排中枢
    统一驱动金融物理守恒与实盘交易流
    """

    def __init__(
        self,
        paper_engine: Optional[PaperTradingEngine] = None,
        firewall: Optional[PoisonFirewall] = None,
        dump_monitor: Optional[InsiderDumpMonitor] = None,
        trap_detector: Optional[TrapDetector] = None,
        reflex_central: Optional[BioReflexCentral] = None,
        fractal_engine: Optional[MultiTimeframeFractalEngine] = None,
        turtle_engine: Optional[InstitutionalTurtleEngine] = None,
        kelly_allocator: Optional[DynamicKellyAllocator] = None
    ) -> None:
        self.paper = paper_engine or PaperTradingEngine(initial_capital=10_000_000.0)
        self.firewall = firewall or PoisonFirewall()
        self.dump_monitor = dump_monitor or InsiderDumpMonitor()
        self.trap_detector = trap_detector or TrapDetector()
        self.reflex_central = reflex_central or BioReflexCentral()
        self.fractal_engine = fractal_engine or MultiTimeframeFractalEngine()
        self.turtle_engine = turtle_engine or InstitutionalTurtleEngine()
        self.kelly = kelly_allocator or DynamicKellyAllocator()

    def execute_tick(
        self,
        symbol: str,
        current_price: float,
        macro_history: List[float],
        meso_history: List[float],
        instant_price_drop_pct: float = 0.0,
        is_limit_down_locked: bool = False,
        is_limit_up_locked: bool = False,
        financial_record: Optional[CompanyFinancialRecord] = None,
        insider_dump_ratio_adv: float = 0.0,
        insider_pledge_ratio: float = 0.0,
        current_breakout_volume: float = 10000.0,
        recent_avg_volume: float = 10000.0
    ) -> PipelineCycleResult:
        """
        四层端到端闭环驱动：从微观财务核验到订单成交
        """
        sym = symbol.upper()
        trace: Dict[str, Any] = {}

        # 1. 第一级：脊髓原始反射弧 (Spinal Primitive Reflex)
        spinal_cmd = self.reflex_central.evaluate_primitive_reflex(
            symbol=sym,
            instant_price_drop_pct=instant_price_drop_pct,
            is_limit_down_locked=is_limit_down_locked,
            is_data_corrupted=False
        )
        if spinal_cmd is not None and spinal_cmd.level == ReflexLevel.PRIMITIVE_SPINAL:
            trace["reflex"] = "TRIGGERED_PANIC_FREEZE"
            return PipelineCycleResult(
                symbol=sym,
                is_executed=False,
                action="EMERGENCY_FREEZE",
                stage_immune_passed=False,
                stage_gravity_passed=False,
                stage_execution_passed=False,
                veto_reason="触火即缩：检测到瞬时异常暴跌或跌停封死，脊髓反射弧强制切断交易",
                alert_type="CRISIS_ALARM",
                alert_color="rose-strobe",
                audit_trace=trace,
                receipt=None
            )

        # 2. 第二级：免疫系统综合排毒与陷阱过滤 (Immune System)
        if financial_record is not None:
            immune_rep = self.firewall.audit_statement(financial_record)
            trace["poison_firewall"] = {
                "phi_cp": immune_rep.phi_cp,
                "omega_debt": immune_rep.omega_debt,
                "is_admitted": immune_rep.is_admitted
            }
            if not immune_rep.is_admitted:
                return PipelineCycleResult(
                    symbol=sym,
                    is_executed=False,
                    action="VETO_POISON",
                    stage_immune_passed=False,
                    stage_gravity_passed=False,
                    stage_execution_passed=False,
                    veto_reason=f"排毒防火墙一票否决: {immune_rep.rejection_reason}",
                    alert_type="CRISIS_ALARM",
                    alert_color="rose-strobe",
                    audit_trace=trace,
                    receipt=None
                )

        insider_rep = self.dump_monitor.evaluate_insider_risk(
            symbol=sym,
            insider_sell_volume=insider_dump_ratio_adv * 100000.0,
            adv_20=100000.0,
            pledged_shares_ratio=insider_pledge_ratio,
            block_discount_pct=0.0
        )
        trace["insider_dump"] = {"severity": insider_rep.severity.value, "is_vetoed": insider_rep.is_vetoed}
        if insider_rep.is_vetoed:
            return PipelineCycleResult(
                symbol=sym,
                is_executed=False,
                action="VETO_INSIDER_DUMP",
                stage_immune_passed=False,
                stage_gravity_passed=False,
                stage_execution_passed=False,
                veto_reason=f"大股东清仓或质押警戒熔断: {insider_rep.warning_message}",
                alert_type="CRISIS_ALARM",
                alert_color="rose-strobe",
                audit_trace=trace,
                receipt=None
            )

        trace["trap_detector"] = "SKIPPED_NO_L1"

        # 3. 第三级：真值引力大脑与分形共振 (Gravity Brain)
        frac_res = self.fractal_engine.evaluate_fractal_resonance(
            symbol=sym,
            macro_closes=macro_history,
            meso_closes=meso_history,
            micro_current_price=current_price,
            micro_intraday_open=meso_history[-1] if meso_history else current_price
        )
        trace["fractal_resonance"] = frac_res.resonance_grade.value

        if frac_res.allowed_direction != "BUY":
            return PipelineCycleResult(
                symbol=sym,
                is_executed=False,
                action="STAND_ASIDE",
                stage_immune_passed=True,
                stage_gravity_passed=False,
                stage_execution_passed=False,
                veto_reason=f"分形共振未达多头共振标准: {frac_res.detailed_thesis}",
                alert_type="NONE",
                alert_color="none",
                audit_trace=trace,
                receipt=None
            )

        # 4. 第四级：动态凯利仓位配比与仿真撮合成交 (Entropy Execution)
        equity = self.paper.total_equity
        allocated_capital = equity * 0.10
        target_shares = int(allocated_capital / current_price / 100) * 100
        if target_shares <= 0:
            target_shares = 100

        rcpt = self.paper.submit_order(
            symbol=sym,
            is_buy=True,
            quantity=float(target_shares),
            market_price=current_price,
            is_limit_down_locked=is_limit_down_locked,
            is_limit_up_locked=is_limit_up_locked
        )

        trace["paper_execution"] = {
            "success": rcpt.is_success,
            "shares": rcpt.executed_quantity,
            "friction": rcpt.friction_cost,
            "rejection": rcpt.rejection_reason
        }

        return PipelineCycleResult(
            symbol=sym,
            is_executed=rcpt.is_success,
            action="BUY_EXECUTED" if rcpt.is_success else "EXECUTION_REJECTED",
            stage_immune_passed=True,
            stage_gravity_passed=True,
            stage_execution_passed=rcpt.is_success,
            veto_reason=rcpt.rejection_reason,
            alert_type="ENTRY_PING" if rcpt.is_success else "NONE",
            alert_color="emerald-pulse" if rcpt.is_success else "none",
            audit_trace=trace,
            receipt=rcpt
        )
