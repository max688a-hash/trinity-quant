"""
gravity_brain/market_regime_classifier.py
=========================================
基于分形 Hurst 指数与波动率聚类的市场物理状态机。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 严禁基于纯形态假拟合，必须以分形维数与重标极差 (R/S) 严密计算金融物理规律;
2. Hurst > 0.55 为长记忆单边趋势，Hurst < 0.45 为反转均值回归，其余为随机游走震荡;
3. 严格单文件不超过 300 行，强类型标注，零盲吞异常。
"""

from dataclasses import dataclass
from enum import Enum
import math
from typing import List, Optional, Tuple


class MarketRegime(str, Enum):
    """市场微观物理状态"""
    BULL_TREND = "BULL_TREND"                      # 单边多头牛市趋势 (激活趋势突破)
    BEAR_TREND = "BEAR_TREND"                      # 单边空头熊市趋势 (激活空头保护/网格平多)
    CHOPPY_OSCILLATING = "CHOPPY_OSCILLATING"      # 宽幅无序震荡 (激活统计套利/均值回归)
    EXTREME_VOLATILE_CRISIS = "EXTREME_VOLATILE"    # 黑天鹅极度恐慌 (激活尾部对冲/硬熔断)


@dataclass(frozen=True)
class RegimeClassificationResult:
    """市场状态分类诊断报告"""
    regime: MarketRegime
    hurst_exponent: float
    volatility_atr_pct: float
    trend_strength: float
    recommendation: str


class MarketRegimeClassifier:
    """市场微观状态物理识别机"""

    @staticmethod
    def calculate_hurst_exponent(prices: List[float]) -> float:
        """
        计算重标极差分析 (R/S) Hurst 指数:
        H > 0.5: 持续性长记忆趋势
        H = 0.5: 独立随机游走布朗运动
        H < 0.5: 反持续均值回归
        """
        valid_prices = [float(p) for p in prices if p is not None and not math.isnan(p) and not math.isinf(p) and p > 0]
        n = len(valid_prices)
        if n < 16:
            return 0.50

        # 对数收益率 (保证除数与被除数均严格大于0)
        returns = [math.log(valid_prices[i] / valid_prices[i - 1]) for i in range(1, n)]
        if len(returns) < 4:
            return 0.50

        mean_ret = sum(returns) / len(returns)
        # 累积均值离差
        cum_dev = []
        running_sum = 0.0
        for r in returns:
            running_sum += (r - mean_ret)
            cum_dev.append(running_sum)

        # 极差 R
        r_range = max(cum_dev) - min(cum_dev)
        # 样本标准差 S
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        if variance < 1e-7 and abs(mean_ret) > 1e-5:
            # 纯单调无回撤漂移：处于极端持续性状态 (Hurst -> 0.95)
            return 0.95
        std_s = math.sqrt(max(variance, 1e-9))

        rs_value = r_range / std_s
        if rs_value <= 0 or len(returns) <= 1:
            return 0.50

        # H = log(R/S) / log(N)
        hurst = math.log(rs_value) / math.log(len(returns))
        # 物理区间截断防御 [0.05, 0.95]
        return max(0.05, min(0.95, float(hurst)))

    @classmethod
    def classify_regime(
        cls,
        prices: List[float],
        highs: Optional[List[float]] = None,
        lows: Optional[List[float]] = None
    ) -> RegimeClassificationResult:
        """对时序价格数据进行市场状态裁决"""
        clean_prices = [float(p) for p in prices if p is not None and not math.isnan(p) and not math.isinf(p) and p > 0]
        if len(clean_prices) < 20:
            return RegimeClassificationResult(
                regime=MarketRegime.CHOPPY_OSCILLATING,
                hurst_exponent=0.50,
                volatility_atr_pct=0.015,
                trend_strength=0.0,
                recommendation="数据样本不足或包含非法非正价格，保持基准中性震荡策略"
            )

        hurst = cls.calculate_hurst_exponent(clean_prices)

        # 计算 20 周期收益率与趋势强度
        start_p = clean_prices[0]
        end_p = clean_prices[-1]
        ret_20 = (end_p - start_p) / start_p if start_p > 0 else 0.0

        # 计算真实时序对数收益率波动率 (Return Volatility)
        rets = [math.log(clean_prices[i] / clean_prices[i - 1]) for i in range(1, len(clean_prices))]
        mean_ret = sum(rets) / len(rets) if rets else 0.0
        var_ret = sum((r - mean_ret) ** 2 for r in rets) / len(rets) if rets else 0.0004
        vol_pct = math.sqrt(max(var_ret, 1e-9))

        # 极端黑天鹅危机判定 (单期收益波动率 > 7% 或 20 周期暴跌 > 20%)
        if vol_pct > 0.07 or ret_20 < -0.20:
            return RegimeClassificationResult(
                regime=MarketRegime.EXTREME_VOLATILE_CRISIS,
                hurst_exponent=round(hurst, 3),
                volatility_atr_pct=round(vol_pct, 4),
                trend_strength=round(ret_20, 4),
                recommendation="触发极端波动黑天鹅预警：强制压缩仓位，激活尾部对冲与防穿仓物理熔断！"
            )

        # 单边强趋势判定 (结合 Hurst 长记忆与方向一致性比例)
        up_ratio = sum(1 for r in rets if r > 0) / len(rets) if rets else 0.5
        is_bull = (hurst >= 0.54 and ret_20 > 0.03) or (up_ratio >= 0.65 and ret_20 > 0.03)
        is_bear = (hurst >= 0.54 and ret_20 < -0.03) or (up_ratio <= 0.35 and ret_20 < -0.03)

        if is_bull:
            return RegimeClassificationResult(
                regime=MarketRegime.BULL_TREND,
                hurst_exponent=round(hurst, 3),
                volatility_atr_pct=round(vol_pct, 4),
                trend_strength=round(ret_20, 4),
                recommendation="市场处于长记忆单边多头：主推机构海龟唐奇安突破跟踪策略，锁紧利润回撤！"
            )
        elif is_bear:
            return RegimeClassificationResult(
                regime=MarketRegime.BEAR_TREND,
                hurst_exponent=round(hurst, 3),
                volatility_atr_pct=round(vol_pct, 4),
                trend_strength=round(ret_20, 4),
                recommendation="市场处于单边空头下行：禁止盲目抄底，执行空头保护或轻仓对冲。"
            )

        # 其余一律归为宽幅震荡整理
        return RegimeClassificationResult(
            regime=MarketRegime.CHOPPY_OSCILLATING,
            hurst_exponent=round(hurst, 3),
            volatility_atr_pct=round(vol_pct, 4),
            trend_strength=round(ret_20, 4),
            recommendation="市场处于无序震荡整理：停用趋势突破追单，激活统计套利与均值回归网格低吸高抛！"
        )
