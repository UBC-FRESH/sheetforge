"""Generated Python module contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal


JsonValue = str | int | float | bool | None | list[Any] | dict[str, Any]
DiagnosticSeverity = Literal["info", "warning", "error"]
GeneratedSymbolKind = Literal["input", "intermediate", "output"]


@dataclass(frozen=True)
class GenerationDiagnostic:
    """Generation concern tied to workbook or generated-code provenance."""

    code: str
    message: str
    severity: DiagnosticSeverity = "warning"
    location: str | None = None
    raw_value: JsonValue = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GenerationDiagnostic":
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
class GeneratedSymbol:
    """Generated Python symbol tied back to workbook provenance."""

    cell_ref: str
    symbol_name: str
    kind: GeneratedSymbolKind
    raw_formula: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeneratedSymbol":
        return cls(
            cell_ref=data["cell_ref"],
            symbol_name=data["symbol_name"],
            kind=data["kind"],
            raw_formula=data.get("raw_formula"),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "cell_ref": self.cell_ref,
            "symbol_name": self.symbol_name,
            "kind": self.kind,
            "raw_formula": self.raw_formula,
        }


@dataclass(frozen=True)
class GeneratedModuleContract:
    """Contract for one generated standalone Python module."""

    workbook_id: str
    module_name: str
    entrypoint: str = "calculate"
    input_refs: tuple[str, ...] = field(default_factory=tuple)
    output_refs: tuple[str, ...] = field(default_factory=tuple)
    symbols: tuple[GeneratedSymbol, ...] = field(default_factory=tuple)
    include_provenance_comments: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeneratedModuleContract":
        return cls(
            workbook_id=data["workbook_id"],
            module_name=data["module_name"],
            entrypoint=data.get("entrypoint", "calculate"),
            input_refs=tuple(data.get("input_refs", [])),
            output_refs=tuple(data.get("output_refs", [])),
            symbols=tuple(GeneratedSymbol.from_dict(item) for item in data.get("symbols", [])),
            include_provenance_comments=data.get("include_provenance_comments", True),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "workbook_id": self.workbook_id,
            "module_name": self.module_name,
            "entrypoint": self.entrypoint,
            "input_refs": list(self.input_refs),
            "output_refs": list(self.output_refs),
            "symbols": [symbol.to_dict() for symbol in self.symbols],
            "include_provenance_comments": self.include_provenance_comments,
        }


@dataclass(frozen=True)
class GenerationResult:
    """Result of generating one Python module."""

    contract: GeneratedModuleContract
    source_code: str = ""
    diagnostics: tuple[GenerationDiagnostic, ...] = field(default_factory=tuple)

    @property
    def generated(self) -> bool:
        return bool(self.source_code) and not any(diagnostic.severity == "error" for diagnostic in self.diagnostics)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GenerationResult":
        return cls(
            contract=GeneratedModuleContract.from_dict(data["contract"]),
            source_code=data.get("source_code", ""),
            diagnostics=tuple(GenerationDiagnostic.from_dict(item) for item in data.get("diagnostics", [])),
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "contract": self.contract.to_dict(),
            "source_code": self.source_code,
            "generated": self.generated,
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }


def symbol_name_for_cell_ref(cell_ref: str) -> str:
    """Build a stable Python identifier from a canonical workbook cell ref."""

    symbol = re.sub(r"[^0-9A-Za-z_]+", "_", cell_ref).strip("_").lower()
    if not symbol:
        return "cell"
    if symbol[0].isdigit():
        return f"cell_{symbol}"
    return symbol
