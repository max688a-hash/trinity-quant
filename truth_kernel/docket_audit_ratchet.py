"""
入池宗卷单向棘轮：真实财报体检否决后，禁止再写成可买。
truth_kernel 不得依赖 gravity_brain。
"""

from __future__ import annotations

import json
import logging
import math
import os
from dataclasses import asdict, replace
from typing import Any, Dict, Optional

from truth_kernel.pool_admission_auditor import AdmissionDocket, AdmissionGrade

_LOG = logging.getLogger(__name__)
_AUDIT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "real_financials",
    "audit_summary.json",
)


def _root(symbol: str) -> str:
    return str(symbol or "").split(".")[0].strip().upper()


def _finite(value: Any) -> Optional[float]:
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        _LOG.warning("宗卷棘轮数值无法解析: %s", exc)
        return None
    if not math.isfinite(num):
        return None
    return num


def _audit_rows(path: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fp:
            payload = json.load(fp)
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        _LOG.error("宗卷棘轮读取体检档案失败: %s", exc)
        return {}
    if not isinstance(payload, dict):
        return {}
    summary = payload.get("summary")
    stocks = summary.get("stocks") if isinstance(summary, dict) else []
    if not isinstance(stocks, list):
        return {}
    rows: Dict[str, Dict[str, Any]] = {}
    for row in stocks:
        if not isinstance(row, dict):
            continue
        key = _root(str(row.get("symbol", "")))
        if key:
            rows[key] = row
    return rows


def apply_audit_ratchet(
    docket: AdmissionDocket,
    audit_path: Optional[str] = None,
) -> AdmissionDocket:
    """
    体检未覆盖的标的保持原宗卷。
    覆盖且否决 / Φ<0.30 / Ω>0.40 → is_buyable_now=False，数字改体检值。
    """
    rows = _audit_rows(audit_path or _AUDIT_PATH)
    row = rows.get(_root(docket.symbol))
    if row is None:
        return docket
    phi = _finite(row.get("phi_cp"))
    omega = _finite(row.get("omega_debt"))
    admitted = bool(row.get("is_admitted"))
    new_phi = phi if phi is not None else docket.blood_purity
    new_omega = omega if omega is not None else docket.debt_toxicity
    still_buyable = admitted and new_phi >= 0.30 and new_omega <= 0.40
    if still_buyable:
        return replace(docket, blood_purity=new_phi, debt_toxicity=new_omega, is_buyable_now=True)
    return replace(
        docket,
        blood_purity=new_phi,
        debt_toxicity=new_omega,
        is_buyable_now=False,
        grade=AdmissionGrade.WATCHLIST,
        current_action_advice="法证体检否决，禁止当作可买，禁止手打与纸上成交",
    )


def docket_as_public_dict(docket: AdmissionDocket) -> Dict[str, Any]:
    """JSON 安全宗卷：枚举写成字符串，前端不得再读本地可买表。"""
    payload = asdict(docket)
    payload["grade"] = docket.grade.value
    payload["horizon"] = docket.horizon.value
    return payload
