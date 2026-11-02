"""
Test penerimaan T5 dan T6 sesuai PRD §7.
T5: Kombinasi 1–5 seluruh kolom D..Z Tab 4 = Lampiran F.1 (toleransi relatif 1e-9, string identical)
T6: BAU Total Production, NPV10, dan PNE Take = nilai acuan Excel V5
"""

import os
import pytest
import numpy as np
import pandas as pd
from athena_app.core.loader import V5DataLoader
from athena_app.core.combinations import filter_hard_constraints, filter_compatibility
from athena_app.core.contingency import calculate_contingency
from athena_app.core.costs import calculate_costs_per_well
from athena_app.core.projection import calculate_bau_projection, project_combination_annual_flows
from athena_app.core.metrics import calculate_scenario_financial_metrics
from athena_app.config.v5_cell_map import NAME_TO_OLD_ID, NAME_TO_NEW_ID

EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Angker_BCC_Excel_Calculations_V5.xlsx")
GOLDEN_SA_PATH = os.path.join(os.path.dirname(__file__), "golden", "golden_SA_453.csv")


@pytest.fixture(scope="module")
def app_context():
    loader = V5DataLoader(EXCEL_PATH)
    data = loader.load_all()
    passed_methods, combos_1092 = filter_hard_constraints(data["methods_18"])
    combos_453 = filter_compatibility(
        combos_1092,
        data["compat_matrix"],
        NAME_TO_OLD_ID,
        NAME_TO_NEW_ID,
    )
    bau_data = calculate_bau_projection(data["existing_data"])
    golden = pd.read_csv(GOLDEN_SA_PATH, keep_default_na=False)
    return data, combos_453, bau_data, golden


def test_t6_bau_metrics(app_context):
    data, _, bau_data, _ = app_context

    # 1. Total Production = 6,710,685.24 bbl
    assert abs(bau_data["total_prod"] - 6710685.24) < 1.0

    # 2. PNE Take @64, 80, 117
    m = bau_data["metrics"]
    assert abs(m[64.0]["pne_take"] - (-61802260.03)) < 0.1
    assert abs(m[80.0]["pne_take"] - (-26369841.95)) < 0.1
    assert abs(m[117.0]["pne_take"] - 55567624.86) < 0.1

    # 3. NPV10 @64, 80, 117
    assert abs(m[64.0]["npv10"] - (-29719524.79)) < 0.1
    assert abs(m[80.0]["npv10"] - (-7293006.25)) < 0.1
    assert abs(m[117.0]["npv10"] - 44568317.89) < 0.1


def test_t5_combinations_1_to_5(app_context):
    data, combos_453, bau_data, golden = app_context
    ed = data["existing_data"]
    cp = data["contoh_perhitungan"]
    method_by_new_id = {m["id_new"]: m for m in data["methods_13"]}

    # Cek kombinasi 1 s.d. 5
    for i in range(5):
        c = combos_453[i]
        combo_methods = [method_by_new_id[mid] for mid in c["new_ids"]]
        cont = calculate_contingency(combo_methods, ed["wc0"], data["overlap_weights"])
        costs = calculate_costs_per_well(c["new_ids"], data["breakdown_items"])
        flows = project_combination_annual_flows(c, cont, costs, ed, cp, bau_data)
        metrics = calculate_scenario_financial_metrics(flows, ed, bau_data)

        # Basic flow checks
        assert abs(flows["total_prod"] - golden.loc[i, "Total Production (bbl)"]) / golden.loc[i, "Total Production (bbl)"] < 1e-9
        assert abs(flows["rem_oil"] - golden.loc[i, "Remaining Oil (bbl)"]) / golden.loc[i, "Remaining Oil (bbl)"] < 1e-9
        assert abs(flows["total_water"] - golden.loc[i, "Total Water (bbl)"]) / golden.loc[i, "Total Water (bbl)"] < 1e-9
        assert abs(flows["total_cpx"] - golden.loc[i, "Total CAPEX"]) / golden.loc[i, "Total CAPEX"] < 1e-9
        assert abs(flows["total_opx"] - golden.loc[i, "Total OPEX"]) / golden.loc[i, "Total OPEX"] < 1e-9

        # Prices 64, 80, 117
        for P in [64, 80, 117]:
            p_data = metrics["prices"][P]
            # PNE Take
            assert abs(p_data["pne_take"] - golden.loc[i, f"{P}$ PNE Take"]) / abs(golden.loc[i, f"{P}$ PNE Take"]) < 1e-9
            # Gov Take
            assert abs(p_data["gov_take"] - golden.loc[i, f"{P}$ Gov Take"]) / abs(golden.loc[i, f"{P}$ Gov Take"]) < 1e-9
            # NPVs
            assert abs(p_data["npv8"] - golden.loc[i, f"{P}$ NPV8"]) / abs(golden.loc[i, f"{P}$ NPV8"]) < 1e-9
            assert abs(p_data["npv10"] - golden.loc[i, f"{P}$ NPV10"]) / abs(golden.loc[i, f"{P}$ NPV10"]) < 1e-9
            assert abs(p_data["npv12"] - golden.loc[i, f"{P}$ NPV12"]) / abs(golden.loc[i, f"{P}$ NPV12"]) < 1e-9

            # IRR
            expected_irr = golden.loc[i, f"{P}$ IRR"]
            actual_irr = p_data["irr"]
            if expected_irr in ["n/a", "n/m"]:
                assert actual_irr == expected_irr
            else:
                assert abs(actual_irr - float(expected_irr)) < 1e-9
