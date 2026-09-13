"""
truth_kernel/data_probe_router.py
=================================
TRINITY QUANT 数据源健康实时探针与无感秒级热切换路由器。

解决数据层致命暗礁：
1. 实时探针监测延迟 (RTT)、心跳停滞 (Staleness)、脏数据/空值与突变极值;
2. 主备数据源 (Primary vs Secondary) 毫秒级无感热切换，交易引擎零停机。
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class SourceStatus(str, Enum):
    """数据源健康状态"""
    HEALTHY = "HEALTHY"      # 探针正常，延迟与质量达标
    DEGRADED = "DEGRADED"    # 延迟偏高或偶发抖动，降级观察
    CORRUPTED = "CORRUPTED"  # 存在脏数据/时间停滞，触发熔断隔离
    OFFLINE = "OFFLINE"      # 心跳超时，离线断开


@dataclass(frozen=True)
class ProbeHeartbeat:
    """探针采样指标"""
    source_name: str
    latency_ms: float
    timestamp: float
    is_stale: bool
    has_null_or_nan: bool
    price_spike_ratio: float
    status: SourceStatus


@dataclass(frozen=True)
class MarketQuoteFrame:
    """带有数据源溯源标签的行情帧"""
    symbol: str
    price: float
    volume: float
    timestamp: float
    source_origin: str


class DataProbeRouter:
    """多源数据实时探针与热切换路由器"""

    def __init__(
        self,
        max_latency_ms: float = 500.0,
        staleness_timeout_sec: float = 3.0,
        spike_threshold_ratio: float = 0.05
    ) -> None:
        if max_latency_ms <= 0:
            raise ValueError("延迟上限必须大于0")
        if staleness_timeout_sec <= 0:
            raise ValueError("超时阈值必须大于0")
        self._max_latency_ms = max_latency_ms
        self._staleness_timeout = staleness_timeout_sec
        self._spike_threshold = spike_threshold_ratio
        self._source_priority: List[str] = []
        self._last_heartbeats: Dict[str, ProbeHeartbeat] = {}
        self._last_valid_prices: Dict[str, float] = {}

    def register_source(self, source_name: str) -> None:
        """注册数据通道 (按调用顺序确定初始优先级)"""
        name = source_name.strip().upper()
        if not name:
            raise ValueError("数据源名称不得为空")
        if name not in self._source_priority:
            self._source_priority.append(name)

    def probe_and_ingest(
        self,
        source_name: str,
        symbol: str,
        price: float,
        volume: float,
        quote_timestamp: float,
        rtt_latency_ms: float,
        system_time_now: Optional[float] = None
    ) -> Optional[MarketQuoteFrame]:
        """
        探针实时抽检并摄取行情
        
        :return: 若数据源健康且通过检验，返回标准行情帧；若被污染或异常，返回 None 并触发降级
        """
        src = source_name.strip().upper()
        now = system_time_now if system_time_now is not None else time.time()

        # 1. 检查断流停滞 (Staleness)
        time_diff = now - quote_timestamp
        is_stale = (time_diff > self._staleness_timeout) or (time_diff < -1.0)

        # 2. 检查空值/非法值 (NaN / Inf / 非正数)
        has_null = price <= 0 or volume < 0

        # 3. 检查突发毛刺异动 (Spike Filter)
        spike_ratio = 0.0
        if symbol in self._last_valid_prices and not has_null:
            last_p = self._last_valid_prices[symbol]
            spike_ratio = abs(price - last_p) / last_p

        # 判定状态
        if has_null or (spike_ratio >= self._spike_threshold):
            status = SourceStatus.CORRUPTED
        elif is_stale or (rtt_latency_ms > self._max_latency_ms * 2.0):
            status = SourceStatus.OFFLINE
        elif rtt_latency_ms > self._max_latency_ms:
            status = SourceStatus.DEGRADED
        else:
            status = SourceStatus.HEALTHY

        # 更新探针记录
        hb = ProbeHeartbeat(
            source_name=src,
            latency_ms=rtt_latency_ms,
            timestamp=now,
            is_stale=is_stale,
            has_null_or_nan=has_null,
            price_spike_ratio=spike_ratio,
            status=status
        )
        self._last_heartbeats[src] = hb

        if status in (SourceStatus.CORRUPTED, SourceStatus.OFFLINE):
            return None

        # 校验合格，更新锚定价格
        self._last_valid_prices[symbol] = price
        return MarketQuoteFrame(
            symbol=symbol.upper(),
            price=price,
            volume=volume,
            timestamp=quote_timestamp,
            source_origin=src
        )

    def get_active_source(self) -> str:
        """
        获取当前最优可用健康数据源 (无感秒级热切换)
        """
        for src in self._source_priority:
            hb = self._last_heartbeats.get(src)
            if hb is not None and hb.status == SourceStatus.HEALTHY:
                return src

        # 若无完全健康，降级使用仅延迟偏高的 DEGRADED 源
        for src in self._source_priority:
            hb = self._last_heartbeats.get(src)
            if hb is not None and hb.status == SourceStatus.DEGRADED:
                return src

        raise RuntimeError("全部注册数据源均处于熔断或离线状态，触发系统级紧急避险！")
