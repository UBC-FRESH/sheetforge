Synthetic Notebook Interface
============================

This tiny example uses a small generated-model-shaped ``calculate(inputs=None)`` function, wraps it
with ``ModelFacade``, and renders outputs, a declared table, and a baseline-vs-scenario comparison as
DataFrames.

Open the literate notebook:

- :download:`synthetic-notebook-interface.ipynb <../../examples/notebooks/synthetic-notebook-interface.ipynb>`

Run it from the repository root:

.. code-block:: bash

   python examples/synthetic/notebook_interface.py

Use it from a notebook stored under ``tmp/notebooks/``:

.. code-block:: python

   from pathlib import Path
   import sys

   repo_root = Path.cwd().resolve()
   while repo_root != repo_root.parent and not (repo_root / "pyproject.toml").exists():
       repo_root = repo_root.parent

   if not (repo_root / "pyproject.toml").exists():
       raise RuntimeError("Could not find the Modelwright repository root.")

   sys.path.insert(0, str(repo_root))

   from examples.synthetic.notebook_interface import build_facade
   from modelwright.notebooks import compare_scenarios_frame, inputs_frame, outputs_frame, table_frame

   facade = build_facade()
   baseline = facade.scenario(name="baseline", inputs={"Inputs!B2": 100, "Inputs!B3": 0.1})
   shock = baseline.with_input("Inputs!B2", 120)

   inputs_frame(facade, shock)

Source
------

.. literalinclude:: ../../examples/synthetic/notebook_interface.py
   :language: python
