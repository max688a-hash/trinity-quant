"""
entropy_execution/trade_statistics.py
=====================================
滚动实证交易统计器：把已平仓交易的真实收益率序列转换为凯利输入。

    p  = 盈利笔数 / 总笔数                        （后验胜率）
    b  = 平均盈利幅度 / 平均亏损幅度              （盈亏比）
    CVaR_α = -E[ r | r <= VaR_α ]                 （α 尾部条件在险价值，收益率口径）

样本不足 (n < min_samples) 时 has_sufficient_evidence=False，调用方必须走显式冷启动仓位，
严禁用写死的 0.65 / 2.0 / 0.08 冒充“实证参数”。
"""

import math
from collections import deque
from dataclasses import dataclass
from typing import Deque, Iterable, List, Optional


@dataclass(frozen=True)
class KellyInputs:
    """凯利分配器实证输入"""
    sample_size: int
    win_rate: float
    payoff_ratio: float
    cvar_alpha: float
    has_sufficient_evidence: bool


class RollingTradeStatistics:
    """滚动窗口交易收益统计（仅接受已实现、扣除摩擦后的单笔收益率）"""

    def __init__(self, window: int = 60, min_samples: int = 20, cvar_confidence: float = 0.95) -> None:
        if window <= 0 or min_samples <= 0 or min_samples > window:
            raise ValueError("window/min_samples 非法")
        if not 0.5 < cvar_confidence < 1.0:
            raise ValueError("cvar_confidence 必须在 (0.5, 1.0)")
        self.window = window
        self.min_samples = min_samples
        self.cvar_confidence = cvar_confidence
        self._returns: Deque[float] = deque(maxlen=window)

    def record_closed_trade(self, net_return_pct: float) -> None:
        """记录一笔已平仓交易的净收益率（含摩擦）"""
        if math.isnan(net_return_pct) or math.isinf(net_return_pct):
            return
        self._returns.append(float(net_return_pct))

    def extend(self, net_returns: Iterable[float]) -> None:
        for r in net_returns:
            self.record_closed_trade(r)

    @property
    def sample_size(self) -> int:
        return len(self._returns)

    def compute(self) -> KellyInputs:
        """从滚动窗口计算 p / b / CVaR；不足样本时输出零优势（edge<=0）"""
        rets: List[float] = list(self._returns)
        n = len(rets)
        if n == 0:
            return KellyInputs(0, 0.0, 0.0, 1.0, False)
        wins = [r for r in rets if r > 0]
        losses = [-r for r in rets if r <= 0]
        win_rate = len(wins) / n
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        if avg_loss <= 0:
            payoff = 0.0 if not wins else 10.0
        else:
            payoff = avg_win / avg_loss
        cvar = self._cvar(rets)
        return KellyInputs(
            sample_size=n,
            win_rate=round(win_rate, 4),
            payoff_ratio=round(payoff, 4),
            cvar_alpha=round(cvar, 4),
            has_sufficient_evidence=n >= self.min_samples,
        )

    def _cvar(self, rets: List[float]) -> float:
        srt = sorted(rets)
        tail_n = max(1, int(math.floor(len(srt) * (1.0 - self.cvar_confidence))))
        tail = srt[:tail_n]
        mean_tail = sum(tail) / len(tail)
        return max(0.0, min(1.0, -mean_tail))


def kelly_inputs_from_returns(returns: Iterable[float], min_samples: int = 20) -> KellyInputs:
    """一次性从收益率序列计算凯利输入（回测滚动窗口用）"""
    rets = [r for r in returns if not (math.isnan(r) or math.isinf(r))]
    window = max(min_samples, len(rets), 1)
    stats = RollingTradeStatistics(window=window, min_samples=min_samples)
    stats.extend(rets)
    return stats.compute()


def resolve_optional_market_cap(price: float, shares_outstanding: Optional[float]) -> Optional[float]:
    """市值 = 价格 × 总股本；缺股本时返回 None，严禁用常量顶替"""
    if shares_outstanding is None or shares_outstanding <= 0 or price <= 0:
        return None
    if math.isnan(shares_outstanding) or math.isinf(shares_outstanding):
        return None
    return price * shares_outstanding
