"""
gravity_brain/commodity_basis_truth.py
======================================
TRINITY QUANT 大宗商品基差引力与期限结构模型。

根据持有成本物理模型（Cost of Carry）：
F(t, T) = S(t) * exp((r + c - y)*(T - t))
测算现货基差（Basis）、升贴水结构（Contango vs Backwardation）
以及展期收益率（Roll Yield），识别期货多头的展期流血陷阱。
"""

import math
from dataclasses import dataclass
from enum import Enum


class TermStructureRegime(str, Enum):
    """期限结构形态分类"""
    BACKWARDATION = "BACKWARDATION"  # 现货升水/近高远低 (多头展期红利)
    CONTANGO = "CONTANGO"            # 现货贴水/近低远高 (多头展期流血)
    FLAT = "FLAT"                    # 期限结构平坦


@dataclass(frozen=True)
class BasisTruthMetrics:
    """商品基差与期限结构度量"""
    symbol: str
    spot_price: float
    near_price: float
    far_price: float
    days_between_contracts: int
    basis: float
    basis_rate: float
    annualized_roll_yield: float
    structure: TermStructureRegime
    roll_drag_penalty: float

    @property
    def is_favorable_for_long(self) -> bool:
        """多头是否有正向展期引力保护"""
        return self.structure == TermStructureRegime.BACKWARDATION and self.annualized_roll_yield > 0.02


class CommodityBasisEngine:
    """商品基差与展期真值计算引擎"""

    def __init__(self, high_contango_drag_threshold: float = 0.15) -> None:
        if high_contango_drag_threshold <= 0:
            raise ValueError("Contango惩罚阈值必须大于0")
        self._drag_threshold = high_contango_drag_threshold

    def compute(
        self,
        symbol: str,
        spot_price: float,
        near_price: float,
        far_price: float,
        days_between: int
    ) -> BasisTruthMetrics:
        """
        计算基差与展期收益率
        
        :param symbol: 商品代码 (如 SA, C, RB)
        :param spot_price: 现货真实价格 (物理成交价)
        :param near_price: 近月/主力期货合约价格
        :param far_price: 远月/次主力期货合约价格
        :param days_between: 远近合约交割日差值 (天数)
        :return: BasisTruthMetrics
        """
        if spot_price <= 0 or near_price <= 0 or far_price <= 0:
            raise ValueError("现货与期货价格必须严格大于0")
        if days_between <= 0:
            raise ValueError(f"合约跨期天数必须大于0: {days_between}")

        # 现货基差 Basis = Spot - Future_near
        basis = spot_price - near_price
        basis_rate = basis / spot_price

        # 年化展期收益率 Roll Yield = (P_near - P_far) / P_near * (365 / days)
        # 近月高于远月时 (Backwardation), 换月买入更便宜的远月, 展期收益为正
        # 近月低于远月时 (Contango), 换月买入更贵的远月, 展期收益为负 (流血)
        raw_roll = (near_price - far_price) / near_price
        ann_roll_yield = raw_roll * (365.0 / float(days_between))

        if math.isinf(ann_roll_yield) or math.isnan(ann_roll_yield):
            ann_roll_yield = 0.0

        if ann_roll_yield > 0.01:
            structure = TermStructureRegime.BACKWARDATION
            roll_drag_penalty = 0.0
        elif ann_roll_yield < -0.01:
            structure = TermStructureRegime.CONTANGO
            # 若 Contango 年化损耗超过阈值，计算对应的多头价值惩罚因子 [0, 1]
            abs_drag = abs(ann_roll_yield)
            if abs_drag >= self._drag_threshold:
                roll_drag_penalty = min(1.0, (abs_drag - self._drag_threshold) / self._drag_threshold + 0.20)
            else:
                roll_drag_penalty = 0.05
        else:
            structure = TermStructureRegime.FLAT
            roll_drag_penalty = 0.0

        return BasisTruthMetrics(
            symbol=symbol.upper(),
            spot_price=spot_price,
            near_price=near_price,
            far_price=far_price,
            days_between_contracts=days_between,
            basis=basis,
            basis_rate=basis_rate,
            annualized_roll_yield=ann_roll_yield,
            structure=structure,
            roll_drag_penalty=roll_drag_penalty
        )
