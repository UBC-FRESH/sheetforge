from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook


EXPECTED_OUTPUTS = {
    "Calc!B1": 5,
    "Calc!B2": 1,
    "Calc!B3": 6,
    "Calc!B4": 1.5,
    "Calc!B5": 9,
    "Calc!B6": -3,
    "Calc!B7": "xy",
    "Calc!B8": False,
    "Calc!B9": True,
    "Calc!B10": True,
    "Calc!B11": False,
    "Calc!B12": False,
    "Calc!B13": True,
    "Calc!B14": True,
    "Calc!B15": 1.5,
    "Calc!B16": "yes",
    "Calc!B17": True,
}


def build_workbook(path: str | Path) -> Path:
    """Write a small workbook covering currently supported semantics."""

    workbook_path = Path(path)
    workbook_path.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    inputs = workbook.active
    inputs.title = "Inputs"
    calc = workbook.create_sheet("Calc")

    inputs["A1"] = "Input"
    inputs["B1"] = "Value"
    inputs["A2"] = "Number"
    inputs["B2"] = 3
    inputs["A3"] = "Text"
    inputs["B3"] = "x"
    inputs["A4"] = "Denominator"
    inputs["B4"] = 2

    calc["A1"] = "Semantics"
    calc["B1"] = "=Inputs!B2+Inputs!B4"
    calc["B2"] = "=Inputs!B2-Inputs!B4"
    calc["B3"] = "=Inputs!B2*Inputs!B4"
    calc["B4"] = "=Inputs!B2/Inputs!B4"
    calc["B5"] = "=Inputs!B2^Inputs!B4"
    calc["B6"] = "=-Inputs!B2"
    calc["B7"] = '=Inputs!B3&"y"'
    calc["B8"] = "=FALSE"
    calc["B9"] = "=Inputs!B2>Inputs!B4"
    calc["B10"] = "=Inputs!B2>=Inputs!B4"
    calc["B11"] = "=Inputs!B2<Inputs!B4"
    calc["B12"] = "=Inputs!B2<=Inputs!B4"
    calc["B13"] = "=Inputs!B2=Inputs!B2"
    calc["B14"] = "=Inputs!B2<>Inputs!B4"
    calc["B15"] = "=ROUND(B4,1)"
    calc["B16"] = '=IF(B9,"yes","no")'
    calc["B17"] = "=TRUE"

    workbook.save(workbook_path)
    return workbook_path
