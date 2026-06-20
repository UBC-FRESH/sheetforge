"""Sheetforge package skeleton."""

from sheetforge.validation import (
    ComparisonResult,
    ComparisonRules,
    Diagnostic,
    MISSING_VALUE,
    OracleConfig,
    ScenarioInput,
    ScenarioOutput,
    ValidationReport,
    ValidationScenario,
    compare_scalar_output,
    load_validation_scenario,
)

__version__ = "0.0.0"

__all__ = [
    "ComparisonResult",
    "ComparisonRules",
    "Diagnostic",
    "MISSING_VALUE",
    "OracleConfig",
    "ScenarioInput",
    "ScenarioOutput",
    "ValidationReport",
    "ValidationScenario",
    "__version__",
    "compare_scalar_output",
    "load_validation_scenario",
]
