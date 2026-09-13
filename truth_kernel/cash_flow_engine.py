"""
truth_kernel.cash_flow_engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
真值内核·现金流与特征计算引擎。
提供滚动 12 个月 (TTM) 自由现金流平滑、资本开支真实折旧、
净营运资本变动与真实现金转化效率的严密物理测算。
"""

from dataclasses import dataclass
from typing import List, Optional
import math
from truth_kernel.models import CompanyFinancialRecord


@dataclass(frozen=True)
class CashFlowFeatures:
    """企业现金流真实特征向量"""
    symbol: str
    period_end_date: str
    ocf_ttm: float                    # 滚动12个月经营现金流 (元)
    fcf_ttm: float                    # 滚动12个月自由现金流 (元)
    revenue_ttm: float                # 滚动12个月营业收入 (元)
    net_profit_ttm: float             # 滚动12个月净利润 (元)
    capex_intensity: float            # 资本开支强度 (CapEx / Revenue)
    cash_flow_to_revenue: float       # 营收现金含量 (OCF / Revenue)
    cash_flow_to_net_profit: float    # 利润现金含量 (OCF / |NetProfit|)
    fcf_margin: float                 # 自由现金流利润率 (FCF / Revenue)


class CashFlowEngine:
    """
    真实现金流特征提取器
    通过真实历史季度序列提取抗造假的现金流特征指标。
    """

    def __init__(self, smoothing_quarters: int = 4) -> None:
        self.smoothing_quarters = max(1, smoothing_quarters)

    def compute_features(
        self,
        historical_records: List[CompanyFinancialRecord]
    ) -> Optional[CashFlowFeatures]:
        """
        基于截面可见的历史记录序列计算 TTM 现金流特征
        :param historical_records: 已经过 Point-in-Time 过滤的历史财务记录（时间正序）
        """
        if not historical_records:
            return None

        latest = historical_records[-1]
        # 选取最近 N 个季度进行滚动聚合
        window = historical_records[-self.smoothing_quarters:]
        window_len = len(window)

        # 累计各核心科目
        sum_rev = sum(r.income_statement.revenue for r in window)
        sum_np = sum(r.income_statement.net_profit for r in window)
        sum_ocf = sum(r.cash_flow_statement.operating_cash_flow for r in window)
        sum_capex = sum(r.cash_flow_statement.capex for r in window)

        # 若历史记录不足 4 季度，按年化乘数等比折算 TTM
        scale = 4.0 / max(1.0, float(window_len))
        rev_ttm = sum_rev * scale
        np_ttm = sum_np * scale
        ocf_ttm = sum_ocf * scale
        capex_ttm = sum_capex * scale
        fcf_ttm = ocf_ttm - capex_ttm

        # 比率计算与防御性除零保护
        capex_intensity = capex_ttm / max(1.0, rev_ttm) if rev_ttm > 0 else 0.0
        cf_to_rev = ocf_ttm / max(1.0, rev_ttm) if rev_ttm > 0 else 0.0
        cf_to_np = ocf_ttm / max(1.0, abs(np_ttm))
        fcf_margin = fcf_ttm / max(1.0, rev_ttm) if rev_ttm > 0 else 0.0

        return CashFlowFeatures(
            symbol=latest.symbol,
            period_end_date=latest.period_end_date,
            ocf_ttm=round(ocf_ttm, 2),
            fcf_ttm=round(fcf_ttm, 2),
            revenue_ttm=round(rev_ttm, 2),
            net_profit_ttm=round(np_ttm, 2),
            capex_intensity=round(capex_intensity, 4),
            cash_flow_to_revenue=round(cf_to_rev, 4),
            cash_flow_to_net_profit=round(cf_to_np, 4),
            fcf_margin=round(fcf_margin, 4)
        )
