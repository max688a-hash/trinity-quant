"""
entropy_execution.backtest_engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
高保真事件驱动回测引擎 (High-Fidelity Event-Driven Backtest Engine)。
全流程闭环集成：
1. PIT 时点财务数据加载 (truth_kernel)
2. 一票否决排毒过滤 (immune_system)
3. 真值引力定价与 Alpha 信号 (gravity_brain)
4. 动态防爆凯利仓位决策 (DynamicKellyAllocator)
5. 全真实双向滑点、印花税、佣金摩擦撮合 (FrictionEngine)
6. 组合回撤熔断与几何复利监测 (PortfolioGuardian)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from truth_kernel.models import CompanyFinancialRecord
from immune_system.poison_firewall import PoisonFirewall
from gravity_brain.alpha_engine import GravityAlphaEngine
from entropy_execution.dynamic_kelly import DynamicKellyAllocator
from entropy_execution.friction_engine import FrictionEngine, OrderExecutionResult
from entropy_execution.portfolio_guardian import PortfolioGuardian, RiskMetrics


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


class EventDrivenBacktester:
    """
    事件驱动回测执行器
    严禁无摩擦成本回测，严禁使用未来函数。
    """

    def __init__(
        self,
        initial_cash: float = 10_000_000.0, # 初始资金 1000 万
        friction_engine: Optional[FrictionEngine] = None,
        kelly_allocator: Optional[DynamicKellyAllocator] = None,
        portfolio_guardian: Optional[PortfolioGuardian] = None
    ) -> None:
        self.initial_cash = initial_cash
        self.friction_engine = friction_engine or FrictionEngine()
        self.kelly = kelly_allocator or DynamicKellyAllocator()
        self.guardian = portfolio_guardian or PortfolioGuardian()
        self.alpha_engine = GravityAlphaEngine()

    def run_simulation(
        self,
        historical_snapshots: List[Dict[str, CompanyFinancialRecord]],
        price_feeds: List[Dict[str, float]],
        periods_per_year: int = 4
    ) -> BacktestReport:
        """
        运行全周期时序回测
        :param historical_snapshots: 按时间升序的每期财务报表现状 {symbol: record}
        :param price_feeds: 与时序严格对齐的真实市场价格矩阵 {symbol: price}
        :param periods_per_year: 年化周期系数 (季频为 4，日频为 252)
        """
        cash = self.initial_cash
        holdings: Dict[str, int] = {}  # symbol -> shares
        equity_curve: List[float] = [self.initial_cash]
        total_friction = 0.0
        total_trades = 0

        steps = min(len(historical_snapshots), len(price_feeds))

        for t in range(steps):
            financials = historical_snapshots[t]
            prices = price_feeds[t]

            # 1. 计算当前持仓市值与组合总净资产
            portfolio_asset_val = sum(holdings.get(s, 0) * prices.get(s, 0.0) for s in holdings)
            current_total_equity = cash + portfolio_asset_val

            # 2. 检查组合风控熔断机制
            metrics = self.guardian.evaluate_returns(equity_curve, periods_per_year=periods_per_year)
            if metrics.circuit_breaker_active:
                for s, shares in list(holdings.items()):
                    if shares > 0 and s in prices:
                        fill = self.friction_engine.execute_sell(s, prices[s], shares)
                        cash += fill.net_cash_impact
                        total_friction += fill.total_friction
                        total_trades += 1
                        holdings[s] = 0
                equity_curve.append(cash)
                continue

            # 3. 对当前财务记录执行 Alpha 定价与排序
            records_list = list(financials.values())
            candidates = self.alpha_engine.rank_universe(records_list)

            # 4. 根据动态凯利决策目标持仓
            target_shares: Dict[str, int] = {}
            for c in candidates:
                sym = c.symbol
                cur_price = prices.get(sym, 0.0)
                if cur_price <= 0:
                    continue

                if not c.is_firewall_admitted or c.signal == "VETO":
                    target_shares[sym] = 0
                    continue

                k_res = self.kelly.calculate_weight(
                    symbol=sym,
                    win_rate=0.65,
                    payoff_ratio=2.0,
                    cvar_alpha=0.08,
                    gravity_potential=0.30,
                    is_firewall_admitted=True
                )
                target_value = current_total_equity * k_res.target_weight
                raw_shares = int(target_value / cur_price)
                target_shares[sym] = (raw_shares // 100) * 100

            # 5. 执行调仓换股与摩擦撮合
            for sym, cur_shares in list(holdings.items()):
                target = target_shares.get(sym, 0)
                if cur_shares > target:
                    sell_delta = cur_shares - target
                    fill = self.friction_engine.execute_sell(sym, prices[sym], sell_delta)
                    cash += fill.net_cash_impact
                    total_friction += fill.total_friction
                    total_trades += 1
                    holdings[sym] = target

            for sym, target in target_shares.items():
                cur_shares = holdings.get(sym, 0)
                if target > cur_shares:
                    buy_delta = target - cur_shares
                    buy_price = prices.get(sym, 0.0)
                    cost_estimate = buy_price * buy_delta * 1.002
                    if cash >= cost_estimate and buy_price > 0:
                        fill = self.friction_engine.execute_buy(sym, buy_price, buy_delta)
                        cash += fill.net_cash_impact
                        total_friction += fill.total_friction
                        total_trades += 1
                        holdings[sym] = holdings.get(sym, 0) + buy_delta

            end_asset_val = sum(holdings.get(s, 0) * prices.get(s, 0.0) for s in holdings)
            equity_curve.append(cash + end_asset_val)

        final_equity = equity_curve[-1]
        final_metrics = self.guardian.evaluate_returns(equity_curve, periods_per_year=periods_per_year)
        net_ret = (final_equity - self.initial_cash) / max(1.0, self.initial_cash)

        return BacktestReport(
            initial_cash=self.initial_cash,
            final_equity=round(final_equity, 2),
            total_net_return=round(net_ret, 4),
            cagr=final_metrics.cagr,
            max_drawdown=final_metrics.max_drawdown,
            total_trades=total_trades,
            total_friction_cost=round(total_friction, 2),
            risk_metrics=final_metrics,
            equity_curve=equity_curve
        )
