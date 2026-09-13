"""
entropy_execution.dynamic_kelly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
实现抗极端尾部风险的动态非对称凯利公式 (Dynamic Convex Kelly Allocation)。
数学核心：
f* = max(0, [(p*b - q)/b] * [1 / (1 + γ * CVaR_α)] * min(1.0, max(0, (V_G - P_t)/P_t)))
将下行在险价值 (CVaR) 惩罚因子与真值引力势能深度调制，杜绝高杠杆爆仓。
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass(frozen=True)
class KellyAllocationResult:
    """动态凯利仓位配比结果"""
    symbol: str
    target_weight: float             # 最优推荐目标仓位权重 (0.0 ~ 0.20)
    raw_kelly_fraction: float        # 未经风险惩罚的原始凯利分数
    cvar_penalty_multiplier: float   # 尾部风险抑制因子 1 / (1 + γ * CVaR)
    gravity_potential_scale: float   # 引力折价调节乘数 min(1.0, G_potential)
    is_vetoed: bool                  # 是否因一票否决而强制归零
    allocation_reason: str           # 仓位决策理由


class DynamicKellyAllocator:
    """
    动态防爆凯利仓位分配器
    严格执行组合与单标的风险硬约束：
    1. 单标的持仓硬上限 20%（防止单一黑天鹅冲击）
    2. 组合总仓位 <= 100%（绝对禁止任何借贷杠杆）
    3. 下行 CVaR 飙升时自动削减仓位，抑制波动性拖累 (Volatility Drag)
    """

    def __init__(
        self,
        cvar_penalty_gamma: float = 2.50,
        max_single_position: float = 0.20,
        min_win_rate_threshold: float = 0.50
    ) -> None:
        self.gamma = max(0.0, cvar_penalty_gamma)
        self.max_single_position = min(1.0, max(0.01, max_single_position))
        self.min_win_rate = min_win_rate_threshold

    def calculate_weight(
        self,
        symbol: str,
        win_rate: float,
        payoff_ratio: float,
        cvar_alpha: float,
        gravity_potential: Optional[float] = None,
        is_firewall_admitted: bool = True
    ) -> KellyAllocationResult:
        """
        计算单只标的的最优目标仓位权重
        :param win_rate: 预期胜率 p (0.0 ~ 1.0)
        :param payoff_ratio: 盈亏比 b = 预期收益 / 预期止损
        :param cvar_alpha: 置信度下的条件在险价值 CVaR (0.0 ~ 1.0)
        :param gravity_potential: 引力势能比率 (V_G - P) / P
        :param is_firewall_admitted: 是否通过排毒防火墙
        """
        # 0. 数学防爆防御：严防 NaN / Inf 毒化仓位计算
        if (
            math.isnan(win_rate) or math.isinf(win_rate) or
            math.isnan(payoff_ratio) or math.isinf(payoff_ratio) or
            math.isnan(cvar_alpha) or math.isinf(cvar_alpha) or
            (gravity_potential is not None and (math.isnan(gravity_potential) or math.isinf(gravity_potential)))
        ):
            return KellyAllocationResult(
                symbol=symbol,
                target_weight=0.0,
                raw_kelly_fraction=0.0,
                cvar_penalty_multiplier=0.0,
                gravity_potential_scale=0.0,
                is_vetoed=True,
                allocation_reason="输入指标包含 NaN 或 Inf 异常浮点值，触发数学安全熔断保护"
            )

        # 1. 一票否决硬约束：未通过排毒标的，仓位坚决归零
        if not is_firewall_admitted:
            return KellyAllocationResult(
                symbol=symbol,
                target_weight=0.0,
                raw_kelly_fraction=0.0,
                cvar_penalty_multiplier=0.0,
                gravity_potential_scale=0.0,
                is_vetoed=True,
                allocation_reason="未通过免疫排毒防火墙，执行一票否决清仓"
            )

        # 2. 经典凯利公式基础分数 f = (p * b - q) / b
        p = min(0.99, max(0.01, win_rate))
        b = max(0.01, payoff_ratio)
        q = 1.0 - p
        edge = (p * b) - q

        if edge <= 0:
            return KellyAllocationResult(
                symbol=symbol,
                target_weight=0.0,
                raw_kelly_fraction=0.0,
                cvar_penalty_multiplier=1.0,
                gravity_potential_scale=0.0,
                is_vetoed=False,
                allocation_reason=f"数学期望优势不足: edge={edge:.3f} <= 0"
            )

        raw_kelly = edge / b

        # 3. 极端下行风险 CVaR 惩罚因子 1 / (1 + γ * CVaR)
        safe_cvar = max(0.01, min(1.0, cvar_alpha))
        cvar_penalty = 1.0 / (1.0 + (self.gamma * safe_cvar))

        # 4. 真值引力势能调制因子
        if gravity_potential is not None:
            # 只有当市价低于真值 (G_potential > 0) 时才分配核心仓位
            # 若市价严重高估 (G_potential < 0)，势能乘数归零
            gp_scale = max(0.0, min(1.0, gravity_potential))
        else:
            gp_scale = 1.0  # 未提供时采用保守中性因子

        if gp_scale <= 0:
            return KellyAllocationResult(
                symbol=symbol,
                target_weight=0.0,
                raw_kelly_fraction=round(raw_kelly, 4),
                cvar_penalty_multiplier=round(cvar_penalty, 4),
                gravity_potential_scale=0.0,
                is_vetoed=False,
                allocation_reason="市价高于真值引力核心 (G_potential <= 0)，不具备安全边际"
            )

        # 5. 动态合成最优仓位
        target_f = raw_kelly * cvar_penalty * gp_scale

        # 6. 单标的硬性风控截断 (如不超过 20%)
        final_weight = min(self.max_single_position, max(0.0, target_f))

        return KellyAllocationResult(
            symbol=symbol,
            target_weight=round(final_weight, 4),
            raw_kelly_fraction=round(raw_kelly, 4),
            cvar_penalty_multiplier=round(cvar_penalty, 4),
            gravity_potential_scale=round(gp_scale, 4),
            is_vetoed=False,
            allocation_reason=f"通过排毒，引力势能={gp_scale:.2f}，CVaR抑制={cvar_penalty:.2f}"
        )
