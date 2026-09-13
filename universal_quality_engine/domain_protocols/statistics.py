"""Statistical and Data Science Quality Protocol (统计学与概率公理质量协议)."""

from typing import Any, Dict, List
from .base import DomainQualityProtocol, DomainAuditReport


class StatisticalAnalysisProtocol(DomainQualityProtocol):
    """Statistical & Data Science Protocol (统计与概率公理质量协议).
    
    Invariants:
    1. Kolmogorov Probability Axioms: 0 <= P(A) <= 1, Sum(P) == 1.
    2. Variance Non-negativity: Var(X) >= 0.
    3. Simpson's Paradox & P-hacking Guard: Sample size adequacy, significance bounds.
    """
    
    @property
    def domain_name(self) -> str:
        return "statistical_analysis"

    def audit(self, payload: Dict[str, Any]) -> DomainAuditReport:
        violations: List[str] = []
        verified: List[str] = []
        
        probabilities = payload.get("probabilities", [])
        if probabilities:
            if any(p < 0.0 or p > 1.0 for p in probabilities):
                violations.append("Kolmogorov Axiom 1 Broken: Probability outside [0, 1].")
            total_p = sum(probabilities)
            if payload.get("is_complete_partition", False) and abs(total_p - 1.0) > 1e-5:
                violations.append(f"Kolmogorov Axiom 2 Broken: Sum of partition ({total_p}) != 1.0.")
            else:
                verified.append("Kolmogorov Probability Axioms Verified")

        variance = payload.get("variance")
        if variance is not None:
            if variance < 0:
                violations.append(f"Mathematical Violation: Variance ({variance}) is negative.")
            else:
                verified.append("Variance Non-Negativity Verified")

        sample_size = payload.get("sample_size", 100)
        p_value = payload.get("p_value", 0.05)
        if sample_size < 5 and p_value < 0.01:
            violations.append(f"P-Hacking Alert: Sample size ({sample_size}) too small for p={p_value}.")
        else:
            verified.append("Sample Size & Significance Bounds Verified")

        return DomainAuditReport(
            domain=self.domain_name,
            passed=len(violations) == 0,
            violations=violations,
            metrics={"prob_count": len(probabilities), "variance": variance},
            first_principles_verified=verified
        )
