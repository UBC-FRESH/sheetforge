from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from modelwright.freshforge import MODELWRIGHT_PROVIDER_ID, provider_factory


EXAMPLE_PATH = Path("examples/freshforge/generated_model_workflow.yaml")
EXPECTED_PLAN_ORDER = [
    "extract_workbook",
    "build_graph",
    "infer_contract",
    "generate_model",
    "execute_model",
    "evaluate_model",
    "summarize_conversion",
]


def _registry_with_modelwright_provider():
    from freshforge.providers import ProviderRegistry

    registry = ProviderRegistry()
    registry.register(provider_factory())
    return registry


def test_provider_factory_returns_modelwright_provider() -> None:
    provider = provider_factory()

    assert provider.__class__.__name__ == "ModelwrightFreshForgeProvider"
    assert MODELWRIGHT_PROVIDER_ID == "modelwright"


def test_provider_metadata_serializes_deterministically() -> None:
    pytest.importorskip("freshforge")
    metadata = provider_factory().metadata()

    assert metadata.to_dict() == {
        "id": "modelwright",
        "version": "0.1.0a6",
        "node_types": [
            {
                "id": "workbook_extract",
                "inputs": [],
                "outputs": ["workbook_record"],
                "parameters": ["workbook"],
                "artifacts": ["workbook_record"],
                "name": "Extract workbook",
                "description": "Declare extraction of workbook facts into a WorkbookRecord.",
            },
            {
                "id": "workbook_graph",
                "inputs": ["workbook_record"],
                "outputs": ["dependency_graph"],
                "parameters": [],
                "artifacts": ["dependency_graph"],
                "name": "Build workbook dependency graph",
                "description": "Declare dependency graph construction from an extracted workbook record.",
            },
            {
                "id": "model_infer_contract",
                "inputs": ["workbook_record", "dependency_graph"],
                "outputs": ["generated_contract", "formula_expressions", "input_constants"],
                "parameters": ["module_name"],
                "artifacts": ["output_refs", "contract", "expressions", "constants", "inference_result"],
                "name": "Infer generated-model contract",
                "description": "Declare selected-output generated-model contract inference.",
            },
            {
                "id": "model_generate",
                "inputs": ["generated_contract", "formula_expressions", "input_constants"],
                "outputs": ["generated_model"],
                "parameters": [],
                "artifacts": ["generated_model", "generation_result"],
                "name": "Generate Python model",
                "description": "Declare standalone Python model generation from explicit JSON artifacts.",
            },
            {
                "id": "model_execute",
                "inputs": ["generated_contract", "generated_model"],
                "outputs": ["generated_values"],
                "parameters": [],
                "artifacts": ["generated_values"],
                "name": "Execute generated model",
                "description": "Declare generated-model execution for selected outputs.",
            },
            {
                "id": "validation_evaluate",
                "inputs": ["generated_contract", "generated_model"],
                "outputs": ["validation_report"],
                "parameters": ["scenario"],
                "artifacts": ["scenario", "evaluation_report"],
                "name": "Evaluate generated model",
                "description": "Declare generated-model evaluation against cached or oracle-backed values.",
            },
            {
                "id": "conversion_plan",
                "inputs": ["workbook_record", "dependency_graph"],
                "outputs": ["conversion_plan"],
                "parameters": ["benchmark_role"],
                "artifacts": ["conversion_plan"],
                "name": "Build conversion plan",
                "description": "Declare a Modelwright conversion-plan summary for the workflow boundary.",
            },
        ],
        "name": "Modelwright workflow provider",
        "description": (
            "Non-executing provider for Modelwright workbook extraction, "
            "generated-model materialization, and validation workflow planning."
        ),
    }


def test_pyproject_declares_freshforge_entry_point_without_direct_dependency() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    entry_points = pyproject["project"]["entry-points"]["freshforge.providers"]
    assert entry_points["modelwright"] == "modelwright.freshforge:provider_factory"
    optional = pyproject["project"]["optional-dependencies"]
    assert "freshforge" not in optional
    assert "freshforge" not in "\n".join(pyproject["project"]["dependencies"])


def test_modelwright_import_does_not_import_freshforge_eagerly() -> None:
    script = "import sys; import modelwright; print('freshforge' in sys.modules)"
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "False"


def test_example_workflow_validates_and_plans() -> None:
    pytest.importorskip("freshforge")
    from freshforge.loading import load_workflow
    from freshforge.planning import create_run_plan
    from freshforge.validation import validate_workflow_with_providers

    spec, load_diagnostics = load_workflow(EXAMPLE_PATH)
    assert spec is not None
    assert load_diagnostics == []

    diagnostics = validate_workflow_with_providers(
        spec,
        registry=_registry_with_modelwright_provider(),
        structural_diagnostics=load_diagnostics,
    )
    assert diagnostics == []

    plan = create_run_plan(
        spec,
        diagnostics=diagnostics,
        registry=_registry_with_modelwright_provider(),
    )
    assert not plan.has_errors
    assert [node.id for node in plan.nodes] == EXPECTED_PLAN_ORDER
    assert {node.provider_id for node in plan.nodes} == {"modelwright"}


def test_missing_required_parameter_returns_provider_diagnostic() -> None:
    pytest.importorskip("freshforge")
    from freshforge.loading import load_workflow_document
    from freshforge.validation import validate_workflow_document, validate_workflow_with_providers

    document = load_workflow_document(EXAMPLE_PATH)
    del document["nodes"][0]["parameters"]["workbook"]
    spec, structural = validate_workflow_document(document)

    assert spec is not None
    diagnostics = validate_workflow_with_providers(
        spec,
        registry=_registry_with_modelwright_provider(),
        structural_diagnostics=structural,
    )

    assert {diagnostic.code for diagnostic in diagnostics} == {
        "modelwright.parameters.missing"
    }
    assert diagnostics[0].location == "nodes[0].parameters.workbook"
