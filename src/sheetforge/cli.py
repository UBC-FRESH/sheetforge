"""Command-line wrappers for Sheetforge JSON workflows."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from sheetforge.extraction import extract_workbook
from sheetforge.formulas import FormulaExpression
from sheetforge.generation import GeneratedModuleContract, generate_python_module
from sheetforge.graph import build_dependency_graph
from sheetforge.validation import build_validation_report, load_validation_scenario


JsonValue = str | int | float | bool | None | list[Any] | dict[str, Any]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Sheetforge CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    payload = args.handler(args)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sheetforge")
    subcommands = parser.add_subparsers(dest="command", required=True)

    extract_parser = subcommands.add_parser("extract", help="extract workbook facts as JSON")
    extract_parser.add_argument("workbook", help="path to a source workbook")
    extract_parser.set_defaults(handler=_extract_command)

    graph_parser = subcommands.add_parser("graph", help="build dependency graph JSON from a workbook")
    graph_parser.add_argument("workbook", help="path to a source workbook")
    graph_parser.set_defaults(handler=_graph_command)

    generate_parser = subcommands.add_parser("generate", help="generate Python from JSON contracts")
    generate_parser.add_argument("--contract", required=True, help="path to a generated module contract JSON file")
    generate_parser.add_argument("--expressions", required=True, help="path to a formula expressions JSON object")
    generate_parser.add_argument("--constants", help="optional path to an input constants JSON object")
    generate_parser.add_argument("--output", help="optional path for generated Python source")
    generate_parser.set_defaults(handler=_generate_command)

    report_parser = subcommands.add_parser("validate-report", help="build validation report JSON")
    report_parser.add_argument("--scenario", required=True, help="path to a validation scenario JSON file")
    report_parser.add_argument("--generated-values", required=True, help="path to generated output values JSON object")
    report_parser.add_argument("--oracle-values", required=True, help="path to oracle output values JSON object")
    report_parser.set_defaults(handler=_validate_report_command)

    return parser


def _extract_command(args: argparse.Namespace) -> dict[str, JsonValue]:
    workbook = extract_workbook(args.workbook)
    return workbook.to_dict()


def _graph_command(args: argparse.Namespace) -> dict[str, JsonValue]:
    workbook = extract_workbook(args.workbook)
    graph = build_dependency_graph(workbook)
    return graph.to_dict()


def _generate_command(args: argparse.Namespace) -> dict[str, JsonValue]:
    contract = GeneratedModuleContract.from_dict(_load_object(args.contract))
    expressions = {
        cell_ref: FormulaExpression.from_dict(expression)
        for cell_ref, expression in _load_object(args.expressions).items()
    }
    constants = _load_object(args.constants) if args.constants else {}
    output_path = Path(args.output) if args.output else None
    result = generate_python_module(
        contract=contract,
        expressions=expressions,
        constants=constants,
        output_path=output_path,
    )
    return result.to_dict()


def _validate_report_command(args: argparse.Namespace) -> dict[str, JsonValue]:
    scenario = load_validation_scenario(args.scenario)
    report = build_validation_report(
        scenario=scenario,
        generated_values=_load_object(args.generated_values),
        oracle_values=_load_object(args.oracle_values),
    )
    return report.to_dict()


def _load_object(path: str | Path) -> dict[str, JsonValue]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


if __name__ == "__main__":
    raise SystemExit(main())
