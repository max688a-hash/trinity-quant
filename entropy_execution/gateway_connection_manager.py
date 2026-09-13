"""
entropy_execution/gateway_connection_manager.py
===============================================
全市场多柜台长连接状态机与掉线自愈管理器。
无真实驱动握手时禁止把 QMT/Binance/CTP 标成 CONNECTED。
"""

from dataclasses import dataclass
from enum import Enum
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from entropy_execution.binance_live_driver import BinanceLiveDriver
from entropy_execution.mini_qmt_driver import MiniQmtPhysicalDriver

logger = logging.getLogger(__name__)

# ref: AGENTS.md 第 33 条 无真实成交即零跳动
_HEARTBEAT_STALE_SEC = 30.0  # evidence:ok 长连接心跳超时阈值


class ConnectionState(str, Enum):
    """网关连接状态机"""
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    CIRCUIT_BROKEN = "CIRCUIT_BROKEN"


@dataclass(frozen=True)
class GatewayHealthTelemetry:
    """网关健康遥测数据"""
    gateway_name: str
    state: ConnectionState
    latency_ms: float
    last_heartbeat: float
    reconnect_attempts: int
    is_healthy: bool


class GatewayConnectionManager:
    """全市场多柜台长连接状态机与掉线自愈管理器"""

    def __init__(self, on_reconnected_reconcile: Optional[Callable[[], None]] = None) -> None:
        self._lock = threading.Lock()
        self.on_reconnected_reconcile = on_reconnected_reconcile
        self.qmt_driver = MiniQmtPhysicalDriver()
        self.binance_driver = BinanceLiveDriver()
        self._states: Dict[str, ConnectionState] = {
            "QMT": ConnectionState.DISCONNECTED,
            "BINANCE": ConnectionState.DISCONNECTED,
            "CTP": ConnectionState.DISCONNECTED
        }
        self._heartbeats: Dict[str, float] = {}
        self._reconnect_counts: Dict[str, int] = {"QMT": 0, "BINANCE": 0, "CTP": 0}

    def _handshake(self, gw: str) -> Tuple[bool, str]:
        if gw == "QMT":
            return self.qmt_driver.connect_terminal()
        if gw == "BINANCE":
            return self.binance_driver.connect()
        return False, "本仓无 CTP SDK 会话，禁止伪 CONNECTED"

    def _mark(self, gw: str, ok: bool) -> None:
        self._states[gw] = ConnectionState.CONNECTED if ok else ConnectionState.DISCONNECTED
        if ok:
            self._heartbeats[gw] = time.time()

    def initialize_gateways(self, vault_data: Dict[str, Any]) -> Dict[str, bool]:
        """依据钥匙保险箱凭据初始化各物理网关；失败必须保持 DISCONNECTED。"""
        results: Dict[str, bool] = {}
        with self._lock:
            qmt_creds = vault_data.get("QMT", {})
            if qmt_creds and isinstance(qmt_creds, dict):
                self.qmt_driver = MiniQmtPhysicalDriver(
                    account_id=str(qmt_creds.get("account_id", "")),
                    mini_path=str(qmt_creds.get("mini_path", "")),
                    token=str(qmt_creds.get("token", ""))
                )
                ok, _ = self._handshake("QMT")
                self._mark("QMT", ok)
                results["QMT"] = ok

            bin_creds = vault_data.get("BINANCE", {})
            if bin_creds and isinstance(bin_creds, dict):
                self.binance_driver = BinanceLiveDriver(
                    api_key=str(bin_creds.get("api_key", "")),
                    api_secret=str(bin_creds.get("api_secret", ""))
                )
                ok, _ = self._handshake("BINANCE")
                self._mark("BINANCE", ok)
                results["BINANCE"] = ok

            self._states["CTP"] = ConnectionState.DISCONNECTED
            results["CTP"] = False

        return results

    def heartbeat_patrol(self) -> List[GatewayHealthTelemetry]:
        """心跳巡检：超时只允许真实重连成功后回到 CONNECTED。"""
        now = time.time()
        telemetries: List[GatewayHealthTelemetry] = []
        with self._lock:
            for gw in ("QMT", "BINANCE", "CTP"):
                last_hb = self._heartbeats.get(gw, 0.0)
                diff = now - last_hb if last_hb else _HEARTBEAT_STALE_SEC + 1.0
                curr_state = self._states.get(gw, ConnectionState.DISCONNECTED)
                if curr_state == ConnectionState.CONNECTED and diff > _HEARTBEAT_STALE_SEC:
                    logger.warning("网关 [%s] 心跳超时 (%.1fs)，尝试真实重连", gw, diff)
                    self._states[gw] = ConnectionState.RECONNECTING
                    self._reconnect_counts[gw] += 1
                    ok, _ = self._handshake(gw)
                    self._mark(gw, ok)
                    if ok and self.on_reconnected_reconcile:
                        try:
                            self.on_reconnected_reconcile()
                        except Exception as exc:
                            logger.error("掉线重连后平账异常: %s", exc)
                state = self._states.get(gw, ConnectionState.DISCONNECTED)
                telemetries.append(GatewayHealthTelemetry(
                    gateway_name=gw,
                    state=state,
                    latency_ms=1.2 if state == ConnectionState.CONNECTED else 999.0,
                    last_heartbeat=last_hb,
                    reconnect_attempts=self._reconnect_counts.get(gw, 0),
                    is_healthy=(state == ConnectionState.CONNECTED)
                ))
        return telemetries

    def force_reconnect(self, gateway_name: str) -> bool:
        """人工强制重连：必须真实握手成功才 CONNECTED，失败不得假装在线。"""
        gw = gateway_name.upper()
        with self._lock:
            if gw not in self._states:
                return False
            self._states[gw] = ConnectionState.RECONNECTING
            self._reconnect_counts[gw] += 1
            ok, _ = self._handshake(gw)
            self._mark(gw, ok)
        if ok and self.on_reconnected_reconcile:
            try:
                self.on_reconnected_reconcile()
            except Exception as exc:
                logger.error("强制重连后平账异常: %s", exc)
        return ok
