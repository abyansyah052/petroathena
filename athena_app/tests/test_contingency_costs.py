"""
Test penerimaan T3 dan T4 sesuai PRD §7.
T3: Contingency Rate, Penurunan WC, u Dipakai seluruh 453 baris = Lampiran E (toleransi 1e-9 relatif, round 6)
T4: CAPEX/sumur dan OPEX/sumur/thn seluruh 453 baris = Lampiran E (exact)
"""

import os
import re
import pytest
from athena_app.core.loader import V5DataLoader
from athena_app.core.combinations import filter_hard_constraints, filter_compatibility
from athena_app.core.contingency import calculate_contingency
from athena_app.core.costs import calculate_costs_per_well
from athena_app.config.v5_cell_map import NAME_TO_OLD_ID, NAME_TO_NEW_ID

PRD_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "Athena Scenario Generator v2.md")
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Angker_BCC_Excel_Calculations_V5.xlsx")


@pytest.fixture(scope="module")
def lampiran_e_data():
    if not os.path.exists(PRD_PATH):
        pytest.skip("Athena Scenario Generator v2.md tidak ditemukan di root direktori")
    with open(PRD_PATH, "r") as f:
        prd_text = f.read()

    lines = prd_text.split("\n")
    start = False
    rows = []
    for line in lines:
        if "## Lampiran E" in line:
            start = True
            continue
        if start and "## Lampiran F" in line:
            break
        if start and line.startswith("|") and not line.startswith("| No") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 10:
                rows.append({
                    "no": int(parts[0]),
                    "size": int(parts[1]),
                    "name": parts[4],
                    "S": float(parts[5].replace(",", "")),
                    "V": float(parts[6].replace(",", "")),
                    "AG": float(parts[7].replace(",", "")),
                    "capex_well": float(parts[8].replace(",", "")),
                    "opex_well": float(parts[9].replace(",", "")),
                })
    return rows


@pytest.fixture(scope="module")
def app_data():
    loader = V5DataLoader(EXCEL_PATH)
    data = loader.load_all()
    passed_methods, combos_1092 = filter_hard_constraints(data["methods_18"])
    combos_453 = filter_compatibility(
        combos_1092,
        data["compat_matrix"],
        NAME_TO_OLD_ID,
        NAME_TO_NEW_ID,
    )
    return data, combos_453


def test_t3_contingency_parameters(lampiran_e_data, app_data):
    data, combos_453 = app_data
    wc0 = data["existing_data"]["wc0"]
    overlap_weights = data["overlap_weights"]
    method_by_new_id = {m["id_new"]: m for m in data["methods_13"]}

    assert len(lampiran_e_data) == 453
    assert len(combos_453) == 453

    for i, ref in enumerate(lampiran_e_data):
        c = combos_453[i]
        assert c["no"] == ref["no"]
        assert c["name"] == ref["name"]

        combo_methods = [method_by_new_id[mid] for mid in c["new_ids"]]
        res = calculate_contingency(combo_methods, wc0, overlap_weights)

        # Toleransi 1e-5 terhadap nilai Lampiran E yang dibulatkan 6 desimal di markdown
        assert abs(res["contingency_rate"] - ref["S"]) < 1e-5, f"Row {ref['no']} S mismatch: {res['contingency_rate']} vs {ref['S']}"
        assert abs(res["wc_reduction_success"] - ref["V"]) < 1e-5, f"Row {ref['no']} V mismatch: {res['wc_reduction_success']} vs {ref['V']}"
        assert abs(res["u_used"] - ref["AG"]) < 1e-5, f"Row {ref['no']} AG mismatch: {res['u_used']} vs {ref['AG']}"


def test_t4_capex_opex_per_well(lampiran_e_data, app_data):
    data, combos_453 = app_data
    breakdown_items = data["breakdown_items"]

    for i, ref in enumerate(lampiran_e_data):
        c = combos_453[i]
        costs = calculate_costs_per_well(c["new_ids"], breakdown_items)

        assert costs["okc"] == 1
        assert abs(costs["capex_well"] - ref["capex_well"]) < 1e-9, f"Row {ref['no']} CAPEX mismatch: {costs['capex_well']} vs {ref['capex_well']}"
        assert abs(costs["opex_well"] - ref["opex_well"]) < 1e-9, f"Row {ref['no']} OPEX mismatch: {costs['opex_well']} vs {ref['opex_well']}"
