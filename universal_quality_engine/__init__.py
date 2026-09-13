"""Universal Quality Assurance & Acceptance Engine (UIQC Engine).

Export public APIs for domain-agnostic and domain-specific quality inspection.
"""

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
from .protocol_synthesizer import (
    AutonomousDomainDetector,
    DynamicProtocolSynthesizer,
    ProtocolRegistry,
    DomainFingerprint,
    GLOBAL_PROTOCOL_REGISTRY,
)
from .core_inspector import (
    UniversalCodebaseInspector,
    UniversalUIUXInspector,
    InspectionResult,
)

__all__ = [
    "DomainQualityProtocol",
    "DomainAuditReport",
    "EducationPedagogyProtocol",
    "FinancialAccountingProtocol",
    "QuantitativeFinanceProtocol",
    "SportsHealthProtocol",
    "PsychologicalConsultProtocol",
    "StatisticalAnalysisProtocol",
    "AutonomousDomainDetector",
    "DynamicProtocolSynthesizer",
    "ProtocolRegistry",
    "DomainFingerprint",
    "GLOBAL_PROTOCOL_REGISTRY",
    "UniversalCodebaseInspector",
    "UniversalUIUXInspector",
    "InspectionResult",
]
