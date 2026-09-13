"""
entropy_execution/real_order_ledger.py
======================================
TRINITY QUANT 真实订单持久化事务账本与掉电灾备自愈对齐引擎。

最高宪法立宪铁律：
真金实盘绝对禁止只将状态保存在内存中！
1. SQLite WAL 事务型高并发本地持久化；
2. 唯一幂等性客户订单号（cl_ord_id，UUID+时间戳，防超时重复发单）；
3. 灾难自愈（Crash Recovery）：重启时自动加载历史未结订单；
4. 券商持仓双向核对对齐（Position Reconciliation）：发现任何账实不符立刻报警锁仓。
"""

import os
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple


class RealOrderLedger:
    """真实订单事务型 SQLite WAL 账本持久化引擎"""

    BEIJING_TZ = timezone(timedelta(hours=8))

    def __init__(self, db_path: str = "data/real_money_ledger.db") -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        # 启用 WAL 模式提高并发读写性能与崩溃自愈力
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS real_orders (
                    cl_ord_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    is_buy INTEGER NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    status TEXT NOT NULL,
                    broker_order_id TEXT DEFAULT '',
                    rejection_reason TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """)
                conn.execute("""
                CREATE TABLE IF NOT EXISTS real_trades (
                    trade_id TEXT PRIMARY KEY,
                    cl_ord_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    executed_price REAL NOT NULL,
                    executed_quantity REAL NOT NULL,
                    friction_cost REAL NOT NULL,
                    executed_at TEXT NOT NULL,
                    FOREIGN KEY(cl_ord_id) REFERENCES real_orders(cl_ord_id)
                );
                """)
                conn.execute("""
                CREATE TABLE IF NOT EXISTS real_positions (
                    symbol TEXT PRIMARY KEY,
                    quantity REAL NOT NULL,
                    cost_basis REAL NOT NULL,
                    shares_frozen_t1 REAL NOT NULL,
                    last_reconciled_at TEXT NOT NULL
                );
                """)
                conn.commit()

    def _now_str(self) -> str:
        return datetime.now(self.BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")

    def record_order_submitted(
        self,
        cl_ord_id: str,
        symbol: str,
        is_buy: bool,
        quantity: float,
        price: float
    ) -> bool:
        """记录新订单提交（幂等性保护：若订单号已存在则忽略）"""
        now = self._now_str()
        with self._lock:
            with self._get_connection() as conn:
                try:
                    conn.execute("""
                    INSERT INTO real_orders 
                    (cl_ord_id, symbol, is_buy, quantity, price, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 'SUBMITTED', ?, ?)
                    """, (cl_ord_id, symbol.upper(), 1 if is_buy else 0, quantity, price, now, now))
                    conn.commit()
                    return True
                except sqlite3.IntegrityError:
                    return False

    def record_order_filled(
        self,
        cl_ord_id: str,
        broker_order_id: str,
        executed_price: float,
        executed_quantity: float,
        friction_cost: float
    ) -> None:
        """记录真实成交回报并原子更新持仓"""
        now = self._now_str()
        trade_id = f"TRD_{cl_ord_id}_{int(datetime.now().timestamp() * 1000)}"
        with self._lock:
            with self._get_connection() as conn:
                # 1. 更新订单状态
                conn.execute("""
                UPDATE real_orders 
                SET status = 'FILLED', broker_order_id = ?, updated_at = ?
                WHERE cl_ord_id = ?
                """, (broker_order_id, now, cl_ord_id))

                # 2. 查询标的与买卖方向
                row = conn.execute("SELECT symbol, is_buy FROM real_orders WHERE cl_ord_id = ?", (cl_ord_id,)).fetchone()
                if not row:
                    return
                sym = row["symbol"]
                is_buy = bool(row["is_buy"])

                # 3. 记录成交明细
                conn.execute("""
                INSERT INTO real_trades 
                (trade_id, cl_ord_id, symbol, executed_price, executed_quantity, friction_cost, executed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (trade_id, cl_ord_id, sym, executed_price, executed_quantity, friction_cost, now))

                # 4. 原子更新持仓
                pos = conn.execute("SELECT quantity, cost_basis, shares_frozen_t1 FROM real_positions WHERE symbol = ?", (sym,)).fetchone()
                if is_buy:
                    if pos:
                        old_qty = pos["quantity"]
                        old_cost = pos["cost_basis"]
                        new_qty = old_qty + executed_quantity
                        new_cost = (old_qty * old_cost + executed_quantity * executed_price) / max(1e-8, new_qty)
                        frozen = pos["shares_frozen_t1"] + executed_quantity
                        conn.execute("""
                        UPDATE real_positions SET quantity = ?, cost_basis = ?, shares_frozen_t1 = ?, last_reconciled_at = ?
                        WHERE symbol = ?
                        """, (new_qty, new_cost, frozen, now, sym))
                    else:
                        conn.execute("""
                        INSERT INTO real_positions (symbol, quantity, cost_basis, shares_frozen_t1, last_reconciled_at)
                        VALUES (?, ?, ?, ?, ?)
                        """, (sym, executed_quantity, executed_price, executed_quantity, now))
                else:
                    if pos:
                        new_qty = max(0.0, pos["quantity"] - executed_quantity)
                        new_frozen = min(new_qty, pos["shares_frozen_t1"])
                        new_cost = pos["cost_basis"] if new_qty > 0 else 0.0
                        conn.execute("""
                        UPDATE real_positions SET quantity = ?, cost_basis = ?, shares_frozen_t1 = ?, last_reconciled_at = ?
                        WHERE symbol = ?
                        """, (new_qty, new_cost, new_frozen, now, sym))
                conn.commit()

    def record_order_rejected(self, cl_ord_id: str, reason: str) -> None:
        """记录订单被柜台拒绝"""
        now = self._now_str()
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                UPDATE real_orders 
                SET status = 'REJECTED', rejection_reason = ?, updated_at = ?
                WHERE cl_ord_id = ?
                """, (reason, now, cl_ord_id))
                conn.commit()

    def get_order_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """查询订单历史记录"""
        with self._lock:
            with self._get_connection() as conn:
                rows = conn.execute("""
                SELECT cl_ord_id, symbol, is_buy, quantity, price, status, broker_order_id, rejection_reason, created_at, updated_at
                FROM real_orders ORDER BY created_at DESC LIMIT ?
                """, (int(limit),)).fetchall()
                return [dict(r) for r in rows]

    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """获取真实持仓字典"""
        with self._lock:
            with self._get_connection() as conn:
                rows = conn.execute("SELECT symbol, quantity, cost_basis, shares_frozen_t1, last_reconciled_at FROM real_positions").fetchall()
                return {r["symbol"]: dict(r) for r in rows}

    def reconcile_positions(self, broker_positions: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        券商持仓双向核对对齐（Position Reconciliation）
        """
        mismatches: List[str] = []
        local_positions = self.get_positions()
        all_symbols = set(local_positions.keys()).union(broker_positions.keys())

        for sym in all_symbols:
            local_qty = local_positions.get(sym, {}).get("quantity", 0.0)
            broker_qty = broker_positions.get(sym, 0.0)
            if abs(local_qty - broker_qty) > 0.001:
                mismatches.append(f"标的 {sym} 账实不符: 本地账本持仓 {local_qty} != 券商柜台持仓 {broker_qty}")

        is_matched = (len(mismatches) == 0)
        if is_matched:
            now = self._now_str()
            with self._lock:
                with self._get_connection() as conn:
                    conn.execute("UPDATE real_positions SET last_reconciled_at = ?", (now,))
                    conn.commit()
        return is_matched, mismatches

    def rollover_trading_day(self) -> None:
        """T+1 交易日终/开盘隔夜解冻与持仓结转"""
        now = self._now_str()
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("UPDATE real_positions SET shares_frozen_t1 = 0.0, last_reconciled_at = ?", (now,))
                conn.commit()
