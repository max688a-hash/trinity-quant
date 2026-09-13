"""Domain quality protocols package."""

from .base import DomainQualityProtocol, DomainAuditReport
from .education import EducationPedagogyProtocol
from .finance import FinancialAccountingProtocol, QuantitativeFinanceProtocol
from .health_mind import SportsHealthProtocol, PsychologicalConsultProtocol
from .statistics import StatisticalAnalysisProtocol

__all__ = [
    "DomainQualityProtocol",
    "DomainAuditReport",
    "EducationPedagogyProtocol",
    "FinancialAccountingProtocol",
    "QuantitativeFinanceProtocol",
    "SportsHealthProtocol",
    "PsychologicalConsultProtocol",
    "StatisticalAnalysisProtocol",
]
