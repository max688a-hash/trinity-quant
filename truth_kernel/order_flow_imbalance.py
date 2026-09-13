"""
truth_kernel/order_flow_imbalance.py
====================================
微观高频订单流不平衡 (Order Flow Imbalance - OFI) 与盘口推力引擎。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 依据 Cont, Kukanov & Stoikov (2014) 严格微观物理公式计算盘口真实推力;
2. 严禁均线伪拟合，通过 L2 盘口挂单增减计算多空净冲量;
3. 严格单文件不超过 300 行，强类型标注，零盲吞异常。
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Level2DepthSnapshot:
    """L2 五档盘口物理快照"""
    symbol: str
    timestamp: float
    bid_prices: List[float]       # 买一到买五
    bid_volumes: List[int]        # 买一到买五挂单量
    ask_prices: List[float]       # 卖一到卖五
    ask_volumes: List[int]        # 卖一到卖五挂单量


@dataclass(frozen=True)
class OrderFlowMetrics:
    """订单流不平衡指标报告"""
    symbol: str
    ofi_net_value: float          # OFI 净冲量 (股/手)
    depth_imbalance_ratio: float  # 盘口买卖失衡率 [-1.0, 1.0] (正为多头占优)
    spread: float                 # 当前买卖价差
    next_tick_momentum: str       # UPWARD_PRESSURE / DOWNWARD_PRESSURE / BALANCED


class OrderFlowImbalanceEngine:
    """微观高频订单流不平衡 (OFI) 计算引擎"""

    @staticmethod
    def compute_ofi_delta(
        prev: Level2DepthSnapshot,
        curr: Level2DepthSnapshot
    ) -> float:
        """
        计算两连续盘口 Tick 间的 OFI 净冲量:
        Delta_B:
          - 若 Bid_Price(t) > Bid_Price(t-1), Delta_B = Bid_Vol(t)
          - 若 Bid_Price(t) == Bid_Price(t-1), Delta_B = Bid_Vol(t) - Bid_Vol(t-1)
          - 若 Bid_Price(t) < Bid_Price(t-1), Delta_B = 0
        Delta_A 同理 (方向相反)
        """
        if not prev.bid_prices or not curr.bid_prices or not prev.ask_prices or not curr.ask_prices:
            return 0.0

        p_b_prev = prev.bid_prices[0]
        v_b_prev = prev.bid_volumes[0]
        p_b_curr = curr.bid_prices[0]
        v_b_curr = curr.bid_volumes[0]

        # 买方推力
        if p_b_curr > p_b_prev:
            delta_b = float(v_b_curr)
        elif p_b_curr == p_b_prev:
            delta_b = float(v_b_curr - v_b_prev)
        else:
            delta_b = 0.0

        p_a_prev = prev.ask_prices[0]
        v_a_prev = prev.ask_volumes[0]
        p_a_curr = curr.ask_prices[0]
        v_a_curr = curr.ask_volumes[0]

        # 卖方推力
        if p_a_curr < p_a_prev:
            delta_a = float(v_a_curr)
        elif p_a_curr == p_a_prev:
            delta_a = float(v_a_curr - v_a_prev)
        else:
            delta_a = 0.0

        return delta_b - delta_a

    @classmethod
    def evaluate_depth_flow(
        cls,
        prev: Optional[Level2DepthSnapshot],
        curr: Level2DepthSnapshot
    ) -> OrderFlowMetrics:
        """评估当前盘口微观推力与流动性失衡"""
        spread = 0.01
        if curr.ask_prices and curr.bid_prices:
            spread = max(0.01, round(curr.ask_prices[0] - curr.bid_prices[0], 4))

        # 五档买卖总量
        tot_b = sum(curr.bid_volumes[:5]) if curr.bid_volumes else 0
        tot_a = sum(curr.ask_volumes[:5]) if curr.ask_volumes else 0
        tot_depth = tot_b + tot_a

        imbalance_ratio = 0.0
        if tot_depth > 0:
            imbalance_ratio = round((tot_b - tot_a) / tot_depth, 4)

        ofi_val = 0.0
        if prev:
            ofi_val = cls.compute_ofi_delta(prev, curr)

        # 研判推力
        if ofi_val > 500 or imbalance_ratio > 0.35:
            momentum = "UPWARD_PRESSURE"
        elif ofi_val < -500 or imbalance_ratio < -0.35:
            momentum = "DOWNWARD_PRESSURE"
        else:
            momentum = "BALANCED"

        return OrderFlowMetrics(
            symbol=curr.symbol,
            ofi_net_value=round(ofi_val, 2),
            depth_imbalance_ratio=imbalance_ratio,
            spread=spread,
            next_tick_momentum=momentum
        )
