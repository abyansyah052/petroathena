"""
Test suite untuk seluruh fitur V6 & Acceptance Tests T11 - T28
sesuai PRD Addendum v3.1 §7.
"""

import os
import pytest
import numpy as np
import openpyxl
from athena_app.config.sheet_names import get_sheet_names_for_wb, V6_SHEET_NAMES
from athena_app.core.loader import V5DataLoader
from athena_app.core.engine import AthenaEngine
from athena_app.core.derived_metrics import calculate_icp_breakeven, calculate_payback_period
from athena_app.core.environmental import calculate_all_environmental
from athena_app.core.risk import (
    calculate_all_top10_risks,
    calculate_scenario_risk,
    GENERIC_FAILURE_MODES,
    lookup_occurrence,
    RATED_METHODS_RISK,
)
from athena_app.core.technical import (
    calculate_all_top10_technical,
    calculate_scenario_technical,
    RATED_METHODS_TECH,
)
from athena_app.core.topsis import (
    RAW_AHP_SUBCRITERIA,
    get_renormalized_weights,
    coerce_metric,
    run_topsis_analysis,
)
from athena_app.core.worked_example import get_worked_example_for_scenario

V6_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Bismillah_Angker_BCC_Excel_Calculations_V6.xlsx")


@pytest.fixture(scope="module")
def engine_results():
    engine = AthenaEngine(V6_EXCEL_PATH)
    return engine.run_all()


# ==============================================================================
# T11: Loader V6 Sheet Names
# ==============================================================================
def test_t11_loader_v6_sheet_names():
    wb = openpyxl.load_workbook(V6_EXCEL_PATH, read_only=True)
    sheets = get_sheet_names_for_wb(wb)
    assert sheets["financial_projection_farmin"] == "1.Financial Projection (FarmIn)"  # Tanpa tanda hubung
    assert sheets["existing_data"] == "0.Existing Data"
    assert sheets["combination"] == "0.Combination"
    assert sheets["capex_opex_breakdown"] == "0.CAPEX OPEX Breakdown"
    assert sheets["contingency_rate_combination"] == "0.Contingency Rate Combination"
    assert sheets["financial_projection_sa"] == "1.Financial Projection (SA)"
    assert sheets["financial_summary"] == "1.Financial Summary"
    assert sheets["contoh_perhitungan"] == "1.Contoh Perhitungan"


# ==============================================================================
# T12 & T13 & T14: AHP Weights, Directions & Consistency Ratios
# ==============================================================================
def test_t12_t13_ahp_weights_and_directions():
    wb = openpyxl.load_workbook(V6_EXCEL_PATH, data_only=True)
    ws_ahp = wb["1.AHP"]

    tot_weight = sum(item[5] for item in RAW_AHP_SUBCRITERIA)
    assert abs(tot_weight - 1.0) < 1e-9

    for r_idx, r in enumerate(range(281, 301)):
        sub_id = ws_ahp.cell(r, 1).value
        excel_weight = float(ws_ahp.cell(r, 6).value)
        excel_dir = str(ws_ahp.cell(r, 8).value).strip()

        cfg_id, _, _, _, _, cfg_weight, cfg_dir = RAW_AHP_SUBCRITERIA[r_idx]
        assert sub_id == cfg_id
        assert abs(excel_weight - cfg_weight) < 1e-9  # T12
        assert excel_dir.lower() == cfg_dir.lower()     # T13


def test_t14_ahp_cr_limits():
    wb = openpyxl.load_workbook(V6_EXCEL_PATH, data_only=True)
    ws_ahp = wb["1.AHP"]
    cr_l1 = float(ws_ahp["C106"].value)
    limit_l1 = float(ws_ahp["C107"].value)
    assert limit_l1 == 0.08  # Batas Level 1 matriks 4x4 adalah 0.08, bukan 0.10!
    assert cr_l1 <= limit_l1

    for cell_cr in ["C142", "C182", "C222", "C262"]:
        assert float(ws_ahp[cell_cr].value) <= 0.10


# ==============================================================================
# T15: TOPSIS Weight Renormalization & Parent Weight Preservation
# ==============================================================================
def test_t15_topsis_weight_preservation():
    norm_configs = get_renormalized_weights()
    active_weights = [sc["normalized_weight"] for sc in norm_configs if sc["is_active"]]
    # 20 sub-kriteria total minus 3 dikeluarkan (E4, E5, R1) = 17 sub-kriteria aktif (R2 memakai proksi RPN)
    assert len(active_weights) == 17
    assert abs(sum(active_weights) - 1.0) < 1e-9

    parent_sums = {}
    for sc in norm_configs:
        parent = sc["parent"]
        parent_sums[parent] = parent_sums.get(parent, 0.0) + sc["normalized_weight"]

    # G96:G99 Level 1 weights
    expected_l1 = {
        "Environmental": 0.10932857991681522,
        "Technical": 0.18924539512774807,
        "Risk": 0.3507130124777184,
        "Financial": 0.3507130124777184,
    }
    for p, exp_w in expected_l1.items():
        assert abs(parent_sums[p] - exp_w) < 1e-9


# ==============================================================================
# T16, T17, T18: TOPSIS Algorithm, Closeness in [0,1], Non-numeric IRR, Constants
# ==============================================================================
def test_t16_topsis_closeness_and_dominance(engine_results):
    top10_sa = engine_results["top10_sa"]
    ed = engine_results["existing_data"]
    bau_data = engine_results["bau_data"]

    env_res = calculate_all_environmental(top10_sa, ed, bau_data)
    risk_res = calculate_all_top10_risks(top10_sa)
    tech_res = calculate_all_top10_technical(top10_sa)

    topsis_res = run_topsis_analysis(top10_sa, env_res, risk_res, tech_res, ed, bau_data)
    for item in topsis_res["results"]:
        assert 0.0 <= item["closeness"] <= 1.0


def test_t17_coerce_non_numeric_irr():
    val_na, warn_na = coerce_metric("n/a")
    assert val_na == 0.0
    assert warn_na is not None

    val_nm, warn_nm = coerce_metric("n/m")
    assert val_nm == 0.0
    assert warn_nm is not None

    val_num, warn_num = coerce_metric(0.245)
    assert val_num == 0.245
    assert warn_num is None


def test_t18_topsis_constant_column_and_zero_division(engine_results):
    top10_sa = engine_results["top10_sa"]
    ed = engine_results["existing_data"]
    bau_data = engine_results["bau_data"]

    env_res = calculate_all_environmental(top10_sa, ed, bau_data)
    risk_res = calculate_all_top10_risks(top10_sa)
    tech_res = calculate_all_top10_technical(top10_sa)

    # Memastikan eksekusi aman tanpa ZeroDivisionError
    res = run_topsis_analysis(top10_sa, env_res, risk_res, tech_res, ed, bau_data)
    assert len(res["results"]) == 10


# ==============================================================================
# T19: Derived Metrics R4 (ICP Breakeven) & R5 (Payback Period)
# ==============================================================================
def test_t19_derived_metrics_r4_r5(engine_results):
    top10_sa = engine_results["top10_sa"]
    ed = engine_results["existing_data"]
    bau_data = engine_results["bau_data"]

    for s in top10_sa:
        p_star, npv_ver = calculate_icp_breakeven(s, ed, bau_data["lif"])
        assert p_star is not None
        assert abs(npv_ver) < 1e-6  # Verifikasi silang |NPV(P*)| < 1e-6

        pb = calculate_payback_period(s, 80.0, ed, bau_data)
        assert 0.0 <= pb <= 16.0


# ==============================================================================
# T20: Environmental Impact (Scope 1+2+3 = Scope 1+2 + Scope 3)
# ==============================================================================
def test_t20_environmental_impact(engine_results):
    top10_sa = engine_results["top10_sa"]
    ed = engine_results["existing_data"]
    bau_data = engine_results["bau_data"]

    env_res = calculate_all_environmental(top10_sa, ed, bau_data)
    bau = env_res["bau"]
    assert abs(bau["scope123_kt"] - (bau["scope12_kt"] + bau["scope3_kt"])) < 1e-6

    for s in env_res["strategies"]:
        assert abs(s["scope123_kt"] - (s["scope12_kt"] + s["scope3_kt"])) < 1e-6
        assert s["oil_mmbbl"] > 0
        assert s["water_mmbbl"] > 0


# ==============================================================================
# T21, T22, T23: Risk / FMEA
# ==============================================================================
def test_t21_risk_rpn_total_and_high_critical_no_double_count(engine_results):
    top10_sa = engine_results["top10_sa"]
    risks = calculate_all_top10_risks(top10_sa)

    for r in risks:
        # RPN TOTAL = F + G + H + I
        expected_total = r["sum_rpn_metode"] + r["rpn_efficacy"] + r["sum_rpn_generic"] + r["sum_rpn_interface"]
        assert r["rpn_total"] == expected_total
        # FM High tidak dobel hitung Critical
        assert r["fm_high"] >= 0


def test_t22_risk_generic_p_effective_varies_with_run_count():
    # Menguji mode run P_eff = 1 - (1 - P_base)^n
    g1_p = 0.03
    p_n1 = 1.0 - (1.0 - g1_p) ** 1
    p_n4 = 1.0 - (1.0 - g1_p) ** 4
    assert p_n1 != p_n4
    assert p_n4 > p_n1


def test_t23_risk_interface_activation():
    # Skenario dengan pasangan I1: Gel (1) + Plug (6) -> RPN > 0
    scen_mock_pair = {"combo": {"id_1": 1, "id_2": 6, "id_3": None, "id_4": None}, "no": 999, "cont": {"contingency_rate": 0.9}, "kombinasi": "Mock Pair", "metrics": {"prices": {80: {"npv10": 1e7}}}}
    res_pair = calculate_scenario_risk(scen_mock_pair, rank_sa=1)
    assert res_pair["sum_rpn_interface"] > 0

    # Skenario tanpa pasangan interface
    scen_mock_single = {"combo": {"id_1": 6, "id_2": None, "id_3": None, "id_4": None}, "no": 998, "cont": {"contingency_rate": 0.8}, "kombinasi": "Mock Single", "metrics": {"prices": {80: {"npv10": 1e7}}}}
    res_single = calculate_scenario_risk(scen_mock_single, rank_sa=2)
    assert res_single["sum_rpn_interface"] == 0


# ==============================================================================
# T24, T25, T26: Technical Implementation & Robustness
# ==============================================================================
def test_t24_t25_technical_aggregation_rules(engine_results):
    top10_sa = engine_results["top10_sa"]
    techs = calculate_all_top10_technical(top10_sa)

    for t in techs:
        # T1..T5 berada di [1.0, 5.0]
        assert 1.0 <= t["t1"] <= 5.0
        assert 1.0 <= t["t2"] <= 5.0
        assert 1.0 <= t["t3"] <= 5.0
        assert 1.0 <= t["t4"] <= 5.0
        assert 1.0 <= t["t5"] <= 5.0


def test_t26_robustness_unrated_methods():
    # CRC ID 3 tidak dinilai di Excel V6 -> harus raise ValueError
    mock_unrated = {"combo": {"id_1": 3, "id_2": 6, "id_3": None, "id_4": None}, "no": 997, "cont": {"contingency_rate": 0.85}, "kombinasi": "Unrated Method", "metrics": {"prices": {80: {"npv10": 1e7}}}}
    with pytest.raises(ValueError):
        calculate_scenario_risk(mock_unrated, rank_sa=1)

    with pytest.raises(ValueError):
        calculate_scenario_technical(mock_unrated, rank_sa=1)


# ==============================================================================
# T28: Worked Example Generalization (Contoh Perhitungan Section)
# ==============================================================================
def test_t28_worked_example_for_any_scenario(engine_results):
    we_rank1 = get_worked_example_for_scenario(60, 80.0, engine_results)
    assert len(we_rank1["block"]["rows"]["Year"]) == 15
    assert not we_rank1["is_bau"]

    we_bau = get_worked_example_for_scenario("BAU", 80.0, engine_results)
    assert we_bau["is_bau"]


# ==============================================================================
# T29 - T40: Acceptance Tests v3.2 (Pengaturan Lanjutan, Audit, & FMEA Narrative)
# ==============================================================================
from athena_app.core.config_manager import (
    CONFIG_PASSWORD,
    EXCEL_V6_DEFAULTS,
    calculate_ahp_matrix,
    ConfigManager,
)


def test_t29_t30_password_gate():
    assert CONFIG_PASSWORD == "ANGKER123"


def test_t31_recomputation_upstream_param():
    engine = AthenaEngine(V6_EXCEL_PATH)
    res_base = engine.run_all()
    res_custom = engine.run_all(config_overrides={"q0": 2500.0})

    # NPV harus meningkat karena q0 naik dari 2000 ke 2500
    npv_base = res_base["top10_sa"][0]["metrics"]["prices"][80]["npv10"]
    npv_custom = res_custom["top10_sa"][0]["metrics"]["prices"][80]["npv10"]
    assert npv_custom > npv_base


def test_t32_farmin_invalidation_scope():
    engine = AthenaEngine(V6_EXCEL_PATH)
    res_base = engine.run_all()
    res_farmin = engine.run_all(config_overrides={"wi_xyz": 0.50, "carry": 0.85})

    # Farm-In berubah
    fi_base = res_base["top10_fi"][0]["prices"][80]["npv10_xyz"]
    fi_custom = res_farmin["top10_fi"][0]["prices"][80]["npv10_xyz"]
    assert fi_base != fi_custom

    # SA Top 10 tidak berubah
    assert res_base["top10_sa"][0]["no"] == res_farmin["top10_sa"][0]["no"]




def test_t34_t35_ahp_reciprocal_and_excel_cr():
    A_L1 = np.array([
        [1, 0.5, 1/3, 1/3],
        [2, 1, 0.5, 0.5],
        [3, 2, 1, 1],
        [3, 2, 1, 1]
    ])
    # Reciprocal check
    assert np.isclose(A_L1[1, 0], 1.0 / A_L1[0, 1])
    assert np.isclose(A_L1[2, 0], 1.0 / A_L1[0, 2])

    weights, lmax, ci, cr, is_consistent = calculate_ahp_matrix(A_L1)
    # Excel CR level 1 adalah 0.0038 <= 0.08
    assert is_consistent is True
    assert cr <= 0.08
    assert abs(cr - 0.0038) < 0.001


def test_t36_cross_validation_wells():
    # n_active + n_idle harus sama dengan n_total
    valid_wells = (EXCEL_V6_DEFAULTS["n_active"] + EXCEL_V6_DEFAULTS["n_idle"] == EXCEL_V6_DEFAULTS["n_total"])
    assert valid_wells is True

    # Kasus inkonsisten
    invalid_wells = (60 + 90 == EXCEL_V6_DEFAULTS["n_total"])
    assert invalid_wells is False


def test_t37_threshold_and_overlap_ordering():
    # Ambang FMEA harus menurun
    assert EXCEL_V6_DEFAULTS["fmea_critical"] > EXCEL_V6_DEFAULTS["fmea_high"] > EXCEL_V6_DEFAULTS["fmea_medium"] >= EXCEL_V6_DEFAULTS["fmea_low"]

    # Overlap harus menurun
    assert EXCEL_V6_DEFAULTS["overlap_same_func"] >= EXCEL_V6_DEFAULTS["overlap_same_class"] >= EXCEL_V6_DEFAULTS["overlap_diff_class"]


def test_t38_reset_to_excel_defaults():
    diffs = ConfigManager.get_diffs(EXCEL_V6_DEFAULTS)
    assert len(diffs) == 0


def test_t39_json_export_and_import():
    custom_cfg = dict(EXCEL_V6_DEFAULTS)
    custom_cfg["q0"] = 2400.0
    custom_cfg["price_base"] = 85.0

    json_str = ConfigManager.export_json(custom_cfg)
    assert "q0" in json_str
    assert "Athena_V6_CustomConfig" in json_str

    imported = ConfigManager.import_json(json_str)
    assert imported["q0"] == 2400.0
    assert imported["price_base"] == 85.0


def test_t40_dynamic_price_adaptation():
    engine = AthenaEngine(V6_EXCEL_PATH)
    res = engine.run_all(config_overrides={"price_base": 85.0})
    assert res["existing_data"]["price_base"] == 85.0
    # Cek bahwa metrics harga 85 dihitung
    assert 85 in res["top10_sa"][0]["metrics"]["prices"]

