import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

from sheetforge.extraction import extract_workbook
from sheetforge.formulas import translate_formula_cell
from sheetforge.generation import (
    GeneratedModuleContract,
    GeneratedSymbol,
    GenerationResult,
    generate_python_module,
    symbol_name_for_cell_ref,
)
from sheetforge.graph import build_dependency_graph
from tests.fixtures.synthetic_model.build_workbook import build_workbook


def synthetic_generation_inputs(tmp_path: Path) -> tuple[GeneratedModuleContract, dict, dict]:
    workbook = extract_workbook(build_workbook(tmp_path / "synthetic_model.xlsx"))
    graph = build_dependency_graph(workbook)
    formula_cells = {cell.cell_ref: cell for cell in workbook.cells if cell.formula is not None}
    expressions = {
        cell_ref: translate_formula_cell(cell, graph)
        for cell_ref, cell in formula_cells.items()
    }
    constants = {
        cell.cell_ref: cell.raw_value
        for cell in workbook.cells
        if cell.formula is None and cell.cell_ref in {"Inputs!B2", "Inputs!B3", "Inputs!B4"}
    }
    formula_order = ("Calc!B2", "Calc!B3", "Calc!B4", "Summary!B2", "Summary!B3")
    contract = GeneratedModuleContract(
        workbook_id=workbook.workbook_id,
        module_name="synthetic_model",
        input_refs=tuple(constants),
        output_refs=("Summary!B2", "Summary!B3"),
        symbols=(
            tuple(
                GeneratedSymbol(
                    cell_ref=cell_ref,
                    symbol_name=symbol_name_for_cell_ref(cell_ref),
                    kind="input",
                )
                for cell_ref in constants
            )
            + tuple(
                GeneratedSymbol(
                    cell_ref=cell_ref,
                    symbol_name=symbol_name_for_cell_ref(cell_ref),
                    kind="output" if cell_ref.startswith("Summary!") else "intermediate",
                    raw_formula=formula_cells[cell_ref].formula.raw_formula if formula_cells[cell_ref].formula else None,
                )
                for cell_ref in formula_order
            )
        ),
    )
    return contract, expressions, constants


def load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("generated_synthetic_model", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_generate_python_module_writes_standalone_synthetic_model(tmp_path: Path) -> None:
    contract, expressions, constants = synthetic_generation_inputs(tmp_path)
    output_path = tmp_path / "generated_model.py"

    result = generate_python_module(
        contract=contract,
        expressions=expressions,
        constants=constants,
        output_path=output_path,
    )

    assert result.generated is True
    assert output_path.exists()
    assert "Source workbook: synthetic_model.xlsx" in result.source_code
    assert "# Calc!B2: =BaseVolume*(1+GrowthRate)" in result.source_code
    assert "def calculate(inputs=None):" in result.source_code
    assert "openpyxl" not in result.source_code
    module = load_module(output_path)
    assert module.calculate() == {"Summary!B2": 70.2, "Summary!B3": "ok"}


def test_generate_python_module_uses_input_overrides(tmp_path: Path) -> None:
    contract, expressions, constants = synthetic_generation_inputs(tmp_path)
    output_path = tmp_path / "generated_model.py"

    result = generate_python_module(
        contract=contract,
        expressions=expressions,
        constants=constants,
        output_path=output_path,
    )
    module = load_module(output_path)

    assert result.generated is True
    assert module.calculate({"Inputs!B2": 10}) == {"Summary!B2": 7.02, "Summary!B3": "low"}


def test_generate_python_module_payload_round_trips_without_writing(tmp_path: Path) -> None:
    contract, expressions, constants = synthetic_generation_inputs(tmp_path)

    result = generate_python_module(contract=contract, expressions=expressions, constants=constants)
    payload = result.to_dict()

    assert result.generated is True
    assert not (tmp_path / "generated_model.py").exists()
    assert json.loads(json.dumps(payload)) == payload
    assert GenerationResult.from_dict(payload) == result


def test_generate_python_module_reports_missing_expression(tmp_path: Path) -> None:
    contract, expressions, constants = synthetic_generation_inputs(tmp_path)
    expressions.pop("Summary!B3")

    result = generate_python_module(contract=contract, expressions=expressions, constants=constants)

    assert result.generated is False
    assert result.source_code == ""
    assert result.diagnostics[0].code == "missing_formula_expression"
    assert result.diagnostics[0].location == "Summary!B3"
