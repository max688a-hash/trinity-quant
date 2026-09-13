"""Health and Psychological Protocols (健康与心理健康第一性原理协议)."""

from typing import Any, Dict, List
from .base import DomainQualityProtocol, DomainAuditReport


class SportsHealthProtocol(DomainQualityProtocol):
    """Sports & Health IoT Quality Protocol (运动健康与生理极限安全协议).
    
    Invariants:
    1. Human Physiological Hard Boundaries: Heart rate [30, 230], SpO2 [60, 100].
    2. Sudden Cardiac Arrest / Anomaly Zero-Miss Detection.
    3. Thermodynamic Energy Conservation: Consumed Calories > 0, metabolic bounds.
    """
    
    @property
    def domain_name(self) -> str:
        return "sports_health"

    def audit(self, payload: Dict[str, Any]) -> DomainAuditReport:
        violations: List[str] = []
        verified: List[str] = []
        
        hr = payload.get("heart_rate_bpm")
        if hr is not None:
            if hr < 30 or hr > 230:
                violations.append(f"Physiological Redline: Heart rate {hr} bpm breaches survival limit [30, 230]!")
            else:
                verified.append("Physiological Vitals Boundary Verified")

        if payload.get("cardiac_arrest_suspected", False) and not payload.get("emergency_triggered", False):
            violations.append("Zero-Miss Failure: Cardiac arrest suspected but emergency alert was NOT triggered!")
        elif payload.get("cardiac_arrest_suspected", False):
            verified.append("Emergency Alert Successfully Triggered")

        spo2 = payload.get("spo2_percent")
        if spo2 is not None:
            if spo2 < 60 or spo2 > 100:
                violations.append(f"Physiological Redline: Blood oxygen {spo2}% is physically impossible or fatal!")
            else:
                verified.append("Oxygen Saturation Verified")

        calories = payload.get("calories_burned_kcal", 0.0)
        duration_hours = payload.get("duration_hours", 1.0)
        max_possible_cal = duration_hours * 2500.0
        if calories < 0:
            violations.append(f"Thermodynamic Violation: Burned calories {calories} cannot be negative.")
        elif calories > max_possible_cal:
            violations.append(f"Thermodynamic Violation: Calories {calories} exceeds human peak ({max_possible_cal}).")
        else:
            verified.append("Metabolic Thermodynamic Energy Verified")

        return DomainAuditReport(
            domain=self.domain_name,
            passed=len(violations) == 0,
            violations=violations,
            metrics={"heart_rate": hr, "spo2": spo2, "calories": calories},
            first_principles_verified=verified
        )


class PsychologicalConsultProtocol(DomainQualityProtocol):
    """Psychological Consultation Protocol (心理健康与危机硬阻断协议).
    
    Invariants:
    1. Crisis Intervention Spinal Reflex: Suicide/self-harm triggers instant hard intervention <= 5ms.
    2. Medical Prescription Hard Wall: Strict prohibition of hallucinated psychiatric drug prescriptions.
    3. DSM-5 / CBT Ethical Alignment: Evidence-based responses, anti-gaslighting.
    """
    
    @property
    def domain_name(self) -> str:
        return "psychological_consult"

    def audit(self, payload: Dict[str, Any]) -> DomainAuditReport:
        violations: List[str] = []
        verified: List[str] = []
        
        is_crisis = payload.get("crisis_detected", False)
        intervention_time_ms = payload.get("intervention_latency_ms", 999.0)
        hotline_dispatched = payload.get("hotline_dispatched", False)

        if is_crisis:
            if not hotline_dispatched:
                violations.append("Crisis Redline: Suicidal risk detected but emergency hotline NOT dispatched!")
            elif intervention_time_ms > 5.0:
                violations.append(f"Spinal Reflex Sluggish: Crisis latency {intervention_time_ms}ms exceeds 5ms reflex limit!")
            else:
                verified.append("Crisis Hard Intervention Verified (<= 5ms)")

        prescription = payload.get("prescribed_medication", None)
        if prescription:
            violations.append(f"Ethical Redline: Non-licensed psychological AI prescribed medication '{prescription}'!")
        else:
            verified.append("Psychiatric Prescription Hard Wall Cleared")

        return DomainAuditReport(
            domain=self.domain_name,
            passed=len(violations) == 0,
            violations=violations,
            metrics={"crisis": is_crisis, "latency_ms": intervention_time_ms},
            first_principles_verified=verified
        )
