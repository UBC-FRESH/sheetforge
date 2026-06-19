# Sheetforge

`sheetforge` is an early-stage project for turning spreadsheet workbooks into transparent, version-controlled, standalone Python models.

The intended direction is a generic workflow that can inspect workbook structure, extract formulas and dependencies, generate maintainable Python source, and validate the generated model against the original workbook outputs.

This repository is currently a bootstrap skeleton. It does not yet define a Python package, command-line interface, dependency manager, test framework, catalog schema, or CI contract.

## Current Focus

- Capture the project contract and agent-assisted workflow.
- Research spreadsheet parsing, formula evaluation, dependency graph, code-generation, and validation approaches.
- Avoid committing private notes, source workbooks, generated clones, or large artifacts while the project shape is still being established.

## Repository Conventions

- `AGENTS.md` is the working contract for AI coding agents.
- `ROADMAP.md` is the current plan and next-step tracker.
- `CHANGE_LOG.md` is the append-only project narrative.
- `planning/` contains focused design notes and research records that are too detailed for the roadmap.
- `tmp/` is ignored local working space for private notes, source workbooks, experiments, and generated scratch outputs.
