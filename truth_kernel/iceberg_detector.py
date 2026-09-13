"""
truth_kernel/iceberg_detector.py
================================
高频盘口隐形挂单与冰山吸筹嗅探器 (Iceberg Hidden Liquidity Detector)。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 严禁基于玄学猜想，严格比对盘口显式挂单变化量与逐笔成交量差额;
2. 累积成交 > 显式消耗时，判定存在机构冰山单补单 (Reloading Hidden Orders);
3. 严格单文件不超过 300 行，强类型标注，零盲吞异常。
"""

from dataclasses import dataclass
from enum import Enum
import time
from typing import Dict, List, Optional


class IcebergType(str, Enum):
    """冰山委托类型"""
    NONE = "NONE"
    BUY_ACCUMULATION = "BUY_ACCUMULATION"        # 主力买方隐形吸筹冰山
    SELL_DISTRIBUTION = "SELL_DISTRIBUTION"      # 主力卖方隐形出货冰山


@dataclass(frozen=True)
class IcebergDetectionReport:
    """冰山嗅探检测报告"""
    symbol: str
    price_level: float
    detected_type: IcebergType
    visible_volume: int
    executed_volume: int
    estimated_hidden_volume: int
    confidence_score: float
    timestamp: float


class IcebergDetector:
    """盘口微观冰山委托逆向嗅探器"""

    @classmethod
    def inspect_price_level(
        cls,
        symbol: str,
        price_level: float,
        is_bid: bool,
        initial_visible_vol: int,
        executed_trade_vol: int,
        remaining_visible_vol: int
    ) -> IcebergDetectionReport:
        """
        嗅探指定价位是否存在冰山委托:
        若没有冰山: 剩余量 应等于 (初始量 - 成交量)
        若存在冰山: 实际成交量 >> (初始量 - 剩余量)
        隐形吸收量 = 成交量 - (初始量 - 剩余量)
        """
        init_vol = max(0, int(initial_visible_vol))
        exec_vol = max(0, int(executed_trade_vol))
        rem_vol = max(0, int(remaining_visible_vol))
        expected_consumed = init_vol - rem_vol
        hidden_volume = exec_vol - expected_consumed

        if hidden_volume > 200 and exec_vol > init_vol * 1.5 and init_vol > 0:
            # 明确发现隐形补单吸筹/出货
            iceberg_type = IcebergType.BUY_ACCUMULATION if is_bid else IcebergType.SELL_DISTRIBUTION
            confidence = min(0.98, 0.60 + (hidden_volume / (init_vol + 1e-5)) * 0.1)
            return IcebergDetectionReport(
                symbol=symbol,
                price_level=price_level,
                detected_type=iceberg_type,
                visible_volume=rem_vol,
                executed_volume=exec_vol,
                estimated_hidden_volume=hidden_volume,
                confidence_score=round(confidence, 2),
                timestamp=time.time()
            )

        return IcebergDetectionReport(
            symbol=symbol,
            price_level=price_level,
            detected_type=IcebergType.NONE,
            visible_volume=remaining_visible_vol,
            executed_volume=executed_trade_vol,
            estimated_hidden_volume=0,
            confidence_score=0.0,
            timestamp=time.time()
        )
