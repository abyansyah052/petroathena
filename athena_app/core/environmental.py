"""
Module core/environmental.py: Model Dampak Lingkungan (Scope 1, 2, 3, dan Produced Water).
Sesuai PRD Addendum v3.1 §4.1 dan aturan audit Excel V6 ('1.Environmental Impact').
"""

from typing import Dict, Any, List
import numpy as np


# Parameter Emisi & Konversi dari '0.Existing Data'!B96:B160
BBL_PER_M3 = 6.2898               # B115
GWP_CH4 = 29.8                    # B113 (AR6)
SCALE_FACTOR = 1.0                # B104

# Scope 1 (IPCC Tier 1 per m3 minyak)
S1_FUGITIVE_CH4 = 0.00295         # B120
S1_VENTING_CH4 = 0.01035          # B121
S1_FLARING_CH4 = 2.5e-5           # B122
S1_FLARING_CO2 = 0.0405           # B123

# Scope 2 (Grid Sumatera & Pengangkatan Buatan)
GRID_SUMATERA_FACTOR = 0.805      # B127 (tCO2e/MWh)
LIFT_ELECTRICITY_KWH_PER_BBL = 0.52 # B128 (kWh/bbl fluida)

# Scope 3
S3_COMBUSTION_T_PER_BBL = 0.43218 # B133 (10.29 kg/gal * 42 gal / 1000)
S3_FRACTION_BURNED = 1.0          # B134 (Kat. 11 aktif)

# Rig Workover Diesel
RIG_EMISSION_PER_DAY = 2.9871673128 # B158 (tCO2e/hari)
RIG_DAYS_IDLE = 17.0              # B159
RIG_DAYS_ACTIVE = 5.0             # B160 (Placeholder teknis)

# Pajak Karbon (Shadow cost)
CARBON_PRICE_USD = 1.6978889580621428 # B145 (Rp30.000 / Rp17.669)


def calculate_scenario_environmental(
    scenario_info: Dict[str, Any],
    existing_data: Dict[str, Any],
    rank_sa: int,
    is_bau: bool = False,
    bau_data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Menghitung profil emisi Scope 1, Scope 2, Scope 3, Produced Water,
    dan intensitas emisi 15 tahun sesuai '1.Environmental Impact'.
    """
    N = 15
    if is_bau:
        prd = bau_data["bpr"]
        wc = existing_data["wc0"]
        wat_tot = prd * wc / (1.0 - wc)
        contingency_p = None
        s1_rig = np.zeros(N)
        name = "BAU - tanpa treatment"
        no_val = 0
        npv10_80 = 0.0
    else:
        flows = scenario_info["flows"]
        pra = flows["pra"]
        pri = flows["pri"]
        prd = flows["prd"]
        wca = flows["wca"]
        wci = flows["wci"]
        wat_act = pra * wca / (1.0 - wca)
        wat_idl = pri * wci / (1.0 - wci)
        wat_tot = wat_act + wat_idl
        
        contingency_p = scenario_info["cont"]["contingency_rate"]
        s1_rig = np.zeros(N)
        n_act = existing_data["n_active"]
        n_idl = existing_data["n_idle"]
        rig_days_idl = float(existing_data.get("rig_days_idle", RIG_DAYS_IDLE))
        rig_days_act = float(existing_data.get("rig_days_active", RIG_DAYS_ACTIVE))
        rig_em_day = float(existing_data.get("rig_emission_per_day", RIG_EMISSION_PER_DAY))
        s1_rig[0] = (n_idl * rig_days_idl + n_act * rig_days_act) * rig_em_day
        name = scenario_info["kombinasi"]
        no_val = scenario_info["no"]
        npv10_80 = scenario_info["metrics"]["prices"][80]["npv10"] / 1e6

    liquid_lifted = prd + wat_tot
    oil_m3 = prd / BBL_PER_M3

    # Parameter dinamis dari existing_data / config_overrides
    scale_factor = float(existing_data.get("scale_factor", SCALE_FACTOR))
    gwp_ch4 = float(existing_data.get("gwp_ch4", GWP_CH4))
    s1_fug = float(existing_data.get("s1_fugitive_ch4", S1_FUGITIVE_CH4))
    s1_vent = float(existing_data.get("s1_venting_ch4", S1_VENTING_CH4))
    s1_flare_ch4 = float(existing_data.get("s1_flaring_ch4", S1_FLARING_CH4))
    s1_flare_co2 = float(existing_data.get("s1_flaring_co2", S1_FLARING_CO2))
    grid_factor = float(existing_data.get("grid_factor_sumatera", GRID_SUMATERA_FACTOR))
    lift_kwh = float(existing_data.get("lift_kwh_per_bbl", LIFT_ELECTRICITY_KWH_PER_BBL))
    s3_combust = float(existing_data.get("s3_oil_combustion", S3_COMBUSTION_T_PER_BBL))

    if "carbon_price_rp" in existing_data and "usd_rate" in existing_data:
        carbon_price_usd = float(existing_data["carbon_price_rp"]) / float(existing_data["usd_rate"])
    else:
        carbon_price_usd = float(existing_data.get("carbon_price_usd", CARBON_PRICE_USD))

    # Scope 1
    s1_fug_vent = oil_m3 * (s1_fug + s1_vent) * gwp_ch4 * scale_factor
    s1_flaring_ch4 = oil_m3 * s1_flare_ch4 * gwp_ch4 * scale_factor
    s1_flaring_co2 = oil_m3 * s1_flare_co2 * scale_factor
    scope1_annual = s1_fug_vent + s1_flaring_ch4 + s1_flaring_co2 + s1_rig

    # Scope 2
    electricity_kwh = liquid_lifted * lift_kwh
    scope2_annual = (electricity_kwh / 1000.0) * grid_factor

    # Scope 3 (Kat. 11)
    scope3_annual = prd * s3_combust * S3_FRACTION_BURNED

    scope12_annual = scope1_annual + scope2_annual
    scope123_annual = scope12_annual + scope3_annual

    # Ringkasan 15 Tahun
    tot_oil_bbl = float(np.sum(prd))
    tot_water_bbl = float(np.sum(wat_tot))
    s1_kt = float(np.sum(scope1_annual) / 1000.0)
    s2_kt = float(np.sum(scope2_annual) / 1000.0)
    s12_kt = float(np.sum(scope12_annual) / 1000.0)
    s3_kt = float(np.sum(scope3_annual) / 1000.0)
    s123_kt = float(np.sum(scope123_annual) / 1000.0)

    int_s12 = float(np.sum(scope12_annual) * 1000.0 / tot_oil_bbl)
    int_s123 = float(np.sum(scope123_annual) * 1000.0 / tot_oil_bbl)
    wor = float(tot_water_bbl / tot_oil_bbl)
    carbon_cost_usd_mn = float(np.sum(scope12_annual) * carbon_price_usd / 1e6)


    return {
        "no": no_val,
        "name": name,
        "rank_sa": rank_sa if not is_bau else "-",
        "is_bau": is_bau,
        "contingency_p": contingency_p,
        "oil_mmbbl": tot_oil_bbl / 1e6,
        "water_mmbbl": tot_water_bbl / 1e6,
        "scope1_kt": s1_kt,
        "scope2_kt": s2_kt,
        "scope12_kt": s12_kt,
        "scope3_kt": s3_kt,
        "scope123_kt": s123_kt,
        "int_s12": int_s12,
        "int_s123": int_s123,
        "wor": wor,
        "carbon_cost_usd_mn": carbon_cost_usd_mn,
        "npv10_80": npv10_80,
    }


def calculate_all_environmental(
    top10_sa: List[Dict[str, Any]],
    existing_data: Dict[str, Any],
    bau_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Menghitung profil lingkungan untuk Baseline BAU dan seluruh 10 skenario Top-10.
    Memberikan peringkat Env. Rank berdasarkan intensitas Scope 1+2 (ascending).
    """
    bau_env = calculate_scenario_environmental(
        {}, existing_data, rank_sa=0, is_bau=True, bau_data=bau_data
    )

    strategies_env = []
    for rank_idx, s in enumerate(top10_sa):
        res = calculate_scenario_environmental(
            s, existing_data, rank_sa=rank_idx + 1, is_bau=False
        )
        # Delta vs BAU
        res["delta_int_s12_vs_bau"] = (res["int_s12"] - bau_env["int_s12"]) / bau_env["int_s12"]
        res["delta_total_vs_bau"] = (res["scope123_kt"] - bau_env["scope123_kt"]) / bau_env["scope123_kt"]
        strategies_env.append(res)

    # Env. rank (kolom Q): RANK(intensitas_S1+2, Q6:Q15, 1) -> ascending (makin rendah makin baik, tie sama)
    all_ints = [s["int_s12"] for s in strategies_env]
    for item in strategies_env:
        # Excel RANK ascending: jumlah nilai yang lebih kecil + 1
        item["env_rank"] = sum(1 for v in all_ints if v < item["int_s12"] - 1e-9) + 1

    return {
        "bau": bau_env,
        "strategies": strategies_env,
    }
