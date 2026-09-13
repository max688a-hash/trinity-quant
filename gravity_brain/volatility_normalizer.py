"""
gravity_brain/volatility_normalizer.py
======================================
TRINITY QUANT 标的波动自适应归一化引擎。

基于金融物理第一性原理，消除绝对价格点数陷阱，
将玉米（~25点）、白银（百点级）、纯碱（几十点）及股票
映射到无量纲标准差坐标系与 ATR 百分比波动带。
"""

import math
from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class VolatilityMetrics:
    r"""
    无量纲波动度量指标
    
    数学推导：
    - atr: 平均真实波幅 TR_t = max(H-L, |H-C_prev|, |L-C_prev|)
    - atr_ratio: 相对波幅比例 ATR / P_t
    - rolling_mean: 滚动均价 \mu_t
    - rolling_std: 滚动标准差 \sigma_t
    - z_score: 偏离度分数 Z_t = (P_t - \mu_t) / \sigma_t
    - lower_band / upper_band: 常态内生波动边界 [\mu - k*\sigma, \mu + k*\sigma]
    """
    symbol: str
    current_price: float
    atr: float
    atr_ratio: float
    rolling_mean: float
    rolling_std: float
    z_score: float
    lower_band: float
    upper_band: float

    @property
    def is_within_normal_range(self) -> bool:
        r"""判断是否处于 \pm 2\sigma 常态阻尼振荡区间"""
        return abs(self.z_score) <= 2.0

    @property
    def is_extreme_deviation(self) -> bool:
        r"""判断是否突破 \pm 3\sigma 极端质变边界"""
        return abs(self.z_score) > 3.0


class VolatilityNormalizer:
    """标的自适应波动空间归一化计算器"""

    def __init__(self, window: int = 20, band_multiplier: float = 2.0) -> None:
        if window < 3:
            raise ValueError(f"滚动窗口必须大于等于3: {window}")
        if band_multiplier <= 0:
            raise ValueError(f"波动边界倍数必须大于0: {band_multiplier}")
        self._window = window
        self._band_multiplier = band_multiplier

    def compute(
        self,
        symbol: str,
        closes: Sequence[float],
        highs: Optional[Sequence[float]] = None,
        lows: Optional[Sequence[float]] = None
    ) -> VolatilityMetrics:
        """
        计算标的的动态波动空间与偏离度
        
        :param symbol: 标的代码
        :param closes: 收盘价序列 (按时序正向排列)
        :param highs: 最高价序列 (可选，若无则近似使用收盘价)
        :param lows: 最低价序列 (可选，若无则近似使用收盘价)
        :return: VolatilityMetrics
        """
        if not symbol:
            raise ValueError("标的代码不得为空")
        n = len(closes)
        if n < self._window:
            raise ValueError(f"价格序列长度 {n} 低于最小窗口 {self._window}")

        # 防御性数值检查
        for idx, p in enumerate(closes):
            if math.isnan(p) or math.isinf(p) or p <= 0:
                raise ValueError(f"收盘价在索引 {idx} 处非法: {p}")

        cur_price = closes[-1]
        recent_closes = list(closes[-self._window:])
        mean_p = sum(recent_closes) / float(self._window)
        
        # 样本标准差 (Bessel's correction)
        var_p = sum((x - mean_p) ** 2 for x in recent_closes) / float(self._window - 1)
        std_p = math.sqrt(max(var_p, 1e-12))

        # 计算真实波幅 True Range
        tr_list: list[float] = []
        for i in range(1, n):
            c_prev = closes[i - 1]
            c_curr = closes[i]
            h_curr = highs[i] if highs is not None else c_curr
            l_curr = lows[i] if lows is not None else c_curr
            
            if h_curr < l_curr:
                raise ValueError(f"最高价 {h_curr} 低于最低价 {l_curr} (索引 {i})")

            tr = max(h_curr - l_curr, abs(h_curr - c_prev), abs(l_curr - c_prev))
            tr_list.append(tr)

        # 取最近 window-1 个 TR 计算 ATR
        recent_tr = tr_list[-(self._window - 1):] if tr_list else [std_p]
        atr = sum(recent_tr) / float(len(recent_tr)) if recent_tr else std_p
        atr_ratio = atr / cur_price

        # Z-Score 无量纲偏离度
        z_score = (cur_price - mean_p) / std_p

        lower_b = mean_p - self._band_multiplier * std_p
        upper_b = mean_p + self._band_multiplier * std_p

        return VolatilityMetrics(
            symbol=symbol.upper(),
            current_price=cur_price,
            atr=atr,
            atr_ratio=atr_ratio,
            rolling_mean=mean_p,
            rolling_std=std_p,
            z_score=z_score,
            lower_band=lower_b,
            upper_band=upper_b
        )
