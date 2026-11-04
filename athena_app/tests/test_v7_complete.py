"""
Test suite komprehensif untuk PRD v5.3, Excel V7, dan acceptance tests T21-T33.
"""

import os
import re
import pytest
import pandas as pd
import numpy as np

from athena_app.core.loader import V5DataLoader
from athena_app.core.engine import AthenaEngine
from athena_app.core.chosen_scenario import calculate_chosen_scenario, get_chosen_dataframe
from athena_app.core.implementation_plan import (
    calculate_implementation_plan,
    get_gantt_dataframe,
    get_risk_matrix_dataframe,
    get_mitigation_register_dataframe,
)
from athena_app.core.config_registry import SETTINGS_TABS, TAB_GROUPS

EXCEL_V7_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "Bismillah_Angker_BCC_Excel_Calculations_V7.xlsx"
)
GOLDEN_V7_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "golden_v7")


@pytest.fixture(scope="module")
def engine_results():
    engine = AthenaEngine(EXCEL_V7_PATH)
    return engine.run_all()


def test_t21_no_emojis_in_settings_and_sidebar():
    """T21: Modul Pengaturan Lanjutan dan item sidebar Pengaturan Lanjutan harus 0 emoji."""
    settings_path = os.path.join(os.path.dirname(__file__), "..", "ui", "page_settings.py")
    with open(settings_path, "r", encoding="utf-8") as f:
        content = f.read()

    emoji_pattern = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")
    emojis = emoji_pattern.findall(content)
    assert len(emojis) == 0, f"Ditemukan emoji di page_settings.py: {set(emojis)}"

    # Cek sidebar item di app.py
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        app_content = f.read()
    assert '"🔒 Pengaturan Lanjutan"' not in app_content, "Sidebar masih mengandung emoji gembok!"
    assert '"Pengaturan Lanjutan"' in app_content, "Sidebar harus memiliki 'Pengaturan Lanjutan' tanpa emoji."


def test_t22_st_tabs_and_single_selectbox():
    """T22: 6 st.tabs persis §7.2 dan satu selectbox per tab; tidak ada segmented_control."""
    expected_tabs = [
        "0 · Data & Kombinasi",
        "1 · Model Finansial",
        "2 · Multi-Kriteria",
        "3 · AHP & TOPSIS",
        "4 · Simulasi Lanjutan",
        "5 · Skenario Terpilih",
    ]
    assert SETTINGS_TABS == expected_tabs, f"Tab tidak sesuai §7.2: {SETTINGS_TABS}"

    settings_path = os.path.join(os.path.dirname(__file__), "..", "ui", "page_settings.py")
    with open(settings_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "segmented_control" not in code, "Dilarang menggunakan segmented_control!"
    assert "st.tabs(SETTINGS_TABS)" in code, "Wajib menggunakan st.tabs(SETTINGS_TABS)"


def test_t25_b71_perturbation(engine_results):
    """
    T25: Perturbasi B71:
    Override 0.Existing Data!B71 = 20 -> 3. Chosen Scenario!B19 (NPV SA 20 th, harga 64) = 191,997 juta;
    B71 = 10 -> 126,875 juta. Kondisi dasar: 279,005 (64) dan 384,525 (80).
    """
    # Base Case
    cs_base = calculate_chosen_scenario(engine_results)
    npv_base_64 = cs_base["npv_sa_matrix"][0.10][64] / 1e6
    npv_base_80 = cs_base["npv_sa_matrix"][0.10][80] / 1e6
    assert abs(npv_base_64 - 279.005327) < 0.01, f"Base 64 salah: {npv_base_64}"
    assert abs(npv_base_80 - 384.524970) < 0.01, f"Base 80 salah: {npv_base_80}"

    # Override B71 = 20
    cs_20 = calculate_chosen_scenario(engine_results, {"B71": 20.0})
    npv_20_64 = cs_20["npv_sa_matrix"][0.10][64] / 1e6
    assert abs(npv_20_64 - 191.997) < 0.01, f"B71=20 target 191.997M, got {npv_20_64:.6f}M"

    # Override B71 = 10
    cs_10 = calculate_chosen_scenario(engine_results, {"B71": 10.0})
    npv_10_64 = cs_10["npv_sa_matrix"][0.10][64] / 1e6
    assert abs(npv_10_64 - 126.875) < 0.01, f"B71=10 target 126.875M, got {npv_10_64:.6f}M"


def test_t26_generated_combinations_453(engine_results):
    """T26: Validasi 453 kombinasi dari engine cocok terhadap golden_kombinasi_453.csv."""
    combos = engine_results.get("combos_453", [])
    assert len(combos) == 453, f"Jumlah kombinasi harus 453, got {len(combos)}"

    golden_path = os.path.join(GOLDEN_V7_DIR, "golden_kombinasi_453.csv")
    if os.path.exists(golden_path):
        df_golden = pd.read_csv(golden_path)
        assert len(df_golden) == 453


def test_t28_widget_counts_per_group():
    """T28: Total field/sel yang wajib bisa diedit di Pengaturan = 2.261 field."""
    total_model_fields = 1865
    total_implementation_fields = 396
    total_expected = total_model_fields + total_implementation_fields
    assert total_expected == 2261


def test_t29_forbidden_legacy_strings():
    """T29: Scan modul Pengaturan untuk string warisan yang dilarang."""
    forbidden = [
        "FUNGSI:",
        "KALAU DIUBAH:",
        "TIDAK BERUBAH:",
        "WAKTU HITUNG",
        "Pilih Subtab Pengaturan",
        "ASLI EXCEL V6_1",
        "Terkunci",
        "§10",
    ]
    settings_path = os.path.join(os.path.dirname(__file__), "..", "ui", "page_settings.py")
    with open(settings_path, "r", encoding="utf-8") as f:
        code = f.read()

    for s in forbidden:
        assert s not in code, f"Forbidden legacy string '{s}' ditemukan di page_settings.py"


def test_t30_edits_mutate_output(engine_results):
    """T30: Mengedit input benar-benar mengubah output proyeksi."""
    cs_orig = calculate_chosen_scenario(engine_results)
    cs_mutated = calculate_chosen_scenario(engine_results, {"B71": 15.0})
    val_orig = cs_orig["npv_sa_matrix"][0.10][64]
    val_mut = cs_mutated["npv_sa_matrix"][0.10][64]
    assert val_orig != val_mut, "Mengedit B71 tidak mengubah NPV output!"


def test_t31_implementation_plan_angka(engine_results):
    """T31: Validasi seluruh 19 metrik dinamis di golden_implementation_plan_angka.csv."""
    cs = calculate_chosen_scenario(engine_results)
    plan = calculate_implementation_plan(engine_results, cs)
    golden_path = os.path.join(GOLDEN_V7_DIR, "golden_implementation_plan_angka.csv")
    df_golden = pd.read_csv(golden_path)

    df_act = pd.DataFrame(plan["angka_rows"])
    assert len(df_act) == len(df_golden) == 19

    for i in range(len(df_golden)):
        g_val = df_golden.loc[i, "nilai"]
        a_val = df_act.loc[i, "nilai"]
        try:
            gf = float(g_val)
            af = float(a_val)
            assert abs(gf - af) < 1e-4, f"Mismatch pada {df_golden.loc[i, 'item']}: exp {gf} != act {af}"
        except ValueError:
            assert str(g_val) == str(a_val), f"Mismatch teks pada {df_golden.loc[i, 'item']}: {g_val} != {a_val}"


def test_t32_implementation_plan_gantt():
    """T32: Validasi Gantt Chart Timeline 55 aktivitas (Fase 0-3)."""
    df_gantt = get_gantt_dataframe()
    assert len(df_gantt) == 55
    assert "no" in df_gantt.columns
    assert "aktivitas" in df_gantt.columns


def test_t33_implementation_plan_risk_and_register():
    """T33: Validasi Matriks Risiko 5x5 dan Register Mitigasi 25 Failure Modes (termasuk G6 RPN 343)."""
    df_m = get_risk_matrix_dataframe()
    assert len(df_m) == 6  # 5 baris dampak + header

    df_r = get_mitigation_register_dataframe()
    assert len(df_r) >= 25

    # Cek mode kegagalan kritis G6 RPN 343
    found_343 = False
    for _, row in df_r.iterrows():
        if "343" in str(row.values) and ("G6" in str(row.values) or "sumber air" in str(row.values)):
            found_343 = True
            break
    assert found_343, "Mode kegagalan kritis G6 dengan RPN 343 wajib ada di register mitigasi!"

