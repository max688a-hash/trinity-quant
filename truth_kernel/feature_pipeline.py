"""
truth_kernel.feature_pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
真值时点特征提取流水线。
将时空防穿透日历 (PITCalendar) 与现金流特征引擎集成，
支持为任意历史截面快速提取绝对无未来函数的企业造血特征矩阵。
"""

from typing import Dict, List, Optional
from truth_kernel.models import CompanyFinancialRecord
from truth_kernel.pit_calendar import PITCalendar
from truth_kernel.cash_flow_engine import CashFlowEngine, CashFlowFeatures


class TruthFeaturePipeline:
    """
    点时特征生成管线
    严格确保在 as_of_date 仅读取该时间截面已披露的财务数据。
    """

    def __init__(
        self,
        calendar: PITCalendar,
        cash_flow_engine: Optional[CashFlowEngine] = None
    ) -> None:
        self.calendar = calendar
        self.cf_engine = cash_flow_engine or CashFlowEngine()

    def extract_features(
        self,
        symbol: str,
        as_of_date: str,
        lookback_quarters: int = 4
    ) -> Optional[CashFlowFeatures]:
        """为单只标的提取指定日期的时点现金流特征"""
        # 1. 从 PITCalendar 取出截至 as_of_date 的历史披露记录
        hist = self.calendar.get_historical_records(
            symbol=symbol,
            as_of_date=as_of_date,
            limit=lookback_quarters
        )
        if not hist:
            return None

        # 2. 调用现金流引擎提取 TTM 特征
        return self.cf_engine.compute_features(hist)

    def extract_universe_features(
        self,
        symbols: List[str],
        as_of_date: str,
        lookback_quarters: int = 4
    ) -> Dict[str, CashFlowFeatures]:
        """批量提取股票池特征矩阵"""
        result: Dict[str, CashFlowFeatures] = {}
        for sym in symbols:
            feat = self.extract_features(sym, as_of_date, lookback_quarters)
            if feat is not None:
                result[sym] = feat
        return result
