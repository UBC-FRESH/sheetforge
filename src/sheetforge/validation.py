"""Validation report records.

These objects describe validation results; they do not run workbook or generated
model comparisons themselves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


JsonValue = str | int | float | bool | None | list[Any] | dict[str, Any]
OutputKind = Literal["number", "text", "boolean", "blank", "error"]
ReportStatus = Literal["pass", "fail"]
DiagnosticSeverity = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class Diagnostic:
    """Run-level diagnostic not tied to one output comparison."""

    diagnostic_code: str
    message: str
    severity: DiagnosticSeverity = "warning"
    location: str | None = None

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "diagnostic_code": self.diagnostic_code,
            "message": self.message,
            "severity": self.severity,
            "location": self.location,
        }


@dataclass(frozen=True)
class ComparisonResult:
    """Comparison result for one declared workbook output."""

    scenario_id: str
    cell_ref: str
    kind: OutputKind
    generated: JsonValue
    oracle: JsonValue
    matches: bool
    tolerance: float | None
    difference: float | None
    diagnostic_code: str | None
    message: str
    oracle_backend: str

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "scenario_id": self.scenario_id,
            "cell_ref": self.cell_ref,
            "kind": self.kind,
            "generated": self.generated,
            "oracle": self.oracle,
            "matches": self.matches,
            "tolerance": self.tolerance,
            "difference": self.difference,
            "diagnostic_code": self.diagnostic_code,
            "message": self.message,
            "oracle_backend": self.oracle_backend,
        }


@dataclass(frozen=True)
class ValidationReport:
    """Validation report for one scenario."""

    scenario_id: str
    oracle_backend: str
    comparisons: tuple[ComparisonResult, ...] = field(default_factory=tuple)
    diagnostics: tuple[Diagnostic, ...] = field(default_factory=tuple)

    @property
    def mismatches(self) -> tuple[ComparisonResult, ...]:
        return tuple(comparison for comparison in self.comparisons if not comparison.matches)

    @property
    def status(self) -> ReportStatus:
        if self.mismatches or any(diagnostic.severity == "error" for diagnostic in self.diagnostics):
            return "fail"
        return "pass"

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "scenario_id": self.scenario_id,
            "oracle_backend": self.oracle_backend,
            "status": self.status,
            "comparisons": [comparison.to_dict() for comparison in self.comparisons],
            "mismatches": [comparison.to_dict() for comparison in self.mismatches],
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }
