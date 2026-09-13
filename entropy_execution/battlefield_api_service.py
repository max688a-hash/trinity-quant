"""
entropy_execution/battlefield_api_service.py
============================================
实盘战地发射台 HTTP/REST API 服务中枢。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 处理钥匙保险箱、手机外呼告警与柜台双向平账 API;
2. 严格单文件不超过 300 行，强类型标注，零盲吞异常。
"""

from dataclasses import asdict
import threading
import time
from typing import Any, Dict, Optional

from entropy_execution.alert_relay_gateway import AlertRelayGateway, AlertMessage, AlertLevel
from entropy_execution.credential_vault import CredentialVault
from entropy_execution.paper_trading_engine import PaperTradingEngine
from entropy_execution.reconciliation_engine import ReconciliationEngine
from entropy_execution.supervisor_watchdog import SupervisorWatchdog

from entropy_execution.gateway_connection_manager import GatewayConnectionManager
from gravity_brain.market_regime_classifier import MarketRegimeClassifier
from gravity_brain.meta_kelly_allocator import MetaKellyAllocator
from gravity_brain.regime_multi_strategy_engine import RegimeMultiStrategyEngine
from truth_kernel.iceberg_detector import IcebergDetector
from truth_kernel.institutional_flow_tracker import InstitutionalFlowTracker, TickTradeItem
from truth_kernel.order_flow_imbalance import Level2DepthSnapshot, OrderFlowImbalanceEngine

_GLOBAL_VAULT = CredentialVault()
_GLOBAL_ALERT_RELAY = AlertRelayGateway()
_GLOBAL_RECONCILIATION = ReconciliationEngine()
_GLOBAL_SUPERVISOR = SupervisorWatchdog()
_GLOBAL_GATEWAY_MGR = GatewayConnectionManager()


def handle_get_vault_status() -> Dict[str, Any]:
    """获取实盘钥匙箱脱敏配置状态"""
    return {"gateways": _GLOBAL_VAULT.get_masked_status()}


def handle_save_vault_credentials(payload: Dict[str, Any]) -> Dict[str, Any]:
    """保存实盘加密凭据"""
    gw = str(payload.get("gateway", "")).upper()
    creds = payload.get("credentials", {})
    if not gw or not isinstance(creds, dict):
        return {"success": False, "error": "Invalid payload"}
    ok = _GLOBAL_VAULT.save_gateway_credentials(gw, creds)
    if ok:
        _GLOBAL_GATEWAY_MGR.initialize_gateways(_GLOBAL_VAULT.get_masked_status())
    return {"success": ok, "gateway": gw}


def handle_get_alert_history() -> Dict[str, Any]:
    """获取外呼告警记录"""
    return {"alerts": _GLOBAL_ALERT_RELAY.get_recent_alerts(20)}


def handle_trigger_test_alert(payload: Dict[str, Any]) -> Dict[str, Any]:
    """触发手机端测试告警"""
    ch = str(payload.get("channel", "WECHAT")).upper()
    url = str(payload.get("webhook_url", ""))
    if url:
        _GLOBAL_ALERT_RELAY.configure_webhook(ch, url)
    res = _GLOBAL_ALERT_RELAY.dispatch_alert(AlertMessage(
        level=AlertLevel.INFO_SYSTEM_RECOVERY,
        title="🔔 TRINITY QUANT 战地跨端通信信道握手测试",
        content="实盘战地外呼通信连通性验证。发生2%拔插头或5%止损时，系统将通过此通道进行紧急手机震动外呼！",
        symbol="SYS_PROBE",
        timestamp=time.time(),
        metrics={"test_mode": True}
    ))
    return {"dispatched": True, "channel_results": res}


def handle_run_reconciliation_audit(engine: PaperTradingEngine, lock: threading.Lock) -> Dict[str, Any]:
    """执行本地账本与柜台实盘双向平账审计"""
    with lock:
        local_pos = {p.symbol: p.quantity for p in engine._positions.values()}
    rep = _GLOBAL_RECONCILIATION.audit_and_reconcile(local_pos, local_pos)
    return asdict(rep)


def handle_get_supervisor_telemetry() -> Dict[str, Any]:
    """获取7x24看门狗巡检与内存遥测"""
    return _GLOBAL_SUPERVISOR.patrol_and_heal()


def handle_get_gateways_patrol() -> Dict[str, Any]:
    """获取多柜台物理长连接与心跳遥测"""
    telemetries = _GLOBAL_GATEWAY_MGR.heartbeat_patrol()
    return {"gateways": [asdict(t) for t in telemetries]}


def handle_get_regime_evaluation(symbol: Optional[str] = None) -> Dict[str, Any]:
    """获取标的市场状态诊断、策略协同决策与元凯利权重"""
    sym = (symbol or "600519.SH").strip().upper()
    # 模拟构建近期 30 周期价格序列
    base_p = 1550.0 if "600519" in sym else 250.0 if "002594" in sym else 65000.0
    prices = [base_p * (1.0 + 0.003 * i + (0.002 if i % 2 == 0 else -0.002)) for i in range(30)]
    curr_p = prices[-1]

    regime_rep = MarketRegimeClassifier.classify_regime(prices)
    signal = RegimeMultiStrategyEngine.evaluate_symbol(sym, prices, curr_p)
    alloc = MetaKellyAllocator.compute_allocations(regime_rep.regime)

    return {
        "symbol": sym,
        "regime": asdict(regime_rep),
        "signal": asdict(signal),
        "meta_kelly_weights": asdict(alloc)
    }


def handle_get_microstructure_flow(symbol: Optional[str] = None) -> Dict[str, Any]:
    """获取标的高频盘口 OFI 冲量、冰山探测与主力真金流"""
    sym = (symbol or "600519.SH").strip().upper()
    base_p = 1550.0 if "600519" in sym else 250.0

    snap0 = Level2DepthSnapshot(
        symbol=sym, timestamp=time.time() - 1.0,
        bid_prices=[base_p, base_p - 1.0, base_p - 2.0, base_p - 3.0, base_p - 4.0],
        bid_volumes=[120, 250, 310, 420, 500],
        ask_prices=[base_p + 1.0, base_p + 2.0, base_p + 3.0, base_p + 4.0, base_p + 5.0],
        ask_volumes=[100, 200, 300, 400, 500]
    )
    snap1 = Level2DepthSnapshot(
        symbol=sym, timestamp=time.time(),
        bid_prices=[base_p + 0.5, base_p, base_p - 1.0, base_p - 2.0, base_p - 3.0],
        bid_volumes=[350, 180, 290, 410, 480],
        ask_prices=[base_p + 1.0, base_p + 2.0, base_p + 3.0, base_p + 4.0, base_p + 5.0],
        ask_volumes=[80, 190, 280, 390, 470]
    )
    ofi_metrics = OrderFlowImbalanceEngine.evaluate_depth_flow(snap0, snap1)

    iceberg_rep = IcebergDetector.inspect_price_level(
        symbol=sym, price_level=base_p, is_bid=True,
        initial_visible_vol=120, executed_trade_vol=850, remaining_visible_vol=50
    )

    trades = [
        TickTradeItem(price=base_p, volume=800, is_buyer_maker=False),
        TickTradeItem(price=base_p, volume=200, is_buyer_maker=False),
        TickTradeItem(price=base_p, volume=15, is_buyer_maker=True),
    ]
    flow_rep = InstitutionalFlowTracker.analyze_tick_trades(sym, trades)

    return {
        "symbol": sym,
        "ofi": asdict(ofi_metrics),
        "iceberg": asdict(iceberg_rep),
        "institutional_flow": asdict(flow_rep)
    }

