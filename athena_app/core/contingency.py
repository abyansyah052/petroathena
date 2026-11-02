"""
Module contingency.py: kalkulasi Tab 3c (Contingency Rate Combination).
Menghitung interaksi metode dalam kombinasi: Overlap, p, r, u, dan batas fisik WC
sesuai PRD §4 Tab 3c.
"""

import itertools
import math
from typing import List, Dict, Any


def calculate_contingency(
    methods: List[Dict[str, Any]],
    wc0: float,
    overlap_weights: Dict[str, float] = None,
) -> Dict[str, Any]:
    """
    Menghitung seluruh parameter Contingency Rate Combination untuk satu kombinasi metode.
    methods: list dict metode (memiliki key 'p', 'r', 'u', 'class', 'f1', 'f2')
    """
    if overlap_weights is None:
        overlap_weights = {
            "same_function": 0.8,
            "same_class": 0.4,
            "diff_class": 0.15,
        }

    n = len(methods)
    p_vals = [m["p"] for m in methods]
    r_vals = [m["r"] for m in methods]
    u_vals = [m["u"] for m in methods]

    # Overlap antar pasangan metode
    if n < 2:
        p_overlap = 0.0
    else:
        ov_list = []
        for m_i, m_j in itertools.combinations(methods, 2):
            f_i = {m_i["f1"]}
            if m_i.get("f2"):
                f_i.add(m_i["f2"])
            f_j = {m_j["f1"]}
            if m_j.get("f2"):
                f_j.add(m_j["f2"])

            if f_i.intersection(f_j):
                ov = overlap_weights["same_function"]
            elif m_i["class"] == m_j["class"]:
                ov = overlap_weights["same_class"]
            else:
                ov = overlap_weights["diff_class"]
            ov_list.append(ov)
        p_overlap = sum(ov_list) / len(ov_list)

    # p Independen (Q), p Tertinggi (R), Contingency Rate (S)
    prod_1_minus_p = 1.0
    for p in p_vals:
        prod_1_minus_p *= (1.0 - p)
    p_indep = 1.0 - prod_1_minus_p
    p_max = max(p_vals)
    contingency_rate = p_max + (1.0 - p_overlap) * (p_indep - p_max)

    # r Independen (T), r Tertinggi (U), Penurunan WC jika berhasil (V)
    prod_1_minus_r = 1.0
    for r in r_vals:
        prod_1_minus_r *= (1.0 - r)
    r_indep = 1.0 - prod_1_minus_r
    r_max = max(r_vals)
    wc_reduction_success = r_max + (1.0 - p_overlap) * (r_indep - r_max)

    # WC Baru jika berhasil (W), Penurunan WC Ekspektasi (X)
    wc_new_success = wc0 * (1.0 - wc_reduction_success)
    wc_reduction_expected = contingency_rate * wc_reduction_success

    # Uplift: Yield u/r (AC), u Tertinggi (AD), u Gabungan (AE)
    sum_u = sum(u_vals)
    sum_r = sum(r_vals)
    yield_ur = (sum_u / sum_r) if sum_r > 0 else 0.0
    u_max = max(u_vals)
    u_combined = max(u_max, wc_reduction_success * yield_ur)

    # Batas Fisik WC (AF), u Dipakai (AG), Kenaikan Minyak Ekspektasi (AH)
    physical_limit_wc = ((1.0 - wc_new_success) / (1.0 - wc0)) - 1.0
    u_used = min(u_combined, physical_limit_wc)
    oil_increase_expected = contingency_rate * u_used

    return {
        "n": n,
        "p_vals": p_vals,
        "r_vals": r_vals,
        "u_vals": u_vals,
        "p_overlap": p_overlap,
        "p_indep": p_indep,
        "p_max": p_max,
        "contingency_rate": contingency_rate,  # S
        "r_indep": r_indep,
        "r_max": r_max,
        "wc_reduction_success": wc_reduction_success,  # V
        "wc_new_success": wc_new_success,  # W
        "wc_reduction_expected": wc_reduction_expected,  # X
        "yield_ur": yield_ur,  # AC
        "u_max": u_max,  # AD
        "u_combined": u_combined,  # AE
        "physical_limit_wc": physical_limit_wc,  # AF
        "u_used": u_used,  # AG
        "oil_increase_expected": oil_increase_expected,  # AH
    }
