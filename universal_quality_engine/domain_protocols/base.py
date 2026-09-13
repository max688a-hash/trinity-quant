"""Base domain quality protocol definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DomainAuditReport:
    """Standardized domain audit report across all disciplines."""
    domain: str
    passed: bool
    violations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    first_principles_verified: List[str] = field(default_factory=list)


class DomainQualityProtocol(ABC):
    """Abstract base class for all domain-specific physical/logical quality protocols."""
    
    @property
    @abstractmethod
    def domain_name(self) -> str:
        """The canonical name of the domain."""
        pass

    @abstractmethod
    def audit(self, payload: Dict[str, Any]) -> DomainAuditReport:
        """Audits domain state/data against invariant physical & logical conservation laws."""
        pass
