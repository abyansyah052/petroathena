"""
Test penerimaan T8, T9, dan T10 sesuai PRD §7.
T8: Top-10 Farm-In seluruh kolom, RANK, dan Skor = golden_FarmIn_top10.csv
T9: Tab 6 konsistensi pemetaan dari Tab 4 & Tab 5
T10: Tab 7 kombinasi 1–5 dan BAU: Total produksi, CAPEX, NI, NPV utama = nilai acuan
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
from athena_app.core.farmin import calculate_farmin_projection
from athena_app.core.summary import build_financial_summary
from athena_app.core.worked_example import generate_detailed_annual_block
from athena_app.config.v5_cell_map import NAME_TO_OLD_ID, NAME_TO_NEW_ID

EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Angker_BCC_Excel_Calculations_V5.xlsx")
GOLDEN_FI_PATH = os.path.join(os.path.dirname(__file__), "golden", "golden_FarmIn_top10.csv")


@pytest.fixture(scope="module")
def full_app_pipeline():
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
    method_by_new_id = {m["id_new"]: m for m in data["methods_13"]}

    sa_scenarios = []
    metric_keys_15 = []
    for P in [64, 80, 117]:
        for m in ["take", "npv8", "npv10", "npv12", "irr"]:
            metric_keys_15.append(f"{P}_{m}")

    for i, c in enumerate(combos_453):
        combo_methods = [method_by_new_id[mid] for mid in c["new_ids"]]
        cont = calculate_contingency(combo_methods, ed["wc0"], data["overlap_weights"])
        costs = calculate_costs_per_well(c["new_ids"], data["breakdown_items"])
        flows = project_combination_annual_flows(c, cont, costs, ed, cp, bau_data)
        metrics = calculate_scenario_financial_metrics(flows, ed, bau_data)

        row_dict = {
            "idx": i,
            "no": c["no"],
            "kombinasi": c["name"],
            "flows": flows,
            "metrics": metrics,
            "cont": cont,
            "costs": costs,
        }
        for P in [64, 80, 117]:
            p_data = metrics["prices"][P]
            row_dict[f"{P}_take"] = p_data["pne_take"]
            row_dict[f"{P}_npv8"] = p_data["npv8"]
            row_dict[f"{P}_npv10"] = p_data["npv10"]
            row_dict[f"{P}_npv12"] = p_data["npv12"]
            row_dict[f"{P}_irr"] = p_data["irr"]
        sa_scenarios.append(row_dict)

    _, scores_sa, sa_ranks = compute_ranks_and_scores(sa_scenarios, metric_keys_15)
    for i in range(len(sa_scenarios)):
        sa_scenarios[i]["sa_rank"] = int(sa_ranks[i])
        sa_scenarios[i]["sa_score"] = scores_sa[i]

    top10_sa = sorted(sa_scenarios, key=lambda s: s["sa_rank"])[:10]
    top10_fi = calculate_farmin_projection(top10_sa, ed, cp)
    summary_rows = build_financial_summary(top10_sa, top10_fi)

    golden_fi = pd.read_csv(GOLDEN_FI_PATH, keep_default_na=False)
    return data, bau_data, sa_scenarios, top10_sa, top10_fi, summary_rows, golden_fi


def test_t8_farmin_top10(full_app_pipeline):
    data, _, _, top10_sa, top10_fi, _, golden_fi = full_app_pipeline

    assert len(top10_fi) == 10

    for i in range(10):
        fi = top10_fi[i]
        assert fi["rank_sa"] == golden_fi.loc[i, "No (Rank SA)"]
        assert fi["no_kombinasi"] == golden_fi.loc[i, "No kombinasi"]
        assert fi["kombinasi"] == golden_fi.loc[i, "Kombinasi"]

        # CAPEX PNE & XYZ (rel tol 1e-9)
        assert abs(fi["cpx_pne"] - golden_fi.loc[i, "CAPEX PNE"]) / abs(golden_fi.loc[i, "CAPEX PNE"]) < 1e-9
        assert abs(fi["cpx_xyz"] - golden_fi.loc[i, "CAPEX XYZ"]) / abs(golden_fi.loc[i, "CAPEX XYZ"]) < 1e-9

        # OPEX PNE & XYZ (rel tol 1e-9)
        assert abs(fi["opx_pne"] - golden_fi.loc[i, "OPEX PNE"]) / abs(golden_fi.loc[i, "OPEX PNE"]) < 1e-9
        assert abs(fi["opx_xyz"] - golden_fi.loc[i, "OPEX XYZ"]) / abs(golden_fi.loc[i, "OPEX XYZ"]) < 1e-9

        # Metrik per harga (rel tol 1e-9)
        for P in [64, 80, 117]:
            assert abs(fi[f"{P}_take_pne"] - golden_fi.loc[i, f"{P}$ PNE Take"]) / abs(golden_fi.loc[i, f"{P}$ PNE Take"]) < 1e-9
            assert abs(fi[f"{P}_take_xyz"] - golden_fi.loc[i, f"{P}$ XYZ Take"]) / abs(golden_fi.loc[i, f"{P}$ XYZ Take"]) < 1e-9
            assert abs(fi[f"{P}_gov_take"] - golden_fi.loc[i, f"{P}$ Gov. Take"]) / abs(golden_fi.loc[i, f"{P}$ Gov. Take"]) < 1e-9

            assert abs(fi[f"{P}_npv8_pne"] - golden_fi.loc[i, f"{P}$ NPV,8 PNE"]) / abs(golden_fi.loc[i, f"{P}$ NPV,8 PNE"]) < 1e-9
            assert abs(fi[f"{P}_npv10_pne"] - golden_fi.loc[i, f"{P}$ NPV,10 PNE"]) / abs(golden_fi.loc[i, f"{P}$ NPV,10 PNE"]) < 1e-9
            assert abs(fi[f"{P}_npv12_pne"] - golden_fi.loc[i, f"{P}$ NPV,12 PNE"]) / abs(golden_fi.loc[i, f"{P}$ NPV,12 PNE"]) < 1e-9

            assert abs(fi[f"{P}_npv8_xyz"] - golden_fi.loc[i, f"{P}$ NPV,8 XYZ"]) / abs(golden_fi.loc[i, f"{P}$ NPV,8 XYZ"]) < 1e-9
            assert abs(fi[f"{P}_npv10_xyz"] - golden_fi.loc[i, f"{P}$ NPV,10 XYZ"]) / abs(golden_fi.loc[i, f"{P}$ NPV,10 XYZ"]) < 1e-9
            assert abs(fi[f"{P}_npv12_xyz"] - golden_fi.loc[i, f"{P}$ NPV,12 XYZ"]) / abs(golden_fi.loc[i, f"{P}$ NPV,12 XYZ"]) < 1e-9

            # IRR PNE & XYZ
            gold_irr_pne = golden_fi.loc[i, f"{P}$ IRR PNE"]
            gold_irr_xyz = golden_fi.loc[i, f"{P}$ IRR XYZ"]
            if gold_irr_pne in ["n/a", "n/m"]:
                assert fi[f"{P}_irr_pne"] == gold_irr_pne
            else:
                assert abs(fi[f"{P}_irr_pne"] - float(gold_irr_pne)) < 1e-7

            if gold_irr_xyz in ["n/a", "n/m"]:
                assert fi[f"{P}_irr_xyz"] == gold_irr_xyz
            else:
                assert abs(fi[f"{P}_irr_xyz"] - float(gold_irr_xyz)) < 1e-7

        # Skor & RANK Farm-In
        assert abs(fi["skor_fi"] - golden_fi.loc[i, "Skor"]) < 1e-9
        assert fi["rank_fi"] == int(golden_fi.loc[i, "RANK"])


def test_t9_financial_summary_mapping(full_app_pipeline):
    _, _, _, top10_sa, top10_fi, summary_rows, _ = full_app_pipeline

    assert len(summary_rows) == 10
    for i in range(10):
        s = summary_rows[i]
        sa = top10_sa[i]
        fi = top10_fi[i]

        assert s["No"] == fi["rank_sa"]
        assert s["Kombinasi"] == fi["kombinasi"]
        assert s["Contingency Rate"] == fi["contingency_rate"]
        assert s["Total Production"] == fi["total_prod"]

        assert s["CAPEX SA"] == fi["cpx_sa"]
        assert s["CAPEX PNE"] == fi["cpx_pne"]
        assert s["CAPEX XYZ"] == fi["cpx_xyz"]

        assert s["OPEX SA"] == fi["opx_sa"]
        assert s["OPEX PNE"] == fi["opx_pne"]
        assert s["OPEX XYZ"] == fi["opx_xyz"]

        for P in [64, 80, 117]:
            assert s[f"{P}$ NPV,10 SA"] == sa[f"{P}_npv10"]
            assert s[f"{P}$ NPV,10 PNE"] == fi[f"{P}_npv10_pne"]
            assert s[f"{P}$ NPV,10 XYZ"] == fi[f"{P}_npv10_xyz"]

            assert s[f"{P}$ IRR SA"] == sa[f"{P}_irr"]
            assert s[f"{P}$ IRR PNE"] == fi[f"{P}_irr_pne"]
            assert s[f"{P}$ IRR XYZ"] == fi[f"{P}_irr_xyz"]

            assert s[f"{P}$ Take SA"] == sa[f"{P}_take"]
            assert s[f"{P}$ Take PNE"] == fi[f"{P}_take_pne"]
            assert s[f"{P}$ Take XYZ"] == fi[f"{P}_take_xyz"]
            assert s[f"{P}$ Gov. Take FI"] == fi[f"{P}_gov_take"]

        assert s["RANK (1 = terbaik)"] == fi["rank_fi"]


def test_t10_worked_example_audit(full_app_pipeline):
    data, bau_data, sa_scenarios, _, _, _, _ = full_app_pipeline
    ed = data["existing_data"]
    cp = data["contoh_perhitungan"]

    # Kombinasi 1 s.d. 5 audit trail
    for i in range(5):
        s_item = sa_scenarios[i]
        block = generate_detailed_annual_block(s_item, 80.0, ed, cp, bau_data, is_bau=False)

        total_prod = np.sum(block["rows"]["Production (bbl)"])
        total_cpx = np.sum(block["rows"]["CAPEX"])
        total_ni = np.sum(block["rows"]["Net Income (SA)"])
        npv10_sa = block["decision_metrics"]["SA"]["NPV,10"]
        npv10_pne = block["decision_metrics"]["PNE (FI)"]["NPV,10"]
        npv10_xyz = block["decision_metrics"]["XYZ (FI)"]["NPV,10"]

        assert abs(total_prod - s_item["flows"]["total_prod"]) < 1e-7
        assert abs(total_cpx - s_item["flows"]["total_cpx"]) < 1e-7
        assert abs(total_ni - s_item["80_take"]) < 1e-7
        assert abs(npv10_sa - s_item["80_npv10"]) < 1e-7
