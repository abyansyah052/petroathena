"""
Test penerimaan T7 sesuai PRD §7.
T7: Seluruh 453 baris Tab 4 (termasuk RANK & Skor) = golden_SA_453.csv
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
from athena_app.core.ranking import compute_ranks_and_scores
from athena_app.config.v5_cell_map import NAME_TO_OLD_ID, NAME_TO_NEW_ID

EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Angker_BCC_Excel_Calculations_V5.xlsx")
GOLDEN_SA_PATH = os.path.join(os.path.dirname(__file__), "golden", "golden_SA_453.csv")


def test_t7_all_453_scenarios_and_ranking():
    loader = V5DataLoader(EXCEL_PATH)
    data = loader.load_all()
    ed = data["existing_data"]
    cp = data["contoh_perhitungan"]

    passed_methods, combos_1092 = filter_hard_constraints(data["methods_18"])
    combos_453 = filter_compatibility(
        combos_1092,
        data["compat_matrix"],
        NAME_TO_OLD_ID,
        NAME_TO_NEW_ID,
    )
    bau_data = calculate_bau_projection(ed)
    golden = pd.read_csv(GOLDEN_SA_PATH, keep_default_na=False)

    method_by_new_id = {m["id_new"]: m for m in data["methods_13"]}

    scenario_rows = []
    # Jalankan proyeksi dan kalkulasi metrik untuk seluruh 453 kombinasi
    for i, c in enumerate(combos_453):
        combo_methods = [method_by_new_id[mid] for mid in c["new_ids"]]
        cont = calculate_contingency(combo_methods, ed["wc0"], data["overlap_weights"])
        costs = calculate_costs_per_well(c["new_ids"], data["breakdown_items"])
        flows = project_combination_annual_flows(c, cont, costs, ed, cp, bau_data)
        metrics = calculate_scenario_financial_metrics(flows, ed, bau_data)

        # Verifikasi kolom fisik dan biaya
        assert abs(flows["total_prod"] - golden.loc[i, "Total Production (bbl)"]) / golden.loc[i, "Total Production (bbl)"] < 1e-7
        assert abs(flows["rem_oil"] - golden.loc[i, "Remaining Oil (bbl)"]) / golden.loc[i, "Remaining Oil (bbl)"] < 1e-7
        assert abs(flows["total_water"] - golden.loc[i, "Total Water (bbl)"]) / golden.loc[i, "Total Water (bbl)"] < 1e-7
        assert abs(flows["total_cpx"] - golden.loc[i, "Total CAPEX"]) / golden.loc[i, "Total CAPEX"] < 1e-9
        assert abs(flows["total_opx"] - golden.loc[i, "Total OPEX"]) / golden.loc[i, "Total OPEX"] < 1e-7

        row_dict = {
            "no": c["no"],
            "kombinasi": c["name"],
            "total_cpx": flows["total_cpx"],
        }
        for P in [64, 80, 117]:
            p_data = metrics["prices"][P]
            row_dict[f"{P}_take"] = p_data["pne_take"]
            row_dict[f"{P}_gov"] = p_data["gov_take"]
            row_dict[f"{P}_npv8"] = p_data["npv8"]
            row_dict[f"{P}_npv10"] = p_data["npv10"]
            row_dict[f"{P}_npv12"] = p_data["npv12"]
            row_dict[f"{P}_irr"] = p_data["irr"]

            # Verifikasi nilai metrik finansial
            assert abs(p_data["pne_take"] - golden.loc[i, f"{P}$ PNE Take"]) / abs(golden.loc[i, f"{P}$ PNE Take"]) < 1e-7
            assert abs(p_data["gov_take"] - golden.loc[i, f"{P}$ Gov Take"]) / abs(golden.loc[i, f"{P}$ Gov Take"]) < 1e-7
            assert abs(p_data["npv8"] - golden.loc[i, f"{P}$ NPV8"]) / abs(golden.loc[i, f"{P}$ NPV8"]) < 1e-7
            assert abs(p_data["npv10"] - golden.loc[i, f"{P}$ NPV10"]) / abs(golden.loc[i, f"{P}$ NPV10"]) < 1e-7
            assert abs(p_data["npv12"] - golden.loc[i, f"{P}$ NPV12"]) / abs(golden.loc[i, f"{P}$ NPV12"]) < 1e-7

            expected_irr = golden.loc[i, f"{P}$ IRR"]
            if expected_irr in ["n/a", "n/m"]:
                assert p_data["irr"] == expected_irr
            else:
                assert abs(p_data["irr"] - float(expected_irr)) < 1e-7

        scenario_rows.append(row_dict)

    # 15 metrik untuk ranking
    metric_keys = []
    for P in [64, 80, 117]:
        for m in ["take", "npv8", "npv10", "npv12", "irr"]:
            metric_keys.append(f"{P}_{m}")

    ranks_matrix, scores, global_ranks = compute_ranks_and_scores(scenario_rows, metric_keys)

    # Verifikasi seluruh 453 Skor dan RANK
    for i in range(len(scenario_rows)):
        expected_score = golden.loc[i, "Skor"]
        expected_rank = int(golden.loc[i, "Rank"])

        assert abs(scores[i] - expected_score) < 1e-9, f"Row {i+1} Skor mismatch: {scores[i]} vs {expected_score}"
        assert global_ranks[i] == expected_rank, f"Row {i+1} Rank mismatch: {global_ranks[i]} vs {expected_rank}"
