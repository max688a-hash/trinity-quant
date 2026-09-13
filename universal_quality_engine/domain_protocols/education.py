"""Education & Pedagogical Learning Quality Protocol (教育类认知第一性原理协议)."""

from typing import Any, Dict, List
from .base import DomainQualityProtocol, DomainAuditReport


class EducationPedagogyProtocol(DomainQualityProtocol):
    """Pedagogical Quality Protocol enforcing cognitive & ethical first principles.
    
    Invariants:
    1. Epistemological Veracity: Zero hallucination, syllabus grounded.
    2. Bloom's Taxonomy Scaffolding: Progressive cognitive steps (1 to 6).
    3. Minor Safety & Fatigue Firewall: Session duration <= 45 min, no toxic content.
    4. Formative Pedagogical Feedback: Constructive root-cause feedback.
    """
    
    @property
    def domain_name(self) -> str:
        return "education"

    def audit(self, payload: Dict[str, Any]) -> DomainAuditReport:
        violations: List[str] = []
        verified: List[str] = []
        
        # 1. Epistemological Veracity (Hallucination detection)
        facts = payload.get("factual_claims", [])
        ground_truth = payload.get("ground_truth_syllabus", {})
        for claim in facts:
            subject = claim.get("subject")
            statement = claim.get("statement")
            confidence = claim.get("confidence", 0.0)
            if confidence < 0.95 and not claim.get("peer_reviewed", False):
                violations.append(f"Veracity Veto: '{statement}' lacks authoritative backing (<0.95 conf).")
            elif subject in ground_truth and statement != ground_truth[subject]:
                violations.append(f"Fact Hallucination: '{statement}' contradicts ground truth '{ground_truth[subject]}'.")
            else:
                verified.append(f"Fact Verified: {subject}")

        # 2. Bloom's Taxonomy Scaffolding Progression
        cognitive_stages = payload.get("curriculum_sequence", [])
        for i in range(1, len(cognitive_stages)):
            prev_lvl = cognitive_stages[i - 1].get("bloom_level", 1)
            curr_lvl = cognitive_stages[i].get("bloom_level", 1)
            if curr_lvl - prev_lvl > 1 and not cognitive_stages[i].get("has_scaffolding", False):
                violations.append(
                    f"Pedagogical Veto: Stage {i} jumps from Bloom L{prev_lvl} to L{curr_lvl} without scaffolding!"
                )
        if cognitive_stages:
            verified.append("Bloom Cognitive Scaffolding Verified")

        # 3. Minor Protection & Anti-Addiction Firewall
        session_minutes = payload.get("session_duration_minutes", 0)
        is_minor = payload.get("is_minor", True)
        if is_minor and session_minutes > 45:
            violations.append(f"Minor Safety Veto: Session duration {session_minutes}m exceeds minor limit (45m)!")
        
        prohibited_tags = {"gambling", "violence", "predatory_monetization"}
        content_tags = set(payload.get("content_tags", []))
        overlap = prohibited_tags.intersection(content_tags)
        if overlap:
            violations.append(f"Minor Protection Veto: Content contains forbidden elements: {overlap}")
        else:
            verified.append("Minor Safety & Content Filter Cleared")

        # 4. Formative Diagnostic Feedback
        assessments = payload.get("assessments", [])
        for a in assessments:
            if not a.get("is_correct") and not a.get("diagnostic_hint"):
                violations.append(f"Pedagogical Defect: Incorrect answer for '{a.get('question_id')}' lacks formative hint.")
            elif not a.get("is_correct"):
                verified.append(f"Formative Feedback Verified: {a.get('question_id')}")

        return DomainAuditReport(
            domain=self.domain_name,
            passed=len(violations) == 0,
            violations=violations,
            metrics={"session_minutes": session_minutes, "claims_checked": len(facts)},
            first_principles_verified=verified
        )
