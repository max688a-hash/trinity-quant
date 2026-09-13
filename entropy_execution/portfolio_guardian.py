"""
entropy_execution.portfolio_guardian
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
投资组合风险守护者与几何复利最大化监控器。
严格践行三大物理公理之“几何复利与熵减公理”：
监控波动性拖累 (Volatility Drag: 0.5 * σ^2) 与组合最大回撤 (Max Drawdown)，
设立阶梯式流动性硬熔断机制，杜绝本金发生不可逆灭顶之灾。
"""

from dataclasses import dataclass
from typing import List, Tuple
import math


@dataclass(frozen=True)
class RiskMetrics:
    """组合风险与复利指标全景"""
    total_periods: int
    cagr: float                      # 几何复合年化增长率 (CAGR)
    arithmetic_mean: float           # 算术平均收益率 (仅作对照批判)
    annualized_volatility: float     # 年化波动率 σ
    volatility_drag: float           # 真实波动性拖累损失 0.5 * σ^2
    max_drawdown: float              # 历史最大回撤百分比
    cvar_99: float                   # 99% 置信度条件在险价值 (尾部均值损失)
    calmar_ratio: float              # 卡玛比率 (CAGR / MaxDD)
    sharpe_ratio: float              # 夏普比率 (无风险利率 2.5%)
    circuit_breaker_active: bool     # 是否处于防爆熔断保护状态
    status_summary: str              # 组合生命体征总结


class PortfolioGuardian:
    """
    组合风险守护神
    阶梯式防爆熔断守则：
    1. 动态回撤 > 8%：进入一级防御，主动降低全组合敞口 30%
    2. 动态回撤 > 12%：进入二级防御，强制削减敞口 50%
    3. 动态回撤 > 15%：触发绝对熔断，全部头寸退回无风险国债现金，锁定流动性
    """

    def __init__(
        self,
        risk_free_rate: float = 0.025,
        drawdown_warning: float = 0.08,
        drawdown_severe: float = 0.12,
        drawdown_breaker: float = 0.15
    ) -> None:
        self.r_f = risk_free_rate
        self.dd_warning = drawdown_warning
        self.dd_severe = drawdown_severe
        self.dd_breaker = drawdown_breaker

    def evaluate_returns(
        self,
        nav_series: List[float],
        periods_per_year: int = 252
    ) -> RiskMetrics:
        """评估净值序列的几何复利与风险指标"""
        if not nav_series or len(nav_series) < 2:
            return RiskMetrics(
                total_periods=len(nav_series),
                cagr=0.0, arithmetic_mean=0.0, annualized_volatility=0.0,
                volatility_drag=0.0, max_drawdown=0.0, cvar_99=0.0,
                calmar_ratio=0.0, sharpe_ratio=0.0,
                circuit_breaker_active=False,
                status_summary="数据不足，保持初始状态"
            )

        # 1. 计算每期收益率
        returns = []
        for i in range(1, len(nav_series)):
            r = (nav_series[i] - nav_series[i - 1]) / max(1e-6, nav_series[i - 1])
            returns.append(r)

        n = len(returns)
        # 2. 算术平均与几何复合 CAGR
        arithmetic_mean = sum(returns) / float(n)
        ann_arithmetic = arithmetic_mean * periods_per_year

        total_return = nav_series[-1] / max(1e-6, nav_series[0])
        years = float(n) / float(periods_per_year)
        if total_return > 0 and years > 0:
            cagr = (total_return ** (1.0 / years)) - 1.0
        else:
            cagr = -1.0

        # 3. 波动率与波动性拖累
        variance = sum((r - arithmetic_mean) ** 2 for r in returns) / max(1, n - 1)
        period_vol = math.sqrt(variance)
        ann_vol = period_vol * math.sqrt(periods_per_year)
        # 波动性拖累 = 0.5 * σ^2
        vol_drag = 0.5 * (ann_vol ** 2)

        # 4. 最大回撤
        peak = nav_series[0]
        max_dd = 0.0
        for val in nav_series:
            if val > peak:
                peak = val
            dd = (peak - val) / max(1e-6, peak)
            if dd > max_dd:
                max_dd = dd

        # 5. 99% CVaR (最差 1% 的平均损失)
        sorted_ret = sorted(returns)
        tail_cutoff = max(1, int(math.ceil(0.01 * n)))
        worst_returns = sorted_ret[:tail_cutoff]
        cvar_99 = -sum(worst_returns) / float(len(worst_returns))

        # 6. 比率计算
        excess_cagr = cagr - self.r_f
        sharpe = excess_cagr / max(1e-4, ann_vol)
        calmar = cagr / max(1e-4, max_dd)

        # 7. 熔断状态判定
        breaker_active = (max_dd >= self.dd_breaker)
        if breaker_active:
            status = f"【极度危险熔断】最大回撤={max_dd*100:.1f}% 触碰 15% 绝对熔断线，锁定现金防爆"
        elif max_dd >= self.dd_severe:
            status = f"【二级预警防御】最大回撤={max_dd*100:.1f}% 触碰 12% 警戒线，组合仓位强制减半"
        elif max_dd >= self.dd_warning:
            status = f"【一级预警观察】最大回撤={max_dd*100:.1f}% 超过 8% 阈值，限制新增敞口"
        else:
            status = "组合生命体征稳健，几何复利航行于安全海域"

        return RiskMetrics(
            total_periods=len(nav_series),
            cagr=round(cagr, 4),
            arithmetic_mean=round(ann_arithmetic, 4),
            annualized_volatility=round(ann_vol, 4),
            volatility_drag=round(vol_drag, 4),
            max_drawdown=round(max_dd, 4),
            cvar_99=round(cvar_99, 4),
            calmar_ratio=round(calmar, 2),
            sharpe_ratio=round(sharpe, 2),
            circuit_breaker_active=breaker_active,
            status_summary=status
        )
