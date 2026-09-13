"""
尸检只输出选股引擎未准入的法证否决。
引擎已准入的标的（含长江电力）禁止再写成债务猝死。
"""

from __future__ import annotations

import json
import logging
import math
import os
from typing import Any, Dict, List, Optional

from gravity_brain.auto_screener_engine import AutoScreenerEngine

_LOG = logging.getLogger(__name__)

_AUDIT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "real_financials",
    "audit_summary.json",
)


def _root(symbol: str) -> str:
    return str(symbol or "").split(".")[0].strip().upper()


def _qualified_roots() -> set[str]:
    return {
        _root(candidate.symbol)
        for candidate in AutoScreenerEngine().run_screening()
        if candidate.is_qualified
    }


def _finite(value: Any) -> Optional[float]:
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        _LOG.warning("尸检数值无法解析: %s", exc)
        return None
    if not math.isfinite(num):
        return None
    return num


def _unavailable() -> Dict[str, Any]:
    return {"status": "DATA_UNAVAILABLE", "count": 0, "cases": []}


def _veto_reasons(details: Dict[str, Any], root: str) -> List[str]:
    node = details.get(root)
    if not isinstance(node, dict):
        return []
    latest = node.get("latest_status")
    if not isinstance(latest, dict):
        return []
    raw = latest.get("veto_reasons")
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def _period(details: Dict[str, Any], root: str, fallback: str) -> str:
    node = details.get(root)
    if isinstance(node, dict):
        latest = node.get("latest_status")
        if isinstance(latest, dict):
            stamped = str(latest.get("period_end_date") or "").strip()
            if stamped:
                return stamped
    return fallback


def list_forensic_autopsy(audit_path: Optional[str] = None) -> Dict[str, Any]:
    """
    读取真实财报体检档案，剔除选股引擎已准入样本。
    缺档或坏 JSON → DATA_UNAVAILABLE，禁止回退本地玩具池。
    """
    path = audit_path or _AUDIT_PATH
    if not os.path.isfile(path):
        return _unavailable()
    try:
        with open(path, encoding="utf-8") as fp:
            payload = json.load(fp)
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        _LOG.error("尸检法证档案读取失败: %s", exc)
        return _unavailable()
    if not isinstance(payload, dict):
        return _unavailable()

    qualified = _qualified_roots()
    details = payload.get("details")
    if not isinstance(details, dict):
        details = {}
    summary = payload.get("summary")
    stocks = summary.get("stocks") if isinstance(summary, dict) else []
    if not isinstance(stocks, list):
        return _unavailable()

    cases: List[Dict[str, Any]] = []
    for stock in stocks:
        if not isinstance(stock, dict):
            continue
        root = _root(str(stock.get("symbol", "")))
        if not root or root in qualified or bool(stock.get("is_admitted")):
            continue
        reasons = _veto_reasons(details, root)
        if not reasons:
            continue
        name = str(stock.get("name") or root).strip() or root
        cases.append({
            "symbol": root,
            "name": name,
            "phi_cp": _finite(stock.get("phi_cp")),
            "omega_debt": _finite(stock.get("omega_debt")),
            "is_admitted": False,
            "is_buyable": False,
            "veto_reasons": reasons,
            "period_end_date": _period(details, root, str(stock.get("latest_period") or "")),
        })
    return {"status": "OK", "count": len(cases), "cases": cases}
