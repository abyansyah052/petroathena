"""
Module projection.py: proyeksi tahunan 15 tahun (2026-2040) untuk Stand-Alone dan baseline BAU
sesuai PRD §4.1 - §4.3.
"""

import numpy as np
from typing import Dict, Any, List


def calculate_bau_projection(existing_data: Dict[str, Any], prices: List[float] = None) -> Dict[str, Any]:
    """
    Menghitung arus tahunan dan metrik baseline Business-As-Usual (BAU).
    Mendukung harga minyak dinamis (Addendum §10.3).
    """
    ed = existing_data
    if prices is None:
        p_low = float(ed.get("price_low", 64.0))
        p_base = float(ed.get("price_base", 80.0))
        p_high = float(ed.get("price_high", 117.0))
        prices = [p_low, p_base, p_high]

    q0 = ed["q0"]
    d0 = ed["d0"]
    fac_life = int(ed["fac_life"])
    capex_bau_cf = ed["capex_bau_cf"]
    opex_bau = ed["opex_bau"]
    lc0 = ed["lc0"]
    lc_esc = ed["lc_esc"]
    split_c = ed["split_c"]
    split_g = ed["split_g"]
    tax = ed["tax"]
    N = int(ed["N"])
    t_arr = np.arange(N)

    # Produksi minyak BAU
    bpr = q0 * 365.0 * (1.0 - d0) ** t_arr
    total_prod = float(np.sum(bpr))

    # Biaya BAU
    yrc = np.where((t_arr > 0) & (t_arr % fac_life == 0), 1.0, 0.0)
    bcx = yrc * capex_bau_cf
    bop = (1.0 - yrc) * opex_bau
    lif = lc0 * (1.0 + lc_esc) ** t_arr
    total_cpx = float(np.sum(bcx))
    total_opx = float(np.sum(bop) + np.sum(bpr * lif))

    # Net Income BAU per harga P
    nib = {}
    metrics_bau = {}
    for P in prices:
        P_float = float(P)
        ni = (bpr * P_float * split_c - bcx - bop - bpr * lif) * (1.0 - tax)
        nib[P_float] = ni
        nib[int(P_float)] = ni
        pne_take = float(np.sum(ni))
        gov_take = float(np.sum(bpr * P * split_g) + np.sum(ni * (tax / (1.0 - tax))))
        dr_low = float(ed.get("dr_low", 0.08))
        dr_main = float(ed.get("dr_main", 0.10))
        dr_high = float(ed.get("dr_high", 0.12))
        npv8 = float(np.sum(ni / ((1.0 + dr_low) ** t_arr)))
        npv10 = float(np.sum(ni / ((1.0 + dr_main) ** t_arr)))
        npv12 = float(np.sum(ni / ((1.0 + dr_high) ** t_arr)))
        metrics_bau[P] = {
            "pne_take": pne_take,
            "gov_take": gov_take,
            "npv8": npv8,
            "npv10": npv10,
            "npv12": npv12,
        }

    return {
        "t_arr": t_arr,
        "bpr": bpr,
        "total_prod": total_prod,
        "bcx": bcx,
        "bop": bop,
        "lif": lif,
        "total_cpx": total_cpx,
        "total_opx": total_opx,
        "nib": nib,
        "metrics": metrics_bau,
    }


def project_combination_annual_flows(
    combo: Dict[str, Any],
    contingency_params: Dict[str, Any],
    cost_params: Dict[str, Any],
    existing_data: Dict[str, Any],
    contoh_perhitungan: Dict[str, Any],
    bau_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Menghitung vektor arus tahunan panjang N untuk satu kombinasi intervensi.
    """
    ed = existing_data
    cp = contoh_perhitungan
    wc0 = ed["wc0"]
    wc_idle0 = ed["wc_idle0"]
    d0 = ed["d0"]
    q0 = ed["q0"]
    q_idle = ed["q_idle"]
    n_active = ed["n_active"]
    n_idle = ed["n_idle"]
    react_cost = ed["react_cost"]
    alpha = cp["alpha"]
    N = int(ed["N"])
    t_arr = bau_data["t_arr"]
    bcx = bau_data["bcx"]
    bop = bau_data["bop"]
    lif = bau_data["lif"]

    cs = contingency_params["contingency_rate"]
    pw = cs * contingency_params["wc_reduction_success"]
    wna = wc0 * (1.0 - pw)
    wni = wc_idle0 * (1.0 - pw)
    dn = d0 * (1.0 - alpha * pw)
    upl = 1.0 + cs * contingency_params["u_used"]

    # Produksi minyak pra (aktif) & pri (idle)
    pra = np.empty(N)
    pra[0] = q0 * 365.0
    pra[1:] = q0 * 365.0 * upl * (1.0 - dn) ** t_arr[1:]

    pri = np.empty(N)
    pri[0] = 0.0
    pri[1:] = n_idle * q_idle * 365.0 * upl * (1.0 - dn) ** t_arr[1:]

    prd = pra + pri
    total_prod = float(np.sum(prd))
    rem_oil = float(ed["reserve_2p"] - total_prod)

    # Water cut wca & wci
    wca = np.empty(N)
    wca[0] = wc0
    wca[1:] = 1.0 - (1.0 - wna) * (1.0 - dn) ** (t_arr[1:] - 1)

    wci = np.empty(N)
    wci[0] = wc_idle0
    wci[1:] = 1.0 - (1.0 - wni) * (1.0 - dn) ** (t_arr[1:] - 1)

    water_annual = pra * wca / (1.0 - wca) + pri * wci / (1.0 - wci)
    total_water = float(np.sum(water_annual))

    # CAPEX & OPEX tahunan
    cpx = np.zeros(N)
    cpx[0] = (n_active + n_idle) * cost_params["capex_well"] + n_idle * react_cost
    cpx += bcx

    opx = np.copy(bop)
    opx[1:] += (n_active + n_idle) * cost_params["opex_well"]

    total_cpx = float(np.sum(cpx))
    total_opx = float(np.sum(opx) + np.sum(prd * lif))

    return {
        "pra": pra,
        "pri": pri,
        "prd": prd,
        "wca": wca,
        "wci": wci,
        "water_annual": water_annual,
        "cpx": cpx,
        "opx": opx,
        "total_prod": total_prod,
        "rem_oil": rem_oil,
        "total_water": total_water,
        "total_cpx": total_cpx,
        "total_opx": total_opx,
        "cpx_total": total_cpx,
        "opx_total": total_opx,
        "pw": pw,
        "wna": wna,
        "wni": wni,
        "dn": dn,
        "upl": upl,
    }
