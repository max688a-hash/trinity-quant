"""
entropy_execution/autonomous_learning_sandbox.py
=================================================
TRINITY QUANT 自动量化模拟盘影子执行与策略自学习进化中枢。
遵循最高宪法第一性原理：模拟盘是系统的自主学习检测实验室，非人类玩物。
1. 影子巡航 (Shadow Auto-Pilot)：根据真实行情时钟全自动四层流水线撮合；
2. 逐笔复盘 (Trade Autopsy)：捕捉特征快照，精算理论与实际盘口冲击偏差；
3. 贝叶斯自校准：自适应更新动态凯利比例 f* 与棘轮止损带宽；
4. 模型漂移监测：评估策略健康度 H，触发自冷却熔断。
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
import threading
import time
from typing import Any, Dict, List, Optional

from entropy_execution.algorithmic_order_slicer import MarketImpactModel
from entropy_execution.live_pipeline_orchestrator import LivePipelineOrchestrator
from entropy_execution.paper_trading_engine import PaperExecutionReceipt, PaperTradingEngine
from truth_kernel.market_session_clock import MarketSessionClock


class AutopsyVerdict(str, Enum):
    """逐笔复盘归因裁决"""
    ALPHA_EXPANSION_WIN = "ALPHA_EXPANSION_WIN"
    TRAILING_STOP_PROFIT = "TRAILING_STOP_PROFIT"
    NOISE_SHAKEOUT_LOSS = "NOISE_SHAKEOUT_LOSS"
    SLIPPAGE_DRAG_LOSS = "SLIPPAGE_DRAG_LOSS"


@dataclass(frozen=True)
class TradeAutopsyRecord:
    """逐笔订单全要素复盘档案"""
    trade_id: str
    symbol: str
    action: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    friction_cost: float
    holding_seconds: float
    predicted_slippage: float
    realized_slippage: float
    slippage_error: float
    verdict: AutopsyVerdict
    timestamp: str


@dataclass(frozen=True)
class SelfLearningReport:
    """系统自主学习与策略实证报告"""
    total_auto_trades: int
    winning_trades: int
    losing_trades: int
    empirical_win_rate: float
    empirical_payoff_ratio: float
    calibrated_kelly_f: float
    calibrated_trailing_stop_k: float
    calibrated_impact_gamma: float
    strategy_health_index: float
    is_cooling_down: bool
    recent_autopsies: List[Dict[str, Any]]
    learning_synthesis: str


class AutonomousLearningSandbox:
    """全自动量化模拟影子执行与策略自主学习进化引擎"""

    BEIJING_TZ = timezone(timedelta(hours=8))

    def __init__(
        self,
        paper_engine: Optional[PaperTradingEngine] = None,
        orchestrator: Optional[LivePipelineOrchestrator] = None
    ) -> None:
        self._lock = threading.Lock()
        self.paper = paper_engine or PaperTradingEngine(initial_capital=10_000_000.0, enforce_trading_hours=True)
        self.orchestrator = orchestrator or LivePipelineOrchestrator(paper_engine=self.paper)
        self.impact_model = MarketImpactModel()

        # 贝叶斯在线先验与盈亏跟踪 (真实冷启动，严禁虚构赢钱历史)
        self._prior_wins: float = 0.0
        self._prior_losses: float = 0.0
        self._win_pnls: List[float] = []
        self._loss_pnls: List[float] = []

        # 自校准超参数
        self.calibrated_kelly_fraction: float = 0.0
        self.calibrated_stop_k: float = 2.0
        self.calibrated_gamma: float = 0.314
        self.strategy_health_index: float = 1.0
        self.is_cooling_down: bool = False
        self._autopsy_history: List[TradeAutopsyRecord] = []
        self._entry_clock: Dict[str, float] = {}
        self._entry_predicted_slippage: Dict[str, float] = {}

    def _now_str(self) -> str:
        return datetime.now(self.BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")

    def run_autonomous_tick(
        self,
        symbol: str,
        current_price: float,
        macro_history: Optional[List[float]] = None,
        meso_history: Optional[List[float]] = None,
        is_replay_mode: bool = False
    ) -> Dict[str, Any]:
        """全自动无人值守影子执行与检测 Tick"""
        with self._lock:
            sym = symbol.strip().upper()
            clock_eval = MarketSessionClock.evaluate_symbol(sym)
            if not clock_eval.is_open and not is_replay_mode:
                return {"executed": False, "reason": f"交易所闭市 ({clock_eval.reason})，自动执行暂停", "auto_learning_active": True}

            if not macro_history:
                from truth_kernel.historical_kline_service import HistoricalKlineService
                candles = HistoricalKlineService.get_kline(sym, timeframe="D", count=25)
                macro = [float(c["close"]) for c in candles] if len(candles) >= 5 else []
            else:
                macro = macro_history

            if not meso_history:
                from truth_kernel.historical_kline_service import HistoricalKlineService
                candles_m = HistoricalKlineService.get_kline(sym, timeframe="60m", count=12)
                meso = [float(c["close"]) for c in candles_m] if len(candles_m) >= 5 else (macro[:12] if len(macro) >= 12 else [])
            else:
                meso = meso_history

            if not macro or not meso:
                return {"executed": False, "reason": "缺失真实历史K线序列，严禁虚构自造涨价曲线", "auto_learning_active": False}

            pipe_res = self.orchestrator.execute_tick(symbol=sym, current_price=current_price, macro_history=macro, meso_history=meso)
            if pipe_res.is_executed and pipe_res.receipt is not None and sym not in self._entry_clock:
                notional = pipe_res.receipt.executed_price * pipe_res.receipt.executed_quantity
                self._entry_clock[sym] = time.time()
                self._entry_predicted_slippage[sym] = self.impact_model.estimate_impact(sym, notional).estimated_slippage_pct
            self._evaluate_auto_exit(sym, current_price)

            return {
                "executed": pipe_res.is_executed, "action": pipe_res.action,
                "stage_immune_passed": pipe_res.stage_immune_passed,
                "stage_gravity_passed": pipe_res.stage_gravity_passed,
                "stage_execution_passed": pipe_res.stage_execution_passed,
                "veto_reason": pipe_res.veto_reason,
                "receipt": asdict(pipe_res.receipt) if pipe_res.receipt else None
            }

    def _evaluate_auto_exit(self, symbol: str, current_price: float) -> None:
        """自动盯市平仓与归因"""
        pos = self.paper._positions.get(symbol)
        if not pos or pos.quantity <= 0:
            return
        if pos.trailing_stop_price > 0 and current_price <= pos.trailing_stop_price:
            if not pos.shares_frozen_t1:
                rcpt = self.paper.submit_order(symbol=symbol, is_buy=False, quantity=pos.quantity, market_price=current_price, is_replay_mode=True)
                if rcpt.is_success:
                    self._record_autopsy_and_learn(symbol=symbol, entry_price=pos.avg_cost, exit_price=rcpt.executed_price, quantity=rcpt.executed_quantity, friction=rcpt.friction_cost, is_trailing_stop=True, receipt=rcpt)

    def _record_autopsy_and_learn(
        self, symbol: str, entry_price: float, exit_price: float,
        quantity: float, friction: float, is_trailing_stop: bool,
        receipt: Optional[PaperExecutionReceipt] = None
    ) -> None:
        """记录归因并触发贝叶斯在线参数迭代；持仓时长与滑点必须来自真实回执，禁止常量填充"""
        net_pnl = (exit_price - entry_price) * quantity - friction
        gross_notional = max(0.01, entry_price * quantity)
        pnl_pct = net_pnl / gross_notional
        entry_ts = self._entry_clock.pop(symbol, None)
        holding_seconds = (time.time() - entry_ts) if entry_ts is not None else 0.0
        predicted_slip = self._entry_predicted_slippage.pop(symbol, 0.0)
        realized_slip = (receipt.slippage / max(0.01, receipt.executed_price * receipt.executed_quantity)) if receipt else 0.0
        self.orchestrator.record_closed_trade(pnl_pct)

        if net_pnl > 0:
            self._prior_wins += 1.0
            self._win_pnls.append(net_pnl)
            verdict = AutopsyVerdict.TRAILING_STOP_PROFIT if is_trailing_stop else AutopsyVerdict.ALPHA_EXPANSION_WIN
        else:
            self._prior_losses += 1.0
            self._loss_pnls.append(abs(net_pnl))
            verdict = AutopsyVerdict.NOISE_SHAKEOUT_LOSS

        rec = TradeAutopsyRecord(
            trade_id=f"AUTO_{int(time.time() * 1000)}", symbol=symbol, action="BUY->SELL",
            entry_price=round(entry_price, 2), exit_price=round(exit_price, 2),
            quantity=quantity, pnl=round(net_pnl, 2), pnl_pct=round(pnl_pct, 4),
            friction_cost=round(friction, 2), holding_seconds=round(holding_seconds, 1),
            predicted_slippage=round(predicted_slip, 6), realized_slippage=round(realized_slip, 6),
            slippage_error=round(realized_slip - predicted_slip, 6),
            verdict=verdict, timestamp=self._now_str()
        )
        self._autopsy_history.insert(0, rec)
        if len(self._autopsy_history) > 50:
            self._autopsy_history.pop()
        self._calibrate_parameters()

    def _calibrate_parameters(self) -> None:
        """贝叶斯更新后验胜率与盈亏比，动态校准凯利 f* 与棘轮止损带宽"""
        total = self._prior_wins + self._prior_losses
        post_p = self._prior_wins / max(1.0, total)
        avg_win = (sum(self._win_pnls[-10:]) / len(self._win_pnls[-10:])) if self._win_pnls else 0.0
        avg_loss = (sum(self._loss_pnls[-10:]) / len(self._loss_pnls[-10:])) if self._loss_pnls else 0.0
        post_b = (avg_win / avg_loss) if avg_loss > 0 else (10.0 if avg_win > 0 else 0.0)

        # 半凯利配置；无优势时归零，不设人为下限
        raw_kelly = (post_p * post_b - (1.0 - post_p)) / max(0.1, post_b)
        self.calibrated_kelly_fraction = round(max(0.0, min(0.35, raw_kelly * 0.50)), 4)
        self.calibrated_stop_k = 2.2 if post_p > 0.60 else (1.5 if post_p < 0.40 else 2.0)

        # 策略健康度评估与自冷却
        drawdown = self.paper._max_drawdown
        self.strategy_health_index = round(min(1.0, (post_p * 1.5) * max(0.0, 1.0 - (drawdown / 0.05))), 3)
        self.is_cooling_down = (self.strategy_health_index < 0.45 or drawdown >= 0.03)

    def generate_learning_report(self) -> SelfLearningReport:
        """生成系统自主学习与自进化完整报告"""
        with self._lock:
            total = int(self._prior_wins + self._prior_losses)
            wins, losses = int(self._prior_wins), int(self._prior_losses)

            if total == 0:
                syn = (
                    "【系统自学习中枢已就绪】：当前处于零假样本冷启动待命状态，"
                    "尚未产生实盘或影子成交样本，严禁虚构盈利历史；凯利 f*=0，流水线仅以显式冷启动探仓运行。"
                )
                return SelfLearningReport(
                    total_auto_trades=0, winning_trades=0, losing_trades=0,
                    empirical_win_rate=0.0, empirical_payoff_ratio=0.0,
                    calibrated_kelly_f=self.calibrated_kelly_fraction,
                    calibrated_trailing_stop_k=self.calibrated_stop_k,
                    calibrated_impact_gamma=self.calibrated_gamma,
                    strategy_health_index=self.strategy_health_index,
                    is_cooling_down=self.is_cooling_down,
                    recent_autopsies=[],
                    learning_synthesis=syn
                )

            win_rate = wins / max(1, total)
            avg_win = (sum(self._win_pnls[-10:]) / len(self._win_pnls[-10:])) if self._win_pnls else 0.0
            avg_loss = (sum(self._loss_pnls[-10:]) / len(self._loss_pnls[-10:])) if self._loss_pnls else 0.0
            payoff = (avg_win / avg_loss) if avg_loss > 0 else (10.0 if avg_win > 0 else 0.0)

            syn = (
                f"【系统自学习总结】：基于最近 {total} 笔自动影子模拟成交实证，"
                f"后验胜率收敛于 {win_rate * 100:.1f}%，盈亏比为 {payoff:.2f}。"
                f"动态半凯利因子自进化至 f*={self.calibrated_kelly_fraction * 100:.1f}%；"
                f"最近一笔滑点误差 {self._autopsy_history[0].slippage_error if self._autopsy_history else 0.0:+.5f}，"
                f"当前策略健康度指数为 {self.strategy_health_index * 100:.1f}/100 ("
                f"{'🟢 运行在健康区间' if not self.is_cooling_down else '⚠️ 已触发模型退化自冷却熔断'})。"
            )

            return SelfLearningReport(
                total_auto_trades=total, winning_trades=wins, losing_trades=losses,
                empirical_win_rate=round(win_rate, 4), empirical_payoff_ratio=round(payoff, 2),
                calibrated_kelly_f=self.calibrated_kelly_fraction,
                calibrated_trailing_stop_k=self.calibrated_stop_k,
                calibrated_impact_gamma=self.calibrated_gamma,
                strategy_health_index=self.strategy_health_index,
                is_cooling_down=self.is_cooling_down,
                recent_autopsies=[asdict(a) for a in self._autopsy_history[:10]],
                learning_synthesis=syn
            )
