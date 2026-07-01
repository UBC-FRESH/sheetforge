"""FreshForge provider integration for Modelwright workflow stages.

This module is intentionally non-executing. It describes Modelwright's
workbook-to-generated-model workflow stages for FreshForge validation,
inspection, and planning, but it does not run Modelwright commands, read source
workbooks, or materialize artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODELWRIGHT_PROVIDER_ID = "modelwright"
MODELWRIGHT_PROVIDER_VERSION = "0.1.0a6"


@dataclass(frozen=True)
class _NodeContract:
    id: str
    name: str
    description: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()


_NODE_CONTRACTS: tuple[_NodeContract, ...] = (
    _NodeContract(
        id="workbook_extract",
        name="Extract workbook",
        description="Declare extraction of workbook facts into a WorkbookRecord.",
        outputs=("workbook_record",),
        parameters=("workbook",),
        artifacts=("workbook_record",),
    ),
    _NodeContract(
        id="workbook_graph",
        name="Build workbook dependency graph",
        description="Declare dependency graph construction from an extracted workbook record.",
        inputs=("workbook_record",),
        outputs=("dependency_graph",),
        artifacts=("dependency_graph",),
    ),
    _NodeContract(
        id="model_infer_contract",
        name="Infer generated-model contract",
        description="Declare selected-output generated-model contract inference.",
        inputs=("workbook_record", "dependency_graph"),
        outputs=("generated_contract", "formula_expressions", "input_constants"),
        parameters=("module_name",),
        artifacts=("output_refs", "contract", "expressions", "constants", "inference_result"),
    ),
    _NodeContract(
        id="model_generate",
        name="Generate Python model",
        description="Declare standalone Python model generation from explicit JSON artifacts.",
        inputs=("generated_contract", "formula_expressions", "input_constants"),
        outputs=("generated_model",),
        artifacts=("generated_model", "generation_result"),
    ),
    _NodeContract(
        id="model_execute",
        name="Execute generated model",
        description="Declare generated-model execution for selected outputs.",
        inputs=("generated_contract", "generated_model"),
        outputs=("generated_values",),
        artifacts=("generated_values",),
    ),
    _NodeContract(
        id="validation_evaluate",
        name="Evaluate generated model",
        description="Declare generated-model evaluation against cached or oracle-backed values.",
        inputs=("generated_contract", "generated_model"),
        outputs=("validation_report",),
        parameters=("scenario",),
        artifacts=("scenario", "evaluation_report"),
    ),
    _NodeContract(
        id="conversion_plan",
        name="Build conversion plan",
        description="Declare a Modelwright conversion-plan summary for the workflow boundary.",
        inputs=("workbook_record", "dependency_graph"),
        outputs=("conversion_plan",),
        parameters=("benchmark_role",),
        artifacts=("conversion_plan",),
    ),
)


class ModelwrightFreshForgeProvider:
    """Non-executing FreshForge provider for Modelwright workflow stages."""

    def metadata(self) -> Any:
        """Return FreshForge provider metadata."""
        node_type_metadata, provider_metadata = _freshforge_metadata_types()
        return provider_metadata(
            id=MODELWRIGHT_PROVIDER_ID,
            version=MODELWRIGHT_PROVIDER_VERSION,
            name="Modelwright workflow provider",
            description=(
                "Non-executing provider for Modelwright workbook extraction, "
                "generated-model materialization, and validation workflow planning."
            ),
            node_types=tuple(
                node_type_metadata(
                    id=contract.id,
                    name=contract.name,
                    description=contract.description,
                    inputs=contract.inputs,
                    outputs=contract.outputs,
                    parameters=contract.parameters,
                    artifacts=contract.artifacts,
                )
                for contract in _NODE_CONTRACTS
            ),
        )

    def validate_node(
        self,
        node: Any,
        node_type: Any,
        *,
        location: str,
    ) -> tuple[Any, ...]:
        """Validate broad Modelwright node shape without executing Modelwright."""
        diagnostic, severity = _freshforge_diagnostic_types()
        diagnostics: list[Any] = []
        diagnostics.extend(
            _missing_key_diagnostics(
                diagnostic=diagnostic,
                severity=severity,
                required=tuple(node_type.inputs),
                actual=node.inputs,
                field_name="inputs",
                location=location,
            )
        )
        diagnostics.extend(
            _missing_key_diagnostics(
                diagnostic=diagnostic,
                severity=severity,
                required=tuple(node_type.outputs),
                actual=node.outputs,
                field_name="outputs",
                location=location,
            )
        )
        diagnostics.extend(
            _missing_key_diagnostics(
                diagnostic=diagnostic,
                severity=severity,
                required=tuple(node_type.parameters),
                actual=node.parameters,
                field_name="parameters",
                location=location,
            )
        )
        artifacts = node.artifacts if isinstance(node.artifacts, dict) else {}
        diagnostics.extend(
            _missing_key_diagnostics(
                diagnostic=diagnostic,
                severity=severity,
                required=tuple(node_type.artifacts),
                actual=artifacts,
                field_name="artifacts",
                location=location,
            )
        )
        diagnostics.extend(
            _empty_parameter_diagnostics(
                diagnostic=diagnostic,
                severity=severity,
                parameters=node.parameters,
                required=tuple(node_type.parameters),
                location=location,
            )
        )
        return tuple(diagnostics)


def provider_factory() -> ModelwrightFreshForgeProvider:
    """Return the Modelwright FreshForge provider for entry-point discovery."""
    return ModelwrightFreshForgeProvider()


def _freshforge_metadata_types() -> tuple[Any, Any]:
    try:
        from freshforge.providers import (  # type: ignore[import-untyped]
            NodeTypeMetadata,
            ProviderMetadata,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "The Modelwright FreshForge integration requires FreshForge to be installed separately."
        ) from exc
    return NodeTypeMetadata, ProviderMetadata


def _freshforge_diagnostic_types() -> tuple[Any, Any]:
    try:
        from freshforge.records import (  # type: ignore[import-untyped]
            Diagnostic,
            DiagnosticSeverity,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "The Modelwright FreshForge integration requires FreshForge to be installed separately."
        ) from exc
    return Diagnostic, DiagnosticSeverity


def _missing_key_diagnostics(
    *,
    diagnostic: Any,
    severity: Any,
    required: tuple[str, ...],
    actual: dict[str, Any],
    field_name: str,
    location: str,
) -> tuple[Any, ...]:
    return tuple(
        diagnostic(
            severity=severity.ERROR,
            code=f"modelwright.{field_name}.missing",
            message=(
                f"Modelwright node requires {field_name} key '{key}' for "
                "non-executing workflow planning."
            ),
            location=f"{location}.{field_name}.{key}",
        )
        for key in required
        if key not in actual
    )


def _empty_parameter_diagnostics(
    *,
    diagnostic: Any,
    severity: Any,
    parameters: dict[str, Any],
    required: tuple[str, ...],
    location: str,
) -> tuple[Any, ...]:
    diagnostics: list[Any] = []
    for key in required:
        value = parameters.get(key)
        if isinstance(value, str) and not value.strip():
            diagnostics.append(
                diagnostic(
                    severity=severity.ERROR,
                    code="modelwright.parameters.empty",
                    message=f"Modelwright node parameter '{key}' must be nonempty.",
                    location=f"{location}.parameters.{key}",
                )
            )
    return tuple(diagnostics)
