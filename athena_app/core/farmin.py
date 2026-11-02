"""
Module farmin.py: kalkulasi Financial Projection (Farm-In) untuk Top-10 skenario Stand-Alone
sesuai PRD §4.5 (Tab 5).
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from athena_app.core.irr import calculate_irr
from athena_app.core.ranking import compute_ranks_and_scores


def calculate_farmin_projection(
    top10_sa_scenarios: List[Dict[str, Any]],
    existing_data: Dict[str, Any],
    contoh_perhitungan: Dict[str, Any],
    prices: List[int] = None,
) -> List[Dict[str, Any]]:
    """
    Menghitung ulang proyeksi finansial Farm-In (PNE vs Partner XYZ) untuk 10 skenario teratas SA.
    Mendukung harga minyak dinamis (Addendum §10.3).
    """
    ed = existing_data
    cp = contoh_perhitungan

    if prices is None:
        p_low = int(ed.get("price_low", 64))
        p_base = int(ed.get("price_base", 80))
        p_high = int(ed.get("price_high", 117))
        prices = [p_low, p_base, p_high]

    wi_pne = cp["wi_pne"]
    wi_xyz = cp["wi_xyz"]
    carry = cp["carry"]
    tax = ed["tax"]
    reserve_2p = ed["reserve_2p"]
    capex_bau_cf = ed["capex_bau_cf"]
    cf_cycles = int((ed["N"] - 1) // ed["fac_life"])  # 2 siklus (t=5, t=10)

    # 30 metrik untuk Farm-In ranking (10 metrik per harga)
    metric_keys_30 = []
    for P in prices:
        for m in [
            "take_pne", "take_xyz",
            "npv8_pne", "npv10_pne", "npv12_pne",
            "npv8_xyz", "npv10_xyz", "npv12_xyz",
            "irr_pne", "irr_xyz"
        ]:
            metric_keys_30.append(f"{P}_{m}")

    fi_rows = []
    for item in top10_sa_scenarios:
        flows = item["flows"]
        metrics = item["metrics"]

        tot_prod = flows["total_prod"]
        rem_oil = reserve_2p - tot_prod
        tot_wat = flows["total_water"]
        tot_cpx_sa = flows["total_cpx"]
        tot_opx_sa = flows["total_opx"]

        # capex0: treatment capex at t=0
        capex0 = tot_cpx_sa - capex_bau_cf * cf_cycles

        # Pembagian CAPEX & OPEX
        cpx_pne = wi_pne * (capex_bau_cf * cf_cycles) + (1.0 - carry) * capex0
        cpx_xyz = wi_xyz * (capex_bau_cf * cf_cycles) + carry * capex0
        opx_pne = tot_opx_sa * wi_pne
        opx_xyz = tot_opx_sa * wi_xyz

        # Penyesuaian carry di t=0
        adjP = (wi_pne - (1.0 - carry)) * (1.0 - tax) * capex0
        adjX = (wi_xyz - carry) * (1.0 - tax) * capex0

        row = {
            "rank_sa": item["sa_rank"],
            "no_kombinasi": item["no"],
            "kombinasi": item["kombinasi"],
            "contingency_rate": item["cont"]["contingency_rate"],
            "total_prod": tot_prod,
            "rem_oil": rem_oil,
            "total_water": tot_wat,
            "cpx_sa": tot_cpx_sa,
            "cpx_pne": cpx_pne,
            "cpx_xyz": cpx_xyz,
            "opx_sa": tot_opx_sa,
            "opx_pne": opx_pne,
            "opx_xyz": opx_xyz,
            "capex0": capex0,
            "adjP": adjP,
            "adjX": adjX,
            "prices": {},
        }

        for P in prices:
            p_sa = metrics["prices"][P]
            inc = metrics["annual_inc"][P]

            take_pne = wi_pne * p_sa["pne_take"] + adjP
            take_xyz = wi_xyz * p_sa["pne_take"] + adjX
            gov_take = p_sa["gov_take"]  # Gov Take tidak berubah

            npv8_pne = wi_pne * p_sa["npv8"] + adjP
            npv10_pne = wi_pne * p_sa["npv10"] + adjP
            npv12_pne = wi_pne * p_sa["npv12"] + adjP

            npv8_xyz = wi_xyz * p_sa["npv8"] + adjX
            npv10_xyz = wi_xyz * p_sa["npv10"] + adjX
            npv12_xyz = wi_xyz * p_sa["npv12"] + adjX

            # Inkremental arus kas PNE dan XYZ
            incP = np.copy(inc) * wi_pne
            incP[0] += adjP
            irr_pne = calculate_irr(incP)

            incX = np.copy(inc) * wi_xyz
            incX[0] += adjX
            irr_xyz = calculate_irr(incX)

            row[f"{P}_take_pne"] = take_pne
            row[f"{P}_take_xyz"] = take_xyz
            row[f"{P}_gov_take"] = gov_take
            row[f"{P}_npv8_pne"] = npv8_pne
            row[f"{P}_npv10_pne"] = npv10_pne
            row[f"{P}_npv12_pne"] = npv12_pne
            row[f"{P}_npv8_xyz"] = npv8_xyz
            row[f"{P}_npv10_xyz"] = npv10_xyz
            row[f"{P}_npv12_xyz"] = npv12_xyz
            row[f"{P}_irr_pne"] = irr_pne
            row[f"{P}_irr_xyz"] = irr_xyz

            row["prices"][P] = {
                "take_pne": take_pne,
                "take_xyz": take_xyz,
                "gov_take": gov_take,
                "npv8_pne": npv8_pne,
                "npv10_pne": npv10_pne,
                "npv12_pne": npv12_pne,
                "npv8_xyz": npv8_xyz,
                "npv10_xyz": npv10_xyz,
                "npv12_xyz": npv12_xyz,
                "irr_pne": irr_pne,
                "irr_xyz": irr_xyz,
            }

        fi_rows.append(row)

    # Hitung ranking 30 metrik Farm-In
    ranks_matrix, scores_fi, ranks_fi = compute_ranks_and_scores(fi_rows, metric_keys_30)

    for i in range(len(fi_rows)):
        fi_rows[i]["skor_fi"] = scores_fi[i]
        fi_rows[i]["rank_fi"] = int(ranks_fi[i])
        fi_rows[i]["rank_details"] = {metric_keys_30[j]: ranks_matrix[i, j] for j in range(len(metric_keys_30))}

    return fi_rows
