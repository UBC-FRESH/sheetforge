# Literate Notebook Examples

These notebooks are tracked examples for the Sphinx Examples Gallery.

- `synthetic-notebook-interface.ipynb` is a tiny, fast notebook that can be checked in default tests.
- `fable-2020-notebook-interface.ipynb` documents the production-size generated 2020 FABLE model
  workflow. The notebook contains known-valid stored outputs, while full execution remains opt-in
  because the generated model import and calculation are intentionally large.

Open them from a source checkout with JupyterLab or Jupyter Notebook. The first code cell adds the
repository root to `sys.path` so imports from the local `examples/` directory resolve.
