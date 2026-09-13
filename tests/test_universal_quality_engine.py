"""Comprehensive Test Suite for Universal Quality Engine (UIQC v3.0).

Tests:
1. Education Pedagogy first principles (veracity, scaffolding, minor safety, feedback).
2. Financial, Sports Health, Psychology, Statistics, and Quant protocols.
3. Dynamic domain discovery and autonomous protocol synthesis on unseen domains.
4. Universal codebase & UI/UX inspectors.
"""

import unittest
from universal_quality_engine.domain_protocols import (
    EducationPedagogyProtocol,
    FinancialAccountingProtocol,
    SportsHealthProtocol,
    PsychologicalConsultProtocol,
    StatisticalAnalysisProtocol,
    QuantitativeFinanceProtocol,
)
from universal_quality_engine.protocol_synthesizer import (
    AutonomousDomainDetector,
    DynamicProtocolSynthesizer,
    ProtocolRegistry,
)
from universal_quality_engine.core_inspector import (
    UniversalCodebaseInspector,
    UniversalUIUXInspector,
)


class TestUniversalQualityEngine(unittest.TestCase):
    """Zero-water physical unit tests for UIQC engine across multiple disciplines."""

    def setUp(self) -> None:
        self.edu_proto = EducationPedagogyProtocol()
        self.fin_proto = FinancialAccountingProtocol()
        self.health_proto = SportsHealthProtocol()
        self.psych_proto = PsychologicalConsultProtocol()
        self.stat_proto = StatisticalAnalysisProtocol()
        self.quant_proto = QuantitativeFinanceProtocol()
        self.detector = AutonomousDomainDetector()
        self.registry = ProtocolRegistry()

    # --- 1. Education Protocol Tests ---
    def test_education_happy_path(self) -> None:
        payload = {
            "factual_claims": [{"subject": "Math", "statement": "2+2=4", "confidence": 0.99}],
            "ground_truth_syllabus": {"Math": "2+2=4"},
            "curriculum_sequence": [{"bloom_level": 1}, {"bloom_level": 2}],
            "session_duration_minutes": 30,
            "is_minor": True,
            "content_tags": ["math"],
            "assessments": [{"question_id": "q1", "is_correct": False, "diagnostic_hint": "Check addition table"}]
        }
        report = self.edu_proto.audit(payload)
        self.assertTrue(report.passed)
        self.assertIn("Bloom Cognitive Scaffolding Verified", report.first_principles_verified)

    def test_education_hallucination_and_scaffolding_veto(self) -> None:
        payload = {
            "factual_claims": [{"subject": "History", "statement": "Moon is cheese", "confidence": 0.5}],
            "ground_truth_syllabus": {"History": "Moon is rock"},
            "curriculum_sequence": [{"bloom_level": 1}, {"bloom_level": 4, "has_scaffolding": False}],
            "session_duration_minutes": 60,
            "is_minor": True,
            "content_tags": ["gambling"]
        }
        report = self.edu_proto.audit(payload)
        self.assertFalse(report.passed)
        self.assertTrue(any("Fact Hallucination" in v or "Veracity Veto" in v for v in report.violations))
        self.assertTrue(any("Pedagogical Veto" in v for v in report.violations))
        self.assertTrue(any("Minor Safety Veto" in v for v in report.violations))
        self.assertTrue(any("Minor Protection Veto" in v for v in report.violations))

    # --- 2. Accounting & Health & Psych Tests ---
    def test_accounting_balance_invariant(self) -> None:
        bad_payload = {"assets": 1000.0, "liabilities": 500.0, "equity": 200.0}
        report = self.fin_proto.audit(bad_payload)
        self.assertFalse(report.passed)
        self.assertIn("Accounting Invariant Broken", report.violations[0])

    def test_sports_health_zero_miss_emergency(self) -> None:
        alert_payload = {
            "heart_rate_bpm": 240,
            "spo2_percent": 55,
            "cardiac_arrest_suspected": True,
            "emergency_triggered": False
        }
        report = self.health_proto.audit(alert_payload)
        self.assertFalse(report.passed)
        self.assertTrue(any("Physiological Redline" in v for v in report.violations))
        self.assertTrue(any("Zero-Miss Failure" in v for v in report.violations))

    def test_psychological_crisis_and_prescription(self) -> None:
        crisis_payload = {
            "crisis_detected": True,
            "intervention_latency_ms": 12.0,  # Sluggish > 5ms
            "hotline_dispatched": True,
            "prescribed_medication": "Alprazolam"
        }
        report = self.psych_proto.audit(crisis_payload)
        self.assertFalse(report.passed)
        self.assertTrue(any("Spinal Reflex Sluggish" in v for v in report.violations))
        self.assertTrue(any("Ethical Redline" in v for v in report.violations))

    # --- 3. Statistical & Quant Tests ---
    def test_statistical_kolmogorov_violation(self) -> None:
        payload = {"probabilities": [0.6, 0.7], "is_complete_partition": True, "variance": -1.0}
        report = self.stat_proto.audit(payload)
        self.assertFalse(report.passed)
        self.assertTrue(any("Kolmogorov Axiom 2 Broken" in v for v in report.violations))
        self.assertTrue(any("Mathematical Violation: Variance" in v for v in report.violations))

    def test_quant_friction_and_arithmetic_disguise(self) -> None:
        payload = {"friction_accounted": False, "uses_arithmetic_mean_annualized": True}
        report = self.quant_proto.audit(payload)
        self.assertFalse(report.passed)
        self.assertTrue(any("friction" in v.lower() for v in report.violations))
        self.assertTrue(any("arithmetic mean" in v.lower() for v in report.violations))

    # --- 4. Autonomous Discovery & Dynamic Synthesis ---
    def test_unseen_domain_auto_detection_and_synthesis(self) -> None:
        novel_code = """
import astropy
class SatelliteTrajectory:
    def calculate_orbit(self, altitude_km):
        quaternion = [1, 0, 0, 0]
        telemetry = "nominal"
        thrust = 500.0
        return quaternion
"""
        fingerprint = self.detector.detect_from_code(novel_code, "flight_controller.py")
        self.assertEqual(fingerprint.domain_name, "aerospace_avionics")
        self.assertIn("Angular Momentum Conservation", fingerprint.conservation_laws)

        # Synthesize protocol dynamically
        proto = self.registry.resolve_or_synthesize("aerospace_avionics", novel_code)
        self.assertEqual(proto.domain_name, "aerospace_avionics")

        # Test audit on dynamic protocol
        valid_payload = {
            "invariants": {"momentum_conservation": 0.0},
            "redline_bounds": {"telemetry_jitter": {"min": 0, "max": 10, "current": 2}},
            "has_mock_or_stub": False
        }
        report = proto.audit(valid_payload)
        self.assertTrue(report.passed)

        invalid_payload = {
            "invariants": {"momentum_conservation": 15.4},
            "has_mock_or_stub": True
        }
        bad_report = proto.audit(invalid_payload)
        self.assertFalse(bad_report.passed)
        self.assertTrue(any("Dynamic Law Veto" in v for v in bad_report.violations))
        self.assertTrue(any("Integrity Veto" in v for v in bad_report.violations))

    # --- 5. Codebase & UI Inspectors ---
    def test_codebase_and_ui_inspectors(self) -> None:
        code_inspector = UniversalCodebaseInspector(max_file_lines=300)
        # Test line-count and fake-stub detection
        fake_code = "def fake():\n    pass\n"
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(fake_code)
            tf_name = tf.name
        
        res = code_inspector.inspect_file(tf_name)
        self.assertFalse(res.passed)
        self.assertTrue(any("Fake Stub Veto" in v for v in res.violations))

        # Test UI/UX inspector
        ui_inspector = UniversalUIUXInspector()
        bad_html = "<html><body><script>window.addEventListener('touchmove', e => e.preventDefault());</script></body></html>"
        ui_res = ui_inspector.inspect_html(bad_html)
        self.assertFalse(ui_res.passed)
        self.assertTrue(any("touchmove preventDefault()" in v for v in ui_res.violations))


if __name__ == "__main__":
    unittest.main()
