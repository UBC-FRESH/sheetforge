import pytest

from modelwright.wrappers import (
    ModelFacade,
    Scenario,
    WrapperDeclarationError,
    WrapperExecutionError,
    cell,
    report,
    table,
)


def generated_model(inputs=None):
    inputs = inputs or {}
    base = inputs.get("Inputs!B2", 100)
    growth = inputs.get("Inputs!B3", 0.1)
    return {
        "Summary!B2": base * (1 + growth),
        "Summary!C2": base * 2,
        "Summary!B3": "ok",
        "Summary!C3": base + 5,
    }


def test_model_facade_wraps_generated_model_with_scenario_tables_and_reports() -> None:
    facade = ModelFacade(
        generated_model,
        cells=[
            cell("Inputs!B2", name="base", label="Base volume", role="input", unit="t"),
            cell("Inputs!B3", name="growth", label="Growth rate", role="input", unit="fraction"),
            cell("Summary!B2", name="projected", label="Projected volume", role="output", unit="t"),
        ],
        tables=[
            table(
                "summary_grid",
                sheet="Summary",
                range_ref="B2:C3",
                row_labels=["volume", "status"],
                column_labels=["primary", "secondary"],
            )
        ],
        reports=[report("summary", cells=["base", "projected"], tables=["summary_grid"])],
    )

    scenario = facade.scenario(inputs={"Inputs!B2": 50}).with_input("Inputs!B3", 0.2)

    assert facade.inputs()["base"].cell_ref == "Inputs!B2"
    assert facade.outputs()["projected"].cell_ref == "Summary!B2"
    assert facade.calculate(scenario) == {
        "Summary!B2": 60.0,
        "Summary!C2": 100,
        "Summary!B3": "ok",
        "Summary!C3": 55,
    }

    input_view = facade.inspect("Inputs!B2", scenario)
    assert input_view.to_dict() == {
        "cell_ref": "Inputs!B2",
        "name": "base",
        "label": "Base volume",
        "role": "input",
        "unit": "t",
        "description": None,
        "value": 50,
        "has_value": True,
    }

    table_view = facade.table("summary_grid", scenario)
    assert table_view.to_dict() == {
        "name": "summary_grid",
        "sheet": "Summary",
        "range_ref": "B2:C3",
        "rows": ["volume", "status"],
        "columns": ["primary", "secondary"],
        "cell_refs": [["Summary!B2", "Summary!C2"], ["Summary!B3", "Summary!C3"]],
        "values": [[60.0, 100], ["ok", 55]],
        "label": None,
        "description": None,
    }

    report_payload = facade.report("summary", scenario)
    assert report_payload["cells"]["base"]["value"] == 50
    assert report_payload["cells"]["projected"]["value"] == 60.0
    assert report_payload["tables"]["summary_grid"]["values"] == [[60.0, 100], ["ok", 55]]


def test_scenario_is_copy_on_write_and_normalizes_input_refs() -> None:
    original = Scenario.from_inputs(inputs={"Inputs!B2": 10})
    updated = original.with_input("Inputs!B3", 0.25)

    assert original.inputs == {"Inputs!B2": 10}
    assert updated.inputs == {"Inputs!B2": 10, "Inputs!B3": 0.25}


def test_table_declaration_validates_label_shape() -> None:
    with pytest.raises(WrapperDeclarationError, match="row labels"):
        table("bad_rows", sheet="Summary", range_ref="A1:A2", row_labels=["only one"])

    with pytest.raises(WrapperDeclarationError, match="column labels"):
        table("bad_columns", sheet="Summary", range_ref="A1:B1", column_labels=["only one"])


def test_facade_validates_duplicate_names_and_report_references() -> None:
    with pytest.raises(WrapperDeclarationError, match="duplicate cell declaration"):
        ModelFacade(
            generated_model,
            cells=[
                cell("Inputs!B2", name="base"),
                cell("Inputs!B3", name="base"),
            ],
        )

    with pytest.raises(WrapperDeclarationError, match="unknown table"):
        ModelFacade(generated_model, reports=[report("bad", tables=["missing"])])


def test_facade_wraps_generated_model_execution_errors() -> None:
    def broken_model(inputs=None):
        raise RuntimeError("boom")

    facade = ModelFacade(broken_model)

    with pytest.raises(WrapperExecutionError, match="calculation failed"):
        facade.calculate()
