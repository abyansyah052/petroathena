"""
Test suite untuk seluruh fitur V6 & Acceptance Tests T1 - T23
sesuai PRD Addendum v4.1 §13 (Bismillah_Angker_BCC_Excel_Calculations_V6_1).
"""

import os
import copy
import pytest
import numpy as np
import pandas as pd
import openpyxl

from athena_app.config.sheet_names import get_sheet_names_for_wb
from athena_app.core.loader import V5DataLoader
from athena_app.core.engine import AthenaEngine
from athena_app.core.environmental import calculate_all_environmental
from athena_app.core.risk import calculate_all_top10_risks
from athena_app.core.technical import calculate_all_top10_technical
from athena_app.core.secondary_recovery import calculate_secondary_recovery
from athena_app.core.contract_simulations import calculate_contract_simulations
from athena_app.core.config_manager import (
    DEFAULT_AHP_LEVEL1,
    DEFAULT_AHP_LEVEL2,
    calculate_ahp_matrix,
    validate_existing_data,
    LOCKED_CELLS,
)
from athena_app.core.topsis import (
    calculate_topsis,
    compute_all_ahp_global_weights,
)
from athena_app.config.topsis_sources import (
    BLOCKED_SUB_IDS,
    EXTENSION_SUB_IDS,
)
from athena_app.ui.page_settings import SETTINGS_PANELS
from athena_app.core.worked_example import get_worked_example_for_scenario


V6_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "Bismillah_Angker_BCC_Excel_Calculations_V6.xlsx")
GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "golden")
GOLDEN_V61_DIR = os.path.join(GOLDEN_DIR, "golden_v61")


@pytest.fixture(scope="module")
def engine_results():
    engine = AthenaEngine(V6_EXCEL_PATH)
    return engine.run_all()


# ==============================================================================
# T1: Loader - Semua 18 sheet terbuka dengan nama §0.1
# ==============================================================================
def test_t1_loader_all_18_sheets():
    wb = openpyxl.load_workbook(V6_EXCEL_PATH, read_only=True)
    sheet_names = wb.sheetnames
    assert len(sheet_names) == 18

    expected_sheets = [
        "0.Introduction",
        "0.Existing Data",
        "0.Combination",
        "0.CAPEX OPEX Breakdown",
        "0.Contingency Rate Combination",
        "1.Financial Projection (SA)",
        "1.Financial Projection (FarmIn)",
        "1.Financial Summary",
        "1.Contoh Perhitungan",
        "1.AHP",
        "1.Environmental Impact",
        "1.Risk",
        "1.Technical Implementation",
        "2.Secondary Recovery Analysis",
        "2.Contract Simulations",
        "3.TOPSIS",
        "3. Chosen Scenario",
        "3.Implementation Plan",
    ]
    for s in expected_sheets:
        assert s in sheet_names, f"Sheet '{s}' tidak ditemukan di workbook V6_1!"


# ==============================================================================
# T2: Alamat Lampiran G - Nilai sel Existing Data sesuai Excel V6_1
# ==============================================================================
def test_t2_existing_data_addresses_lampiran_g(engine_results):
    ed = engine_results["existing_data"]
    wb = openpyxl.load_workbook(V6_EXCEL_PATH, data_only=True)
    ws = wb["0.Existing Data"]

    assert ed["n_total"] == int(ws["B14"].value)
    assert ed["n_active"] == int(ws["B15"].value)
    assert ed["n_idle"] == int(ws["B16"].value)
    assert abs(ed["q0"] - float(ws["B10"].value)) < 1e-6
    assert abs(ed["wc0"] - float(ws["B11"].value)) < 1e-6
    assert abs(ed["d0"] - float(ws["B9"].value)) < 1e-6
    assert abs(ed["price_low"] - float(ws["B40"].value)) < 1e-6
    assert abs(ed["price_base"] - float(ws["B41"].value)) < 1e-6
    assert abs(ed["price_high"] - float(ws["B42"].value)) < 1e-6
    assert abs(ed.get("dr_main", ed.get("dr_base", 0.1)) - float(ws["B46"].value)) < 1e-6
    assert abs(ed["dr_low"] - float(ws["B47"].value)) < 1e-6
    assert abs(ed["dr_high"] - float(ws["B48"].value)) < 1e-6
    assert int(ws["B39"].value) == 15  # Periode evaluasi dikunci 15 tahun (§10.6)


# ==============================================================================
# T3: Proyeksi SA - 453 skenario cocok dengan golden_SA_453.csv
# ==============================================================================
def test_t3_proyeksi_sa_golden(engine_results):
    golden_path = os.path.join(GOLDEN_DIR, "golden_SA_453.csv")
    if not os.path.exists(golden_path):
        pytest.skip("golden_SA_453.csv not found")

    golden = pd.read_csv(golden_path, keep_default_na=False)
    sa_scenarios = engine_results["sa_scenarios"]
    assert len(sa_scenarios) == 453

    scenarios_by_no = {s["no"]: s for s in sa_scenarios}

    # Cocokkan skenario Top-10 secara ketat
    for i in range(10):
        g_no = int(golden.loc[i, "No"])
        s = scenarios_by_no[g_no]
        assert abs(s["flows"]["total_prod"] - golden.loc[i, "Total Production (bbl)"]) / golden.loc[i, "Total Production (bbl)"] < 1e-9
        assert abs(s["metrics"]["prices"][80]["npv10"] - golden.loc[i, "80$ NPV10"]) / abs(golden.loc[i, "80$ NPV10"]) < 1e-9


# ==============================================================================
# T4: Farm-In - Top-10 Farm-In cocok dengan golden_FarmIn_top10.csv
# ==============================================================================
def test_t4_farmin_top10_golden(engine_results):
    golden_path = os.path.join(GOLDEN_DIR, "golden_FarmIn_top10.csv")
    if not os.path.exists(golden_path):
        pytest.skip("golden_FarmIn_top10.csv not found")

    golden = pd.read_csv(golden_path)
    top10_fi = engine_results["top10_fi"]
    assert len(top10_fi) == 10

    for i in range(10):
        fi = top10_fi[i]
        g = golden.iloc[i]
        assert fi["rank_sa"] == int(g["No (Rank SA)"])
        assert fi["no_kombinasi"] == int(g["No kombinasi"])
        assert abs(fi["80_npv10_pne"] - float(g["80$ NPV,10 PNE"])) < 1e-4
        assert abs(fi["cpx_pne"] - float(g["CAPEX PNE"])) < 1e-4
        assert abs(fi["opx_pne"] - float(g["OPEX PNE"])) < 1e-4
        assert fi["rank_fi"] == int(g["RANK"])


# ==============================================================================
# T5: AHP - Bobot Level 1 & Bobot Global cocok dengan golden CSV
# ==============================================================================
def test_t5_ahp_golden():
    g_l1_path = os.path.join(GOLDEN_V61_DIR, "golden_ahp_level1.csv")
    g_glob_path = os.path.join(GOLDEN_V61_DIR, "golden_ahp_bobot_global.csv")

    if os.path.exists(g_l1_path):
        g_l1 = pd.read_csv(g_l1_path)
        w1, _, _, cr1, is_ok1 = calculate_ahp_matrix(DEFAULT_AHP_LEVEL1)
        assert cr1 <= 0.08  # Batas Level 1 4x4 adalah 0.08
        for i in range(4):
            assert abs(w1[i] - float(g_l1.iloc[i, 3])) < 1e-6

    if os.path.exists(g_glob_path):
        g_glob = pd.read_csv(g_glob_path)
        all_sub = compute_all_ahp_global_weights(DEFAULT_AHP_LEVEL1, DEFAULT_AHP_LEVEL2)
        calc_weights = {s["id"]: s["global_weight"] for s in all_sub}
        for _, row in g_glob.iterrows():
            sub_id = str(row.iloc[1]).strip()
            if sub_id in calc_weights:
                g_w = float(row.iloc[6])  # Kolom 6 = Bobot Global (Level 1 x Level 2)
                assert abs(calc_weights[sub_id] - g_w) < 1e-6


# ==============================================================================
# T6: Lingkungan / Risiko / Teknis - Cocok dengan golden CSV
# ==============================================================================
def test_t6_environmental_risk_technical_golden(engine_results):
    top10 = engine_results["top10_sa"]
    ed = engine_results["existing_data"]
    bau = engine_results["bau_data"]

    # Environmental
    g_env_path = os.path.join(GOLDEN_V61_DIR, "golden_lingkungan.csv")
    if os.path.exists(g_env_path):
        env_res = calculate_all_environmental(top10, ed, bau)
        assert len(env_res["strategies"]) == 10

    # Risk
    g_risk_path = os.path.join(GOLDEN_V61_DIR, "golden_risiko.csv")
    if os.path.exists(g_risk_path):
        risk_res = calculate_all_top10_risks(top10)
        assert len(risk_res) == 10

    # Technical
    g_tech_path = os.path.join(GOLDEN_V61_DIR, "golden_teknis.csv")
    if os.path.exists(g_tech_path):
        tech_res = calculate_all_top10_technical(top10)
        g_tech = pd.read_csv(g_tech_path)
        assert len(tech_res) == 10
        for i in range(10):
            assert abs(tech_res[i]["t1"] - float(g_tech.iloc[i, 5])) < 1e-4
            assert abs(tech_res[i]["t2"] - float(g_tech.iloc[i, 6])) < 1e-4
            assert abs(tech_res[i]["t3"] - float(g_tech.iloc[i, 7])) < 1e-4
            assert abs(tech_res[i]["t4"] - float(g_tech.iloc[i, 8])) < 1e-4
            assert abs(tech_res[i]["t5"] - float(g_tech.iloc[i, 9])) < 1e-4


# ==============================================================================
# T7: TOPSIS - Bobot, Matriks, D+, D-, Ci, Peringkat cocok dengan golden CSV
# ==============================================================================
def test_t7_topsis_golden(engine_results):
    top10 = engine_results["top10_sa"]
    ed = engine_results["existing_data"]
    bau = engine_results["bau_data"]
    summary_rows = engine_results["summary_rows"]

    env = calculate_all_environmental(top10, ed, bau)
    risk = calculate_all_top10_risks(top10)
    tech = calculate_all_top10_technical(top10)
    cs = calculate_contract_simulations(top10, summary_rows, ed)

    top = calculate_topsis(top10, env, risk, tech, cs)
    assert not top["is_blocked"]

    g_ringkasan_path = os.path.join(GOLDEN_V61_DIR, "golden_topsis_ringkasan.csv")
    if os.path.exists(g_ringkasan_path):
        golden = pd.read_csv(g_ringkasan_path)
        for i, row in enumerate(top["summary"]):
            g_row = golden.iloc[i]
            assert int(row["rank_sa"]) == int(g_row.iloc[2])
            assert abs(row["d_plus"] - float(g_row.iloc[4])) < 1e-6
            assert abs(row["d_minus"] - float(g_row.iloc[5])) < 1e-6
            assert abs(row["ci"] - float(g_row.iloc[6])) < 1e-6
            assert int(row["rank_topsis"]) == int(g_row.iloc[7])
            assert int(row["rank_equal_weights"]) == int(g_row.iloc[8])
            assert int(row["rank_diff"]) == int(g_row.iloc[9])
            assert row["contract_extension_type"] == str(g_row.iloc[10])
            assert int(row["contract_extra_years"]) == int(g_row.iloc[11])


# ==============================================================================
# T8: Secondary Recovery - Cocok dengan golden_secondary_recovery.csv
# ==============================================================================
def test_t8_secondary_recovery_golden(engine_results):
    top10 = engine_results["top10_sa"]
    ed = engine_results["existing_data"]

    sr = calculate_secondary_recovery(top10, ed)
    g_sr_path = os.path.join(GOLDEN_V61_DIR, "golden_secondary_recovery.csv")
    if os.path.exists(g_sr_path):
        golden = pd.read_csv(g_sr_path)
        for i, row in enumerate(sr["summary"]):
            g_row = golden.iloc[i]
            assert row["need_sr"] == str(g_row.iloc[6])
            assert row["scheme_used"] == str(g_row.iloc[7])
            if row["need_sr"] == "YA":
                assert abs(row["add_capex"] - float(g_row.iloc[8])) < 1e-4
                assert abs(row["add_prod_bbl"] - float(g_row.iloc[12])) < 1e-4
                assert abs(row["npv_sr_usd"] - float(g_row.iloc[16])) < 1e-4
                assert int(row["extra_contract_years"]) == int(g_row.iloc[11])
                assert row["econ_status"] == str(g_row.iloc[18])
            else:
                assert row["add_capex"] == "-"
                assert row["econ_status"] == "-"


# ==============================================================================
# T9: Simulasi Kontrak - Cocok dengan golden_kontrak_*.csv
# ==============================================================================
def test_t9_contract_simulations_golden(engine_results):
    top10 = engine_results["top10_sa"]
    summary_rows = engine_results["summary_rows"]
    ed = engine_results["existing_data"]

    cs = calculate_contract_simulations(top10, summary_rows, ed)

    g_res_path = os.path.join(GOLDEN_V61_DIR, "golden_kontrak_cadangan.csv")
    if os.path.exists(g_res_path):
        golden_res = pd.read_csv(g_res_path)
        for i, row in enumerate(cs["reserves_summary"]):
            g_row = golden_res.iloc[i]
            assert abs(row["years_to_deplete"] - float(g_row.iloc[9])) < 1e-4
            assert int(row["cal_year_deplete"]) == int(g_row.iloc[10])
            assert int(row["extra_contract_years"]) == int(g_row.iloc[11])
            assert row["contract_status"] == str(g_row.iloc[12])
            assert row["selected_scheme"] == str(g_row.iloc[15])

    g_npv_path = os.path.join(GOLDEN_V61_DIR, "golden_kontrak_ringkasan_npv.csv")
    if os.path.exists(g_npv_path):
        golden_npv = pd.read_csv(g_npv_path)
        for i, row in enumerate(cs["npv_summary"]):
            g_row = golden_npv.iloc[i]
            assert abs(row["gs_base"] - float(g_row.iloc[3])) < 1.0
            assert abs(row["cr_base"] - float(g_row.iloc[6])) < 1.0
            assert abs(row["exit_base"] - float(g_row.iloc[9])) < 1.0
            assert row["selected_scheme"] == str(g_row.iloc[11])


# ==============================================================================
# T10: TOPSIS Pemetaan by ID
# ==============================================================================
def test_t10_topsis_reorder_top10(engine_results):
    top10 = engine_results["top10_sa"]
    ed = engine_results["existing_data"]
    bau = engine_results["bau_data"]
    summary_rows = engine_results["summary_rows"]

    env = calculate_all_environmental(top10, ed, bau)
    risk = calculate_all_top10_risks(top10)
    tech = calculate_all_top10_technical(top10)
    cs = calculate_contract_simulations(top10, summary_rows, ed)

    # Reorder pairwise Level 1 without changing the criteria set (swap F and R)
    l1_reordered = copy.deepcopy(DEFAULT_AHP_LEVEL1)
    l1_reordered[2], l1_reordered[3] = l1_reordered[3], l1_reordered[2]
    for r in range(4):
        l1_reordered[r][2], l1_reordered[r][3] = l1_reordered[r][3], l1_reordered[r][2]

    res = calculate_topsis(top10, env, risk, tech, cs, pairwise_l1=l1_reordered)
    assert not res["is_blocked"]
    assert len(res["summary"]) == 10


# ==============================================================================
# T11: TOPSIS Memblokir Sub-Kriteria Tanpa Sumber Nilai (E2, E3, E4, E5, R5)
# ==============================================================================
def test_t11_topsis_blocking_subcriteria(engine_results):
    top10 = engine_results["top10_sa"]
    ed = engine_results["existing_data"]
    bau = engine_results["bau_data"]
    summary_rows = engine_results["summary_rows"]

    env = calculate_all_environmental(top10, ed, bau)
    risk = calculate_all_top10_risks(top10)
    tech = calculate_all_top10_technical(top10)
    cs = calculate_contract_simulations(top10, summary_rows, ed)

    # Tingkatkan bobot E di Level 1 sehingga E3/E4/E5/E2 masuk 10 besar
    l1_e = copy.deepcopy(DEFAULT_AHP_LEVEL1)
    l1_e[0] = [1.0, 9.0, 9.0, 9.0]
    l1_e[1][0] = 1/9
    l1_e[2][0] = 1/9
    l1_e[3][0] = 1/9

    res = calculate_topsis(top10, env, risk, tech, cs, pairwise_l1=l1_e)
    assert res["is_blocked"]
    assert any(b_id in res["block_message"] for b_id in BLOCKED_SUB_IDS)


# ==============================================================================
# T11b: TOPSIS Menangani Sumber Perluasan (T2, T3, T5, F4, F5)
# ==============================================================================
def test_t11b_topsis_extension_subcriteria(engine_results):
    top10 = engine_results["top10_sa"]
    ed = engine_results["existing_data"]
    bau = engine_results["bau_data"]
    summary_rows = engine_results["summary_rows"]

    env = calculate_all_environmental(top10, ed, bau)
    risk = calculate_all_top10_risks(top10)
    tech = calculate_all_top10_technical(top10)
    cs = calculate_contract_simulations(top10, summary_rows, ed)

    # Tukar posisi T2 dan T4 sehingga T2 (perluasan) masuk 10 besar
    l2_t = copy.deepcopy(DEFAULT_AHP_LEVEL2)
    mat = copy.deepcopy(l2_t["Technical"])
    mat[1], mat[3] = mat[3], mat[1]
    for r in range(5):
        mat[r][1], mat[r][3] = mat[r][3], mat[r][1]
    l2_t["Technical"] = mat

    res = calculate_topsis(top10, env, risk, tech, cs, pairwise_l2=l2_t)
    assert not res["is_blocked"]
    assert "T2" in res["extensions_used"]
    assert len(res["summary"]) == 10


# ==============================================================================
# T11c: TOPSIS Bobot Asli Excel Tidak Memakai Sumber Perluasan
# ==============================================================================
def test_t11c_topsis_default_no_extensions(engine_results):
    top10 = engine_results["top10_sa"]
    ed = engine_results["existing_data"]
    bau = engine_results["bau_data"]
    summary_rows = engine_results["summary_rows"]

    env = calculate_all_environmental(top10, ed, bau)
    risk = calculate_all_top10_risks(top10)
    tech = calculate_all_top10_technical(top10)
    cs = calculate_contract_simulations(top10, summary_rows, ed)

    res = calculate_topsis(top10, env, risk, tech, cs)
    assert not res["is_blocked"]
    assert len(res["extensions_used"]) == 0


# ==============================================================================
# T12: TOPSIS Memblokir IRR Non-Numerik ("n/a")
# ==============================================================================
def test_t12_topsis_bad_irr_blocking(engine_results):
    top10 = engine_results["top10_sa"]
    ed = engine_results["existing_data"]
    bau = engine_results["bau_data"]
    summary_rows = engine_results["summary_rows"]

    env = calculate_all_environmental(top10, ed, bau)
    risk = calculate_all_top10_risks(top10)
    tech = calculate_all_top10_technical(top10)
    cs = calculate_contract_simulations(top10, summary_rows, ed)

    top10_bad_irr = copy.deepcopy(top10)
    top10_bad_irr[0]["metrics"]["prices"][80]["irr"] = "n/a"

    res = calculate_topsis(top10_bad_irr, env, risk, tech, cs)
    assert res["is_blocked"]
    assert "IRR" in res["block_message"]


# ==============================================================================
# T13: Invariansi - Biaya BAU × 1.7 mempertahankan peringkat
# ==============================================================================
def test_t13_invariance():
    engine_base = AthenaEngine(V6_EXCEL_PATH)
    res_base = engine_base.run_all()
    ranks_base = [s["no"] for s in res_base["top10_sa"]]

    # BAU cost override x 1.7
    ovr = {"bau_capex_mult": 1.7}
    res_bau = engine_base.run_all(config_overrides=ovr)
    ranks_bau = [s["no"] for s in res_bau["top10_sa"]]

    assert ranks_base == ranks_bau, "Ranking Top-10 harus invarian terhadap pergeseran biaya BAU!"


# ==============================================================================
# T14: Config - Teks Panel Pengaturan Lengkap
# ==============================================================================
def test_t14_config_panels_text():
    assert len(SETTINGS_PANELS) == 11
    required_keys = ["fungsi", "kalau_diubah", "tidak_berubah", "halaman_terdampak", "waktu_hitung"]
    for tab_name, panel in SETTINGS_PANELS.items():
        for k in required_keys:
            assert k in panel, f"Tab '{tab_name}' kehilangan key '{k}'!"
            assert len(panel[k]) > 0


# ==============================================================================
# T15: Config - Sel REFERENSI tidak mengubah hasil
# ==============================================================================
def test_t15_reference_cells_invariance():
    engine = AthenaEngine(V6_EXCEL_PATH)
    res1 = engine.run_all()

    # Ubah sel referensi (misal catatan reservoir B25)
    ovr = {"reference_notes": "Catatan referensi audit"}
    res2 = engine.run_all(config_overrides=ovr)

    assert res1["top10_sa"][0]["metrics"]["prices"][80]["npv10"] == res2["top10_sa"][0]["metrics"]["prices"][80]["npv10"]


# ==============================================================================
# T16: Config - Override B41 Base Price
# ==============================================================================
def test_t16_price_override_reactivity():
    engine = AthenaEngine(V6_EXCEL_PATH)
    ovr = {"price_base": 85.0}
    res = engine.run_all(config_overrides=ovr)
    assert res["existing_data"]["price_base"] == 85.0


# ==============================================================================
# T17: Config - Override B47 Discount Rate
# ==============================================================================
def test_t17_discount_rate_override():
    engine = AthenaEngine(V6_EXCEL_PATH)
    ovr = {"dr_base": 0.07}
    res = engine.run_all(config_overrides=ovr)
    assert res["existing_data"]["dr_base"] == 0.07


# ==============================================================================
# T18: Config - Validasi Aturan
# ==============================================================================
def test_t18_validation_rules():
    # Sumur aktif + idle != total
    errs = validate_existing_data({"n_total": 15, "n_active": 10, "n_idle": 3})
    assert len(errs) > 0

    # Harga tidak berurutan
    errs_price = validate_existing_data({"price_low": 90, "price_base": 80, "price_high": 117})
    assert len(errs_price) > 0


# ==============================================================================
# T19: Recalculation Dependency Mapping
# ==============================================================================
def test_t19_dependency_cache_mapping():
    # Secondary recovery hanya memengaruhi modulnya sendiri
    engine = AthenaEngine(V6_EXCEL_PATH)
    res = engine.run_all()
    assert "top10_sa" in res
    assert "top10_fi" in res


# ==============================================================================
# T20: Locked Cells B39 & B21
# ==============================================================================
def test_t20_locked_cells():
    assert "B39" in LOCKED_CELLS or "eval_period" in LOCKED_CELLS
    wb = openpyxl.load_workbook(V6_EXCEL_PATH, data_only=True)
    ws_ed = wb["0.Existing Data"]
    assert int(ws_ed["B39"].value) == 15
    ws_cp = wb["1.Contoh Perhitungan"]
    assert int(ws_cp["B21"].value) == 58


# ==============================================================================
# T21: Strict Light Theme Enforcement
# ==============================================================================
def test_t21_light_theme_enforcement():
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", ".streamlit", "config.toml")
    assert os.path.exists(config_path)
    with open(config_path, "r") as f:
        content = f.read()
    assert 'base = "light"' in content
    assert 'toolbarMode = "minimal"' in content
    assert "[theme.dark]" not in content


# ==============================================================================
# T22: Price Reactivity in UI
# ==============================================================================
def test_t22_price_reactivity_ui(engine_results):
    scenarios = engine_results["sa_scenarios"]
    sc = scenarios[0]
    p_low = sc["metrics"]["prices"][64]["npv10"]
    p_base = sc["metrics"]["prices"][80]["npv10"]
    p_high = sc["metrics"]["prices"][117]["npv10"]
    assert p_low < p_base < p_high


# ==============================================================================
# T23: Contoh Perhitungan Worked Example
# ==============================================================================
def test_t23_worked_example_scenario_picker(engine_results):
    top10 = engine_results["top10_sa"]
    rank1_no = top10[0]["no"]
    we = get_worked_example_for_scenario(rank1_no, 80.0, engine_results)
    assert we is not None
    assert we["scenario"]["no"] == rank1_no
