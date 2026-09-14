"""
entropy_execution/physical_broker_gateways.py
=============================================
把具备真实 SDK/REST 会话的物理驱动 (MiniQmtPhysicalDriver / BinanceLiveDriver)
适配为 AbstractBrokerGateway，供 RealBrokerRouter 路由真金委托。

铁律：
1. 驱动未握手 → connect 返回 False，submit 一律 REJECTED；
2. 柜台仅回“已受理”→ 状态为 SUBMITTED、成交量 0，严禁本地伪 FILLED；
3. 成交量/价格必须由后续柜台回报或对账得到，本模块不得臆造。
"""

from typing import Any, Dict

from entropy_execution.binance_live_driver import BinanceLiveDriver
from entropy_execution.broker_gateway_adapter import (
    AbstractBrokerGateway,
    BrokerGatewayType,
    RealOrderRequest,
    RealOrderResponse,
    RealOrderStatus,
    reject_without_live_session,
)
from entropy_execution.mini_qmt_driver import MiniQmtPhysicalDriver


def _rejected(req: RealOrderRequest, reason: str) -> RealOrderResponse:
    return RealOrderResponse(
        cl_ord_id=req.cl_ord_id, broker_order_id="", status=RealOrderStatus.REJECTED,
        executed_price=0.0, executed_quantity=0.0, friction_cost=0.0,
        rejection_reason=reason, is_live_combat=False,
    )


def _submitted(req: RealOrderRequest, broker_order_id: str) -> RealOrderResponse:
    """柜台受理 ≠ 成交；成交数据留待回报/对账填充"""
    return RealOrderResponse(
        cl_ord_id=req.cl_ord_id, broker_order_id=broker_order_id, status=RealOrderStatus.SUBMITTED,
        executed_price=0.0, executed_quantity=0.0, friction_cost=0.0,
        rejection_reason="", is_live_combat=True,
    )


class QmtPhysicalGateway(AbstractBrokerGateway):
    """A 股 MiniQMT 物理网关（xtquant 会话）"""

    def __init__(self, driver: MiniQmtPhysicalDriver) -> None:
        super().__init__(BrokerGatewayType.QMT_STOCK)
        self.driver = driver
        self.is_connected = bool(driver.is_connected)

    def connect(self, credentials: Dict[str, Any]) -> bool:
        if isinstance(credentials, dict) and credentials.get("account_id"):
            self.driver = MiniQmtPhysicalDriver(
                account_id=str(credentials.get("account_id", "")),
                mini_path=str(credentials.get("mini_path", "")),
                token=str(credentials.get("token", "")),
            )
        ok, _ = self.driver.connect_terminal()
        self.is_connected = bool(ok)
        return self.is_connected

    def disconnect(self) -> None:
        self.driver.disconnect_terminal()
        self.is_connected = False

    def submit_order(self, req: RealOrderRequest) -> RealOrderResponse:
        if not self.driver.is_connected:
            return reject_without_live_session(req)
        qty = int(req.quantity)
        if qty <= 0 or qty % 100 != 0:
            return _rejected(req, f"A 股委托数量必须为 100 的整数倍: {req.quantity}")
        ok, order_id, msg = self.driver.place_order(req.symbol, req.is_buy, qty, req.price)
        if not ok:
            return _rejected(req, msg)
        return _submitted(req, order_id)

    def cancel_order(self, cl_ord_id: str) -> bool:
        ok, _ = self.driver.cancel_order(cl_ord_id)
        return bool(ok)

    def query_account(self) -> Dict[str, float]:
        snap = self.driver.query_account_assets()
        return {"total_asset": snap.total_asset, "cash": snap.cash_available, "market_value": snap.market_value}


class BinancePhysicalGateway(AbstractBrokerGateway):
    """Binance 现货签名 REST 物理网关"""

    def __init__(self, driver: BinanceLiveDriver) -> None:
        super().__init__(BrokerGatewayType.BINANCE_CRYPTO)
        self.driver = driver
        self.is_connected = bool(driver.is_connected)

    def connect(self, credentials: Dict[str, Any]) -> bool:
        if isinstance(credentials, dict) and credentials.get("api_key"):
            self.driver = BinanceLiveDriver(
                api_key=str(credentials.get("api_key", "")),
                api_secret=str(credentials.get("api_secret", "")),
            )
        ok, _ = self.driver.connect()
        self.is_connected = bool(ok)
        return self.is_connected

    def disconnect(self) -> None:
        self.driver.is_connected = False
        self.is_connected = False

    def submit_order(self, req: RealOrderRequest) -> RealOrderResponse:
        if not self.driver.is_connected:
            return reject_without_live_session(req)
        side = "BUY" if req.is_buy else "SELL"
        ok, order_id, msg = self.driver.place_order(req.symbol, side, req.quantity, req.price, req.order_type)
        if not ok:
            return _rejected(req, msg)
        return _submitted(req, order_id)

    def cancel_order(self, cl_ord_id: str) -> bool:
        symbol, _, order_id = cl_ord_id.partition(":")
        if not order_id:
            return False
        ok, _ = self.driver.cancel_order(symbol, order_id)
        return bool(ok)

    def query_account(self) -> Dict[str, float]:
        balances = self.driver.query_balances()
        return {b.asset: b.free + b.locked for b in balances}
