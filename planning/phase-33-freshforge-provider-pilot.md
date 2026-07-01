# Phase 33: FreshForge Provider Pilot

## Summary

Phase 33 adds a plan-only FreshForge provider for Modelwright workflow stages.
It is a maintainer-approved parallel lane while Phase 32 remains active.

## Intent

The provider should let FreshForge discover, validate, inspect, and plan a
Modelwright generated-model workflow without executing Modelwright commands or
reading declared artifacts.

## Node Vocabulary

- `modelwright.workbook_extract`
- `modelwright.workbook_graph`
- `modelwright.model_infer_contract`
- `modelwright.model_generate`
- `modelwright.model_execute`
- `modelwright.validation_evaluate`
- `modelwright.conversion_plan`

## Boundaries

- No `freshforge run`.
- No execution adapter.
- No cache, checkpoint, or artifact materialization.
- No FABLE-specific output-ref discovery in Modelwright.
- No GitHub direct-reference FreshForge dependency in Modelwright package
  metadata while preserving PyPI-safe releases.

## Issue Map

- Parent: #205
- P33.1: #206
- P33.2: #207
- P33.3: #208
- P33.4: #209
- P33.5: #210
