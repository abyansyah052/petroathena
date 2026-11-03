"""
Module engine.py: pipeline komputasi terintegrasi Athena Scenario Generator.
Menjalankan seluruh alur perhitungan dari Tab 1 hingga Tab 7 dalam satu eksekusi cepat (< 2 detik)
dan menyimpan hasilnya untuk UI dan caching.
"""

import time
from typing import Dict, Any, List
import pandas as pd
import numpy as np

from athena_app.core.loader import V5DataLoader
from athena_app.core.combinations import (
    generate_raw_combinations,
    filter_hard_constraints,
    filter_compatibility,
)
from athena_app.core.contingency import calculate_contingency
from athena_app.core.costs import calculate_costs_per_well
from athena_app.core.projection import calculate_bau_projection, project_combination_annual_flows
from athena_app.core.metrics import calculate_scenario_financial_metrics
from athena_app.core.ranking import compute_ranks_and_scores
from athena_app.core.farmin import calculate_farmin_projection
from athena_app.core.summary import build_financial_summary
from athena_app.core.worked_example import build_parameter_comparison_table, generate_detailed_annual_block
from athena_app.config.v5_cell_map import NAME_TO_OLD_ID, NAME_TO_NEW_ID


from athena_app.core.config_manager import ConfigManager, EXCEL_V6_DEFAULTS


class AthenaEngine:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.loader = V5DataLoader(excel_path)
        self.data: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}

    def run_all(self, config_overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        t0 = time.time()
        self.data = self.loader.load_all()
        ed = self.data["existing_data"]
        cp = self.data["contoh_perhitungan"]
        overlap_weights = self.data["overlap_weights"]
        breakdown_items = self.data["breakdown_items"]

        # Inisialisasi ed dengan nilai default EXCEL_V6_DEFAULTS untuk parameter non-sheet
        for k, v in EXCEL_V6_DEFAULTS.items():
            if k not in ed:
                ed[k] = v

        # Terapkan config overrides jika ada (Addendum §10)
        if config_overrides:
            for k, val in config_overrides.items():
                ed[k] = val
            if "eval_period" in config_overrides:
                ed["N"] = int(config_overrides["eval_period"])
            if "split_c" in config_overrides:
                ed["split_g"] = 1.0 - ed["split_c"]
            if "reserve_2p_mmbbl" in config_overrides:
                ed["reserve_2p"] = ed["reserve_2p_mmbbl"] * 1e6
            if "q0" in config_overrides or "n_active" in config_overrides:
                ed["q_idle"] = ed["q0"] / ed["n_active"]
            if "wc0" in config_overrides:
                ed["wc_idle0"] = ed["wc0"]
            if "capex_annual_field" in config_overrides or "fac_life" in config_overrides:
                ed["opex_bau"] = float(ed.get("capex_annual_field", 4.0)) * 1e6
                ed["capex_bau_cf"] = ed["opex_bau"] * float(ed.get("fac_life", 5))
            if "carbon_price_rp" in config_overrides or "usd_rate" in config_overrides:
                ed["carbon_tax_rate"] = float(ed.get("carbon_price_rp", 30000.0)) / float(ed.get("usd_rate", 17669.0))
            if "alpha" in config_overrides:
                cp["alpha"] = config_overrides["alpha"]
            if "wi_xyz" in config_overrides:
                cp["wi_xyz"] = config_overrides["wi_xyz"]
                cp["wi_pne"] = 1.0 - cp["wi_xyz"]
            if "carry" in config_overrides:
                cp["carry"] = config_overrides["carry"]
            if "overlap_same_func" in config_overrides:
                overlap_weights["same_function"] = config_overrides["overlap_same_func"]
            if "overlap_same_class" in config_overrides:
                overlap_weights["same_class"] = config_overrides["overlap_same_class"]
            if "overlap_diff_class" in config_overrides:
                overlap_weights["diff_class"] = config_overrides["overlap_diff_class"]

        # Harga dinamis
        p_low = int(ed.get("price_low", 64))
        p_base = int(ed.get("price_base", 80))
        p_high = int(ed.get("price_high", 117))
        prices = [p_low, p_base, p_high]

        # TAB 1: 4.047 Raw Combinations
        raw_combos = generate_raw_combinations(self.data["methods_18"])

        # TAB 2: Hard Constraint (1.092) & Compatibility (453)
        passed_methods, combos_1092 = filter_hard_constraints(self.data["methods_18"])
        combos_453 = filter_compatibility(
            combos_1092,
            self.data["compat_matrix"],
            NAME_TO_OLD_ID,
            NAME_TO_NEW_ID,
        )

        # TAB 3: Contingency & Costs for 453 combos
        method_by_new_id = {m["id_new"]: m for m in self.data["methods_13"]}
        wc0 = ed["wc0"]

        contingency_list = []
        costs_list = []
        for c in combos_453:
            combo_methods = [method_by_new_id[mid] for mid in c["new_ids"]]
            cont = calculate_contingency(combo_methods, wc0, overlap_weights)
            costs = calculate_costs_per_well(c["new_ids"], breakdown_items)
            contingency_list.append(cont)
            costs_list.append(costs)

        # TAB 4: BAU & SA Projections (453 scenarios)
        bau_data = calculate_bau_projection(ed, prices=prices)

        sa_scenarios = []
        metric_keys_15 = []
        for P in prices:
            for m in ["take", "npv8", "npv10", "npv12", "irr"]:
                metric_keys_15.append(f"{P}_{m}")

        for i, c in enumerate(combos_453):
            flows = project_combination_annual_flows(
                c, contingency_list[i], costs_list[i], ed, cp, bau_data
            )
            metrics = calculate_scenario_financial_metrics(flows, ed, bau_data, prices=prices)

            row_dict = {
                "idx": i,
                "no": c["no"],
                "size": c["size"],
                "kombinasi": c["name"],
                "combo": c,
                "cont": contingency_list[i],
                "costs": costs_list[i],
                "flows": flows,
                "metrics": metrics,
            }
            for P in prices:
                p_data = metrics["prices"][P]
                row_dict[f"{P}_take"] = p_data["pne_take"]
                row_dict[f"{P}_gov"] = p_data["gov_take"]
                row_dict[f"{P}_npv8"] = p_data["npv8"]
                row_dict[f"{P}_npv10"] = p_data["npv10"]
                row_dict[f"{P}_npv12"] = p_data["npv12"]
                row_dict[f"{P}_irr"] = p_data["irr"]
            sa_scenarios.append(row_dict)

        ranks_matrix_sa, scores_sa, sa_ranks = compute_ranks_and_scores(sa_scenarios, metric_keys_15)

        # Build Master SA DataFrame (Tab 4) with canonical headers
        sa_table_rows = []
        for i, s in enumerate(sa_scenarios):
            s["sa_rank"] = int(sa_ranks[i])
            s["sa_score"] = scores_sa[i]
            s["sa_rank_details"] = {metric_keys_15[j]: ranks_matrix_sa[i, j] for j in range(len(metric_keys_15))}

            flows = s["flows"]
            row = {
                "No": s["no"],
                "Kombinasi": s["kombinasi"],
                "Ukuran": s["size"],
                "Contingency Rate": s["cont"]["contingency_rate"],
                "Total Production": flows["total_prod"],
                "Remaining Oil": flows["rem_oil"],
                "Total Water": flows["total_water"],
                "Total CAPEX": flows["total_cpx"],
                "Total OPEX": flows["total_opx"],
            }
            for P in prices:
                p_info = s["metrics"]["prices"][P]
                row[f"{P}$ PNE Take"] = p_info["pne_take"]
                row[f"{P}$ Gov. Take"] = p_info["gov_take"]
                row[f"{P}$ NPV,8"] = p_info["npv8"]
                row[f"{P}$ NPV,10"] = p_info["npv10"]
                row[f"{P}$ NPV,12"] = p_info["npv12"]
                row[f"{P}$ IRR"] = p_info["irr"]

            row["RANK (1 = terbaik)"] = s["sa_rank"]
            row["Skor (Rata-rata rank)"] = s["sa_score"]
            sa_table_rows.append(row)

        df_tab4 = pd.DataFrame(sa_table_rows)

        # TAB 5: Farm-In Top-10
        top10_sa = sorted(sa_scenarios, key=lambda x: x["sa_rank"])[:10]
        top10_fi = calculate_farmin_projection(top10_sa, ed, cp, prices=prices)

        fi_table_rows = []
        for fi in top10_fi:
            row = {
                "No": fi["rank_sa"],
                "Kombinasi": fi["kombinasi"],
                "Contingency Rate": fi["contingency_rate"],
                "Total Production": fi["total_prod"],
                "Remaining Oil": fi["rem_oil"],
                "Total Water": fi["total_water"],
                "Total CAPEX -> PNE": fi["cpx_pne"],
                "Total CAPEX -> XYZ": fi["cpx_xyz"],
                "Total OPEX -> PNE": fi["opx_pne"],
                "Total OPEX -> XYZ": fi["opx_xyz"],
            }
            for P in prices:
                p_fi = fi["prices"][P]
                row[f"{P}$ PNE Take"] = p_fi["take_pne"]
                row[f"{P}$ XYZ Take"] = p_fi["take_xyz"]
                row[f"{P}$ Gov. Take"] = p_fi["gov_take"]
                row[f"{P}$ NPV,8 PNE"] = p_fi["npv8_pne"]
                row[f"{P}$ NPV,10 PNE"] = p_fi["npv10_pne"]
                row[f"{P}$ NPV,12 PNE"] = p_fi["npv12_pne"]
                row[f"{P}$ NPV,8 XYZ"] = p_fi["npv8_xyz"]
                row[f"{P}$ NPV,10 XYZ"] = p_fi["npv10_xyz"]
                row[f"{P}$ NPV,12 XYZ"] = p_fi["npv12_xyz"]
                row[f"{P}$ IRR PNE"] = p_fi["irr_pne"]
                row[f"{P}$ IRR XYZ"] = p_fi["irr_xyz"]

            row["RANK (1 = terbaik)"] = fi["rank_fi"]
            row["Rata-rata rank"] = fi["skor_fi"]
            row["No kombinasi"] = fi["no_kombinasi"]
            fi_table_rows.append(row)

        df_tab5 = pd.DataFrame(fi_table_rows)

        # TAB 6: Financial Summary
        summary_rows = build_financial_summary(top10_sa, top10_fi, prices=prices)
        df_tab6 = pd.DataFrame(summary_rows)

        # TAB 7: Parameter table for Worked Example
        combos_k1_to_k5 = sa_scenarios[:5]
        param_table_tab7 = build_parameter_comparison_table(combos_k1_to_k5, ed)

        duration = time.time() - t0

        config_diffs = ConfigManager.get_diffs(config_overrides) if config_overrides else []
        active_cfg = EXCEL_V6_DEFAULTS.copy()
        if config_overrides:
            active_cfg.update(config_overrides)

        self.results = {
            "duration_sec": duration,
            "raw_combos": raw_combos,
            "passed_methods": passed_methods,
            "combos_1092": combos_1092,
            "combos_453": combos_453,
            "contingency_list": contingency_list,
            "costs_list": costs_list,
            "bau_data": bau_data,
            "sa_scenarios": sa_scenarios,
            "df_tab4": df_tab4,
            "top10_sa": top10_sa,
            "top10_fi": top10_fi,
            "df_tab5": df_tab5,
            "summary_rows": summary_rows,
            "df_tab6": df_tab6,
            "param_table_tab7": param_table_tab7,
            "existing_data": ed,
            "contoh_perhitungan": cp,
            "methods_18": self.data["methods_18"],
            "methods_13": self.data["methods_13"],
            "compat_matrix": self.data["compat_matrix"],
            "breakdown_items": breakdown_items,
            "config_diffs": config_diffs,
            "active_config": active_cfg,
            "price_levels": prices,
        }
        return self.results
