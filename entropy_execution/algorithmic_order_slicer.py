"""
entropy_execution/algorithmic_order_slicer.py
==============================================
TRINITY QUANT 真实大资金冲击滑点抑制与 TWAP / 冰山算法切片执行引擎。

最高宪法立宪铁律：
真金大单直接敲向盘口，是向庄家暴露底牌并承担灾难级滑点的自杀行为！
1. MarketImpactModel: 基于 Almgren-Chriss 平方根法则量化盘口冲击成本；
2. TWAPOrderSlicer: 时间加权平均拆单器，大单平滑离散化分批挂入；
3. IcebergOrderSlicer: 冰山委托算法，可视深度仅 10%~20%，余量暗中随行吃单。
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class SlicerAlgorithm(str, Enum):
    """算法拆单类型"""
    DIRECT = "DIRECT"        # 小额直接成交（免拆单）
    TWAP = "TWAP"            # 时间加权平滑切片 (Time-Weighted Average Price)
    ICEBERG = "ICEBERG"      # 冰山委托隐藏挂单 (Iceberg Execution)


@dataclass(frozen=True)
class ChildOrderSlice:
    """拆单切片子委托明细"""
    slice_index: int
    total_slices: int
    quantity: float
    price_limit: float
    delay_seconds: float
    is_visible: bool
    description: str


@dataclass(frozen=True)
class MarketImpactEstimate:
    """盘口冲击成本精算结果"""
    symbol: str
    order_notional: float
    adv_notional: float
    participation_rate: float
    estimated_slippage_pct: float
    expected_impact_cost_yuan: float
    recommended_slices: int
    recommended_algo: SlicerAlgorithm


class MarketImpactModel:
    """盘口冲击成本精算器 (Almgren-Chriss 模型)"""

    def __init__(self, impact_gamma: float = 0.314) -> None:
        self.gamma = float(impact_gamma)

    def estimate_impact(
        self,
        symbol: str,
        notional: float,
        adv_notional: float = 50_000_000.0,
        daily_volatility: float = 0.02
    ) -> MarketImpactEstimate:
        """
        计算市场冲击成本: Impact = gamma * sigma * sqrt(OrderNotional / ADV)
        """
        adv = max(1_000_000.0, float(adv_notional))
        part_rate = min(1.0, notional / adv)
        vol = max(0.005, float(daily_volatility))

        # 平方根市场冲击定律
        slippage_pct = self.gamma * vol * math.sqrt(part_rate)
        impact_cost = notional * slippage_pct

        # 研判拆单策略
        if notional < 50_000.0:
            rec_algo = SlicerAlgorithm.DIRECT
            rec_slices = 1
        elif notional < 500_000.0:
            rec_algo = SlicerAlgorithm.ICEBERG
            rec_slices = max(3, int(math.ceil(notional / 50_000.0)))
        else:
            rec_algo = SlicerAlgorithm.TWAP
            rec_slices = max(5, min(20, int(math.ceil(notional / 80_000.0))))

        return MarketImpactEstimate(
            symbol=symbol.upper(),
            order_notional=round(notional, 2),
            adv_notional=round(adv, 2),
            participation_rate=round(part_rate, 4),
            estimated_slippage_pct=round(slippage_pct, 5),
            expected_impact_cost_yuan=round(impact_cost, 2),
            recommended_slices=rec_slices,
            recommended_algo=rec_algo
        )


class TWAPOrderSlicer:
    """时间加权平均价格 (TWAP) 拆单执行器"""

    def __init__(self, impact_model: Optional[MarketImpactModel] = None) -> None:
        self.impact_model = impact_model or MarketImpactModel()

    def slice_order(
        self,
        symbol: str,
        is_buy: bool,
        total_quantity: float,
        base_price: float,
        time_window_minutes: int = 20,
        min_slice_qty: float = 1.0
    ) -> List[ChildOrderSlice]:
        """
        将大额母单按时间窗口平均切分为 K 笔随机抖动子单
        """
        total_qty = float(total_quantity)
        px = float(base_price)
        notional = total_qty * px

        impact = self.impact_model.estimate_impact(symbol, notional)
        k_slices = max(1, impact.recommended_slices)
        window_sec = max(60, time_window_minutes * 60)

        # 保证每单最小手数
        single_qty = math.floor(total_qty / k_slices)
        if single_qty < min_slice_qty:
            single_qty = min_slice_qty
            k_slices = max(1, int(math.floor(total_qty / single_qty)))

        slices: List[ChildOrderSlice] = []
        rem_qty = total_qty
        interval = window_sec / max(1, k_slices)

        for i in range(k_slices):
            is_last = (i == k_slices - 1)
            cur_qty = rem_qty if is_last else single_qty
            rem_qty -= cur_qty
            delay = round(i * interval, 1)

            # 防反向抬价：买入限价单浮动上偏 0.05% 保证成交，不超出 0.1% 滑点上限
            limit_px = round(px * (1.0005 if is_buy else 0.9995), 2)
            slices.append(ChildOrderSlice(
                slice_index=i + 1,
                total_slices=k_slices,
                quantity=cur_qty,
                price_limit=limit_px,
                delay_seconds=delay,
                is_visible=True,
                description=f"TWAP 子单 {i+1}/{k_slices}: 延时 {delay}s 挂入 {cur_qty}手 @ ¥{limit_px:.2f}"
            ))
            if rem_qty <= 0:
                break

        return slices


class IcebergOrderSlicer:
    """冰山委托隐藏挂单执行器 (仅显露 10%~20% 盘口深度)"""

    def __init__(self, visible_ratio: float = 0.15) -> None:
        self.visible_ratio = float(visible_ratio)

    def slice_order(
        self,
        symbol: str,
        is_buy: bool,
        total_quantity: float,
        price: float
    ) -> List[ChildOrderSlice]:
        """
        拆分为显式可视子单与隐藏暗池子单
        """
        total_qty = float(total_quantity)
        px = float(price)
        visible_qty = max(1.0, math.floor(total_qty * self.visible_ratio))
        hidden_qty = total_qty - visible_qty

        k_slices = max(2, int(math.ceil(total_qty / visible_qty)))
        slices: List[ChildOrderSlice] = []

        # 第一笔首发显式盘口
        slices.append(ChildOrderSlice(
            slice_index=1,
            total_slices=k_slices,
            quantity=visible_qty,
            price_limit=px,
            delay_seconds=0.0,
            is_visible=True,
            description=f"冰山盘口显式单 1/{k_slices}: 露头 {visible_qty} 股/手 @ ¥{px:.2f}"
        ))

        # 后续暗池子单
        rem = hidden_qty
        idx = 2
        while rem > 0:
            c_qty = min(rem, visible_qty)
            rem -= c_qty
            slices.append(ChildOrderSlice(
                slice_index=idx,
                total_slices=k_slices,
                quantity=c_qty,
                price_limit=px,
                delay_seconds=round((idx - 1) * 30.0, 1),
                is_visible=False,
                description=f"冰山暗池隐藏单 {idx}/{k_slices}: 伺机补单 {c_qty} 股/手"
            ))
            idx += 1

        return slices
