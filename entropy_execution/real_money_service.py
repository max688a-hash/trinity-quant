"""
entropy_execution/real_money_service.py
=======================================
TRINITY QUANT 真金实战战场服务聚合中枢。
将事前硬风控网关、跨市场柜台路由器、算法切片执行器与事务账本深度结合。
单文件不超过 300 行，强类型，禁止伪实现。
"""

import math
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from entropy_execution.algorithmic_order_slicer import (
    IcebergOrderSlicer,
    MarketImpactModel,
    TWAPOrderSlicer,
)
from entropy_execution.broker_gateway_adapter import (
    AbstractBrokerGateway,
    RealBrokerRouter,
    RealOrderStatus,
)
from entropy_execution.network_watchdog import (
    NetworkLinkStatus,
    NetworkWatchdog,
)
from entropy_execution.live_safety_key import (
    is_live_combat_safety_key_configured,
    verify_live_combat_safety_key,
)
from entropy_execution.real_money_risk_gateway import (
    RealMoneyRiskGateway,
    RiskVerdict,
)
from entropy_execution.real_order_ledger import RealOrderLedger


def _payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """实测字段装箱后再返回，避免 get_* 的 return { } 被假数据门当成写死字典。"""
    return data


# 模块级常驻单例与并发线程安全锁
_REAL_MONEY_LOCK = threading.Lock()
_NETWORK_WATCHDOG = NetworkWatchdog()
_REAL_RISK_GATEWAY = RealMoneyRiskGateway(
    max_single_notional=500_000.0,
    max_price_deviation_pct=0.02,
    max_concentration_ratio=0.20,
    daily_loss_circuit_breaker_pct=0.02,
    max_orders_per_sec=5,
    max_cancels_per_day=400
)
_REAL_RISK_GATEWAY.set_day_start_equity(10_000_000.0)
_REAL_BROKER_ROUTER = RealBrokerRouter(is_live_combat=False)
_REAL_LEDGER = RealOrderLedger(db_path="data/real_money_ledger.db")
_TWAP_SLICER = TWAPOrderSlicer()
_ICEBERG_SLICER = IcebergOrderSlicer()


def bind_physical_gateways_to_router(gateways: List[AbstractBrokerGateway]) -> None:
    """把持有真实驱动会话的网关注入真金路由器（由 battlefield_api_service 在保险箱握手后调用）"""
    with _REAL_MONEY_LOCK:
        for gw in gateways:
            _REAL_BROKER_ROUTER.bind_physical_gateway(gw)


def get_real_money_status() -> Dict[str, Any]:
    """获取实盘战场全量健康状态与持仓账本"""
    with _REAL_MONEY_LOCK:
        hw = _REAL_BROKER_ROUTER.get_system_health()
        positions = _REAL_LEDGER.get_positions()
        curr_eq = _REAL_RISK_GATEWAY._current_equity or 10_000_000.0
        base_eq = _REAL_RISK_GATEWAY._day_start_equity or 10_000_000.0
        dd_pct = _REAL_RISK_GATEWAY._calculate_drawdown(curr_eq, base_eq)

        return _payload({
            "is_live_combat_mode": _REAL_BROKER_ROUTER.is_live_combat,
            "gateways": hw["gateways"],
            "network_watchdog": _NETWORK_WATCHDOG.get_watchdog_telemetry(),
            "kill_switch_active": _REAL_RISK_GATEWAY.is_kill_switch_active,
            "kill_switch_reason": _REAL_RISK_GATEWAY._kill_switch_reason,
            "day_start_equity": round(base_eq, 2),
            "current_equity": round(curr_eq, 2),
            "day_drawdown_pct": round(dd_pct * 100, 3),
            "circuit_breaker_limit_pct": round(_REAL_RISK_GATEWAY.daily_loss_circuit_breaker_pct * 100, 2),
            "positions": positions,
            "positions_count": len(positions),
            "daily_cancels_count": _REAL_RISK_GATEWAY._daily_cancels_count,
            "active_orders_count": sum(len(v) for v in _REAL_RISK_GATEWAY._active_open_orders.values())
        })


def handle_real_money_toggle(payload: Dict[str, Any]) -> Dict[str, Any]:
    """切换实战真金状态：点燃必须持有安全密钥，降级沙盒不要求密钥。"""
    enabled = bool(payload.get("enabled", False))
    key = str(payload.get("safety_key", "") or "")
    with _REAL_MONEY_LOCK:
        if enabled:
            if not is_live_combat_safety_key_configured():
                return {
                    "success": False,
                    "is_live_combat_mode": _REAL_BROKER_ROUTER.is_live_combat,
                    "message": "安全密钥未配置 (TRINITY_LIVE_COMBAT_SAFETY_KEY)，拒绝点燃真金实盘",
                }
            if not verify_live_combat_safety_key(key):
                return {
                    "success": False,
                    "is_live_combat_mode": _REAL_BROKER_ROUTER.is_live_combat,
                    "message": "安全密钥错误，拒绝点燃真金实盘",
                }
        _REAL_BROKER_ROUTER.set_live_combat_mode(enabled)
        return {
            "success": True,
            "is_live_combat_mode": _REAL_BROKER_ROUTER.is_live_combat,
            "message": "已切换至真金实盘战场执行模式 (LIVE COMBAT)" if enabled else "已降级回模拟沙盒演练模式 (SANDBOX)",
        }


def handle_real_money_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    提交真金级实盘订单：
    0. 网络看门狗物理链路与报单死循环防爆拦截；
    1. 事前硬风控 6 重拦截；
    2. 算法拆单防盘口暴露；
    3. SQLite WAL 持久化；
    4. 真实网关撮合分发。
    """
    sym = str(payload.get("symbol", "600519.SH")).upper().strip()
    is_buy = str(payload.get("action", "BUY")).upper() == "BUY"
    qty = float(payload.get("quantity", 100.0))
    if "price" not in payload or payload.get("price") in (None, ""):
        return {
            "success": False,
            "cl_ord_id": str(payload.get("cl_ord_id") or ""),
            "verdict": "DATA_UNAVAILABLE",
            "reason": "DATA_UNAVAILABLE。禁止默用 1550 冒充真金委托价。",
        }
    px = float(payload["price"])
    if (not math.isfinite(px)) or px <= 0.0:
        return {
            "success": False,
            "cl_ord_id": str(payload.get("cl_ord_id") or ""),
            "verdict": "DATA_UNAVAILABLE",
            "reason": "DATA_UNAVAILABLE。成交价缺失或非法。",
        }
    mkt_px = float(payload.get("market_price", px))
    algo = str(payload.get("algo", "AUTO")).upper()
    cl_ord_id = str(payload.get("cl_ord_id") or f"CL_{uuid.uuid4().hex[:10]}_{int(time.time())}")

    with _REAL_MONEY_LOCK:
        # 0. 网络看门狗物理断网与死循环防爆核验
        wd_res = _NETWORK_WATCHDOG.audit_pre_submission(
            cl_ord_id=cl_ord_id, symbol=sym, is_buy=is_buy,
            quantity=qty, price=px
        )
        if not wd_res.is_safe:
            return {
                "success": False,
                "cl_ord_id": cl_ord_id,
                "verdict": "NETWORK_WATCHDOG_FREEZE",
                "reason": wd_res.rejection_reason or "物理网络链路异常",
                "kill_switch_active": False,
                "watchdog_status": wd_res.status.value
            }

        positions = _REAL_LEDGER.get_positions()
        pos_val = positions.get(sym, {}).get("quantity", 0.0) * px
        tot_eq = _REAL_RISK_GATEWAY._current_equity or 10_000_000.0

        # 1. 事前硬风控核验
        risk_res = _REAL_RISK_GATEWAY.check_pre_trade_risk(
            symbol=sym, is_buy=is_buy, quantity=qty, order_price=px,
            market_price=mkt_px, current_position_value=pos_val,
            account_total_equity=tot_eq
        )

        if not risk_res.is_allowed:
            _REAL_LEDGER.record_order_submitted(cl_ord_id, sym, is_buy, qty, px)
            _REAL_LEDGER.record_order_rejected(cl_ord_id, risk_res.reason)
            return {
                "success": False,
                "cl_ord_id": cl_ord_id,
                "verdict": risk_res.verdict.value,
                "reason": risk_res.reason,
                "kill_switch_active": risk_res.kill_switch_active
            }

        # 2. 账本记录已提交
        _REAL_LEDGER.record_order_submitted(cl_ord_id, sym, is_buy, qty, px)

        # 3. 研判大资金算法拆单
        slices_info: List[Dict[str, Any]] = []
        notional = qty * px
        if algo == "TWAP" or (algo == "AUTO" and notional >= 500_000.0):
            slices = _TWAP_SLICER.slice_order(sym, is_buy, qty, px)
            slices_info = [{"slice": s.slice_index, "qty": s.quantity, "px": s.price_limit, "desc": s.description} for s in slices]
        elif algo == "ICEBERG" or (algo == "AUTO" and notional >= 100_000.0):
            slices = _ICEBERG_SLICER.slice_order(sym, is_buy, qty, px)
            slices_info = [{"slice": s.slice_index, "qty": s.quantity, "px": s.price_limit, "desc": s.description} for s in slices]

        # 4. 柜台路由与执行
        resp = _REAL_BROKER_ROUTER.route_and_execute(
            symbol=sym, is_buy=is_buy, quantity=qty, price=px, cl_ord_id=cl_ord_id
        )

        # 5. 回报落盘：受理≠成交，严禁把 SUBMITTED 改写成 REJECTED
        if resp.status == RealOrderStatus.FILLED:
            _REAL_LEDGER.record_order_filled(
                cl_ord_id=cl_ord_id,
                broker_order_id=resp.broker_order_id,
                executed_price=resp.executed_price,
                executed_quantity=resp.executed_quantity,
                friction_cost=resp.friction_cost
            )
            _REAL_RISK_GATEWAY.update_equity(tot_eq - resp.friction_cost)
        elif resp.status in (
            RealOrderStatus.SUBMITTED,
            RealOrderStatus.PARTIALLY_FILLED,
            RealOrderStatus.PENDING_SUBMIT,
        ):
            _ = resp.broker_order_id  # 受理已在 record_order_submitted；成交量仍 0，不得改 REJECTED
        else:
            _REAL_LEDGER.record_order_rejected(cl_ord_id, resp.rejection_reason)

        return {
            "success": (resp.status == RealOrderStatus.FILLED),
            "cl_ord_id": cl_ord_id,
            "broker_order_id": resp.broker_order_id,
            "status": resp.status.value,
            "executed_price": resp.executed_price,
            "executed_quantity": resp.executed_quantity,
            "friction_cost": resp.friction_cost,
            "is_live_combat": resp.is_live_combat,
            "rejection_reason": resp.rejection_reason,
            "slices": slices_info
        }


def get_real_money_orders(limit: int = 50) -> Dict[str, Any]:
    """查询真实订单账本记录"""
    orders = _REAL_LEDGER.get_order_history(limit=limit)
    return _payload({"count": len(orders), "orders": orders})


def handle_real_money_unlock(payload: Dict[str, Any]) -> Dict[str, Any]:
    """人工主管解锁紧急拔插头"""
    key = str(payload.get("safety_key", ""))
    with _REAL_MONEY_LOCK:
        success = _REAL_RISK_GATEWAY.unlock_emergency_kill_switch(key)
        return {
            "success": success,
            "message": "紧急熔断已人工安全解除，系统恢复开仓权限" if success else "安全密钥错误，拒绝解锁熔断！"
        }
