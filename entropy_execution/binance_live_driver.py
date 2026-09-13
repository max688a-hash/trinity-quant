"""
entropy_execution/binance_live_driver.py
========================================
全球加密数字资产 Binance 币安 7x24 实盘柜台物理驱动器。
无签名账户握手时禁止点亮 is_connected，禁止离线仿真成交。
"""

from dataclasses import dataclass
import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

# ref: AGENTS.md 第 33 条 无真实成交即零跳动；公开 ping ≠ 账户会话
NO_BINANCE_SESSION = "Binance 握手失败，禁止伪 CONNECTED"


@dataclass(frozen=True)
class BinanceBalance:
    """Binance 资产明细"""
    asset: str
    free: float
    locked: float


@dataclass(frozen=True)
class BinancePosition:
    """Binance 合约/现货持仓快照"""
    symbol: str
    position_amt: float
    entry_price: float
    unrealized_pnl: float


class BinanceLiveDriver:
    """Binance 币安 7x24 实盘柜台物理网络驱动器"""

    BASE_URL = "https://api.binance.com"
    FUTURES_URL = "https://fapi.binance.com"

    def __init__(self, api_key: str = "", api_secret: str = "") -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_connected = False
        self._last_ping: float = 0.0

    def _sign(self, query_string: str) -> str:
        """生成 HMAC-SHA256 签名"""
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _signed_account_request(self) -> urllib.request.Request:
        ts = int(time.time() * 1000)
        params = {"timestamp": ts, "recvWindow": 5000}
        qs = urllib.parse.urlencode(params)
        sig = self._sign(qs)
        return urllib.request.Request(
            f"{self.BASE_URL}/api/v3/account?{qs}&signature={sig}",
            headers={"X-MBX-APIKEY": self.api_key}
        )

    def connect(self) -> Tuple[bool, str]:
        """必须打通签名账户接口；仅有 Key 字符串或公开 ping 不算会话。"""
        if not self.api_key or not self.api_secret:
            self.is_connected = False
            return False, "缺少 Binance API Key 或 Secret"
        try:
            req = self._signed_account_request()
            with urllib.request.urlopen(req, timeout=3) as resp:
                if getattr(resp, "status", 200) != 200:
                    self.is_connected = False
                    return False, f"{NO_BINANCE_SESSION}: HTTP {resp.status}"
                json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            self.is_connected = False
            return False, f"{NO_BINANCE_SESSION}: HTTP {exc.code}"
        except urllib.error.URLError as exc:
            self.is_connected = False
            return False, f"{NO_BINANCE_SESSION}: {exc}"
        except Exception as exc:
            logger.warning("Binance 握手异常: %s", exc)
            self.is_connected = False
            return False, f"{NO_BINANCE_SESSION}: {exc}"
        self.is_connected = True
        self._last_ping = time.time()
        return True, "Binance 签名账户握手成功"

    def query_balances(self) -> List[BinanceBalance]:
        """查询现货/资金账户资产；失败禁止降级成假余额。"""
        if not self.is_connected:
            raise RuntimeError("Binance 驱动未连接！")
        req = self._signed_account_request()
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RuntimeError(f"Binance 查询资产失败，禁止演播余额: {exc}") from exc
        res: List[BinanceBalance] = []
        for b in data.get("balances", []):
            free = float(b.get("free", 0.0))
            locked = float(b.get("locked", 0.0))
            if free > 0 or locked > 0:
                res.append(BinanceBalance(asset=b["asset"], free=free, locked=locked))
        return res

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = "LIMIT"
    ) -> Tuple[bool, str, str]:
        """向 Binance 发送真实委托；失败禁止本地仿真 FILLED。"""
        if not self.is_connected:
            return False, "", "Binance 驱动未连接"
        if quantity <= 0:
            return False, "", "委托数量必须大于 0"
        ts = int(time.time() * 1000)
        params: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
            "timestamp": ts,
            "recvWindow": 5000
        }
        if order_type.upper() == "LIMIT":
            if not price or price <= 0:
                return False, "", "限价单必须指定有效价格"
            params["price"] = price
            params["timeInForce"] = "GTC"
        qs = urllib.parse.urlencode(params)
        sig = self._sign(qs)
        body = f"{qs}&signature={sig}".encode("utf-8")
        req = urllib.request.Request(
            f"{self.BASE_URL}/api/v3/order",
            data=body,
            headers={"X-MBX-APIKEY": self.api_key, "Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return False, "", f"Binance 下单失败，禁止本地仿真: {exc}"
        order_id = str(data.get("orderId", ""))
        if not order_id:
            return False, "", "Binance 未返回 orderId，禁止本地仿真"
        return True, order_id, "Binance 委托成功提交"

    def cancel_order(self, symbol: str, order_id: str) -> Tuple[bool, str]:
        """撤销 Binance 在途委托；失败禁止离线仿真成功。"""
        if not self.is_connected:
            return False, "Binance 驱动未连接"
        ts = int(time.time() * 1000)
        params = {
            "symbol": symbol.upper(),
            "orderId": order_id,
            "timestamp": ts,
            "recvWindow": 5000
        }
        qs = urllib.parse.urlencode(params)
        sig = self._sign(qs)
        req = urllib.request.Request(
            f"{self.BASE_URL}/api/v3/order?{qs}&signature={sig}",
            headers={"X-MBX-APIKEY": self.api_key},
            method="DELETE"
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return False, f"Binance 撤单失败，禁止离线仿真: {exc}"
        return True, f"订单 {order_id} 撤单成功 (状态: {data.get('status')})"
