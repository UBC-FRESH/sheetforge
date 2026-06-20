# Release Readiness And Next Roadmap

Date: 2026-06-20

## Current Readiness

Sheetforge is ready as an early, package-backed research and workflow skeleton for controlled spreadsheet-to-Python experiments.

Ready now:

- workbook extraction records and `openpyxl` extraction;
- normalized workbook references and dependency graph records;
- formula expression records and translation for a narrow supported subset;
- generated Python module contracts and standalone source generation;
- validation scenario/report records and scalar comparison helpers;
- optional `formulas` oracle boundary for supported workbooks;
- thin JSON CLI commands for extraction, graphing, generation, and validation-report assembly;
- local and CI verification with `pytest`;
- lightweight linting with `ruff check`;
- private-workbook evaluation protocol and one sanitized real-workbook findings note.

This is not ready as a general workbook converter or a release-quality user tool.

## Remaining Unsupported Semantics

The highest-priority gaps remain evidence from the first private workbook evaluation:

- structured table-reference formulas;
- unsupported Excel functions;
- unsupported parser token forms;
- unsupported operators;
- external workbook references;
- volatile functions;
- unresolved named ranges;
- formula cells without cached values;
- full-workbook recalculation oracle failures.

These gaps should drive the next implementation horizon. Sheetforge should not claim workbook equivalence until generated outputs are validated against a credible oracle or explicitly scoped cached-value comparisons.

## Next Roadmap Horizon

The next horizon should stay focused on making real workbook behavior explicit and repeatable:

1. Phase 16: expand real-workbook formula and reference semantics from sanitized evidence.
2. Phase 17: define conversion plans so partial conversion, unsupported cells, generated outputs, and validation targets are explicit.
3. Phase 18: automate generated-model execution, oracle/cached-value validation, and evaluation reports.

These phases are backlog lanes. They are not active until Phase 15 is merged and the maintainer activates Phase 16.

## Release Position

Keep the project pre-release.

Do not add package publishing, release artifacts, a compatibility guarantee, or user-facing claims of full conversion until:

- the conversion plan workflow can explain what is converted and what is not;
- generated outputs can be validated repeatably;
- unsupported workbook semantics are reported clearly;
- at least one private workbook evaluation can be rerun through durable commands with sanitized tracked findings.
