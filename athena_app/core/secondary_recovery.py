"""
Module core/secondary_recovery.py: Analisis Kebutuhan Secondary Recovery / EOR
setelah Kontrak Awal 15 Tahun Berakhir.
Sesuai PRD Addendum v4.1 §6 dan sheet '2.Secondary Recovery Analysis'.
"""

from typing import Dict, Any, List, Optional
import numpy as np


# Parameter Default Skema Secondary Recovery ('2.Secondary Recovery Analysis'!B31:Q60)
DEFAULT_SR_SCHEMES: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "Workover",
        "method": "Reaktivasi sumur idle + workover",
        "rf_cases": {1: 0.001, 2: 0.003, 3: 0.005},
        "S": 2,
        "F": 3,
        "decline": 0.15,
        "n_wells": 87.0,
        "capex_per_well": 159279.0,
        "total_capex": 13857273.0,
        "opex_per_well": 6100.0,
        "total_fixed_opex": 530700.0,
        "variable_cost": 0.0,
        "phasing": [1.0] + [0.0] * 14,
    },
    2: {
        "name": "Infill",
        "method": "Sumur infill baru",
        "rf_cases": {1: 0.005, 2: 0.010, 3: 0.020},
        "S": 4,
        "F": 6,
        "decline": 0.10,
        "n_wells": 8.0,
        "capex_per_well": 6000000.0,
        "total_capex": 48000000.0,
        "opex_per_well": 50000.0,
        "total_fixed_opex": 400000.0,
        "variable_cost": 0.0,
        "phasing": [0.0, 0.5, 0.5] + [0.0] * 12,
    },
    3: {
        "name": "EOR",
        "method": "Polymer flooding (chemical EOR)",
        "rf_cases": {1: 0.010, 2: 0.025, 3: 0.040},
        "S": 6,
        "F": 10,
        "decline": 0.05,
        "n_wells": None,
        "capex_per_well": None,
        "capex_ref": 116000000.0,
        "scale_factor": 0.6,
        "total_capex": 69600000.0,
        "opex_pct": 0.04,
        "total_fixed_opex": 2784000.0,
        "variable_cost": 4.5,
        "phasing": [0.05, 0.10, 0.15, 0.35, 0.20, 0.10, 0.05] + [0.0] * 8,
    },
}


def calculate_secondary_recovery(
    top10_sa: List[Dict[str, Any]],
    existing_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Menghitung analisis Secondary Recovery / EOR untuk 10 skenario Top-10.
    """
    cfg = config or {}

    # 1. Parameter Input
    eor_duration = float(cfg.get("sr_duration_eor", 10))
    rf_case = int(cfg.get("sr_rf_case", 2))       # 1=Low, 2=Mid, 3=High
    price_case = int(cfg.get("sr_price_case", 2)) # 1=Low, 2=Base, 3=High
    gate_threshold = float(cfg.get("sr_gate_threshold", 0.10))
    lifting_factor = float(cfg.get("sr_lifting_factor", 1.0))

    stoiip = float(existing_data.get("stoiip", 950.0)) * 1e6
    reserve_2p = float(existing_data.get("reserve_2p_mmbbl", 38.0)) * 1e6
    eval_period = int(existing_data.get("eval_period", 15))
    dr = float(existing_data.get("dr_main", 0.10))
    split_c = float(existing_data.get("split_c", 0.55))
    tax_rate = float(existing_data.get("tax", 0.40))
    lc0 = float(existing_data.get("lc0", 31.0))
    esc = float(existing_data.get("lc_esc", 0.03))

    prices_map = {
        1: float(existing_data.get("price_low", 64.0)),
        2: float(existing_data.get("price_base", 80.0)),
        3: float(existing_data.get("price_high", 117.0)),
    }
    active_price = prices_map.get(price_case, 80.0)

    # 2. Setup Skema
    schemes = {}
    for sid, base_sc in DEFAULT_SR_SCHEMES.items():
        sc = dict(base_sc)
        rf_val = sc["rf_cases"].get(rf_case, 0.01)
        eur = rf_val * stoiip
        F = eor_duration if sid == 3 else sc["F"]
        S = sc["S"]
        d = sc["decline"]
        leff = (F - S) / 2.0 + (1.0 / d)
        uplift_peak = eur / (365.0 * leff)

        sc["rf_selected"] = rf_val
        sc["eur"] = eur
        sc["F"] = F
        sc["leff"] = leff
        sc["uplift_peak"] = uplift_peak
        schemes[sid] = sc

    # 3. Evaluasi per Skenario
    summary_rows = []
    annual_details = {}

    n_need_sr = 0
    scheme_counts = {"Workover": 0, "Infill": 0, "EOR": 0}
    n_positive_npv = 0
    extra_years_list = []
    max_rem_oil_after = 0.0

    for i, s in enumerate(top10_sa):
        prod_15 = float(s["flows"]["total_prod"])
        sisa_oil = max(0.0, reserve_2p - prod_15)
        sisa_pct = sisa_oil / reserve_2p
        need_sr = sisa_pct > gate_threshold

        npv_initial = float(s["metrics"]["prices"][active_price]["npv10"])

        if need_sr:
            n_need_sr += 1
            # Pemilihan skema
            enough_sids = [sid for sid in [1, 2, 3] if schemes[sid]["eur"] >= sisa_oil]
            if enough_sids:
                chosen_sid = min(enough_sids, key=lambda sid: schemes[sid]["total_capex"])
                selection_reason = "Skema termurah yang cukup menutup sisa oil"
            else:
                chosen_sid = 3
                selection_reason = "EUR skema tidak menutup seluruh sisa oil, dipilih skema dengan recovery terbesar"

            sc = schemes[chosen_sid]
            chosen_name = sc["name"]
            scheme_counts[chosen_name] += 1

            S, F, d = sc["S"], sc["F"], sc["decline"]
            uplift_peak = sc["uplift_peak"]

            # Profil 50 tahun (n = 1..50)
            prod_arr = np.zeros(50)
            cum_prod_arr = np.zeros(50)
            capex_arr = np.zeros(50)
            opex_fix_arr = np.zeros(50)
            var_cost_arr = np.zeros(50)
            lifting_arr = np.zeros(50)
            pv_arr = np.zeros(50)

            cum_p = 0.0
            for n in range(1, 51):
                t = n - 1
                j = n - (eval_period + 1) + S

                if j < S:
                    ramp = 0.0
                elif j >= F:
                    ramp = 1.0
                else:
                    ramp = (j - S + 1) / (F - S + 1)

                decline_mult = (1.0 - d) ** max(0, j - F)
                unconstrained_prod = uplift_peak * ramp * decline_mult * 365.0

                actual_prod = min(unconstrained_prod, max(0.0, sisa_oil - cum_p))
                prod_arr[n - 1] = actual_prod
                cum_p += actual_prod
                cum_prod_arr[n - 1] = cum_p

                # Phasing CAPEX
                if 1 <= j <= 15 and j - 1 < len(sc["phasing"]):
                    capex_arr[n - 1] = sc["total_capex"] * sc["phasing"][j - 1]

                if actual_prod > 0:
                    opex_fix_arr[n - 1] = sc["total_fixed_opex"]

                var_cost_arr[n - 1] = actual_prod * sc["variable_cost"]

                lc_rate = lc0 * ((1.0 + esc) ** t) * lifting_factor
                lifting_arr[n - 1] = actual_prod * lc_rate

                rev = actual_prod * active_price * split_c
                taxable = rev - (capex_arr[n - 1] + opex_fix_arr[n - 1] + var_cost_arr[n - 1] + lifting_arr[n - 1])
                tax = taxable * tax_rate
                net = taxable - tax
                df_val = 1.0 / ((1.0 + dr) ** t)
                pv_arr[n - 1] = net * df_val

            add_capex = float(np.sum(capex_arr))
            add_opex = float(np.sum(opex_fix_arr) + np.sum(var_cost_arr))
            add_lifting = float(np.sum(lifting_arr))
            add_npv = float(np.sum(pv_arr))
            extra_years = int(np.sum(prod_arr > 0))
            extra_years_list.append(extra_years)

            add_prod = float(np.sum(prod_arr))
            total_final_prod = prod_15 + add_prod
            sisa_after = max(0.0, sisa_oil - add_prod)
            new_npv_total = npv_initial + add_npv

            is_feasible = (add_npv > 0)
            if is_feasible:
                n_positive_npv += 1
            econ_status = "Layak" if is_feasible else "Tidak layak"

            annual_details[s["no"]] = {
                "prod": prod_arr,
                "cum_prod": cum_prod_arr,
                "capex": capex_arr,
                "opex": opex_fix_arr + var_cost_arr,
                "pv": pv_arr,
            }
        else:
            chosen_sid = 0
            chosen_name = "-"
            selection_reason = "Tidak perlu: sisa oil di bawah ambang"
            add_capex = "-"
            add_opex = "-"
            add_lifting = "-"
            extra_years = "-"
            add_prod = "-"
            total_final_prod = prod_15
            sisa_after = sisa_oil
            add_npv = "-"
            new_npv_total = npv_initial
            econ_status = "-"

        if sisa_after > max_rem_oil_after:
            max_rem_oil_after = sisa_after

        summary_rows.append({
            "scenario_no": s["no"],
            "name": s["kombinasi"],
            "rank_sa": i + 1,
            "contingency_rate": float(s["cont"]["contingency_rate"]),
            "prod_15_bbl": prod_15,
            "rem_oil_bbl": sisa_oil,
            "rem_oil_pct": sisa_pct,
            "need_sr": "YA" if need_sr else "TIDAK",
            "scheme_used": chosen_name,
            "scheme_reason": selection_reason,
            "add_capex": add_capex,
            "add_opex": add_opex,
            "add_lifting": add_lifting,
            "extra_contract_years": extra_years,
            "add_prod_bbl": add_prod,
            "total_final_prod_bbl": total_final_prod,
            "rem_oil_after_sr_bbl": sisa_after,
            "npv_initial_usd": npv_initial,
            "npv_sr_usd": add_npv,
            "new_npv_total_usd": new_npv_total,
            "econ_status": econ_status,
        })

    min_extra_yrs = min(extra_years_list) if extra_years_list else 0
    max_extra_yrs = max(extra_years_list) if extra_years_list else 0

    return {
        "summary": summary_rows,
        "schemes": schemes,
        "annual_details": annual_details,
        "kpi": {
            "n_need_sr": n_need_sr,
            "total_scenarios": len(top10_sa),
            "scheme_composition": f"Workover: {scheme_counts['Workover']}, Infill: {scheme_counts['Infill']}, EOR: {scheme_counts['EOR']}",
            "extra_years_range": f"{min_extra_yrs} sampai {max_extra_yrs}",
            "n_feasible": n_positive_npv,
            "max_rem_oil_after": max_rem_oil_after,
            "reserve_2p": reserve_2p,
            "active_price": active_price,
            "gate_threshold_pct": gate_threshold * 100,
        },
    }

