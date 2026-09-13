"""
immune_system/crowding_monitor.py
=================================
TRINITY QUANT 因子拥挤度与危机相关性坍塌监测器。

解决组合物理与系统性踩踏暗礁：
1. 危机时刻所有资产相关性瞬间飙升向 1.0 的“虚假分散”陷阱;
2. 同质化量化策略因子拥挤度 (Crowded Trades) 与踩踏熔断。
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Sequence


class CrowdingRegime(str, Enum):
    """拥挤度预警等级"""
    HEALTHY_DIVERSE = "HEALTHY_DIVERSE"        # 策略分散度健康，无踩踏风险
    ELEVATED_CONCENTRATION = "ELEVATED_CONC"  # 拥挤度上升，施加适度减仓
    CRITICAL_SQUEEZE = "CRITICAL_SQUEEZE"      # 极度拥挤/相关性坍塌，触发紧急避险


@dataclass(frozen=True)
class CrowdingAuditReport:
    """拥挤度与系统性坍塌审计报告"""
    average_pairwise_correlation: float
    crowding_score: float                     # 0 ~ 100 分
    regime: CrowdingRegime
    suggested_leverage_multiplier: float      # 杠杆系数乘数 (0.3 ~ 1.0)
    warning_message: str


class CrowdingMonitor:
    """组合物理学与拥挤度防爆探测器"""

    def __init__(
        self,
        correlation_crisis_threshold: float = 0.75,
        crowding_danger_score: float = 80.0
    ) -> None:
        if correlation_crisis_threshold <= 0 or correlation_crisis_threshold > 1.0:
            raise ValueError("相关性危机阈值必须在 (0, 1.0] 之间")
        self._corr_threshold = correlation_crisis_threshold
        self._crowd_threshold = crowding_danger_score

    def evaluate_correlation_collapse(
        self,
        returns_matrix: Sequence[Sequence[float]]
    ) -> float:
        """
        计算资产收益率的两两平均相关系数 \bar{\rho}
        
        :param returns_matrix: N 个资产的近 K 期收益率列表 (N >= 2)
        :return: 平均相关系数 [-1.0, 1.0]
        """
        n_assets = len(returns_matrix)
        if n_assets < 2:
            return 0.0

        correlations: List[float] = []
        for i in range(n_assets):
            for j in range(i + 1, n_assets):
                r_i = returns_matrix[i]
                r_j = returns_matrix[j]
                corr = self._calc_pearson(r_i, r_j)
                correlations.append(corr)

        avg_corr = sum(correlations) / float(len(correlations)) if correlations else 0.0
        return avg_corr

    def audit_crowding(
        self,
        avg_correlation: float,
        factor_turnover_heat: float,
        retail_sentiment_skew: float
    ) -> CrowdingAuditReport:
        """
        综合审计拥挤度风险
        
        :param avg_correlation: 资产平均两两相关系数
        :param factor_turnover_heat: 换手热度指标 [0, 1]
        :param retail_sentiment_skew: 散户/同质资金情绪偏度 [0, 1]
        """
        # 拥挤度综合评分 (0~100)
        corr_norm = max(0.0, avg_correlation)
        score = (corr_norm * 40.0) + (factor_turnover_heat * 30.0) + (retail_sentiment_skew * 30.0)

        if avg_correlation >= self._corr_threshold or score >= self._crowd_threshold:
            regime = CrowdingRegime.CRITICAL_SQUEEZE
            multiplier = 0.35  # 紧急压缩杠杆
            msg = f"检测到资产相关性异常飙升至 {avg_correlation:.2f} 或拥挤度破表({score:.1f})，触发防踩踏避险！"
        elif score >= 60.0:
            regime = CrowdingRegime.ELEVATED_CONCENTRATION
            multiplier = 0.70
            msg = f"同质化资金换手过热 (评分 {score:.1f})，进入预警防御态。"
        else:
            regime = CrowdingRegime.HEALTHY_DIVERSE
            multiplier = 1.0
            msg = "组合分散度健康，未见踩踏迹象。"

        return CrowdingAuditReport(
            average_pairwise_correlation=avg_correlation,
            crowding_score=score,
            regime=regime,
            suggested_leverage_multiplier=multiplier,
            warning_message=msg
        )

    @staticmethod
    def _calc_pearson(x: Sequence[float], y: Sequence[float]) -> float:
        """计算皮尔逊相关系数"""
        n = min(len(x), len(y))
        if n < 3:
            return 0.0

        mean_x = sum(x[:n]) / float(n)
        mean_y = sum(y[:n]) / float(n)

        cov = sum((x[k] - mean_x) * (y[k] - mean_y) for k in range(n))
        var_x = sum((x[k] - mean_x) ** 2 for k in range(n))
        var_y = sum((y[k] - mean_y) ** 2 for k in range(n))

        denom = math.sqrt(var_x * var_y)
        if denom <= 1e-12:
            return 0.0
        return max(-1.0, min(1.0, cov / denom))
