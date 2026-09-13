"""
entropy_execution/mini_qmt_driver.py
====================================
A股迅投 QMT / MiniQMT 极速交易柜台物理驱动器。
无 xtquant 会话时禁止点亮 is_connected，禁止演播资金与本地伪委托。
"""

from dataclasses import dataclass
import logging
import os
import time
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ref: AGENTS.md 第 33 条 无真实成交即零跳动
NO_QMT_SESSION = "无真实 MiniQMT/xtquant 会话，禁止伪 CONNECTED"


@dataclass(frozen=True)
class QmtAccountSnapshot:
    """QMT 资金账户物理快照"""
    account_id: str
    total_asset: float
    cash_available: float
    market_value: float
    frozen_cash: float
    timestamp: float
    is_live: bool = True


@dataclass(frozen=True)
class QmtPositionRecord:
    """QMT 持仓标的明细"""
    symbol: str
    volume: int
    can_use_volume: int
    open_price: float
    market_value: float
    floating_pnl: float


class MiniQmtPhysicalDriver:
    """迅投 MiniQMT 极速交易柜台物理驱动器"""

    def __init__(self, account_id: str = "", mini_path: str = "", token: str = "") -> None:
        self.account_id = account_id
        self.mini_path = mini_path
        self.token = token
        self.is_connected = False
        self._xt_trader: Optional[Any] = None
        self._session_id: int = int(time.time() * 1000) % 1000000
        self._last_heartbeat: float = 0.0

    def connect_terminal(self) -> Tuple[bool, str]:
        """连接本地 MiniQMT 客户端；缺路径或缺 SDK 必须失败。"""
        if not self.account_id:
            self.is_connected = False
            return False, "缺少 QMT 资金账号 (account_id)"
        if not self.mini_path or not os.path.exists(self.mini_path):
            self.is_connected = False
            self._xt_trader = None
            return False, NO_QMT_SESSION

        try:
            import importlib
            xttrader_mod = importlib.import_module("xtquant.xttrader")
            xt_type_mod = importlib.import_module("xtquant.xttype")
            session_cls = getattr(xttrader_mod, "XtQuantTrader", None)
            if session_cls is None:
                self.is_connected = False
                return False, NO_QMT_SESSION
            self._xt_trader = session_cls(self.mini_path, self._session_id)
            self._xt_trader.start()
            acc = xt_type_mod.StockAccount(self.account_id)
            res = self._xt_trader.connect()
            if res == 0:
                self._xt_trader.subscribe(acc)
                self.is_connected = True
                self._last_heartbeat = time.time()
                return True, "成功直连本地 MiniQMT 实盘柜台！"
            self.is_connected = False
            self._xt_trader = None
            return False, f"MiniQMT connect 返回 {res}，禁止伪 CONNECTED"
        except ImportError as exc:
            logger.info("未检测到 xtquant: %s", exc)
            self.is_connected = False
            self._xt_trader = None
            return False, NO_QMT_SESSION
        except Exception as exc:
            logger.warning("MiniQMT 握手异常: %s", exc)
            self.is_connected = False
            self._xt_trader = None
            return False, f"MiniQMT 握手失败，禁止伪 CONNECTED: {exc}"

    def disconnect_terminal(self) -> None:
        """安全断开交易会话"""
        if self._xt_trader:
            try:
                self._xt_trader.stop()
            except Exception as exc:
                logger.warning("断开 xt_trader 异常: %s", exc)
        self.is_connected = False
        self._xt_trader = None

    def query_account_assets(self) -> QmtAccountSnapshot:
        """查询柜台资金快照；无会话禁止演播 1000 万。"""
        if not self.is_connected or self._xt_trader is None:
            raise RuntimeError("MiniQMT 柜台未连接，无法查询资产！")
        try:
            import importlib
            xt_type = importlib.import_module("xtquant.xttype")
            acc = xt_type.StockAccount(self.account_id)
            asset_obj = self._xt_trader.query_stock_asset(acc)
        except Exception as exc:
            raise RuntimeError(f"xtquant 查询资产失败，禁止演播资金: {exc}") from exc
        if not asset_obj:
            raise RuntimeError("xtquant 返回空资产，禁止演播资金")
        return QmtAccountSnapshot(
            account_id=self.account_id,
            total_asset=float(asset_obj.total_asset),
            cash_available=float(asset_obj.cash),
            market_value=float(asset_obj.market_value),
            frozen_cash=float(asset_obj.frozen_cash),
            timestamp=time.time(),
            is_live=True
        )

    def query_positions(self) -> List[QmtPositionRecord]:
        """查询当前实盘所有持仓明细"""
        if not self.is_connected or self._xt_trader is None:
            raise RuntimeError("MiniQMT 柜台未连接，无法查询持仓！")
        try:
            import importlib
            xt_type = importlib.import_module("xtquant.xttype")
            acc = xt_type.StockAccount(self.account_id)
            pos_list = self._xt_trader.query_stock_positions(acc) or []
        except Exception as exc:
            raise RuntimeError(f"xtquant 查询持仓失败: {exc}") from exc
        return [
            QmtPositionRecord(
                symbol=p.stock_code,
                volume=int(p.volume),
                can_use_volume=int(p.can_use_volume),
                open_price=float(p.open_price),
                market_value=float(p.market_value),
                floating_pnl=float(p.floating_pnl)
            )
            for p in pos_list
        ]

    def place_order(self, symbol: str, is_buy: bool, quantity: int, price: float) -> Tuple[bool, str, str]:
        """向 MiniQMT 发送订单指令；无会话禁止本地伪委托。"""
        if not self.is_connected or self._xt_trader is None:
            return False, "", "MiniQMT 柜台未连接"
        if quantity <= 0 or price <= 0:
            return False, "", "委托数量与价格必须大于 0"
        order_id = f"QMT_{int(time.time()*1000)}_{symbol[:6]}"
        try:
            import importlib
            xt_type = importlib.import_module("xtquant.xttype")
            acc = xt_type.StockAccount(self.account_id)
            order_type = xt_type.STOCK_BUY if is_buy else xt_type.STOCK_SELL
            ret_order_id = self._xt_trader.order_stock(
                acc, symbol, order_type, quantity, xt_type.FIX_PRICE, price, "TRINITY", order_id
            )
        except Exception as exc:
            return False, "", f"xtquant 下单异常: {exc}"
        if ret_order_id > 0:
            return True, str(ret_order_id), "委托成功下发到券商柜台"
        return False, "", f"券商柜台拒绝委托，返回码: {ret_order_id}"

    def cancel_order(self, order_id: str) -> Tuple[bool, str]:
        """撤回在途委托；无会话禁止本地伪撤单。"""
        if not self.is_connected or self._xt_trader is None:
            return False, "MiniQMT 柜台未连接"
        try:
            import importlib
            xt_type = importlib.import_module("xtquant.xttype")
            acc = xt_type.StockAccount(self.account_id)
            res = self._xt_trader.cancel_order_stock(acc, int(order_id))
        except Exception as exc:
            return False, f"撤单异常: {exc}"
        return (res == 0), f"撤单结果代码: {res}"
