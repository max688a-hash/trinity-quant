"""
entropy_execution.backtest_engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
高保真事件驱动回测引擎 (High-Fidelity Event-Driven Backtest Engine)。
全流程闭环集成：
1. PIT 时点财务数据加载 (truth_kernel)：仅使用 disclosure_date <= 调仓日 的报表
2. 一票否决排毒过滤 (immune_system)
3. 真值引力定价与 Alpha 信号 (gravity_brain)；无股本数据时势能标记为 None（中性），不伪造
4. 动态防爆凯利仓位 (DynamicKellyAllocator)：p / b / CVaR 全部来自本次回测已平仓交易的
   滚动实证统计（严格 walk-forward，只用过去）；样本不足时走显式冷启动探仓
5. 全真实双向滑点、印花税、佣金摩擦撮合 (FrictionEngine)
6. 组合回撤熔断与几何复利监测 (PortfolioGuardian)
7. 退市/长期停牌标的：按最后已知收盘价强制清算并记录，消除幸存者偏差
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from entropy_execution.dynamic_kelly import DynamicKellyAllocator
from entropy_execution.friction_engine import FrictionEngine
from entropy_execution.portfolio_guardian import PortfolioGuardian, RiskMetrics
from entropy_execution.trade_statistics import RollingTradeStatistics
from gravity_brain.alpha_engine import GravityAlphaEngine
from truth_kernel.models import CompanyFinancialRecord


@dataclass(frozen=True)
class BacktestReport:
    """全仿真回测终局审计报告"""
    initial_cash: float
    final_equity: float
    total_net_return: float          # 真实净收益率 (已扣除全部税费滑点)
    cagr: float                      # 几何年化复利
    max_drawdown: float              # 最大回撤
    total_trades: int                # 真实撮合成交笔数
    total_friction_cost: float       # 缴纳印花税、佣金与滑点冲击总额 (元)
    risk_metrics: RiskMetrics
    equity_curve: List[float]
    cold_start_periods: int = 0      # 凯利样本不足、以冷启动探仓运行的期数
    empirical_periods: int = 0       # 凯利以实证 p/b/CVaR 运行的期数
    forced_liquidations: List[str] = field(default_factory=list)
    pit_excluded_records: int = 0    # 因披露日晚于调仓日而被剔除的报表数


@dataclass
class _Lot:
    shares: int
    avg_cost: float


class EventDrivenBacktester:
    """
    事件驱动回测执行器
    严禁无摩擦成本回测，严禁使用未来函数，严禁写死胜率/盈亏比。
    """

    def __init__(
        self,
        initial_cash: float = 10_000_000.0,
        friction_engine: Optional[FrictionEngine] = None,
        kelly_allocator: Optional[DynamicKellyAllocator] = None,
        portfolio_guardian: Optional[PortfolioGuardian] = None,
        min_kelly_samples: int = 20,
        cold_start_weight: float = 0.02,
    ) -> None:
        if not 0.0 < cold_start_weight <= 0.05:
            raise ValueError("冷启动探仓权重必须在 (0, 5%]")
        self.initial_cash = initial_cash
        self.friction_engine = friction_engine or FrictionEngine()
        self.kelly = kelly_allocator or DynamicKellyAllocator()
        self.guardian = portfolio_guardian or PortfolioGuardian()
        self.alpha_engine = GravityAlphaEngine()
        self.min_kelly_samples = min_kelly_samples
        self.cold_start_weight = cold_start_weight

    @staticmethod
    def _pit_filter(records: Dict[str, CompanyFinancialRecord], as_of: Optional[date]) -> tuple[List[CompanyFinancialRecord], int]:
        if as_of is None:
            return list(records.values()), 0
        kept: List[CompanyFinancialRecord] = []
        dropped = 0
        for r in records.values():
            if date.fromisoformat(r.disclosure_date[:10]) <= as_of:
                kept.append(r)
            else:
                dropped += 1
        return kept, dropped

    def _sell(self, sym: str, price: float, shares: int, lots: Dict[str, _Lot], stats: RollingTradeStatistics) -> tuple[float, float]:
        fill = self.friction_engine.execute_sell(sym, price, shares)
        lot = lots[sym]
        cost_basis = lot.avg_cost * shares
        stats.record_closed_trade((fill.net_cash_impact - cost_basis) / max(0.01, cost_basis))
        lot.shares -= shares
        if lot.shares <= 0:
            del lots[sym]
        return fill.net_cash_impact, fill.total_friction

    def _buy(self, sym: str, price: float, shares: int, lots: Dict[str, _Lot]) -> tuple[float, float]:
        fill = self.friction_engine.execute_buy(sym, price, shares)
        lot = lots.get(sym)
        if lot is None:
            lots[sym] = _Lot(shares=shares, avg_cost=-fill.net_cash_impact / shares)
        else:
            total_cost = lot.avg_cost * lot.shares - fill.net_cash_impact
            lot.shares += shares
            lot.avg_cost = total_cost / lot.shares
        return fill.net_cash_impact, fill.total_friction

    def run_simulation(
        self,
        historical_snapshots: List[Dict[str, CompanyFinancialRecord]],
        price_feeds: List[Dict[str, float]],
        periods_per_year: int = 4,
        rebalance_dates: Optional[List[date]] = None,
        shares_outstanding: Optional[Dict[str, float]] = None,
        last_known_prices: Optional[List[Dict[str, float]]] = None,
        warm_start_returns: Optional[List[float]] = None,
    ) -> BacktestReport:
        """
        运行全周期时序回测
        :param historical_snapshots: 按时间升序的每期可见财务报表 {symbol: record}
        :param price_feeds: 与时序对齐的可交易收盘价 {symbol: price}；缺失 = 停牌/退市不可交易
        :param rebalance_dates: 每期调仓日，用于 PIT 披露日过滤（None 则不过滤）
        :param shares_outstanding: 总股本 {symbol: shares}，缺失时引力势能为 None（中性）
        :param last_known_prices: 每期不可交易标的的最后已知收盘价，用于强制清算标价
        :param warm_start_returns: 来自更早样本内窗口的已平仓净收益率（walk-forward 热启动），
                                   必须早于本次回测区间，严禁用本区间结果回填
        """
        cash = self.initial_cash
        lots: Dict[str, _Lot] = {}
        equity_curve: List[float] = [self.initial_cash]
        stats = RollingTradeStatistics(window=max(self.min_kelly_samples, 60), min_samples=self.min_kelly_samples)
        if warm_start_returns:
            stats.extend(warm_start_returns)
        total_friction = 0.0
        total_trades = 0
        cold_periods = 0
        emp_periods = 0
        pit_dropped = 0
        forced: List[str] = []
        steps = min(len(historical_snapshots), len(price_feeds))

        for t in range(steps):
            prices = price_feeds[t]
            as_of = rebalance_dates[t] if rebalance_dates else None
            fallback = last_known_prices[t] if last_known_prices else {}

            # 0. 退市/长期停牌强制清算（幸存者偏差消除）
            for sym in list(lots.keys()):
                if sym not in prices:
                    liq_px = fallback.get(sym)
                    if liq_px is None or liq_px <= 0:
                        continue
                    delta, fric = self._sell(sym, liq_px, lots[sym].shares, lots, stats)
                    cash += delta
                    total_friction += fric
                    total_trades += 1
                    forced.append(f"{sym}@{as_of}:{liq_px}")

            mark_val = sum(l.shares * prices.get(s, 0.0) for s, l in lots.items())
            current_total_equity = cash + mark_val

            # 1. 组合风控熔断
            metrics = self.guardian.evaluate_returns(equity_curve, periods_per_year=periods_per_year)
            if metrics.circuit_breaker_active:
                for sym in list(lots.keys()):
                    if sym in prices:
                        delta, fric = self._sell(sym, prices[sym], lots[sym].shares, lots, stats)
                        cash += delta
                        total_friction += fric
                        total_trades += 1
                equity_curve.append(cash + sum(l.shares * prices.get(s, 0.0) for s, l in lots.items()))
                continue

            # 2. PIT 过滤 + Alpha 排序
            visible, dropped = self._pit_filter(historical_snapshots[t], as_of)
            pit_dropped += dropped
            caps: Dict[str, float] = {}
            if shares_outstanding:
                caps = {s: prices[s] * n for s, n in shares_outstanding.items() if s in prices and n > 0}
            candidates = self.alpha_engine.rank_universe(visible, market_caps=caps or None)

            # 3. 凯利目标仓位（实证 p/b/CVaR，只看过去）
            k_in = stats.compute()
            if k_in.has_sufficient_evidence:
                emp_periods += 1
            else:
                cold_periods += 1
            target_shares: Dict[str, int] = {}
            for c in candidates:
                cur_price = prices.get(c.symbol, 0.0)
                if cur_price <= 0:
                    continue
                if not c.is_firewall_admitted or c.signal == "VETO":
                    target_shares[c.symbol] = 0
                    continue
                gp = ((c.gravity_value - caps[c.symbol]) / caps[c.symbol]) if c.symbol in caps else None
                if k_in.has_sufficient_evidence:
                    weight = self.kelly.calculate_weight(
                        symbol=c.symbol, win_rate=k_in.win_rate, payoff_ratio=k_in.payoff_ratio,
                        cvar_alpha=k_in.cvar_alpha, gravity_potential=gp, is_firewall_admitted=True,
                    ).target_weight
                else:
                    weight = 0.0 if (gp is not None and gp <= 0) else self.cold_start_weight
                target_shares[c.symbol] = (int(current_total_equity * weight / cur_price) // 100) * 100

            # 4. 先卖后买，全摩擦撮合
            for sym in list(lots.keys()):
                target = target_shares.get(sym, 0)
                if lots[sym].shares > target and sym in prices:
                    delta, fric = self._sell(sym, prices[sym], lots[sym].shares - target, lots, stats)
                    cash += delta
                    total_friction += fric
                    total_trades += 1
            for sym, target in target_shares.items():
                cur = lots[sym].shares if sym in lots else 0
                if target > cur:
                    buy_delta = target - cur
                    if cash >= prices[sym] * buy_delta * 1.002:
                        delta, fric = self._buy(sym, prices[sym], buy_delta, lots)
                        cash += delta
                        total_friction += fric
                        total_trades += 1

            equity_curve.append(cash + sum(l.shares * prices.get(s, 0.0) for s, l in lots.items()))

        final_equity = equity_curve[-1]
        final_metrics = self.guardian.evaluate_returns(equity_curve, periods_per_year=periods_per_year)
        return BacktestReport(
            initial_cash=self.initial_cash,
            final_equity=round(final_equity, 2),
            total_net_return=round((final_equity - self.initial_cash) / max(1.0, self.initial_cash), 4),
            cagr=final_metrics.cagr,
            max_drawdown=final_metrics.max_drawdown,
            total_trades=total_trades,
            total_friction_cost=round(total_friction, 2),
            risk_metrics=final_metrics,
            equity_curve=equity_curve,
            cold_start_periods=cold_periods,
            empirical_periods=emp_periods,
            forced_liquidations=forced,
            pit_excluded_records=pit_dropped,
        )
