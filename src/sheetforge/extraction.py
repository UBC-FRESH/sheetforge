"""Workbook extraction records.

These records describe extracted workbook facts; they do not read workbook
files themselves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


JsonValue = str | int | float | bool | None | list[Any] | dict[str, Any]
CellKind = Literal["value", "formula", "blank", "error"]
DiagnosticSeverity = Literal["info", "warning", "error"]
NamedRangeStatus = Literal["resolved", "partially_resolved", "unresolved"]


@dataclass(frozen=True)
class ExtractionDiagnostic:
    """Extraction or interpretation concern tied to workbook provenance."""

    code: str
    message: str
    severity: DiagnosticSeverity = "warning"
    location: str | None = None
    raw_value: JsonValue = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtractionDiagnostic":
        return cls(
            code=data["code"],
            message=data["message"],
            severity=data.get("severity", "warning"),
            location=data.get("location"),
            raw_value=data.get("raw_value"),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "location": self.location,
            "raw_value": self.raw_value,
        }


@dataclass(frozen=True)
class FormulaRecord:
    """Formula text and parsed extraction facts for one formula cell."""

    raw_formula: str
    tokens: tuple[str, ...] = field(default_factory=tuple)
    raw_references: tuple[str, ...] = field(default_factory=tuple)
    normalized_references: tuple[str, ...] = field(default_factory=tuple)
    functions: tuple[str, ...] = field(default_factory=tuple)
    diagnostics: tuple[ExtractionDiagnostic, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FormulaRecord":
        return cls(
            raw_formula=data["raw_formula"],
            tokens=tuple(data.get("tokens", [])),
            raw_references=tuple(data.get("raw_references", [])),
            normalized_references=tuple(data.get("normalized_references", [])),
            functions=tuple(data.get("functions", [])),
            diagnostics=tuple(ExtractionDiagnostic.from_dict(item) for item in data.get("diagnostics", [])),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "raw_formula": self.raw_formula,
            "tokens": list(self.tokens),
            "raw_references": list(self.raw_references),
            "normalized_references": list(self.normalized_references),
            "functions": list(self.functions),
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }


@dataclass(frozen=True)
class CellRecord:
    """Extracted cell facts for one canonical workbook cell reference."""

    cell_ref: str
    kind: CellKind
    raw_value: JsonValue
    data_type: str | None = None
    cached_value: JsonValue = None
    formula: FormulaRecord | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CellRecord":
        formula_data = data.get("formula")
        return cls(
            cell_ref=data["cell_ref"],
            kind=data["kind"],
            raw_value=data.get("raw_value"),
            data_type=data.get("data_type"),
            cached_value=data.get("cached_value"),
            formula=FormulaRecord.from_dict(formula_data) if formula_data is not None else None,
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "cell_ref": self.cell_ref,
            "kind": self.kind,
            "raw_value": self.raw_value,
            "data_type": self.data_type,
            "cached_value": self.cached_value,
            "formula": self.formula.to_dict() if self.formula is not None else None,
        }


@dataclass(frozen=True)
class NamedRangeRecord:
    """Workbook or worksheet scoped defined name."""

    name: str
    scope: str
    raw_definition: str
    destinations: tuple[str, ...] = field(default_factory=tuple)
    status: NamedRangeStatus = "unresolved"
    diagnostics: tuple[ExtractionDiagnostic, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NamedRangeRecord":
        return cls(
            name=data["name"],
            scope=data["scope"],
            raw_definition=data["raw_definition"],
            destinations=tuple(data.get("destinations", [])),
            status=data.get("status", "unresolved"),
            diagnostics=tuple(ExtractionDiagnostic.from_dict(item) for item in data.get("diagnostics", [])),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "name": self.name,
            "scope": self.scope,
            "raw_definition": self.raw_definition,
            "destinations": list(self.destinations),
            "status": self.status,
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }


@dataclass(frozen=True)
class SheetRecord:
    """Worksheet identity and ordering facts."""

    sheet_id: str
    title: str
    state: str
    index: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SheetRecord":
        return cls(
            sheet_id=data["sheet_id"],
            title=data["title"],
            state=data["state"],
            index=data["index"],
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "sheet_id": self.sheet_id,
            "title": self.title,
            "state": self.state,
            "index": self.index,
        }


@dataclass(frozen=True)
class WorkbookRecord:
    """Extracted facts for one source workbook."""

    workbook_id: str
    source_path: str
    sheets: tuple[SheetRecord, ...] = field(default_factory=tuple)
    cells: tuple[CellRecord, ...] = field(default_factory=tuple)
    named_ranges: tuple[NamedRangeRecord, ...] = field(default_factory=tuple)
    diagnostics: tuple[ExtractionDiagnostic, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkbookRecord":
        return cls(
            workbook_id=data["workbook_id"],
            source_path=data["source_path"],
            sheets=tuple(SheetRecord.from_dict(item) for item in data.get("sheets", [])),
            cells=tuple(CellRecord.from_dict(item) for item in data.get("cells", [])),
            named_ranges=tuple(NamedRangeRecord.from_dict(item) for item in data.get("named_ranges", [])),
            diagnostics=tuple(ExtractionDiagnostic.from_dict(item) for item in data.get("diagnostics", [])),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "workbook_id": self.workbook_id,
            "source_path": self.source_path,
            "sheets": [sheet.to_dict() for sheet in self.sheets],
            "cells": [cell.to_dict() for cell in self.cells],
            "named_ranges": [named_range.to_dict() for named_range in self.named_ranges],
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }
