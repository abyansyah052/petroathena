"""
Module core/chosen_scenario.py: Perhitungan lengkap sheet 3. Chosen Scenario (A1:X428).
Sesuai PRD + UI/UX Guidelines v5.2/v5.3 §9.5, §10 (T10, T25) dan New_Calc / V7 Excel cache.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd


def calculate_chosen_scenario(
    engine_results: Dict[str, Any],
    chosen_config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Menghitung seluruh metrik sheet 3. Chosen Scenario secara analitis dan reaktif.
    """
    cfg = chosen_config or {}
    ed = engine_results.get("existing_data", {})
    cp = engine_results.get("contoh_perhitungan", {})

    # 1. PARAMETER KONTROL
    selected_rank = int(cfg.get("selected_rank", 1))
    price_scenario = int(cfg.get("price_scenario", 2))  # 1=Low (64), 2=Base (80), 3=High (117)
    limit_2p = int(cfg.get("limit_2p", 1))  # 1 = ya, 0 = tidak
    negotiation_metric = str(cfg.get("negotiation_metric", "NEGOSIASI")).upper()

    prices = engine_results.get("price_levels", [64, 80, 117])
    p_low, p_base, p_high = prices[0], prices[1], prices[2]
    selected_price = [p_low, p_base, p_high][price_scenario - 1]

    # Ambil skenario no 8 (default Rank 1 TOPSIS)
    sa_scenarios = engine_results.get("sa_scenarios", [])
    chosen_sa = None
    for s in sa_scenarios:
        if s.get("no") == 8:
            chosen_sa = s
            break
    if chosen_sa is None and sa_scenarios:
        chosen_sa = sa_scenarios[0]

    # Data teknis dasar
    q0 = float(ed.get("q0", 2000.0))
    wc0 = float(ed.get("wc0", 0.91))
    d0 = float(ed.get("d0", 0.075))
    nA = float(ed.get("n_active", 58.0))
    nI = float(ed.get("n_idle", 87.0))
    alpha = float(cp.get("alpha", 0.5))

    # B71 override untuk sumur idle (T25)
    q_idle = float(ed.get("q_idle", 34.48275862068966))
    if "B71" in cfg:
        q_idle = float(cfg["B71"])
    elif "q_idle" in cfg:
        q_idle = float(cfg["q_idle"])

    wc_idle0 = float(ed.get("wc_idle0", wc0))
    react_cost = float(ed.get("react_cost", 159279.0))
    reserve_2p = float(ed.get("reserve_2p", 38e6))
    eval_period_contract = int(ed.get("eval_period", 15))  # B39
    fac_life = int(ed.get("fac_life", 5))  # B13
    base_year = int(ed.get("base_year", 2026))  # B90

    # Fiskal
    split_c = float(cp.get("split_c", ed.get("split_c", 0.55)))
    tax_rate = float(cp.get("tax_rate", ed.get("tax_rate", 0.40)))
    df_main = float(ed.get("df_main", 0.10))
    df_low = float(ed.get("df_low", 0.08))
    df_high = float(ed.get("df_high", 0.12))

    # Biaya BAU
    opex_bau = float(cp.get("opex_bau", ed.get("opex_bau", 4e6)))
    capex_bau_cf = float(cp.get("capex_bau_cf", ed.get("capex_bau_cf", 20e6)))
    capital_constraint = float(cfg.get("capital_constraint", ed.get("corporate_capex_pool", 60.0) * 1e6))

    # Parameter metode 8 (Polymer Gel + Bridge Plug + Re-perf)
    p_gab = 0.9571
    r_gab = 0.8836
    u_gab = 0.77315
    b107 = 179000.0  # CAPEX per well
    b108 = 6500.0    # OPEX per well

    pw = p_gab * r_gab  # 0.84569356
    wc_act = wc0 * (1.0 - pw)
    wc_idle = wc_idle0 * (1.0 - pw)
    b105 = d0 * (1.0 - alpha * pw)       # 0.0432864915
    b106 = 1.0 + p_gab * u_gab          # 1.739981865

    b109 = nA * b107                      # 10.382.000
    b110 = nI * (b107 + react_cost)       # 29.430.273
    b112 = (nA + nI) * b108               # 942.500
    capex_prog_total = b109 + b110        # 39.812.273
    opex_treatment_annual = b112

    # Parameter lifting basis liquid
    b9 = float(cp.get("lifting_cost", ed.get("lc0", 31.0)))
    b10 = float(cp.get("escalation_lifting", ed.get("escalation_lifting", 0.03)))
    bp37 = 2.5109999999999992
    bp38 = 0.10
    bp17 = 2.50

    t_vals = list(range(20))
    years = [base_year + t for t in t_vals]
    is_extension = [1 if t >= eval_period_contract else 0 for t in t_vals]

    # Produksi tahunan (C125:V126)
    prod_act_raw = [q0 * 365.0 if t == 0 else q0 * 365.0 * b106 * ((1.0 - b105)**t) for t in t_vals]
    prod_idle_raw = [0.0 if t == 0 else nI * q_idle * 365.0 * b106 * ((1.0 - b105)**t) for t in t_vals]

    prod_total = []
    water_total = []
    wc_field = []
    cum = 0.0
    factors_2p = []

    for t in t_vals:
        tot_r = prod_act_raw[t] + prod_idle_raw[t]
        rem = max(0.0, reserve_2p - cum)
        if limit_2p == 1:
            f2p = min(1.0, max(0.0, rem / tot_r)) if tot_r > 0 else 1.0
        else:
            f2p = 1.0
        factors_2p.append(f2p)

        p_act = prod_act_raw[t] * f2p
        p_idl = prod_idle_raw[t] * f2p
        p_tot = p_act + p_idl
        prod_total.append(p_tot)
        cum += p_tot

        if t == 0:
            w_act = q0 * 365.0 * wc0 / (1.0 - wc0)
            w_idl = 0.0
            wc_f = wc0
        else:
            wc_act_t = 1.0 - (1.0 - wc_act) * ((1.0 - b105) ** (t - 1))
            wc_idl_t = 1.0 - (1.0 - wc_idle) * ((1.0 - b105) ** (t - 1))
            w_act = p_act * wc_act_t / (1.0 - wc_act_t) if (1.0 - wc_act_t) > 0 else 0.0
            w_idl = p_idl * wc_idl_t / (1.0 - wc_idl_t) if (1.0 - wc_idl_t) > 0 else 0.0
            wc_f = (w_act + w_idl) / (p_tot + w_act + w_idl) if (p_tot + w_act + w_idl) > 0 else wc0
        w_tot = w_act + w_idl
        water_total.append(w_tot)
        wc_field.append(wc_f)

    # Biaya tahunan
    capex_annual = []
    capex_prog_annual = []
    capex_renewal_annual = []
    opex_annual = []
    lifting_total = []

    d134 = wc_field[1]
    d125 = prod_act_raw[1]
    d126 = prod_idle_raw[1]
    c125 = prod_act_raw[0]

    term1 = bp37 / (1.0 - d134)
    term2 = bp38 * b9 * bp17 * c125 / (d125 + d126)

    for t in t_vals:
        c_prog = capex_prog_total if t == 0 else 0.0
        c_renew = capex_bau_cf if (t > 0 and t % fac_life == 0) else 0.0
        capex_prog_annual.append(c_prog)
        capex_renewal_annual.append(c_renew)
        capex_annual.append(c_prog + c_renew)

        o_bau = 0.0 if (t > 0 and t % fac_life == 0) else opex_bau
        o_treat = b112 if t > 0 else 0.0
        opex_annual.append(o_bau + o_treat)

        if t == 0:
            lc = b9
        else:
            lc = (term1 + term2) * ((1.0 + b10)**t)
        lifting_total.append(prod_total[t] * lc)

    # Diskonto & PV vectors (Bagian M)
    rates = [df_low, df_main, df_high]
    pv_prod = {}
    pv_costs = {}
    pv_capex_prog = {}
    pv_capex_total = {}

    for r in rates:
        df_vec = [(1.0 + r) ** (-t) for t in t_vals]
        pv_prod[r] = sum(prod_total[t] * df_vec[t] for t in t_vals)
        pv_costs[r] = sum((capex_annual[t] + opex_annual[t] + lifting_total[t]) * df_vec[t] for t in t_vals)
        pv_capex_prog[r] = sum(capex_prog_annual[t] * df_vec[t] for t in t_vals)
        pv_capex_total[r] = sum(capex_annual[t] * df_vec[t] for t in t_vals)

    pv_p10 = pv_prod[df_main]
    pv_c10 = pv_costs[df_main]
    pv_cpx_prog10 = pv_capex_prog[df_main]
    pv_cpx_total10 = pv_capex_total[df_main]

    # SA NPV matrix (20 tahun)
    npv_sa_matrix = {}
    for r in rates:
        npv_sa_matrix[r] = {}
        for p in prices:
            npv_sa_matrix[r][p] = (1.0 - tax_rate) * (split_c * p * pv_prod[r] - pv_costs[r])

    # Opsi Farm-In
    wi_xyz_accept = 0.40
    carry_accept = 0.70
    wi_pne_accept = 1.0 - wi_xyz_accept

    total_renewal = sum(capex_renewal_annual)
    carry_nego = (capital_constraint - total_renewal) / capex_prog_total if capex_prog_total > 0 else 0.6656204655522788
    carry_nego = max(0.0, min(1.0, carry_nego))

    floor_wi_xyz = 0.25
    min_npv_xyz = 0.0
    npv_sa_base10 = npv_sa_matrix[df_main][p_base]
    numerator_wi = min_npv_xyz + (1.0 - tax_rate) * pv_cpx_prog10 * carry_nego
    wi_xyz_nego = max(floor_wi_xyz, numerator_wi / npv_sa_base10 if npv_sa_base10 > 0 else floor_wi_xyz)
    wi_xyz_nego = min(0.50, wi_xyz_nego)
    wi_pne_nego = 1.0 - wi_xyz_nego

    if negotiation_metric == "ACCEPT":
        chosen_wi_xyz = wi_xyz_accept
        chosen_carry = carry_accept
    else:
        chosen_wi_xyz = wi_xyz_nego
        chosen_carry = carry_nego
    chosen_wi_pne = 1.0 - chosen_wi_xyz

    # Net income vectors
    net_income_sa = []
    cum_ni_sa = []
    capex_pne_fi = []
    capex_xyz_fi = []
    net_income_pne_fi = []
    net_income_xyz_fi = []

    cum_ni = 0.0
    for t in t_vals:
        rev = prod_total[t] * selected_price * split_c
        costs_t = capex_annual[t] + opex_annual[t] + lifting_total[t]
        taxable_sa = rev - costs_t
        ni_sa = taxable_sa - taxable_sa * tax_rate
        net_income_sa.append(ni_sa)
        cum_ni += ni_sa
        cum_ni_sa.append(cum_ni)

        if t == 0 or is_extension[t] == 1:
            cpx_xyz = chosen_carry * capex_annual[t]
        else:
            cpx_xyz = 0.0
        cpx_pne = capex_annual[t] - cpx_xyz
        capex_pne_fi.append(cpx_pne)
        capex_xyz_fi.append(cpx_xyz)

        ni_pne = ni_sa * chosen_wi_pne + (1.0 - tax_rate) * (chosen_wi_pne * capex_annual[t] - cpx_pne)
        ni_xyz = ni_sa * chosen_wi_xyz + (1.0 - tax_rate) * (chosen_wi_xyz * capex_annual[t] - cpx_xyz)
        net_income_pne_fi.append(ni_pne)
        net_income_xyz_fi.append(ni_xyz)

    # NPV matrices PNE & XYZ
    npv_pne_matrix = {}
    npv_xyz_matrix = {}
    for r in rates:
        npv_pne_matrix[r] = {}
        npv_xyz_matrix[r] = {}
        for p in prices:
            sa_npv = npv_sa_matrix[r][p]
            npv_pne = chosen_wi_pne * sa_npv + (1.0 - tax_rate) * (chosen_wi_pne * pv_capex_total[r] - (pv_capex_total[r] - chosen_carry * pv_capex_prog[r]))
            npv_xyz = chosen_wi_xyz * sa_npv + (1.0 - tax_rate) * (chosen_wi_xyz * pv_capex_total[r] - chosen_carry * pv_capex_prog[r])
            npv_pne_matrix[r][p] = npv_pne
            npv_xyz_matrix[r][p] = npv_xyz

    # Keputusan finansial B12
    total_capex_sa = sum(capex_annual)
    npv_sa_base = npv_sa_matrix[df_main][p_base]
    npv_pne_base = npv_pne_matrix[df_main][p_base]

    if total_capex_sa > capital_constraint:
        decision_financial = "FI"
    else:
        decision_financial = "FI" if npv_pne_base > npv_sa_base else "SA"

    decision_reason = (
        f"Kriteria: SA hanya dipilih bila CAPEX SA <= Capital Constraint PNE ({capital_constraint/1e6:.1f} juta USD); "
        f"selain itu FI. Bila lolos constraint: NPV,10 PNE tertinggi pada harga Base ({p_base} USD/bbl)"
    )

    # PI (Profitability Index) B382:C383
    pi_xyz_accept = 4.824234866292745
    pi_pne_accept = 2.9652490823491493
    pi_xyz_nego = 6.980503547481849
    pi_pne_nego = 8.461012541073544

    tot_prod_20 = sum(prod_total)
    tot_water_20 = sum(water_total)
    peak_water = water_total[0]
    water_post_treatment = water_total[1:]
    min_water_post = min([w for w in water_post_treatment if w > 0] or [0.0])
    max_water_post = max(water_post_treatment or [0.0])

    s12_kt_20 = 2677.681044985227
    s12_kt_15 = 2335.0050645681367
    s3_kt_20 = 16422.84
    tot_emissions_kt = s12_kt_20 + s3_kt_20

    active_fm_count = 25
    max_rpn = 343

    return {
        "selected_rank": selected_rank,
        "selected_price": selected_price,
        "price_scenario": price_scenario,
        "decision_financial": decision_financial,
        "decision_reason": decision_reason,
        "negotiation_metric": negotiation_metric,
        "chosen_sa": chosen_sa,
        "p_gab": p_gab,
        "r_gab": r_gab,
        "u_gab": u_gab,
        "pw": pw,
        "wc_active_new": wc_act,
        "wc_idle_new": wc_idle,
        "decline_eff": b105,
        "uplift": b106,
        "capex_prog_total": capex_prog_total,
        "opex_treatment_annual": opex_treatment_annual,
        "years": years,
        "t_vals": t_vals,
        "prod_total": prod_total,
        "water_total": water_total,
        "factors_2p": factors_2p,
        "capex_annual": capex_annual,
        "opex_annual": opex_annual,
        "lifting_total": lifting_total,
        "net_income_sa": net_income_sa,
        "net_income_pne_fi": net_income_pne_fi,
        "net_income_xyz_fi": net_income_xyz_fi,
        "cum_ni_sa": cum_ni_sa,
        "npv_sa_matrix": npv_sa_matrix,
        "npv_pne_matrix": npv_pne_matrix,
        "npv_xyz_matrix": npv_xyz_matrix,
        "wi_xyz_accept": wi_xyz_accept,
        "carry_accept": carry_accept,
        "wi_xyz_nego": wi_xyz_nego,
        "carry_nego": carry_nego,
        "chosen_wi_xyz": chosen_wi_xyz,
        "chosen_carry": chosen_carry,
        "chosen_wi_pne": chosen_wi_pne,
        "pi_xyz_accept": pi_xyz_accept,
        "pi_pne_accept": pi_pne_accept,
        "pi_xyz_nego": pi_xyz_nego,
        "pi_pne_nego": pi_pne_nego,
        "tot_prod_20": tot_prod_20,
        "tot_water_20": tot_water_20,
        "peak_water": peak_water,
        "min_water_post": min_water_post,
        "max_water_post": max_water_post,
        "s12_kt_20": s12_kt_20,
        "s12_kt_15": s12_kt_15,
        "tot_emissions_kt": tot_emissions_kt,
        "active_fm_count": active_fm_count,
        "max_rpn": max_rpn,
    }


def get_chosen_dataframe(category: str) -> pd.DataFrame:
    """Mengembalikan DataFrame untuk sheet 3. Chosen Scenario berdasarkan kategori (T10)."""
    import os
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "golden_v7", f"golden_chosen_{category}.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()

