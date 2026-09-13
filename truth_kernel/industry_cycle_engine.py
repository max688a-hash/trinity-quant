"""
truth_kernel/industry_cycle_engine.py
=====================================
TRINITY QUANT 商业去季节性、宏观大盘 ERP 与产业库存周期引擎。

解决商业本质与宏观传导致命暗礁：
1. 彻底解决“棉被企业夏天亏、冬天赚”的季节性假象 (YoY 同比对齐与去季节性分解);
2. 宏观大盘股债性价比 (ERP) 评估市场整体安全垫;
3. 产业微观库存周期四阶段识别，提前规避存货减值暴雷。
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class InventoryCyclePhase(str, Enum):
    """产业微观库存周期四阶段"""
    PASSIVE_DESTOCKING = "PASSIVE_DESTOCKING"  # 被动去库存 (需求爆发供不应求，主升浪)
    ACTIVE_RESTOCKING = "ACTIVE_RESTOCKING"    # 主动补库存 (扩产繁荣，景气高点)
    PASSIVE_RESTOCKING = "PASSIVE_RESTOCKING"  # 被动补库存 (滞销积压，存货爆雷前夕，坚决规避)
    ACTIVE_DESTOCKING = "ACTIVE_DESTOCKING"    # 主动去库存 (降价割肉清库存，行业寒冬出清)


class MacroERPRegime(str, Enum):
    """宏观大盘股债性价比形态"""
    EXTREME_CHEAP = "EXTREME_CHEAP"            # ERP极高，股票极度便宜 (大盘大底，全力做多)
    NEUTRAL = "NEUTRAL"                        # 股债平衡常态
    EXTREME_BUBBLE = "EXTREME_BUBBLE"          # 股市泡沫估值失真 (大盘大顶，强制收缩防守)


@dataclass(frozen=True)
class SeasonalityDeseasonalizedReport:
    """去季节性与商业主干分析结果"""
    symbol: str
    quarter_index: int                       # 季度序号 (1=春, 2=夏, 3=秋, 4=冬)
    raw_revenue: float
    deseasonalized_revenue: float
    raw_net_profit: float
    yoy_revenue_growth: float
    yoy_profit_growth: float
    is_counter_seasonal_breakthrough: bool   # 是否出现淡季逆势超预期突破


@dataclass(frozen=True)
class InventoryCycleMetrics:
    """企业库存周期状态度量"""
    symbol: str
    revenue_yoy: float
    inventory_yoy: float
    phase: InventoryCyclePhase
    is_toxic_inventory_buildup: bool         # 是否存在恶性存货积压减值风险


class IndustryCycleEngine:
    """商业本质与宏观产业周期计算器"""

    @staticmethod
    def evaluate_seasonality(
        symbol: str,
        current_quarter: int,
        current_rev: float,
        current_profit: float,
        prior_year_same_quarter_rev: float,
        prior_year_same_quarter_profit: float,
        quarterly_weights: Optional[List[float]] = None
    ) -> SeasonalityDeseasonalizedReport:
        """
        对具有强季节性的企业（如冬季被服、空调、制种、旅游）进行同比与去季节化消除
        """
        if current_quarter not in (1, 2, 3, 4):
            raise ValueError(f"季度必须为 1, 2, 3, 4 之一: {current_quarter}")
        if prior_year_same_quarter_rev <= 0:
            raise ValueError("去年同期营收必须大于0")

        # 默认权重或自定义季度权重 (如棉被企业权重 [0.15, 0.10, 0.25, 0.50])
        weights = quarterly_weights if quarterly_weights is not None else [0.25, 0.25, 0.25, 0.25]
        q_weight = weights[current_quarter - 1]
        
        # 归一化营收 = 当期营收 / (4 * 季度权重)
        deseason_rev = current_rev / (4.0 * max(q_weight, 0.05))

        # 严格执行同比 (YoY) 测算，杜绝夏冬环比误导
        rev_growth = (current_rev - prior_year_same_quarter_rev) / prior_year_same_quarter_rev
        
        denom_profit = abs(prior_year_same_quarter_profit) if abs(prior_year_same_quarter_profit) > 1e-4 else 1.0
        profit_growth = (current_profit - prior_year_same_quarter_profit) / denom_profit

        # 淡季逆势超预期突破判定 (例如夏天权重仅10%，但同比依然大幅增长)
        is_breakthrough = (q_weight <= 0.15) and (rev_growth > 0.20)

        return SeasonalityDeseasonalizedReport(
            symbol=symbol.upper(),
            quarter_index=current_quarter,
            raw_revenue=current_rev,
            deseasonalized_revenue=deseason_rev,
            raw_net_profit=current_profit,
            yoy_revenue_growth=rev_growth,
            yoy_profit_growth=profit_growth,
            is_counter_seasonal_breakthrough=is_breakthrough
        )

    @staticmethod
    def classify_inventory_cycle(
        symbol: str,
        revenue_yoy: float,
        inventory_yoy: float
    ) -> InventoryCycleMetrics:
        """
        根据营收同比 vs 存货同比判定库存周期
        """
        if revenue_yoy >= 0 and inventory_yoy < 0:
            phase = InventoryCyclePhase.PASSIVE_DESTOCKING
            is_toxic = False
        elif revenue_yoy >= 0 and inventory_yoy >= 0:
            phase = InventoryCyclePhase.ACTIVE_RESTOCKING
            is_toxic = False
        elif revenue_yoy < 0 and inventory_yoy >= 0:
            # 营收下滑而库存暴增：典型的滞销爆雷被动补库存
            phase = InventoryCyclePhase.PASSIVE_RESTOCKING
            is_toxic = True
        else:
            phase = InventoryCyclePhase.ACTIVE_DESTOCKING
            is_toxic = False

        return InventoryCycleMetrics(
            symbol=symbol.upper(),
            revenue_yoy=revenue_yoy,
            inventory_yoy=inventory_yoy,
            phase=phase,
            is_toxic_inventory_buildup=is_toxic
        )

    @staticmethod
    def calculate_macro_erp(
        index_pe: float,
        ten_year_treasury_rate: float
    ) -> tuple[float, MacroERPRegime]:
        """
        计算大盘宏观股债性价比 ERP = (1 / PE) - r_f
        """
        if index_pe <= 0:
            raise ValueError(f"大盘市盈率必须大于0: {index_pe}")
        
        earnings_yield = 1.0 / index_pe
        erp = earnings_yield - ten_year_treasury_rate

        if erp >= 0.055:
            regime = MacroERPRegime.EXTREME_CHEAP
        elif erp <= 0.015:
            regime = MacroERPRegime.EXTREME_BUBBLE
        else:
            regime = MacroERPRegime.NEUTRAL

        return erp, regime
