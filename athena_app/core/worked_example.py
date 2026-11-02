"""
Module worked_example.py: mereplikasi sheet 'Contoh Perhitungan' V5 (Tab 7)
menghasilkan rincian audit tahunan (2026-2040) langkah-demi-langkah per kombinasi dan BAU.
"""

import numpy as np
from typing import Dict, Any, List
from athena_app.core.irr import calculate_irr


def build_parameter_comparison_table(
    combos_data: List[Dict[str, Any]],
    existing_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Menghasilkan tabel ringkasan parameter teknis per kombinasi (K1..K5 default) + BAU
    sesuai tabel A39:G55 sheet Contoh Perhitungan.
    """
    ed = existing_data
    n_act = ed["n_active"]
    n_idl = ed["n_idle"]
    react_c = ed["react_cost"]

    columns = {}
    for c_info in combos_data:
        label = c_info.get("label", f"K{c_info['no']}")
        cont = c_info["cont"]
        costs = c_info["costs"]

        p = cont["contingency_rate"]
        r = cont["wc_reduction_success"]
        p_times_r = p * r
        w_act = cont["wc_new_success"]
        w_idl = cont["wc_new_success"]
        dn = c_info["flows"]["dn"]
        u = cont["u_used"]
        x_upl = 1.0 + p * u

        cpx_w = costs["capex_well"]
        opx_w = costs["opex_well"]

        cpx_act_2026 = cpx_w * n_act
        cpx_idl_2026 = (cpx_w + react_c) * n_idl
        cpx_tot_2026 = cpx_act_2026 + cpx_idl_2026
        opx_tot_annual = opx_w * (n_act + n_idl)

        columns[label] = {
            "Contingency Rate gabungan (p)": p,
            "Penurunan WC jika berhasil (r)": r,
            "Penurunan WC ekspektasi (p x r)": p_times_r,
            "Water cut baru Active": w_act,
            "Water cut baru Idle": w_idl,
            "Decline rate baru": dn,
            "Uplift dipakai (u)": u,
            "Kenaikan produksi dipakai (x = 1 + p*u)": x_upl,
            "CAPEX per sumur": cpx_w,
            "OPEX per sumur per tahun": opx_w,
            "Sumur Active di-treat": n_act,
            "Sumur Idle di-treat": n_idl,
            "CAPEX treatment Active 2026": cpx_act_2026,
            "CAPEX treatment Idle termasuk reaktivasi 2026": cpx_idl_2026,
            "CAPEX treatment total 2026": cpx_tot_2026,
            "OPEX treatment per tahun 2027-2040": opx_tot_annual,
        }

    # Kolom BAU
    columns["BAU"] = {
        "Contingency Rate gabungan (p)": 0.0,
        "Penurunan WC jika berhasil (r)": 0.0,
        "Penurunan WC ekspektasi (p x r)": 0.0,
        "Water cut baru Active": ed["wc0"],
        "Water cut baru Idle": ed["wc_idle0"],
        "Decline rate baru": ed["d0"],
        "Uplift dipakai (u)": 0.0,
        "Kenaikan produksi dipakai (x = 1 + p*u)": 1.0,
        "CAPEX per sumur": 0.0,
        "OPEX per sumur per tahun": 0.0,
        "Sumur Active di-treat": 0,
        "Sumur Idle di-treat": 0,
        "CAPEX treatment Active 2026": 0.0,
        "CAPEX treatment Idle termasuk reaktivasi 2026": 0.0,
        "CAPEX treatment total 2026": 0.0,
        "OPEX treatment per tahun 2027-2040": 0.0,
    }

    return columns


def generate_detailed_annual_block(
    scenario_info: Dict[str, Any],
    price: float,
    existing_data: Dict[str, Any],
    contoh_perhitungan: Dict[str, Any],
    bau_data: Dict[str, Any],
    is_bau: bool = False,
) -> Dict[str, Any]:
    """
    Menghasilkan 36 baris tabel audit tahunan (t=0..14 + Total) untuk harga tertentu.
    """
    ed = existing_data
    cp = contoh_perhitungan
    N = int(ed["N"])
    t_arr = np.arange(N)
    years = [2026 + t for t in range(N)]

    split_c = ed["split_c"]
    split_g = ed["split_g"]
    tax = ed["tax"]
    dr_main = ed["dr_main"]
    fac_life = int(ed["fac_life"])
    capex_bau_cf = ed["capex_bau_cf"]
    opex_bau = ed["opex_bau"]
    lif = bau_data["lif"]

    wi_pne = cp["wi_pne"]
    wi_xyz = cp["wi_xyz"]
    carry = cp["carry"]

    yrc = np.where((t_arr > 0) & (t_arr % fac_life == 0), 1.0, 0.0)

    if is_bau:
        pra = bau_data["bpr"]
        pri = np.zeros(N)
        prd = pra
        # Catatan PRD §8 poin 4: water cut BAU di Tab 7 memakai eksponen t (bukan t-1)
        wca = 1.0 - (1.0 - ed["wc0"]) * (1.0 - ed["d0"]) ** t_arr
        wci = np.full(N, ed["wc_idle0"])
        wat_act = pra * wca / (1.0 - wca)
        wat_idl = np.zeros(N)
        wat_tot = wat_act

        cpx_act = yrc * capex_bau_cf
        cpx_idl = np.zeros(N)
        cpx = cpx_act + cpx_idl

        opx_bau_row = (1.0 - yrc) * opex_bau
        opx_treat = np.zeros(N)
        opx = opx_bau_row + opx_treat
    else:
        flows = scenario_info["flows"]
        costs = scenario_info["costs"]
        n_act = ed["n_active"]
        n_idl = ed["n_idle"]
        react_c = ed["react_cost"]

        pra = flows["pra"]
        pri = flows["pri"]
        prd = flows["prd"]
        wca = flows["wca"]
        wci = flows["wci"]
        wat_act = pra * wca / (1.0 - wca)
        wat_idl = pri * wci / (1.0 - wci)
        wat_tot = wat_act + wat_idl

        # CAPEX Active: t=0 capex_well*n_act; t=5,10 capex_bau_cf
        cpx_act = np.zeros(N)
        cpx_act[0] = costs["capex_well"] * n_act
        cpx_act += yrc * capex_bau_cf

        # CAPEX Idle: t=0 (capex_well + react_cost)*n_idle
        cpx_idl = np.zeros(N)
        cpx_idl[0] = (costs["capex_well"] + react_c) * n_idl
        cpx = cpx_act + cpx_idl

        opx_bau_row = (1.0 - yrc) * opex_bau
        opx_treat = np.zeros(N)
        opx_treat[1:] = costs["opex_well"] * (n_act + n_idl)
        opx = opx_bau_row + opx_treat

    # Keuangan tahunan
    gross_rev = prd * price
    contractor = gross_rev * split_c
    gov = gross_rev * split_g
    lifting_cost = prd * lif

    taxable = contractor - (cpx + opx + lifting_cost)
    tax_amt = taxable * tax
    ni_sa = taxable * (1.0 - tax)

    df = 1.0 / ((1.0 + dr_main) ** t_arr)
    pv_sa = ni_sa * df
    cum_ni_sa = np.cumsum(ni_sa)

    # Farm-In tahunan
    # capex0: treatment capex at t=0
    capex0 = cpx[0]
    adjP = (wi_pne - (1.0 - carry)) * (1.0 - tax) * capex0
    adjX = (wi_xyz - carry) * (1.0 - tax) * capex0

    cpx_pne = np.empty(N)
    cpx_pne[0] = cpx[0] * (1.0 - carry)
    cpx_pne[1:] = cpx[1:] * wi_pne

    cpx_xyz = np.empty(N)
    cpx_xyz[0] = cpx[0] * carry
    cpx_xyz[1:] = cpx[1:] * wi_xyz

    tot_opx_lift = opx + lifting_cost
    opx_pne = tot_opx_lift * wi_pne
    opx_xyz = tot_opx_lift * wi_xyz

    ni_pne = np.empty(N)
    ni_pne[0] = ni_sa[0] * wi_pne + adjP
    ni_pne[1:] = ni_sa[1:] * wi_pne

    ni_xyz = np.empty(N)
    ni_xyz[0] = ni_sa[0] * wi_xyz + adjX
    ni_xyz[1:] = ni_sa[1:] * wi_xyz

    # Incremental vs BAU
    ni_bau = bau_data["nib"][price]
    inc_sa = ni_sa - ni_bau
    cum_inc_sa = np.cumsum(inc_sa)

    rows_dict = {
        "Year": years,
        "Year no": list(t_arr),
        "Production Active (bbl)": pra,
        "Production Idle (bbl)": pri,
        "Production (bbl)": prd,
        "Water cut Active": wca,
        "Water cut Idle": wci,
        "Water Active (bbl)": wat_act,
        "Water Idle (bbl)": wat_idl,
        "Water (bbl)": wat_tot,
        "Gross Revenue": gross_rev,
        "Lifting Cost (USD/bbl)": lif,
        "Kontraktor": contractor,
        "Governance": gov,
        "CAPEX Active (termasuk carry-forward BAU)": cpx_act,
        "CAPEX Idle (termasuk reaktivasi)": cpx_idl,
        "CAPEX": cpx,
        "OPEX BAU": opx_bau_row,
        "OPEX treatment": opx_treat,
        "OPEX": opx,
        "Lifting Cost": lifting_cost,
        "Taxable Income": taxable,
        "Tax": tax_amt,
        "Net Income (SA)": ni_sa,
        "DF": df,
        "PV": pv_sa,
        "Cum. Net Income (SA)": cum_ni_sa,
        "CAPEX PNE (FI)": cpx_pne,
        "CAPEX XYZ (FI)": cpx_xyz,
        "OPEX + Lifting PNE (FI)": opx_pne,
        "OPEX + Lifting XYZ (FI)": opx_xyz,
        "Net Income PNE (FI)": ni_pne,
        "Net Income XYZ (FI)": ni_xyz,
        "Net Income Inkremental vs BAU (SA)": inc_sa,
        "Cum. Inkremental": cum_inc_sa,
    }

    # Financial decision metrics
    npv8_sa = float(np.sum(ni_sa / (1.08 ** t_arr)))
    npv10_sa = float(np.sum(ni_sa / (1.10 ** t_arr)))
    npv12_sa = float(np.sum(ni_sa / (1.12 ** t_arr)))
    irr_sa = calculate_irr(inc_sa) if not is_bau else "n/a"

    inc_pne = np.copy(inc_sa) * wi_pne
    inc_pne[0] += adjP
    irr_pne = calculate_irr(inc_pne) if not is_bau else "n/a"

    inc_xyz = np.copy(inc_sa) * wi_xyz
    inc_xyz[0] += adjX
    irr_xyz = calculate_irr(inc_xyz) if not is_bau else "n/a"

    npv10_pne = float(np.sum(ni_pne / (1.10 ** t_arr)))
    npv10_xyz = float(np.sum(ni_xyz / (1.10 ** t_arr)))

    pne_take_sa = float(np.sum(ni_sa))
    gov_take_sa = float(np.sum(prd * price * split_g) + np.sum(tax_amt))
    pne_take_fi = float(np.sum(ni_pne))
    xyz_take_fi = float(np.sum(ni_xyz))

    decision_metrics = {
        "SA": {
            "NPV,8": npv8_sa,
            "NPV,10": npv10_sa,
            "NPV,12": npv12_sa,
            "IRR": irr_sa,
            "Take": pne_take_sa,
            "Gov. Take": gov_take_sa,
        },
        "PNE (FI)": {
            "NPV,10": npv10_pne,
            "IRR": irr_pne,
            "Take": pne_take_fi,
        },
        "XYZ (FI)": {
            "NPV,10": npv10_xyz,
            "IRR": irr_xyz,
            "Take": xyz_take_fi,
        },
    }

    return {
        "rows": rows_dict,
        "decision_metrics": decision_metrics,
    }


def get_worked_example_for_scenario(
    scenario_id: Any,
    price: float,
    engine_results: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Menghitung rincian audit tahunan (34 baris) dan parameter perlakuan untuk skenario tertentu
    (atau 'BAU') pada tingkat harga tertentu sesuai Addendum §5.4.
    """
    ed = engine_results["existing_data"]
    cp = engine_results["contoh_perhitungan"]
    bau_data = engine_results["bau_data"]
    sa_scenarios = engine_results["sa_scenarios"]

    if scenario_id == "BAU":
        block = generate_detailed_annual_block({}, price, ed, cp, bau_data, is_bau=True)
        param_table = build_parameter_comparison_table([], ed)
        return {"block": block, "param_table": param_table, "scenario": None, "is_bau": True}

    scenario_info = next((s for s in sa_scenarios if s["no"] == int(scenario_id)), None)
    if scenario_info is None:
        scenario_info = sa_scenarios[0]

    block = generate_detailed_annual_block(scenario_info, price, ed, cp, bau_data, is_bau=False)
    param_table = build_parameter_comparison_table([scenario_info], ed)
    return {"block": block, "param_table": param_table, "scenario": scenario_info, "is_bau": False}

