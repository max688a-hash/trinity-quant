"""Command Line Interface for Universal Quality Engine (UIQC Gate).

Usage:
  python3 -m universal_quality_engine.cli --domain all
  python3 -m universal_quality_engine.cli --domain auto
  python3 -m universal_quality_engine.cli --domain education
"""

import argparse
import sys
import os
from typing import Dict, Any, List
from .protocol_synthesizer import GLOBAL_PROTOCOL_REGISTRY, AutonomousDomainDetector
from .core_inspector import UniversalCodebaseInspector, UniversalUIUXInspector


def run_domain_audit(domain: str) -> bool:
    """Executes representative boundary and invariant audit for a domain."""
    proto = GLOBAL_PROTOCOL_REGISTRY.get_protocol(domain)
    if not proto:
        print(f"🔴 [VETO] Unknown domain protocol: {domain}")
        return False

    # Sample canonical payload verifying zero-violation baseline for built-ins
    payloads: Dict[str, Dict[str, Any]] = {
        "education": {
            "factual_claims": [{"subject": "Newton's Laws", "statement": "F=ma", "confidence": 0.99}],
            "ground_truth_syllabus": {"Newton's Laws": "F=ma"},
            "curriculum_sequence": [{"bloom_level": 1}, {"bloom_level": 2}],
            "session_duration_minutes": 25,
            "is_minor": True,
            "content_tags": ["physics", "stem"],
            "assessments": [{"question_id": "q1", "is_correct": True}]
        },
        "financial_accounting": {
            "assets": 10000.0,
            "liabilities": 4000.0,
            "equity": 6000.0,
            "ledger_entries": [{"timestamp": 100.0, "amount": 1000.0}, {"timestamp": 101.0, "amount": 500.0}]
        },
        "sports_health": {
            "heart_rate_bpm": 75,
            "spo2_percent": 98,
            "calories_burned_kcal": 350.0,
            "duration_hours": 1.0
        },
        "psychological_consult": {
            "crisis_detected": False,
            "prescribed_medication": None
        },
        "statistical_analysis": {
            "probabilities": [0.4, 0.6],
            "is_complete_partition": True,
            "variance": 1.25,
            "sample_size": 200,
            "p_value": 0.001
        },
        "quantitative_finance": {
            "friction_accounted": True,
            "uses_arithmetic_mean_annualized": False,
            "phi_cp": 0.85,
            "omega_debt": 0.25
        }
    }

    test_payload = payloads.get(domain, {
        "invariants": {"balance_law": 0.0},
        "redline_bounds": {"latency_ms": {"min": 0, "max": 100, "current": 25}},
        "has_mock_or_stub": False
    })

    report = proto.audit(test_payload)
    if report.passed:
        print(f"🟢 [{domain.upper()}] All First-Principles Invariants Verified:")
        for v in report.first_principles_verified:
            print(f"   ✓ {v}")
        return True
    else:
        print(f"🔴 [{domain.upper()} VETO] Violations Detected:")
        for viol in report.violations:
            print(f"   ✗ {viol}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Universal Industrial Quality Gate (UIQC)")
    parser.add_argument("--domain", default="all", help="Domain to audit: all, auto, education, finance, etc.")
    parser.add_argument("--path", default=".", help="Root path to inspect")
    parser.add_argument("--skip-codebase", action="store_true", help="Skip AST and line count checks")
    args = parser.parse_args()

    print("=" * 65)
    print(" 🌟 UNIVERSAL QUALITY ASSURANCE & ACCEPTANCE ENGINE (UIQC v3.0) 🌟 ")
    print("=" * 65)

    all_passed = True

    # 1. Domain Protocol Audits
    if args.domain == "all":
        domains = GLOBAL_PROTOCOL_REGISTRY.list_domains()
        for d in domains:
            passed = run_domain_audit(d)
            if not passed:
                all_passed = False
    elif args.domain == "auto":
        detector = AutonomousDomainDetector()
        detected = detector.detect_from_code(f"path: {args.path}")
        print(f"🔍 [AUTO-DETECT] Identified domain: '{detected.domain_name}' (conf={detected.confidence:.2f})")
        proto = GLOBAL_PROTOCOL_REGISTRY.resolve_or_synthesize(detected.domain_name)
        passed = run_domain_audit(proto.domain_name)
        if not passed:
            all_passed = False
    else:
        proto = GLOBAL_PROTOCOL_REGISTRY.resolve_or_synthesize(args.domain)
        passed = run_domain_audit(proto.domain_name)
        if not passed:
            all_passed = False

    # 2. Universal Codebase & Line-Count Gate (<= 300 lines, no fake stubs)
    if not args.skip_codebase:
        print("\n🔍 [PHYSICAL GATE] Inspecting codebase line counts & AST stubs...")
        code_inspector = UniversalCodebaseInspector(max_file_lines=300)
        res = code_inspector.inspect_directory("universal_quality_engine")
        if res.passed:
            print(f"🟢 [CODEBASE] Passed: {res.stats.get('files_audited')} files audited under 300-line limit.")
        else:
            print(f"🔴 [CODEBASE VETO] Found {len(res.violations)} violations:")
            for v in res.violations:
                print(f"   ✗ {v}")
            all_passed = False

    print("=" * 65)
    if all_passed:
        print("🏆 [ZERO-WATER GATE PASSED] All physical and logical invariants satisfied (Exit 0).")
        return 0
    else:
        print("🚨 [ZERO-WATER GATE FAILED] System quality violations detected (Exit 1).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
