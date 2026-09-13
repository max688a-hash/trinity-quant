"""
选股默认宇宙：只读真实财报估值/体检档案。
缺档 → 空池，禁止回退写死 Φ=1.05 / Ω=0.42。
"""

from __future__ import annotations

import json
import logging
import math
import os
from typing import Any, Dict, List, Optional

_LOG = logging.getLogger(__name__)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VALUATION_PATH = os.path.join(_ROOT, "data", "real_financials", "valuation_summary.json")
_AUDIT_PATH = os.path.join(_ROOT, "data", "real_financials", "audit_summary.json")


def _root_symbol(symbol: str) -> str:
    return str(symbol or "").split(".")[0].strip().upper()


def _finite(value: Any, fallback: float) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        _LOG.warning("选股宇宙数值无法解析: %s", exc)
        return fallback
    if not math.isfinite(num):
        return fallback
    return num


def _load_json_object(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fp:
            payload = json.load(fp)
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        _LOG.error("选股真值档案读取失败 %s: %s", path, exc)
        return {}
    return payload if isinstance(payload, dict) else {}


def _audit_admitted(path: str) -> Dict[str, bool]:
    payload = _load_json_object(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    stocks = summary.get("stocks") if isinstance(summary, dict) else []
    admitted: Dict[str, bool] = {}
    if not isinstance(stocks, list):
        return admitted
    for row in stocks:
        if not isinstance(row, dict):
            continue
        key = _root_symbol(str(row.get("symbol", "")))
        if not key:
            continue
        admitted[key] = bool(row.get("is_admitted"))
    return admitted


def load_default_screener_universe(
    valuation_path: Optional[str] = None,
    audit_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    从 valuation_summary 装载 Φ/Ω/α/V_G，并用 audit_summary 单向收紧准入。
    体检否决的标的不得因估值表或写死数被标可买。
    """
    valuation = _load_json_object(valuation_path or _VALUATION_PATH)
    if not valuation:
        return []
    audit_map = _audit_admitted(audit_path or _AUDIT_PATH)
    rows: List[Dict[str, Any]] = []
    for raw_sym, info in valuation.items():
        if not isinstance(info, dict):
            continue
        key = _root_symbol(str(raw_sym))
        if not key:
            continue
        firewall_ok = bool(info.get("is_firewall_admitted"))
        if key in audit_map:
            firewall_ok = firewall_ok and audit_map[key]
        rows.append({
            "symbol": key,
            "name": str(info.get("name") or key),
            "phi_cp": _finite(info.get("phi_cp"), 0.0),
            "omega_debt": _finite(info.get("omega_debt"), 99.0),
            "alpha": _finite(info.get("alpha_score"), 0.0),
            "gravity_val": _finite(info.get("gravity_value"), 0.0),
            "is_admitted": firewall_ok,
        })
    return rows
