# IR Prototype Findings

Date: 2026-06-19

## Question

Can the prototype IR contract in `planning/workbook-ir-contract.md` represent the synthetic workbook strongly enough to support dependency analysis and the next generated-code experiment?

## Prototype Setup

Ignored scratch files under `tmp/`:

- `tmp/prototype_emit_ir.py`: emits the prototype IR.
- `tmp/synthetic_model.xlsx`: source workbook fixture.
- `tmp/prototype_ir_output.json`: emitted IR output.
- `tmp/prototype-venv/`: local prototype environment.

Commands used:

```bash
tmp/prototype-venv/bin/python -m py_compile tmp/prototype_emit_ir.py
tmp/prototype-venv/bin/python tmp/prototype_emit_ir.py
```

The output was then checked with a small assertion script against the acceptance criteria from `planning/workbook-ir-contract.md`.

## Verified Output

The emitted IR contains:

- one workbook record for `synthetic_model.xlsx`;
- three sheet records: `Inputs`, `Calc`, and `Summary`;
- two resolved named ranges: `BaseVolume -> Inputs!B2` and `GrowthRate -> Inputs!B3`;
- 22 non-empty cell records;
- five formula records: `Calc!B2`, `Calc!B3`, `Calc!B4`, `Summary!B2`, and `Summary!B3`;
- seven semantic dependency edges;
- seven execution dependency edges;
- five `missing_cached_formula_value` diagnostics, one for each formula cell.

The verified execution dependency edges are:

```text
Inputs!B2 -> Calc!B2
Inputs!B3 -> Calc!B2
Inputs!B4 -> Calc!B3
Calc!B2 -> Calc!B3
Calc!B3 -> Calc!B4
Calc!B4 -> Summary!B2
Summary!B2 -> Summary!B3
```

## Findings

The IR contract is practical for the first controlled workbook:

- `WorkbookRecord`, `SheetRecord`, `NamedRangeRecord`, `CellRecord`, `FormulaRecord`, `DependencyEdge`, and `DiagnosticRecord` all map cleanly to extractable `openpyxl` facts.
- Preserving named ranges as semantic edges while also emitting resolved execution edges worked well for `BaseVolume` and `GrowthRate`.
- Formula records can retain raw formula text, token lists, raw references, normalized references, function names, and formula-local diagnostics without needing a full parser yet.
- Missing cached formula values are correctly represented as warnings, not extraction failures.

No change to `planning/workbook-ir-contract.md` is needed from this prototype.

## Limits

This prototype does not yet prove behavior for:

- multi-cell ranges;
- sheet-local named ranges;
- external workbook links;
- array formulas;
- circular dependencies;
- volatile functions;
- hidden sheets;
- formulas requiring richer parsing than `openpyxl` tokenization.

Those should remain explicit later-test cases rather than being implied by this synthetic fixture.

## Next Step

Close the extraction-contract phase by summarizing Phase 3 inputs:

- the minimum IR fields needed by code generation;
- the supported formula subset for the first generated-code experiment;
- whether the next work should stay under ignored `tmp/` or introduce a minimal tracked prototype module.
