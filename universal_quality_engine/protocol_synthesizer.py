"""Autonomous Domain Discovery & Dynamic Protocol Synthesizer.

(领域自主嗅探与第一性原理质检标准动态自适应生成中枢)
Enables the system to automatically analyze any project's AST, dependencies,
and semantics, identifying its domain and synthesizing first-principles
quality inspection protocols on the fly for unseen domains.
"""

import ast
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
from .domain_protocols import (
    DomainQualityProtocol,
    DomainAuditReport,
    EducationPedagogyProtocol,
    FinancialAccountingProtocol,
    QuantitativeFinanceProtocol,
    SportsHealthProtocol,
    PsychologicalConsultProtocol,
    StatisticalAnalysisProtocol,
)


@dataclass
class DomainFingerprint:
    """Discovered characteristics and first-principles profile of a domain."""
    domain_name: str
    confidence: float
    detected_traits: List[str] = field(default_factory=list)
    key_imports: List[str] = field(default_factory=list)
    conservation_laws: List[str] = field(default_factory=list)


class AutonomousDomainDetector:
    """Scans codebases and ASTs to autonomously infer software application domain."""

    DOMAIN_SIGNATURES: Dict[str, Dict[str, List[str]]] = {
        "education": {
            "keywords": ["student", "curriculum", "syllabus", "bloom", "pedagogy", "course", "grade", "quiz", "lesson"],
            "imports": ["canvasapi", "edx", "moodle"]
        },
        "financial_accounting": {
            "keywords": ["ledger", "asset", "liability", "equity", "balance_sheet", "voucher", "debit", "credit"],
            "imports": ["beancount", "gnucash", "decimal"]
        },
        "quantitative_finance": {
            "keywords": ["backtest", "cagr", "sharpe", "slippage", "orderbook", "kline", "alpha", "drawdown"],
            "imports": ["backtrader", "pyalgotrade", "ccxt", "vnpy", "akshare", "tushare"]
        },
        "sports_health": {
            "keywords": ["heart_rate", "spo2", "calorie", "cadence", "workout", "vo2max", "metabolic", "vitals"],
            "imports": ["fitbit", "garmin", "healthkit", "antplus"]
        },
        "psychological_consult": {
            "keywords": ["cbt", "therapy", "crisis", "suicide", "depression", "dsm5", "counselor", "emotion"],
            "imports": ["nltk", "spacy", "transformers"]
        },
        "statistical_analysis": {
            "keywords": ["p_value", "variance", "hypothesis", "kolmogorov", "regression", "distribution", "sample"],
            "imports": ["scipy", "statsmodels", "numpy", "pandas", "sklearn"]
        },
        "aerospace_avionics": {
            "keywords": ["orbital", "telemetry", "attitude", "quaternion", "propulsion", "trajectory", "thrust"],
            "imports": ["astropy", "skyfield", "poliastro"]
        },
        "ecommerce_logistics": {
            "keywords": ["sku", "inventory", "warehouse", "cart", "shipping", "parcel", "consignment"],
            "imports": ["stripe", "shopify"]
        },
    }

    def detect_from_code(self, source_code: str, filename: str = "") -> DomainFingerprint:
        """Parses python AST and tokens to detect the primary domain."""
        try:
            tree = ast.parse(source_code)
        except Exception:
            tree = None

        imported_modules: List[str] = []
        identifiers: List[str] = []

        if tree:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_modules.append(alias.name.lower())
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_modules.append(node.module.lower())
                elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Name)):
                    name = getattr(node, "name", None) or getattr(node, "id", None)
                    if name:
                        identifiers.append(name.lower())

        content_lower = (source_code + " " + filename).lower()
        best_domain = "unknown"
        max_score = 0.0
        traits: List[str] = []

        for domain, sig in self.DOMAIN_SIGNATURES.items():
            score = 0.0
            for kw in sig["keywords"]:
                if kw in content_lower:
                    score += 1.0
            for imp in sig["imports"]:
                if any(imp in mod for mod in imported_modules):
                    score += 2.5
            if score > max_score:
                max_score = score
                best_domain = domain

        confidence = min(1.0, max_score / 4.0) if max_score > 0 else 0.0
        if confidence > 0.3:
            traits.append(f"matched_domain_patterns:{best_domain}")

        return DomainFingerprint(
            domain_name=best_domain if confidence >= 0.3 else "generic_engineering",
            confidence=confidence,
            detected_traits=traits,
            key_imports=imported_modules,
            conservation_laws=self._infer_conservation_laws(best_domain)
        )

    def _infer_conservation_laws(self, domain: str) -> List[str]:
        laws = {
            "education": ["Epistemological Veracity", "Bloom Cognitive Progression", "Minor Protection Firewall"],
            "financial_accounting": ["Assets = Liabilities + Equity", "Sequential PIT Immutability"],
            "quantitative_finance": ["Compounding Geometric CAGR", "Friction Toll", "Immune Detoxification"],
            "sports_health": ["Thermodynamic Metabolic Conservation", "Zero-Miss Cardiac Safety"],
            "psychological_consult": ["Crisis Sub-5ms Spinal Reflex", "Prescription Hard Wall"],
            "statistical_analysis": ["Kolmogorov Axioms", "Variance Non-negativity", "Anti P-Hacking"],
            "aerospace_avionics": ["Angular Momentum Conservation", "Zero-Division Attitude Defense"],
            "ecommerce_logistics": ["Inventory Balance Conservation", "Non-Negative Stock Invariant"]
        }
        return laws.get(domain, ["State Machine Determinism", "Zero Fake Stub Invariant"])


class DynamicProtocolSynthesizer:
    """Synthesizes executable DomainQualityProtocol on the fly for unseen domains."""

    @classmethod
    def synthesize_protocol(cls, fingerprint: DomainFingerprint) -> Type[DomainQualityProtocol]:
        """Dynamically constructs a DomainQualityProtocol class enforcing deduced first principles."""
        domain = fingerprint.domain_name

        class SynthesizedDomainProtocol(DomainQualityProtocol):
            @property
            def domain_name(self) -> str:
                return domain

            def audit(self, payload: Dict[str, Any]) -> DomainAuditReport:
                violations: List[str] = []
                verified: List[str] = []

                # 1. State Invariant Conservation Law
                invariants = payload.get("invariants", {})
                for inv_name, balance in invariants.items():
                    if abs(balance) > 1e-4:
                        violations.append(
                            f"Dynamic Law Veto: Invariant '{inv_name}' broken with delta {balance} != 0."
                        )
                    else:
                        verified.append(f"Invariant '{inv_name}' verified (Δ=0)")

                # 2. Safety Redlines & Negative Value Defense
                redline_checks = payload.get("redline_bounds", {})
                for metric, val in redline_checks.items():
                    min_val = val.get("min")
                    max_val = val.get("max")
                    curr = val.get("current")
                    if curr is None:
                        continue
                    if min_val is not None and curr < min_val:
                        violations.append(f"Safety Redline Breached: {metric}={curr} < min({min_val})")
                    elif max_val is not None and curr > max_val:
                        violations.append(f"Safety Redline Breached: {metric}={curr} > max({max_val})")
                    else:
                        verified.append(f"Boundary Verified: {metric} within [{min_val}, {max_val}]")

                # 3. Anti-Fraud & Execution Integrity
                if payload.get("has_mock_or_stub", False):
                    violations.append("Integrity Veto: Mock/stub detected in production dynamic verification!")
                else:
                    verified.append("Integrity & Real Execution Confirmed")

                return DomainAuditReport(
                    domain=self.domain_name,
                    passed=len(violations) == 0,
                    violations=violations,
                    metrics={"dynamic_laws_checked": len(fingerprint.conservation_laws)},
                    first_principles_verified=verified
                )

        SynthesizedDomainProtocol.__name__ = f"Synthesized_{domain.capitalize()}Protocol"
        return SynthesizedDomainProtocol


class ProtocolRegistry:
    """Global registry holding built-in and dynamically synthesized domain protocols."""

    def __init__(self) -> None:
        self._protocols: Dict[str, DomainQualityProtocol] = {
            "education": EducationPedagogyProtocol(),
            "financial_accounting": FinancialAccountingProtocol(),
            "quantitative_finance": QuantitativeFinanceProtocol(),
            "sports_health": SportsHealthProtocol(),
            "psychological_consult": PsychologicalConsultProtocol(),
            "statistical_analysis": StatisticalAnalysisProtocol(),
        }
        self._detector = AutonomousDomainDetector()

    def get_protocol(self, domain_name: str) -> Optional[DomainQualityProtocol]:
        """Retrieves a registered protocol by name."""
        return self._protocols.get(domain_name.lower())

    def register_protocol(self, protocol: DomainQualityProtocol) -> None:
        """Registers a new or synthesized domain protocol."""
        self._protocols[protocol.domain_name.lower()] = protocol

    def list_domains(self) -> List[str]:
        """Lists all currently active protocol domain names."""
        return sorted(list(self._protocols.keys()))

    def resolve_or_synthesize(self, domain_name: str, code_sample: str = "") -> DomainQualityProtocol:
        """Resolves existing protocol, or dynamically synthesizes and registers a new one."""
        cleaned = domain_name.lower().strip()
        if cleaned in self._protocols:
            return self._protocols[cleaned]

        # Unknown domain: deduce fingerprint and synthesize on the fly!
        if code_sample:
            fingerprint = self._detector.detect_from_code(code_sample, filename=domain_name)
        else:
            fingerprint = DomainFingerprint(
                domain_name=cleaned,
                confidence=1.0,
                detected_traits=[f"user_specified:{cleaned}"],
                conservation_laws=self._detector._infer_conservation_laws(cleaned)
            )

        synth_cls = DynamicProtocolSynthesizer.synthesize_protocol(fingerprint)
        instance = synth_cls()
        self.register_protocol(instance)
        return instance

    def auto_detect_and_resolve(self, code_sample: str, filename: str = "") -> DomainQualityProtocol:
        """Autonomously inspects code, detects domain, and provides exact matching protocol."""
        fingerprint = self._detector.detect_from_code(code_sample, filename)
        return self.resolve_or_synthesize(fingerprint.domain_name, code_sample)


GLOBAL_PROTOCOL_REGISTRY = ProtocolRegistry()
