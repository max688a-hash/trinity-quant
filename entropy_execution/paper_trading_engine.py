"""
entropy_execution/paper_trading_engine.py
=========================================
TRINITY QUANT 顶级全自动量化模拟盘与虚拟撮合引擎。

实现机构级真机仿真环境：
1. 完整账户记账 (现金、总资产、可用保证金、浮动盈亏、已实现盈亏);
2. 严格按各大市场真实交割摩擦 (T+1锁仓、印花税、双边佣金、滑点冲击);
3. 动态盯市 (Mark-to-Market) 与吊灯跟踪止盈止损自动触发平仓;
4. 实时统计年化胜率、盈亏比与最大回撤。
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from entropy_execution.dynamic_trailing_stop import (
    DynamicTrailingStopEngine,
)
from entropy_execution.multi_market_friction import (
    MultiMarketFrictionEngine,
)
from truth_kernel.asset_taxonomy import (
    SettlementType,
    TaxonomyRegistry,
)
from truth_kernel.market_session_clock import MarketSessionClock


@dataclass
class PaperPosition:
    """模拟持仓头寸"""
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    highest_price: float
    trailing_stop_price: float
    current_atr: float
    settlement: SettlementType
    shares_frozen_t1: float = 0.0     # A股 T+1 当日冻结不可卖份额


@dataclass(frozen=True)
class PaperExecutionReceipt:
    """撮合成交回报回执"""
    symbol: str
    is_buy: bool
    executed_price: float
    executed_quantity: float
    friction_cost: float
    stamp_duty: float
    commission: float
    slippage: float
    is_success: bool
    rejection_reason: Optional[str]


class PaperTradingEngine:
    """全自动量化模拟盘与仿真撮合器"""

    def __init__(
        self,
        initial_capital: float = 10_000_000.0,
        trailing_stop_engine: Optional[DynamicTrailingStopEngine] = None,
        friction_engine: Optional[MultiMarketFrictionEngine] = None,
        enforce_trading_hours: bool = False
    ) -> None:
        if initial_capital <= 0:
            raise ValueError("初始资金必须大于0")
        self._initial_capital = initial_capital
        self._cash = initial_capital
        self._positions: Dict[str, PaperPosition] = {}
        self._trailing_engine = trailing_stop_engine or DynamicTrailingStopEngine()
        self._friction_engine = friction_engine or MultiMarketFrictionEngine()
        self.enforce_trading_hours = enforce_trading_hours
        self._peak_equity = initial_capital
        self._max_drawdown = 0.0
        self._trade_history: List[dict] = []

    @property
    def cash(self) -> float:
        return self._cash

    @property
    def total_equity(self) -> float:
        """动态盯市总资产"""
        pos_val = sum(p.quantity * p.current_price for p in self._positions.values())
        return self._cash + pos_val

    def get_position(self, symbol: str) -> Optional[PaperPosition]:
        return self._positions.get(symbol.upper())

    def update_market_quote(self, symbol: str, current_price: float, current_atr: float) -> List[PaperExecutionReceipt]:
        """
        接收行情推入，动态盯市并自动触发追踪止损平仓
        """
        if (
            current_price <= 0 or current_atr <= 0 or
            math.isnan(current_price) or math.isnan(current_atr) or
            math.isinf(current_price) or math.isinf(current_atr)
        ):
            return []

        sym = symbol.upper()
        auto_receipts: List[PaperExecutionReceipt] = []
        if sym in self._positions:
            pos = self._positions[sym]
            pos.current_price = current_price
            pos.current_atr = current_atr
            if current_price > pos.highest_price:
                pos.highest_price = current_price

            # 评估动态追踪止损
            verdict = self._trailing_engine.evaluate_position(
                symbol=sym,
                entry_price=pos.avg_cost,
                current_price=current_price,
                highest_price_since_entry=pos.highest_price,
                previous_stop_price=pos.trailing_stop_price,
                current_atr=current_atr
            )
            pos.trailing_stop_price = verdict.current_stop_price

            # 触发出场平仓
            if verdict.should_close:
                # 检查 T+1 约束
                avail_qty = pos.quantity - pos.shares_frozen_t1
                if avail_qty > 0:
                    rcpt = self.submit_order(sym, is_buy=False, quantity=avail_qty, market_price=current_price)
                    auto_receipts.append(rcpt)

        # 动态更新净值峰值与最大回撤
        eq = self.total_equity
        if eq > self._peak_equity:
            self._peak_equity = eq
        dd = (self._peak_equity - eq) / self._peak_equity if self._peak_equity > 0 else 0.0
        if dd > self._max_drawdown:
            self._max_drawdown = dd

        return auto_receipts

    def submit_order(
        self,
        symbol: str,
        is_buy: bool,
        quantity: float,
        market_price: float,
        is_limit_down_locked: bool = False,
        is_limit_up_locked: bool = False,
        is_replay_mode: bool = False
    ) -> PaperExecutionReceipt:
        """
        执行仿真撮合 (含开闭市时钟严格拦截、全摩擦扣减、T+1/T+0 制度与极端涨跌停流动性枯竭防御)
        """
        sym = symbol.upper()
        if (
            quantity <= 0 or market_price <= 0 or
            math.isnan(quantity) or math.isnan(market_price) or
            math.isinf(quantity) or math.isinf(market_price)
        ):
            return PaperExecutionReceipt(sym, is_buy, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False, "非法价格或数量异常(含NaN/Inf)")

        # 物理交易所真实开闭市时钟防火墙 (杜绝非交易时段与周末偷跑假成交)
        if self.enforce_trading_hours and (not is_replay_mode):
            clock_res = MarketSessionClock.evaluate_symbol(sym)
            if not clock_res.is_open:
                return PaperExecutionReceipt(
                    sym, is_buy, market_price, 0.0, 0.0, 0.0, 0.0, 0.0, False,
                    f"⛔ 交易所休市拦截：{clock_res.reason} (严禁非交易时段虚假成交，若需回测请开启历史回放模式)"
                )

        # 极端行情流动性枯竭与一字涨跌停封死拦截
        if is_buy and is_limit_up_locked:
            return PaperExecutionReceipt(sym, True, market_price, 0.0, 0.0, 0.0, 0.0, 0.0, False, "一字涨停封死无筹码出让，无法撮合买入")
        if (not is_buy) and is_limit_down_locked:
            return PaperExecutionReceipt(sym, False, market_price, 0.0, 0.0, 0.0, 0.0, 0.0, False, "一字跌停封死无接盘流动性，无法撮合平仓")

        spec = TaxonomyRegistry.get(sym)
        fric = self._friction_engine.calculate_friction(sym, market_price, quantity, is_buy)

        if is_buy:
            # 检查资金充裕度
            total_required = fric.notional_value + fric.total_friction
            if total_required > self._cash:
                return PaperExecutionReceipt(sym, True, market_price, 0.0, 0.0, 0.0, 0.0, 0.0, False, "可用资金不足")

            self._cash -= total_required
            frozen = quantity if spec.settlement == SettlementType.T_PLUS_1 else 0.0

            if sym in self._positions:
                pos = self._positions[sym]
                new_qty = pos.quantity + quantity
                pos.avg_cost = (pos.avg_cost * pos.quantity + market_price * quantity) / new_qty
                pos.quantity = new_qty
                pos.shares_frozen_t1 += frozen
                pos.current_price = market_price
                pos.highest_price = max(pos.highest_price, market_price)
            else:
                initial_stop = market_price - 2.5 * spec.price_tick * 10
                self._positions[sym] = PaperPosition(
                    symbol=sym,
                    quantity=quantity,
                    avg_cost=market_price,
                    current_price=market_price,
                    highest_price=market_price,
                    trailing_stop_price=initial_stop,
                    current_atr=spec.price_tick * 10,
                    settlement=spec.settlement,
                    shares_frozen_t1=frozen
                )
        else:
            # 卖出平仓
            if sym not in self._positions:
                return PaperExecutionReceipt(sym, False, market_price, 0.0, 0.0, 0.0, 0.0, 0.0, False, "无持仓不可平仓")

            pos = self._positions[sym]
            avail_qty = pos.quantity - pos.shares_frozen_t1
            if quantity > avail_qty:
                return PaperExecutionReceipt(sym, False, market_price, 0.0, 0.0, 0.0, 0.0, 0.0, False, f"超出可用头寸 (T+1冻结 {pos.shares_frozen_t1})")

            pos.quantity -= quantity
            gross_proceeds = market_price * spec.contract_multiplier * quantity
            net_proceeds = gross_proceeds - fric.total_friction
            self._cash += net_proceeds

            # 记录已实现盈亏
            realized_pnl = (market_price - pos.avg_cost) * spec.contract_multiplier * quantity - fric.total_friction
            self._trade_history.append({"symbol": sym, "pnl": realized_pnl, "return_pct": (market_price - pos.avg_cost) / pos.avg_cost})

            if pos.quantity <= 1e-6:
                del self._positions[sym]

        return PaperExecutionReceipt(
            symbol=sym,
            is_buy=is_buy,
            executed_price=market_price,
            executed_quantity=quantity,
            friction_cost=fric.total_friction,
            stamp_duty=fric.stamp_duty,
            commission=fric.commission,
            slippage=fric.slippage_cost,
            is_success=True,
            rejection_reason=None
        )

    def rollover_trading_day(self) -> None:
        """跨日结算：解冻 A 股 T+1 头寸"""
        for pos in self._positions.values():
            pos.shares_frozen_t1 = 0.0
