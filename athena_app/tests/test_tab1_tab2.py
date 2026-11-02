"""
Test penerimaan T1 dan T2 sesuai PRD §7.
T1: Raw combinations 4.047
T2: Hard constraint 1.092 -> Compatibility 453 (13/65/161/214)
"""

import os
import pytest
from athena_app.core.loader import V5DataLoader
from athena_app.core.combinations import (
    generate_raw_combinations,
    filter_hard_constraints,
    filter_compatibility,
)
from athena_app.config.v5_cell_map import NAME_TO_OLD_ID, NAME_TO_NEW_ID

EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Angker_BCC_Excel_Calculations_V5.xlsx")


@pytest.fixture(scope="module")
def v5_data():
    loader = V5DataLoader(EXCEL_PATH)
    return loader, loader.load_all()


def test_t1_raw_combinations(v5_data):
    loader, data = v5_data
    raw = generate_raw_combinations(data["methods_18"])

    # 1. Total count == 4047
    assert len(raw) == 4047, f"Expected 4047 raw combinations, got {len(raw)}"

    # 2. Check counts by size: 18, 153, 816, 3060
    sizes = [r["size"] for r in raw]
    assert sizes.count(1) == 18
    assert sizes.count(2) == 153
    assert sizes.count(3) == 816
    assert sizes.count(4) == 3060

    # 3. Identical names and order to Combination!B5:B4051
    ws = loader.wb["Combination"]
    excel_names = [ws.cell(r, 2).value for r in range(5, 4052)]
    py_names = [r["name"] for r in raw]
    assert py_names == excel_names, "Raw combination names or order mismatch with Excel Combination!B5:B4051"


def test_t2_hard_constraint_and_compatibility(v5_data):
    loader, data = v5_data
    passed_methods, combos_1092 = filter_hard_constraints(data["methods_18"])

    # 1. 13 passed methods, 1092 combinations
    assert len(passed_methods) == 13
    assert len(combos_1092) == 1092

    # 2. Compatibility filter gives 453 combinations
    passed_combos = filter_compatibility(
        combos_1092,
        data["compat_matrix"],
        NAME_TO_OLD_ID,
        NAME_TO_NEW_ID,
    )
    assert len(passed_combos) == 453

    # 3. Sizes: 13, 65, 161, 214
    sizes = [c["size"] for c in passed_combos]
    assert sizes.count(1) == 13
    assert sizes.count(2) == 65
    assert sizes.count(3) == 161
    assert sizes.count(4) == 214

    # 4. Identical names and order to Combination!R5:R457
    ws_comb = loader.wb["Combination"]
    excel_final_names = [ws_comb.cell(r, 18).value for r in range(5, 458)]
    py_final_names = [c["name"] for c in passed_combos]
    assert py_final_names == excel_final_names, "Passed combination names mismatch with Excel Combination!R5:R457"

    # 5. Method IDs match CRC!D5:G457
    ws_crc = loader.wb["Contingency Rate Combination"]
    for i, c in enumerate(passed_combos):
        r = i + 5
        row_ids = [ws_crc.cell(r, col).value for col in range(4, 8)]
        clean_excel_ids = [int(x) for x in row_ids if x is not None and str(x).strip() != ""]
        assert c["new_ids"] == clean_excel_ids, f"Mismatch at row {r} (No {c['no']}): py {c['new_ids']} vs excel {clean_excel_ids}"
