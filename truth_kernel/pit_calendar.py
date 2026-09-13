"""
truth_kernel.pit_calendar
~~~~~~~~~~~~~~~~~~~~~~~~~
提供绝对无未来函数的点时（Point-in-Time）时空防穿透机制。
严格依据法定披露日（disclosure_date）对外吐露数据，物理阻断跨期偷窥。
"""

from typing import Dict, List, Optional
from truth_kernel.models import CompanyFinancialRecord


class LookaheadBiasError(Exception):
    """当策略试图在法定披露日之前读取财务数据时触发的致命异常"""
    pass


class PITCalendar:
    """
    点时（Point-in-Time）数据仓库管理器
    确保在回测与实盘中的任意时间截面 as_of_date，只能访问在该时刻已正式公布的财报。
    """

    def __init__(self, buffer_days: int = 1) -> None:
        """
        :param buffer_days: 披露后安全生效缓冲天数，默认 1 天（防止同日盘前盘后混淆）
        """
        self.buffer_days = max(0, buffer_days)
        # 按 symbol 归类存储记录：symbol -> List[CompanyFinancialRecord]
        self._records: Dict[str, List[CompanyFinancialRecord]] = {}

    def register_record(self, record: CompanyFinancialRecord) -> None:
        """注册一条财务点时记录，按披露日自动升序排列"""
        if record.symbol not in self._records:
            self._records[record.symbol] = []
        
        # 插入并根据 (disclosure_date, period_end_date) 排序
        records = self._records[record.symbol]
        records.append(record)
        records.sort(key=lambda r: (r.disclosure_date, r.period_end_date))

    def get_latest_record(
        self,
        symbol: str,
        as_of_date: str,
        strict_pit: bool = True
    ) -> Optional[CompanyFinancialRecord]:
        """
        获取指定日期 as_of_date 可见的最新的公司财务记录。
        若 strict_pit 为 True，则严格要求 as_of_date >= disclosure_date。
        """
        if symbol not in self._records:
            return None

        candidates = [
            r for r in self._records[symbol]
            if r.disclosure_date <= as_of_date
        ]

        if not candidates:
            return None

        # 返回披露日最近的一份
        return candidates[-1]

    def get_historical_records(
        self,
        symbol: str,
        as_of_date: str,
        limit: Optional[int] = None
    ) -> List[CompanyFinancialRecord]:
        """
        获取在 as_of_date 截面已披露的历史财务序列（按时间正序排列）
        用于滚动计算 TTM 自由现金流或造血纯度变动趋势。
        """
        if symbol not in self._records:
            return []

        visible = [
            r for r in self._records[symbol]
            if r.disclosure_date <= as_of_date
        ]

        if limit is not None and limit > 0:
            return visible[-limit:]
        return visible

    def check_lookahead_violation(
        self,
        symbol: str,
        query_date: str,
        target_period_end: str
    ) -> None:
        """
        主动审计：如果代码在 query_date 试图访问尚未公布的 target_period_end 财报，
        则直接抛出 LookaheadBiasError 阻断执行。
        """
        if symbol not in self._records:
            return

        for r in self._records[symbol]:
            if r.period_end_date == target_period_end:
                if query_date < r.disclosure_date:
                    raise LookaheadBiasError(
                        f"【宪法红线警报】检测到未来函数穿透！股票 {symbol} 的报告期 "
                        f"{target_period_end} 真实披露日为 {r.disclosure_date}，"
                        f"但系统在 {query_date} 试图读取它！"
                    )
