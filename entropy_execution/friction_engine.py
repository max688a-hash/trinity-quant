"""
entropy_execution.friction_engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
真实市场摩擦成本测算与高保真撮合引擎。
严格恪守《最高宪法》第 1 条红线：严禁无摩擦成本回测！
每一笔交易必须全量计提：
1. A 股单边印花税（卖出时计提 0.05%）
2. 券商双边佣金（万分之二，设有单笔最低 5 元门槛）
3. 买卖双向滑点冲击（双边 0.10%，买入上浮、卖出下浮）
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class OrderExecutionResult:
    """真实摩擦成交回报单"""
    symbol: str
    action: Literal["BUY", "SELL"]
    shares: int                      # 成交股数 (A 股一手为 100 股)
    nominal_price: float             # 委托名义价格 (元)
    executed_price: float            # 考虑滑点冲击后的真实成交价 (元)
    gross_value: float               # 名义成交金额 (元)
    commission: float                # 券商佣金支出 (元)
    stamp_duty: float                # 卖出印花税支出 (元)
    slippage_cost: float             # 滑点冲击隐性成本 (元)
    total_friction: float            # 摩擦成本总额 (佣金+印花税+滑点)
    net_cash_impact: float           # 对资金账户的实际净变动 (买入为负，卖出为正)


class FrictionEngine:
    """
    高保真交易摩擦引擎
    真实复刻 A 股市场的摩擦引力墙。
    """

    def __init__(
        self,
        stamp_duty_rate: float = 0.0005, # 卖出单边印花税 0.05%
        commission_rate: float = 0.0002, # 双边佣金 万分之二 (0.02%)
        min_commission: float = 5.0,     # 单笔最低佣金 5 元
        slippage_rate: float = 0.0010    # 双边滑点冲击 千分之一 (0.10%)
    ) -> None:
        self.stamp_duty_rate = stamp_duty_rate
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.slippage_rate = slippage_rate

    def execute_buy(
        self,
        symbol: str,
        price: float,
        shares: int
    ) -> OrderExecutionResult:
        """执行买入撮合"""
        if shares <= 0 or price <= 0:
            raise ValueError(f"买入参数非法: price={price}, shares={shares}")

        # 买入滑点：真实成交价在名义价基础上不利上浮 (+0.10%)
        executed_price = price * (1.0 + self.slippage_rate)
        gross_value = price * shares
        actual_asset_cost = executed_price * shares
        slippage_cost = actual_asset_cost - gross_value

        # 买入不收取印花税
        stamp_duty = 0.0

        # 券商佣金 (设 5 元最低门槛)
        raw_comm = gross_value * self.commission_rate
        commission = max(self.min_commission, raw_comm)

        total_friction = commission + stamp_duty + slippage_cost
        # 买入扣减现金 = 资产实际付出 + 佣金
        net_cash_impact = -(actual_asset_cost + commission)

        return OrderExecutionResult(
            symbol=symbol,
            action="BUY",
            shares=shares,
            nominal_price=round(price, 3),
            executed_price=round(executed_price, 3),
            gross_value=round(gross_value, 2),
            commission=round(commission, 2),
            stamp_duty=round(stamp_duty, 2),
            slippage_cost=round(slippage_cost, 2),
            total_friction=round(total_friction, 2),
            net_cash_impact=round(net_cash_impact, 2)
        )

    def execute_sell(
        self,
        symbol: str,
        price: float,
        shares: int
    ) -> OrderExecutionResult:
        """执行卖出撮合"""
        if shares <= 0 or price <= 0:
            raise ValueError(f"卖出参数非法: price={price}, shares={shares}")

        # 卖出滑点：真实成交价在名义价基础上不利下浮 (-0.10%)
        executed_price = price * (1.0 - self.slippage_rate)
        gross_value = price * shares
        actual_asset_received = executed_price * shares
        slippage_cost = gross_value - actual_asset_received

        # 卖出法定计提单边印花税
        stamp_duty = gross_value * self.stamp_duty_rate

        # 券商佣金
        raw_comm = gross_value * self.commission_rate
        commission = max(self.min_commission, raw_comm)

        total_friction = commission + stamp_duty + slippage_cost
        # 卖出到手真金白银 = 成交收回资金 - 佣金 - 印花税
        net_cash_impact = actual_asset_received - commission - stamp_duty

        return OrderExecutionResult(
            symbol=symbol,
            action="SELL",
            shares=shares,
            nominal_price=round(price, 3),
            executed_price=round(executed_price, 3),
            gross_value=round(gross_value, 2),
            commission=round(commission, 2),
            stamp_duty=round(stamp_duty, 2),
            slippage_cost=round(slippage_cost, 2),
            total_friction=round(total_friction, 2),
            net_cash_impact=round(net_cash_impact, 2)
        )
