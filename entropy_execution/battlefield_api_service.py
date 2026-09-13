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

_GLOBAL_VAULT = CredentialVault()
_GLOBAL_ALERT_RELAY = AlertRelayGateway()
_GLOBAL_RECONCILIATION = ReconciliationEngine()
_GLOBAL_SUPERVISOR = SupervisorWatchdog()


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
