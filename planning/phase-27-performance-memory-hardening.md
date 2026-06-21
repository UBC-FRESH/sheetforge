# Phase 27 Performance And Memory Hardening

## Purpose

Phase 27 will make full-workbook generated-model validation practical after Phase 26 establishes the
current correctness boundary for the 2020 FABLE benchmark.

The immediate evidence is that cached extraction and contract inference can now be skipped, but the
generated model still takes substantial time and memory to import, execute, and compare. That cost
needs to be measured before changing architecture.

## Working Hypotheses

These are hypotheses to test, not conclusions:

- Formula cells should not be recomputed repeatedly once `_get(cell_ref)` caches a value.
- Range-heavy formulas may still rebuild and rescan large Python lists many times, especially
  `SUMIF`, `SUMIFS`, `COUNTIF`, and `COUNTIFS`.
- Criteria functions may evaluate and allocate more source range data than needed for excluded rows.
- Importing one very large generated module may create significant parser, bytecode, function-object,
  and symbol-table overhead before `calculate()` starts.
- Pipeline JSON caches may trade CPU time for high memory use because workbook, graph, expression,
  inference, generated-output, and oracle-output records are all materialized as Python objects.
- A small `.xlsx` file can expand to much larger runtime memory because zipped XML, parsed workbook
  records, dependency edges, expression trees, generated Python source, compiled code objects, output
  dictionaries, and validation records are all separate in-memory representations.

## Measurement Plan

Phase 27 should measure before optimizing:

- wall time by pipeline stage;
- generated module import time;
- formula execution time by generated cell or by sheet/block;
- helper time and call counts for `_get`, `_range`, `_table`, criteria functions, lookups, and
  arithmetic/coercion helpers;
- repeated range/table materialization counts;
- peak memory around cache load, generation, import, execution, and comparison.

Raw profiler outputs should stay under ignored `tmp/`. Sanitized conclusions belong in this note or a
successor planning note.

## Baseline Profile: 2026-06-21

Ignored raw artifacts:

- `tmp/p27_profile_generated_model.py`
- `tmp/logs/p27-profile-import-only.log`
- `tmp/logs/p27-profile-full-execution.log`
- `tmp/p27-profile/generated-model-profile.json`
- `tmp/p27-profile/generated_fable_2020_model_profiled.py`

Scope:

- reused the Phase 26 generated source artifact:
  `tmp/p26-fable-full-validation/generated_fable_2020_model.py`;
- did not regenerate extraction, graph, expressions, inference, or source code;
- instrumented a temporary copy of the generated source under ignored `tmp/`;
- measured import-only behavior and full `calculate()` behavior over the 2020 FABLE comparable-output
  universe.

Headline measurements:

- generated source size: 198,767,455 bytes;
- import-only elapsed time: 36.079 seconds in the first run and 34.892 seconds in the full profile;
- maximum RSS after import: about 11,222,896 KiB, or roughly 10.7 GiB;
- full profiled `calculate()` elapsed time: 1,502.321 seconds;
- outputs returned: 281,741;
- formula evaluations: 286,505;
- `_get` calls: 251,517,729;
- `_get` constant hits: 188,153,993;
- `_get` cache hits: 63,077,231;
- `_range` calls: 605,817;
- `_range` addressed cells: 364,236,641;
- `_table` calls: 38,336;
- `_table` addressed cells: 4,141,335.

Helper timing caveat:

- helper timings are cumulative and nested because wrappers time helpers that call other wrapped
  helpers; therefore helper seconds should not be summed or compared directly to wall time;
- call counts and relative ranking are still useful for identifying where runtime work concentrates.

Top helper signals:

- `_sf_sumifs`: 199,343 calls;
- `_sf_value`: 251,715,601 calls;
- `_sf_sum_value`: 356,219 calls;
- `_sf_iferror`: 20,976 calls;
- `_sf_matches_criteria`: 121,247,129 calls;
- `_sf_compare_criteria`: 121,296,032 calls;
- `_sf_criteria_equal`: 121,292,302 calls;
- `_sf_numeric_value`: 242,584,604 calls;
- `_sf_coerce_criteria`: 111,343,168 calls.

Initial conclusion:

- the first optimization target should be repeated range and criteria work, not parallel execution;
- P27.2 should focus on reducing repeated `_range` materialization and `SUMIFS` criteria scans while
  preserving lazy evaluation and runtime circular-dependency behavior;
- import/source size remains a major problem at roughly 35 seconds and 10.7 GiB before calculation,
  but generated execution spends about 25 minutes in the current source backend, so P27.2 comes before
  P27.3 unless new evidence contradicts this baseline;
- `_get` appears to cache formula results as intended, but range and criteria helpers still repeatedly
  ask for very large numbers of constants and cached formula values.

## Optimization Directions

Prefer targeted changes supported by measurements:

- cache immutable range/table views where inputs and constants make reuse safe;
- stream or index criteria-function ranges instead of building fresh nested lists for every call;
- pre-index common lookup/criteria columns if the generated workbook repeatedly queries the same table;
- split very large generated modules or move formula definitions into compact data structures if import
  time or code-object memory dominates;
- replace large JSON cache reloads with a local structured store if object materialization dominates;
- compare outputs incrementally if keeping all generated outputs and oracle outputs resident is wasteful.

## Parallelization Directions

The benchmark host may have many cores and enough memory to support parallel experiments. Phase 27
should test that directly rather than assuming a single-process pipeline is acceptable.

Likely good candidates:

- contract inference partitioned by selected output refs or dependency-closure shards, with a
  deterministic merge step for symbols, constants, expressions, selected outputs, and diagnostics;
- formula translation partitioned by formula cell, because each translation is mostly independent once
  extraction and graph metadata are available;
- generated-source rendering partitioned into module chunks or formula-definition blocks;
- validation comparison partitioned by output refs after generated values and oracle values exist.

Harder candidates:

- generated formula execution inside one workbook model, because `_get(cell_ref)` uses shared caches,
  active evaluation stacks, and lazy dependency discovery;
- criteria/range-heavy formulas that share large table scans, because naive multiprocessing may duplicate
  memory and serialization work rather than reducing runtime;
- runtime circular-dependency detection across worker boundaries.

Parallel execution experiments should record:

- worker count;
- wall time versus CPU time;
- peak resident memory;
- serialization and process-startup overhead;
- deterministic output ordering;
- correctness comparison against the serial result.

The first parallel target should be contract inference. It was already observed as an expensive stage,
and its output can be cached and compared deterministically. Generated execution should be profiled
before parallelizing; if it is dominated by repeated range scans, indexing or memoization may beat
process-level parallelism.

## Guardrails

- Do not use cached workbook values to mask generated-model calculation errors.
- Do not sacrifice lazy branch semantics or runtime cycle detection.
- Keep verbose logging and tailable logs for all long benchmark runs.
- Treat performance regressions and correctness regressions separately in reports.
- Phase 27 should not close unless it states what was measured, what changed, what improved, and what
  remains expensive.
