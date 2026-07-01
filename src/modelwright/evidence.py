"""Compact validation-evidence summaries for generated-model workflows.

This module summarizes artifacts that were already produced by Modelwright
generation, execution, and validation steps. It deliberately does not rerun
those steps, and it does not copy raw generated source, raw generated output
values, workbook contents, or full comparison rows into the shareable summary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

JsonValue = str | int | float | bool | None | list[Any] | dict[str, Any]
EvidenceStatus = Literal["skipped", "incomplete", "complete"]
EquivalenceStatus = Literal["pass", "fail", "incomplete"]


@dataclass(frozen=True)
class ValidationEvidencePaths:
    """Filesystem contract for compact validation-evidence extraction."""

    evidence_id: str
    artifact_dir: Path
    output_dir: Path
    inference_result_path: Path
    generation_result_path: Path
    generated_values_path: Path
    validation_scenario_path: Path
    evaluation_report_path: Path
    summary_json_path: Path
    summary_markdown_path: Path

    @property
    def required_artifact_paths(self) -> tuple[Path, ...]:
        """Return artifacts used as evidence inputs."""

        return (
            self.inference_result_path,
            self.generation_result_path,
            self.generated_values_path,
            self.validation_scenario_path,
            self.evaluation_report_path,
        )


@dataclass(frozen=True)
class ValidationEvidenceSummary:
    """Sanitized validation-evidence summary for publication or CI artifacts."""

    evidence_id: str
    evidence_status: EvidenceStatus
    equivalence_status: EquivalenceStatus
    missing_artifacts: tuple[str, ...] = field(default_factory=tuple)
    artifacts: dict[str, str] = field(default_factory=dict)
    stages: dict[str, JsonValue] = field(default_factory=dict)
    comparison: dict[str, JsonValue] = field(default_factory=dict)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize the compact evidence summary."""

        return {
            "evidence_id": self.evidence_id,
            "evidence_status": self.evidence_status,
            "equivalence_status": self.equivalence_status,
            "missing_artifacts": list(self.missing_artifacts),
            "artifacts": self.artifacts,
            "stages": self.stages,
            "comparison": self.comparison,
            "notes": list(self.notes),
        }


def validation_evidence_paths(
    *,
    evidence_id: str = "generated-model",
    artifact_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    validation_scenario_path: str | Path | None = None,
) -> ValidationEvidencePaths:
    """Build the generic path contract for validation-evidence extraction."""

    artifact_root = Path(artifact_dir) if artifact_dir is not None else Path("tmp/generated-model")
    output_root = Path(output_dir) if output_dir is not None else Path("tmp/validation-evidence") / evidence_id
    scenario_path = (
        Path(validation_scenario_path) if validation_scenario_path is not None else artifact_root / "validation-scenario.json"
    )
    return ValidationEvidencePaths(
        evidence_id=evidence_id,
        artifact_dir=artifact_root,
        output_dir=output_root,
        inference_result_path=artifact_root / "inference-result.json",
        generation_result_path=artifact_root / "generation-result.json",
        generated_values_path=artifact_root / "generated-values.json",
        validation_scenario_path=scenario_path,
        evaluation_report_path=artifact_root / "evaluation-report.json",
        summary_json_path=output_root / "summary.json",
        summary_markdown_path=output_root / "summary.md",
    )


def extract_validation_evidence(
    paths: ValidationEvidencePaths | None = None,
    *,
    evidence_id: str = "generated-model",
    artifact_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    validation_scenario_path: str | Path | None = None,
    require_artifacts: bool = False,
) -> ValidationEvidenceSummary:
    """Extract compact evidence from existing generated-model workflow artifacts."""

    evidence_paths = paths or validation_evidence_paths(
        evidence_id=evidence_id,
        artifact_dir=artifact_dir,
        output_dir=output_dir,
        validation_scenario_path=validation_scenario_path,
    )
    missing = tuple(str(path) for path in evidence_paths.required_artifact_paths if not path.exists())
    if missing and require_artifacts:
        missing_list = ", ".join(missing)
        raise FileNotFoundError(f"missing validation evidence artifact(s): {missing_list}")

    artifacts = _artifact_summary(evidence_paths)
    if missing:
        return ValidationEvidenceSummary(
            evidence_id=evidence_paths.evidence_id,
            evidence_status="skipped",
            equivalence_status="incomplete",
            missing_artifacts=missing,
            artifacts=artifacts,
            notes=("Validation artifacts are missing; evidence extraction was skipped.",),
        )

    inference = _load_json_object(evidence_paths.inference_result_path)
    generation = _load_json_object(evidence_paths.generation_result_path)
    generated_values = _load_json_object(evidence_paths.generated_values_path)
    scenario = _load_json_object(evidence_paths.validation_scenario_path)
    evaluation = _load_json_object(evidence_paths.evaluation_report_path)

    stages: dict[str, JsonValue] = {
        "inference": _inference_stage(inference),
        "generation": _generation_stage(generation),
        "generated_values": _generated_values_stage(generated_values),
        "validation_scenario": _validation_scenario_stage(scenario),
        "evaluation": _evaluation_stage(evaluation),
    }
    comparison = _comparison_summary(evaluation)
    equivalence_status = _equivalence_status(comparison)
    evidence_status: EvidenceStatus = "complete" if equivalence_status in {"pass", "fail"} else "incomplete"
    notes = _summary_notes(missing=(), stages=stages, comparison=comparison)
    return ValidationEvidenceSummary(
        evidence_id=evidence_paths.evidence_id,
        evidence_status=evidence_status,
        equivalence_status=equivalence_status,
        artifacts=artifacts,
        stages=stages,
        comparison=comparison,
        notes=notes,
    )


def write_validation_evidence(
    summary: ValidationEvidenceSummary,
    paths: ValidationEvidencePaths | None = None,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, JsonValue]:
    """Write ``summary.json`` and ``summary.md`` for compact evidence."""

    if paths is not None:
        json_path = paths.summary_json_path
        markdown_path = paths.summary_markdown_path
    else:
        output_root = Path(output_dir) if output_dir is not None else Path("tmp/validation-evidence") / summary.evidence_id
        json_path = output_root / "summary.json"
        markdown_path = output_root / "summary.md"

    json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = summary.to_dict()
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path.write_text(_summary_markdown(summary), encoding="utf-8")
    return {
        "summary": payload,
        "summary_json_path": str(json_path),
        "summary_markdown_path": str(markdown_path),
    }


def _artifact_summary(paths: ValidationEvidencePaths) -> dict[str, str]:
    return {
        "artifact_dir": str(paths.artifact_dir),
        "inference_result": str(paths.inference_result_path),
        "generation_result": str(paths.generation_result_path),
        "generated_values": str(paths.generated_values_path),
        "validation_scenario": str(paths.validation_scenario_path),
        "evaluation_report": str(paths.evaluation_report_path),
        "summary_json": str(paths.summary_json_path),
        "summary_markdown": str(paths.summary_markdown_path),
    }


def _inference_stage(data: dict[str, JsonValue]) -> dict[str, JsonValue]:
    contract = _object(data.get("contract"))
    return {
        "available": True,
        "inferred": bool(data.get("inferred", False)),
        "input_ref_count": _length(contract.get("input_refs")),
        "output_ref_count": _length(contract.get("output_refs")),
        "symbol_count": _length(contract.get("symbols")),
        "expression_count": _length(data.get("expressions")),
        "constant_count": _length(data.get("constants")),
        "diagnostic_count": _diagnostic_count(data),
        "error_diagnostic_count": _diagnostic_count(data, severity="error"),
    }


def _generation_stage(data: dict[str, JsonValue]) -> dict[str, JsonValue]:
    contract = _object(data.get("contract"))
    source_code = data.get("source_code")
    source_size = len(source_code.encode("utf-8")) if isinstance(source_code, str) else None
    source_lines = source_code.count("\n") + 1 if isinstance(source_code, str) and source_code else None
    return {
        "available": True,
        "generated": bool(data.get("generated", False)),
        "input_ref_count": _length(contract.get("input_refs")),
        "output_ref_count": _length(contract.get("output_refs")),
        "symbol_count": _length(contract.get("symbols")),
        "source_size_bytes": source_size,
        "source_line_count": source_lines,
        "diagnostic_count": _diagnostic_count(data),
        "error_diagnostic_count": _diagnostic_count(data, severity="error"),
    }


def _generated_values_stage(data: dict[str, JsonValue]) -> dict[str, JsonValue]:
    contract = _object(data.get("contract"))
    output_values = _object(data.get("output_values"))
    return {
        "available": True,
        "executed": bool(data.get("executed", False)),
        "declared_output_count": _length(contract.get("output_refs")),
        "generated_output_count": len(output_values),
        "diagnostic_count": _diagnostic_count(data),
        "error_diagnostic_count": _diagnostic_count(data, severity="error"),
    }


def _validation_scenario_stage(data: dict[str, JsonValue]) -> dict[str, JsonValue]:
    outputs = _sequence(data.get("outputs"))
    output_kinds = sorted(
        {item.get("kind") for item in outputs if isinstance(item, dict) and isinstance(item.get("kind"), str)}
    )
    return {
        "available": True,
        "scenario_id": data.get("scenario_id"),
        "input_count": _length(data.get("inputs")),
        "output_count": len(outputs),
        "output_kinds": output_kinds,
    }


def _evaluation_stage(data: dict[str, JsonValue]) -> dict[str, JsonValue]:
    generated_execution = _object(data.get("generated_execution"))
    cached_report = _object(data.get("cached_validation_report"))
    oracle_report = _object(data.get("oracle_validation_report"))
    return {
        "available": True,
        "scenario_id": data.get("scenario_id"),
        "generated_executed": bool(generated_execution.get("executed", False)),
        "generated_output_count": _length(generated_execution.get("output_values")),
        "has_cached_validation_report": bool(cached_report),
        "has_oracle_validation_report": bool(oracle_report),
        "cached_validation_status": cached_report.get("status"),
        "oracle_validation_status": oracle_report.get("status"),
        "diagnostic_count": _diagnostic_count(data),
        "error_diagnostic_count": _diagnostic_count(data, severity="error"),
    }


def _comparison_summary(evaluation: dict[str, JsonValue]) -> dict[str, JsonValue]:
    reports = [
        _object(evaluation.get("cached_validation_report")),
        _object(evaluation.get("oracle_validation_report")),
    ]
    report = next((item for item in reports if item), None)
    if report is None:
        return {
            "comparison_counts_available": False,
            "comparable_output_count": None,
            "match_count": None,
            "mismatch_count": None,
            "validation_report_status": None,
            "validation_backend": None,
        }

    comparisons = _sequence(report.get("comparisons"))
    mismatches = _sequence(report.get("mismatches"))
    comparable_count = _find_count(report, _COMPARABLE_KEYS)
    match_count = _find_count(report, _MATCH_KEYS)
    mismatch_count = _find_count(report, _MISMATCH_KEYS)
    if comparable_count is None and comparisons:
        comparable_count = len(comparisons)
    if match_count is None and comparisons:
        match_count = sum(1 for item in comparisons if isinstance(item, dict) and item.get("matches") is True)
    if mismatch_count is None and (comparisons or mismatches):
        mismatch_count = len(mismatches) if mismatches else sum(
            1 for item in comparisons if isinstance(item, dict) and item.get("matches") is False
        )

    counts_available = comparable_count is not None and match_count is not None and mismatch_count is not None
    return {
        "comparison_counts_available": counts_available,
        "comparable_output_count": comparable_count,
        "match_count": match_count,
        "mismatch_count": mismatch_count,
        "validation_report_status": report.get("status"),
        "validation_backend": report.get("oracle_backend"),
        "validation_diagnostic_count": _diagnostic_count(report),
        "validation_error_diagnostic_count": _diagnostic_count(report, severity="error"),
    }


def _equivalence_status(comparison: dict[str, JsonValue]) -> EquivalenceStatus:
    comparable = comparison.get("comparable_output_count")
    matches = comparison.get("match_count")
    mismatches = comparison.get("mismatch_count")
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in (comparable, matches, mismatches)):
        return "incomplete"
    if comparable == matches and mismatches == 0:
        return "pass"
    return "fail"


def _summary_notes(
    *,
    missing: tuple[str, ...],
    stages: dict[str, JsonValue],
    comparison: dict[str, JsonValue],
) -> tuple[str, ...]:
    notes: list[str] = []
    if missing:
        notes.append("Validation artifacts are missing; evidence extraction was skipped.")
    if comparison.get("comparison_counts_available") is not True:
        notes.append("Explicit comparable-output, match, and mismatch counts were not found.")
    diagnostics = sum(
        int(stage.get("diagnostic_count", 0))
        for stage in stages.values()
        if isinstance(stage, dict) and isinstance(stage.get("diagnostic_count"), int)
    )
    if diagnostics:
        notes.append(f"Stage diagnostics were reported: {diagnostics}.")
    return tuple(notes)


def _summary_markdown(summary: ValidationEvidenceSummary) -> str:
    comparison = summary.comparison
    lines = [
        f"# Modelwright Validation Evidence: {summary.evidence_id}",
        "",
        f"- Evidence status: `{summary.evidence_status}`",
        f"- Equivalence status: `{summary.equivalence_status}`",
        f"- Comparable outputs: `{comparison.get('comparable_output_count')}`",
        f"- Matches: `{comparison.get('match_count')}`",
        f"- Mismatches: `{comparison.get('mismatch_count')}`",
        "",
        "## Artifacts",
        "",
    ]
    for key, path in summary.artifacts.items():
        lines.append(f"- `{key}`: `{path}`")
    if summary.missing_artifacts:
        lines.extend(["", "## Missing Artifacts", ""])
        lines.extend(f"- `{path}`" for path in summary.missing_artifacts)
    if summary.notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in summary.notes)
    lines.append("")
    return "\n".join(lines)


def _load_json_object(path: Path) -> dict[str, JsonValue]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def _object(value: JsonValue) -> dict[str, JsonValue]:
    return value if isinstance(value, dict) else {}


def _sequence(value: JsonValue) -> list[JsonValue]:
    return value if isinstance(value, list) else []


def _length(value: JsonValue) -> int | None:
    if isinstance(value, dict | list):
        return len(value)
    return None


def _diagnostic_count(data: dict[str, JsonValue], *, severity: str | None = None) -> int:
    diagnostics = _sequence(data.get("diagnostics"))
    if severity is None:
        return len(diagnostics)
    return sum(1 for item in diagnostics if isinstance(item, dict) and item.get("severity") == severity)


_COMPARABLE_KEYS = ("comparable_output_count", "comparable_outputs", "total_comparable_outputs")
_MATCH_KEYS = ("match_count", "matches", "matched_outputs", "generated_output_matches")
_MISMATCH_KEYS = ("mismatch_count", "mismatches", "mismatched_outputs")


def _find_count(data: JsonValue, keys: tuple[str, ...]) -> int | None:
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
        for value in data.values():
            found = _find_count(value, keys)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_count(item, keys)
            if found is not None:
                return found
    return None
