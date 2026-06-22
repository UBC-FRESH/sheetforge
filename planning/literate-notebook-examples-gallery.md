# Literate Notebook Examples Gallery

Phase 31 adds real tracked Jupyter notebooks to the examples gallery.

The notebooks are teaching artifacts, not only smoke tests. They should follow a literate programming
shape:

- a title markdown cell;
- short explanatory markdown before each code cell;
- code cells that perform one clear step;
- stored outputs after cells where a user should expect visible DataFrame or text output;
- enough context that a new user can follow why the step exists and what the output means.

## Placement

Notebook files live under:

```text
examples/notebooks/
```

Initial notebooks:

- `examples/notebooks/synthetic-notebook-interface.ipynb`
- `examples/notebooks/fable-2020-notebook-interface.ipynb`

The existing Python modules under `examples/synthetic/` and `examples/fable_2020/` remain importable
source examples and are reused by the notebooks.

## Import Setup

The notebooks are source-tree examples. They include a first code cell that adds the repository root
to `sys.path`, so they work when opened from `tmp/notebooks/` or from another working directory inside
the checkout.

The setup cell intentionally uses the local checkout, not a hidden installed package path, because the
examples are meant to teach the source tree and docs together.

## Validation Policy

Default tests should:

- parse every tracked notebook as JSON;
- verify notebook metadata declares a Python 3 kernel;
- verify each notebook has a title, explanatory markdown, code cells, and stored outputs;
- execute or otherwise verify the synthetic notebook outputs;
- verify the FABLE notebook's stored outputs and provenance without running the expensive generated
  FABLE model in default pytest.

Full FABLE notebook execution remains opt-in for local validation because the generated model import
and calculation are intentionally production-sized.

## Non-Goals

Phase 31 does not add:

- a notebook execution service;
- widget dashboards;
- a full spreadsheet UI;
- automatic workbook semantic recovery;
- stable public API guarantees;
- Excel-backed recalculation equivalence.
