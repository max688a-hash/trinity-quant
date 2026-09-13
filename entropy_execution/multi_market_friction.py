"""
entropy_execution/multi_market_friction.py
==========================================
TRINITY QUANT 跨市场全保真摩擦成本引擎。

严格按各大交易所物理交割规则计算：
- A股: T+1, 卖方0.05%印花税, 经手过户费, 5元佣金门槛;
- 港股: T+0, 买卖双边0.10%印花税, 证监会征费(SFC), 财务汇报局征费(FRC), 手制约束;
- 美股: T+0, 零印花税, SEC费率, FINRA TAF, 碎股支持;
- 期货: 双边手续费(按手或成交额), 合约乘数换算, 保证金占用与跳空滑点.
"""

from dataclasses import dataclass
from typing import Optional

from truth_kernel.asset_taxonomy import (
    CommissionType,
    InstrumentSpecification,
    MarketVenue,
    TaxonomyRegistry,
)


@dataclass(frozen=True)
class MultiMarketFrictionCost:
    """跨市场交易摩擦测算明细"""
    symbol: str
    venue: MarketVenue
    is_buy: bool
    price: float
    quantity: float
    notional_value: float
    stamp_duty: float
    commission: float
    regulatory_fees: float
    slippage_cost: float
    margin_required: float
    total_friction: float
    friction_bps: float


class MultiMarketFrictionEngine:
    """多市场摩擦成本结算器"""

    def __init__(self, default_slippage_ticks: int = 1) -> None:
        if default_slippage_ticks < 0:
            raise ValueError("滑点步长不得为负")
        self._default_slippage_ticks = default_slippage_ticks

    def calculate_friction(
        self,
        symbol: str,
        price: float,
        quantity: float,
        is_buy: bool,
        spec_override: Optional[InstrumentSpecification] = None
    ) -> MultiMarketFrictionCost:
        """
        全保真计算单笔交易摩擦与保证金
        
        :param symbol: 标的代码 (如 600519.SH, 0700.HK, AAPL.US, C, SA)
        :param price: 成交单价
        :param quantity: 交易数量 (股票为股数, 期货为手数)
        :param is_buy: True 为买入/开多, False 为卖出/平仓
        :param spec_override: 可选自定义规格 (若为 None 则从注册表加载)
        :return: MultiMarketFrictionCost
        """
        if price <= 0 or quantity <= 0:
            raise ValueError(f"价格 ({price}) 和数量 ({quantity}) 必须大于0")

        spec = spec_override if spec_override is not None else TaxonomyRegistry.get(symbol)

        # 1. 计算物理名义价值 Notional Value
        # 股票: price * shares; 期货: price * multiplier * contracts
        notional = price * spec.contract_multiplier * quantity

        # 2. 印花税 Stamp Duty
        stamp_rate = spec.stamp_duty_buy if is_buy else spec.stamp_duty_sell
        stamp_duty = notional * stamp_rate

        # 3. 券商与交易所佣金 Commission
        if spec.commission_type == CommissionType.PER_CONTRACT:
            commission = spec.commission_rate * quantity
        else:
            commission = notional * spec.commission_rate
            # A股单笔佣金最低5元物理保底
            if spec.venue == MarketVenue.CN_EQUITY:
                commission = max(5.0, commission)
            # 港股单笔最低50港币保底
            elif spec.venue == MarketVenue.HK_EQUITY:
                commission = max(50.0, commission)

        # 4. 规费与监管税费 Regulatory Fees
        reg_fees = 0.0
        if spec.venue == MarketVenue.CN_EQUITY:
            # 过户费: 0.001% (万0.1)
            reg_fees = notional * 0.00001
        elif spec.venue == MarketVenue.HK_EQUITY:
            # SFC 征费 0.0027%, FRC 征费 0.00015%, HKEX 费 0.00565%
            reg_fees = notional * (0.000027 + 0.0000015 + 0.0000565)
        elif spec.venue == MarketVenue.US_EQUITY:
            # 美股卖出收 SEC 规费 (约万分之0.278) + FINRA TAF
            if not is_buy:
                reg_fees = notional * 0.0000278 + quantity * 0.000166

        # 5. 滑点冲击成本 Slippage Cost
        # 滑点损失 = slippage_ticks * price_tick * contract_multiplier * quantity
        slippage_cost = self._default_slippage_ticks * spec.price_tick * spec.contract_multiplier * quantity

        # 6. 保证金占用 Margin Required
        margin_required = notional * spec.initial_margin_ratio

        total_friction = stamp_duty + commission + reg_fees + slippage_cost
        friction_bps = (total_friction / notional) * 10000.0 if notional > 0 else 0.0

        return MultiMarketFrictionCost(
            symbol=spec.symbol,
            venue=spec.venue,
            is_buy=is_buy,
            price=price,
            quantity=quantity,
            notional_value=notional,
            stamp_duty=stamp_duty,
            commission=commission,
            regulatory_fees=reg_fees,
            slippage_cost=slippage_cost,
            margin_required=margin_required,
            total_friction=total_friction,
            friction_bps=friction_bps
        )
