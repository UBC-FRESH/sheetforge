# Phase 35/36 Downstream Automation Chain

Date: 2026-07-01

Purpose: record how Modelwright's next generated-model workflow phases support the downstream
CLEWs-C2020 FreshForge and FABLE Pyculator automation lane.

## Current Boundary

Modelwright owns generic workbook extraction, dependency graphing, formula translation,
generated-model contract inference, Python source generation, generated-model execution, and cached
workbook validation mechanics.

FreshForge owns workflow orchestration, provider discovery, serial local execution, and future run
namespaces/matrices.

FABLE Pyculator owns FABLE-specific workbook surface discovery, output-ref strategy selection,
scenario bundles, notebook rendering, and FABLE-facing validation/publication guidance.

## Coordinated Sequence

1. FreshForge Phase 7 adds run namespaces and compact workflow-run summaries.
2. Modelwright Phase 35 exposes clearer generated-model stage summaries and provider diagnostics.
3. Modelwright Phase 36 extracts compact validation evidence suitable for downstream automation.
4. FABLE Pyculator Phase 18 compares FABLE output-ref strategies using FreshForge namespaces and
   Modelwright summaries.
5. FreshForge Phase 8 adds generic matrix expansion once real strategy/scenario examples justify it.
6. FABLE Pyculator Phases 19 and 20 use those primitives for scenario-bundle orchestration and
   opt-in benchmark workflow upgrades.

## Phase 35 Intent

Phase 35 made Modelwright's generated-model workflow stages easier for downstream tools to
summarize without parsing large raw reports. It consumes FreshForge Phase 7's run namespaces and
whole-run summaries by adding compact provider-owned stage summaries under
`ProviderRunResult.data["summary"]`.

Those summaries focus on status, artifact-independent counts, and diagnostics for infer-contract,
generate, execute, and validation stages. FreshForge still owns the whole-run summary and namespace;
Modelwright owns the stage-specific generated-model facts inside each node result.

It should not add FABLE output-table discovery, scenario-bundle semantics, or FreshForge scheduling
policy.

## Phase 36 Intent

Phase 36 moves generic compact validation evidence extraction closer to the Modelwright stage
that owns generated-model validation. Downstream packages should be able to record sanitized summary
evidence without copying raw validation reports, generated source, source workbooks, or bulky
generated values.

The Modelwright layer owns generic evidence identities, artifact directories, compact JSON/Markdown
writers, and conservative equivalence status rules:

- `pass` only when explicit comparable-output, match, and mismatch counts prove zero mismatches;
- `fail` when explicit counts show mismatches or missing matches;
- `incomplete` when generated execution exists but comparison counts are absent;
- `skipped` when artifacts are missing in an optional evidence-packaging environment.

It should not declare arbitrary workbook equivalence or choose FABLE-specific output-ref strategies.
FABLE Pyculator Phase 20 can later wrap these helpers with FABLE workbook-version defaults and public
benchmark messaging.
