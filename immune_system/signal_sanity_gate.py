"""
immune_system/signal_sanity_gate.py
===================================
TRINITY QUANT 产出信号多维交叉验证门与微观撮合物理过滤器。

解决微观撮合与假流动性致命暗礁：
1. A股一字跌停板绝对无法成交的物理事实 (拒绝纸面富贵);
2. 订单容量红线限制 (单笔严禁超过近5日日均成交量 ADV 的 2%);
3. 盘口漂移与过期信号一票拦截。
"""

from dataclasses import dataclass
import math
from typing import Optional


@dataclass(frozen=True)
class SanityGateResult:
    """信号交叉检验裁决"""
    symbol: str
    is_passed: bool
    adjusted_quantity: float
    veto_reason: Optional[str]
    is_limit_locked: bool


class SignalSanityGate:
    """信号多维物理核验门"""

    def __init__(
        self,
        max_adv_participation_rate: float = 0.02,
        max_price_drift_ratio: float = 0.015,
        max_quote_age_sec: float = 5.0
    ) -> None:
        if max_adv_participation_rate <= 0 or max_adv_participation_rate > 0.10:
            raise ValueError("单笔ADV容量阈值必须在 (0, 0.10] 之间")
        if max_price_drift_ratio <= 0:
            raise ValueError("价格漂移阈值必须大于0")
        self._max_adv_rate = max_adv_participation_rate
        self._max_drift = max_price_drift_ratio
        self._max_quote_age = max_quote_age_sec

    def verify_order(
        self,
        symbol: str,
        is_buy: bool,
        signal_price: float,
        current_market_price: float,
        proposed_quantity: float,
        five_day_adv: float,
        limit_up_price: Optional[float] = None,
        limit_down_price: Optional[float] = None,
        quote_age_sec: float = 0.0
    ) -> SanityGateResult:
        """
        物理交叉检验
        
        :param symbol: 标的代码
        :param is_buy: True 为买入, False 为卖出
        :param signal_price: 策略产出信号时的基准价
        :param current_market_price: 准备向交易所报单时的最新真实成交价
        :param proposed_quantity: 计划下单数量
        :param five_day_adv: 近5日日均成交量 (股数或手数)
        :param limit_up_price: 当日法定涨停价
        :param limit_down_price: 当日法定跌停价
        :param quote_age_sec: 行情延迟秒数
        :return: SanityGateResult
        """
        sym = symbol.upper()

        # 0. 数学防爆防御：严防非法、非正或 NaN 假信号漏入
        if (
            signal_price <= 0 or current_market_price <= 0 or proposed_quantity <= 0 or
            math.isnan(signal_price) or math.isnan(current_market_price) or math.isnan(proposed_quantity) or
            math.isinf(signal_price) or math.isinf(current_market_price) or math.isinf(proposed_quantity)
        ):
            return SanityGateResult(
                symbol=sym,
                is_passed=False,
                adjusted_quantity=0.0,
                veto_reason=f"价格或报单量存在非法非正或异常数值: sig_px={signal_price}, mkt_px={current_market_price}, qty={proposed_quantity}",
                is_limit_locked=False
            )

        # 1. 检验行情是否严重过期
        if quote_age_sec > self._max_quote_age:
            return SanityGateResult(
                symbol=sym,
                is_passed=False,
                adjusted_quantity=0.0,
                veto_reason=f"行情严重过期({quote_age_sec:.1f}s > {self._max_quote_age}s)，一票拦截出单",
                is_limit_locked=False
            )

        # 2. 涨跌停封死无法成交的物理事实检验
        if not is_buy and limit_down_price is not None:
            if abs(current_market_price - limit_down_price) < 1e-4:
                # 跌停板无法卖出！坚决拒绝纸面假撮合
                return SanityGateResult(
                    symbol=sym,
                    is_passed=False,
                    adjusted_quantity=0.0,
                    veto_reason="标的一字跌停封死，物理上无法卖出成交，严禁假设成交伪造净值！",
                    is_limit_locked=True
                )

        if is_buy and limit_up_price is not None:
            if abs(current_market_price - limit_up_price) < 1e-4:
                # 涨停板无法买入！
                return SanityGateResult(
                    symbol=sym,
                    is_passed=False,
                    adjusted_quantity=0.0,
                    veto_reason="标的一字涨停封死，买单封板无法买入！",
                    is_limit_locked=True
                )

        # 3. 价格漂移检验 (Price Drift)
        drift = abs(current_market_price - signal_price) / signal_price
        if drift > self._max_drift:
            return SanityGateResult(
                symbol=sym,
                is_passed=False,
                adjusted_quantity=0.0,
                veto_reason=f"报单瞬时盘口漂移过大({drift*100:.2f}% > {self._max_drift*100:.2f}%)，作废过期信号",
                is_limit_locked=False
            )

        # 4. 流动性冲击与 ADV 承载力压缩 (Order Truncation)
        max_allowed_qty = max(1.0, five_day_adv * self._max_adv_rate)
        if proposed_quantity > max_allowed_qty:
            # 自动压制至冲击安全线
            return SanityGateResult(
                symbol=sym,
                is_passed=True,
                adjusted_quantity=max_allowed_qty,
                veto_reason=f"订单量超过 ADV 2% 冲击安全线，自动从 {proposed_quantity} 压缩至 {max_allowed_qty}",
                is_limit_locked=False
            )

        return SanityGateResult(
            symbol=sym,
            is_passed=True,
            adjusted_quantity=proposed_quantity,
            veto_reason=None,
            is_limit_locked=False
        )
