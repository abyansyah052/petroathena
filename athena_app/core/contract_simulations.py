"""
Module core/contract_simulations.py: Simulasi Kontrak dan Penipisan Cadangan 2P.
Sesuai PRD Addendum v4.1 §7 dan sheet '2.Contract Simulations'.
"""

import math
from typing import Dict, Any, List, Optional
import numpy as np


def calculate_contract_simulations(
    top10_sa: List[Dict[str, Any]],
    summary_rows: List[Dict[str, Any]],
    existing_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Menghitung simulasi perpanjangan kontrak (Gross Split, Cost Recovery, Exit)
    dan penipisan cadangan 2P (60-year forecast) untuk Top-10 skenario.
    """
    cfg = config or {}

    # 1. Parameter Input
    reserve_2p = float(existing_data.get("reserve_2p_mmbbl", 38.0)) * 1e6
    base_year = int(existing_data.get("base_year", 2026))
    eval_period = int(existing_data.get("eval_period", 15))

    prices = {
        "Low": float(existing_data.get("price_low", 64.0)),
        "Base": float(existing_data.get("price_base", 80.0)),
        "High": float(existing_data.get("price_high", 117.0)),
    }
    drs = {
        "Low": float(existing_data.get("dr_low", 0.08)),
        "Base": float(existing_data.get("dr_main", 0.10)),
        "High": float(existing_data.get("dr_high", 0.12)),
    }

    exit_multiples = {
        "Low": float(cfg.get("exit_mult_low", 2.0)),
        "Base": float(cfg.get("exit_mult_base", 4.0)),
        "High": float(cfg.get("exit_mult_high", 8.0)),
    }
    exit_disc = float(cfg.get("exit_risk_discount", 0.15))

    tax_rate = float(existing_data.get("tax", 0.40))
    split_c = float(existing_data.get("split_c", 0.55))
    ftp_rate = float(cfg.get("cost_recovery_ftp", 0.20))
    etbs_c = float(cfg.get("cost_recovery_etbs_contractor", 0.30))
    etbs_g = 1.0 - etbs_c

    cost_basis = int(cfg.get("contract_cost_basis", 1))  # 1 = PNE, 2 = SA
    c0_portion = float(cfg.get("contract_capex_t0_portion", 1.0))
    esc = float(existing_data.get("lc_esc", 0.03))

    n_years = 60
    t_15 = np.arange(15)
    df_main = 1.0 / ((1.0 + drs["Base"]) ** t_15)
    df_low = 1.0 / ((1.0 + drs["Low"]) ** t_15)
    df_high = 1.0 / ((1.0 + drs["High"]) ** t_15)
    esc_factor = (1.0 + esc) ** t_15

    q0_active_yr = float(existing_data.get("q0", 2000.0)) * 365.0
    n_active = float(existing_data.get("n_active", 58.0))
    n_idle = float(existing_data.get("n_idle", 87.0))
    q0_idle_yr = n_idle * (float(existing_data.get("q0", 2000.0)) / n_active) * 365.0

    reserves_summary = []
    npv_summary = []
    scenario_details = {}

    n_depleted_in_contract = 0
    n_need_extension = 0
    n_exceed_horizon = 0
    extension_counts = {"Gross Split": 0, "Cost Recovery": 0, "Exit": 0}

    # Exit values (identik untuk semua skenario)
    exit_low = reserve_2p * exit_multiples["Low"] * (1.0 - exit_disc)
    exit_base = reserve_2p * exit_multiples["Base"] * (1.0 - exit_disc)
    exit_high = reserve_2p * exit_multiples["High"] * (1.0 - exit_disc)

    for i, s in enumerate(top10_sa):
        uplift = s["flows"]["upl"]
        decline_eff = s["flows"]["dn"]

        # Forecast 60 tahun
        prod_60 = np.zeros(n_years)
        prod_60[0] = q0_active_yr
        for t in range(1, n_years):
            prod_60[t] = (q0_active_yr + q0_idle_yr) * uplift * ((1.0 - decline_eff) ** t)
        cum_60 = np.cumsum(prod_60)

        rate_15_bopd = prod_60[14] / 365.0
        cum_15_bbl = cum_60[14]
        rem_2p_15 = max(0.0, reserve_2p - cum_15_bbl)
        ult_rec = q0_active_yr + (q0_active_yr + q0_idle_yr) * uplift * (1.0 - decline_eff) / decline_eff

        if cum_60[-1] >= reserve_2p:
            depleted_in_horizon = "YA"
        elif ult_rec >= reserve_2p:
            depleted_in_horizon = "YA, melewati horizon"
        else:
            depleted_in_horizon = "TIDAK"

        if depleted_in_horizon == "YA":
            count_less = int(np.sum(cum_60 < reserve_2p))
            rem_prod_needed = reserve_2p - (cum_60[count_less - 1] if count_less > 0 else 0.0)
            prod_in_deplete_yr = prod_60[count_less]
            years_to_deplete = count_less + rem_prod_needed / prod_in_deplete_yr
            cal_year_deplete = base_year + math.ceil(years_to_deplete) - 1
            extra_contract_yrs = max(0, math.ceil(years_to_deplete) - eval_period)
            if extra_contract_yrs == 0:
                contract_status = "Habis dalam kontrak awal"
                n_depleted_in_contract += 1
            else:
                contract_status = "Perlu perpanjangan kontrak"
                n_need_extension += 1
            rate_at_deplete = prod_60[math.ceil(years_to_deplete) - 1] / 365.0
        else:
            n_exceed_horizon += 1
            years_to_deplete = None
            cal_year_deplete = None
            extra_contract_yrs = 0
            contract_status = "2P tidak habis dalam horizon"
            rate_at_deplete = None

        rem_never_rec = max(0.0, reserve_2p - ult_rec)

        # Biaya PNE vs SA
        if cost_basis == 1:
            tot_cpx = float(summary_rows[i]["CAPEX PNE"])
            tot_opx = float(summary_rows[i]["OPEX PNE"])
        else:
            tot_cpx = float(summary_rows[i]["CAPEX SA"])
            tot_opx = float(summary_rows[i]["OPEX SA"])

        prod_15 = prod_60[:15]
        denom_opx = np.sum(prod_15 * esc_factor)
        opex_15 = tot_opx * prod_15 * esc_factor / denom_opx if denom_opx > 0 else np.zeros(15)

        capex_15 = np.zeros(15)
        capex_15[0] = tot_cpx * c0_portion
        if eval_period > 1:
            rem_portion = (1.0 - c0_portion) / (eval_period - 1)
            capex_15[1:] = tot_cpx * rem_portion

        # 1. Gross Split NPV
        gs_npvs = {}
        for p_name, p_val in prices.items():
            gs_npvs[p_name] = float(
                (1.0 - tax_rate) * (
                    split_c * p_val * np.sum(prod_15 * df_main)
                    - np.sum(opex_15 * df_main)
                    - np.sum(capex_15 * df_main)
                )
            )

        gs_base_low_dr = float(
            (1.0 - tax_rate) * (
                split_c * prices["Base"] * np.sum(prod_15 * df_low)
                - np.sum(opex_15 * df_low)
                - np.sum(capex_15 * df_low)
            )
        )
        gs_base_high_dr = float(
            (1.0 - tax_rate) * (
                split_c * prices["Base"] * np.sum(prod_15 * df_high)
                - np.sum(opex_15 * df_high)
                - np.sum(capex_15 * df_high)
            )
        )

        # 2. Cost Recovery NPV
        cr_npvs = {}
        cr_schedules = {}
        for p_name, p_val in prices.items():
            cr_pv_main = 0.0
            cr_pv_low = 0.0
            cr_pv_high = 0.0
            carry = 0.0
            sched = []
            for t in range(15):
                gross = prod_15[t] * p_val
                ftp = gross * ftp_rate
                cost_to_recover = opex_15[t] + capex_15[t] + carry
                recovered = min(gross - ftp, cost_to_recover)
                carry = cost_to_recover - recovered
                etbs = gross - ftp - recovered
                c_revenue = (ftp + etbs) * etbs_c + recovered
                taxable = c_revenue - opex_15[t] - capex_15[t]
                c_tax = taxable * tax_rate
                c_take = taxable - c_tax

                cr_pv_main += c_take * df_main[t]
                cr_pv_low += c_take * df_low[t]
                cr_pv_high += c_take * df_high[t]

                sched.append({
                    "year": t,
                    "gross": gross,
                    "ftp": ftp,
                    "cost_to_recover": cost_to_recover,
                    "recovered": recovered,
                    "etbs": etbs,
                    "c_revenue": c_revenue,
                    "taxable": taxable,
                    "c_tax": c_tax,
                    "c_take": c_take,
                })

            cr_npvs[p_name] = float(cr_pv_main)
            cr_schedules[p_name] = sched
            if p_name == "Base":
                cr_base_low_dr = float(cr_pv_low)
                cr_base_high_dr = float(cr_pv_high)

        # Penentuan Pilihan Terbaik pada Base
        options = {
            "Gross Split": gs_npvs["Base"],
            "Cost Recovery": cr_npvs["Base"],
            "Exit": exit_base,
        }
        best_scheme = max(options, key=options.get)
        extension_counts[best_scheme] += 1

        # Cek stabilitas across Low, Base, High
        best_low = max({"Gross Split": gs_npvs["Low"], "Cost Recovery": cr_npvs["Low"], "Exit": exit_low}, key=lambda k: {"Gross Split": gs_npvs["Low"], "Cost Recovery": cr_npvs["Low"], "Exit": exit_low}[k])
        best_high = max({"Gross Split": gs_npvs["High"], "Cost Recovery": cr_npvs["High"], "Exit": exit_high}, key=lambda k: {"Gross Split": gs_npvs["High"], "Cost Recovery": cr_npvs["High"], "Exit": exit_high}[k])
        is_stable = (best_scheme == best_low == best_high)

        reserves_summary.append({
            "scenario_no": s["no"],
            "name": s["kombinasi"],
            "rank_sa": i + 1,
            "contingency_rate": float(s["cont"]["contingency_rate"]),
            "decline_eff": float(decline_eff),
            "rate_15_bopd": float(rate_15_bopd),
            "cum_15_bbl": float(cum_15_bbl),
            "rem_2p_15_bbl": float(rem_2p_15),
            "ult_rec_bbl": float(ult_rec),
            "depleted_in_horizon": depleted_in_horizon,
            "years_to_deplete": float(years_to_deplete) if years_to_deplete is not None else "-",
            "cal_year_deplete": int(cal_year_deplete) if cal_year_deplete is not None else "-",
            "extra_contract_years": int(extra_contract_yrs) if extra_contract_yrs != "-" else "-",
            "contract_status": contract_status,
            "rate_at_deplete": float(rate_at_deplete) if rate_at_deplete is not None else "-",
            "rem_never_rec_bbl": float(rem_never_rec),
            "selected_scheme": best_scheme,
        })

        npv_summary.append({
            "scenario_no": s["no"],
            "name": s["kombinasi"],
            "rank_sa": i + 1,
            "gs_low": gs_npvs["Low"],
            "gs_base": gs_npvs["Base"],
            "gs_high": gs_npvs["High"],
            "cr_low": cr_npvs["Low"],
            "cr_base": cr_npvs["Base"],
            "cr_high": cr_npvs["High"],
            "exit_low": exit_low,
            "exit_base": exit_base,
            "exit_high": exit_high,
            "selected_scheme": best_scheme,
            "gs_base_low_dr": gs_base_low_dr,
            "gs_base_high_dr": gs_base_high_dr,
            "cr_base_low_dr": cr_base_low_dr,
            "cr_base_high_dr": cr_base_high_dr,
            "is_stable": is_stable,
            "best_low": best_low,
            "best_high": best_high,
        })

        scenario_details[s["no"]] = {
            "prod_60": prod_60,
            "cum_60": cum_60,
            "prod_15": prod_15,
            "opex_15": opex_15,
            "capex_15": capex_15,
            "cr_schedule_base": cr_schedules["Base"],
        }

    top_choice = max(extension_counts, key=extension_counts.get)

    return {
        "reserves_summary": reserves_summary,
        "npv_summary": npv_summary,
        "scenario_details": scenario_details,
        "kpi": {
            "n_depleted_in_contract": n_depleted_in_contract,
            "n_need_extension": n_need_extension,
            "n_exceed_horizon": n_exceed_horizon,
            "top_choice": top_choice,
            "extension_counts": extension_counts,
        },
    }

