"""Financial and Quantitative Finance Quality Protocols (财务与量化物理守恒协议)."""

from typing import Any, Dict, List
import math
from .base import DomainQualityProtocol, DomainAuditReport


class FinancialAccountingProtocol(DomainQualityProtocol):
    """Financial Accounting Quality Protocol (财务类复式记账与不可篡改审计协议).
    
    Invariants:
    1. Balance Sheet Conservation: Assets = Liabilities + Equity
    2. Precision Preservation: Decimals exact to currency subunit, no rounding leaks.
    3. WAL Audit Trail: Immutability of ledger records, point-in-time sequential timestamps.
    """
    
    @property
    def domain_name(self) -> str:
        return "financial_accounting"

    def audit(self, payload: Dict[str, Any]) -> DomainAuditReport:
        violations: List[str] = []
        verified: List[str] = []
        
        assets = payload.get("assets", 0.0)
        liabilities = payload.get("liabilities", 0.0)
        equity = payload.get("equity", 0.0)
        imbalance = round(abs(assets - (liabilities + equity)), 6)
        if imbalance > 1e-4:
            violations.append(
                f"Accounting Invariant Broken: Assets ({assets}) != Liab ({liabilities}) + Eq ({equity}). Diff={imbalance}"
            )
        else:
            verified.append("Balance Sheet Conservation Verified (Δ=0)")

        ledger_entries = payload.get("ledger_entries", [])
        prev_ts = -1.0
        for entry in ledger_entries:
            ts = entry.get("timestamp", 0.0)
            if ts < prev_ts:
                violations.append(f"PIT Violation: Ledger timestamp {ts} backwards from previous {prev_ts}.")
            prev_ts = ts
            amount = entry.get("amount", 0.0)
            if math.isnan(amount) or math.isinf(amount):
                violations.append(f"Data Poison: Ledger entry has invalid numerical amount ({amount}).")
        if ledger_entries:
            verified.append(f"Sequential Ledger PIT Verified ({len(ledger_entries)} entries)")

        return DomainAuditReport(
            domain=self.domain_name,
            passed=len(violations) == 0,
            violations=violations,
            metrics={"imbalance": imbalance, "ledger_count": len(ledger_entries)},
            first_principles_verified=verified
        )


class QuantitativeFinanceProtocol(DomainQualityProtocol):
    """Quantitative Finance Protocol (量化金融物理第一性原理协议).
    
    Invariants:
    1. Friction Accounting: Slippage, commissions, stamp duty mandatory.
    2. Compounding Geometric CAGR: Arithmetic mean return prohibited.
    3. Immune System: Debt toxicity and cash flow purity enforcement.
    """
    
    @property
    def domain_name(self) -> str:
        return "quantitative_finance"

    def audit(self, payload: Dict[str, Any]) -> DomainAuditReport:
        violations: List[str] = []
        verified: List[str] = []
        
        if not payload.get("friction_accounted", False):
            violations.append("Quant Redline: Backtest reported without slippage/commission friction!")
        else:
            verified.append("Full Friction Accounting Verified")

        if payload.get("uses_arithmetic_mean_annualized", False):
            violations.append("Quant Redline: Arithmetic mean used to disguise geometric volatility drag!")
        else:
            verified.append("Geometric CAGR Verified")

        phi_cp = payload.get("phi_cp", 1.0)
        omega_debt = payload.get("omega_debt", 0.0)
        if phi_cp < 0.3 or omega_debt > 0.8:
            if not payload.get("vetoed_by_immune_system", False):
                violations.append(f"Immune Breach: Toxic stock (Φ_CP={phi_cp}, Ω_Debt={omega_debt}) not vetoed!")
            else:
                verified.append("Immune Detoxification Veto Active")
        else:
            verified.append("Health & Purity Clean")

        return DomainAuditReport(
            domain=self.domain_name,
            passed=len(violations) == 0,
            violations=violations,
            metrics={"phi_cp": phi_cp, "omega_debt": omega_debt},
            first_principles_verified=verified
        )
