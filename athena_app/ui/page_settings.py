"""
Module ui/page_settings.py: Halaman Pengaturan Lanjutan Ber-password (Tahap 3 · Keputusan).
Memungkinkan modifikasi parameter asumsi numerik dari tahap 0 hingga AHP/TOPSIS,
dilengkapi verifikasi password 'ANGKER123', validasi silang, slider diskret Saaty,
badge CR live, jejak audit, serta ekspor/impor konfigurasi JSON sesuai PRD Addendum v3.2 §10.
Desain profesional bersih tanpa emoticon sesuai permintaan user.
"""

import json
import streamlit as st
import pandas as pd
import numpy as np

from athena_app.core.config_manager import (
    CONFIG_PASSWORD,
    EXCEL_V6_DEFAULTS,
    PARAM_METADATA,
    SAATY_SCALE_VALUES,
    get_saaty_text,
    calculate_ahp_matrix,
    ConfigManager,
)
from athena_app.core.topsis import (
    AHP_LEVEL2_MATRICES,
    get_renormalized_weights,
    SOURCE_TAB_MAP,
)
from athena_app.ui.components import render_footnote


def init_settings_state():
    """Menginisialisasi session state konfigurasi runtime jika belum ada."""
    if "config_unlocked" not in st.session_state:
        st.session_state["config_unlocked"] = False
    if "active_config" not in st.session_state:
        st.session_state["active_config"] = dict(EXCEL_V6_DEFAULTS)
    if "staged_config" not in st.session_state:
        st.session_state["staged_config"] = dict(st.session_state["active_config"])
    
    # Matriks default pairwise AHP
    if "ahp_pairwise_l1" not in st.session_state:
        st.session_state["ahp_pairwise_l1"] = {
            ("E", "T"): 0.5,
            ("E", "R"): 1/3,
            ("E", "F"): 1/3,
            ("T", "R"): 0.5,
            ("T", "F"): 0.5,
            ("R", "F"): 1.0,
        }


def render_settings_page(engine_results: dict):
    init_settings_state()

    st.subheader("Pengaturan Lanjutan (Scenario & Assumption Generator)")
    st.markdown(
        "*Ubah asumsi teknis, finansial, lingkungan, risiko, dan bobot AHP untuk menghasilkan "
        "skenario alternatif secara dinamis.*"
    )

    # 1. GATE PASSWORD (PRD Addendum §10.2)
    if not st.session_state["config_unlocked"]:
        col_gate, _ = st.columns([1.2, 2])
        with col_gate:
            st.info("Akses pengaturan generator skenario kustom dilindungi kata sandi.")
            with st.form("config_unlock_form"):
                pwd_input = st.text_input("Masukkan Kata Sandi:", type="password", key="pwd_field")
                submit_unlock = st.form_submit_button("Buka Kunci Pengaturan", use_container_width=True)
                if submit_unlock:
                    if pwd_input == CONFIG_PASSWORD:
                        st.session_state["config_unlocked"] = True
                        st.success("Kata sandi benar. Membuka akses pengaturan...")
                        st.rerun()
                    else:
                        st.error("Kata sandi salah.")
        return

    # 2. STATUS ASUMSI AKTIF (PRD Addendum §10.2 & §10.7)
    diffs = ConfigManager.get_diffs(st.session_state["active_config"])
    staged_diffs = ConfigManager.get_diffs(st.session_state["staged_config"])

    if len(diffs) > 0:
        st.warning(
            f"ASUMSI AKTIF: KUSTOM — {len(diffs)} parameter diubah dari nilai Excel V6. "
            f"Seluruh model kalkulasi hilir mencerminkan penyesuaian ini."
        )
    else:
        st.info(
            "ASUMSI AKTIF: ASLI EXCEL V6 — Seluruh perhitungan 453 skenario dan modul multi-kriteria "
            "menggunakan nilai default acuan resmi."
        )

    # 3. 4 SUBTAB PIPELINE (Tahap 0 / 1 / 2 / 3)
    tab0, tab1, tab2, tab3 = st.tabs([
        "0 · Data & Kombinasi",
        "1 · Model Finansial",
        "2 · Multi-Kriteria",
        "3 · AHP & TOPSIS",
    ])

    cfg = st.session_state["staged_config"]

    # -------------------------------------------------------------------------
    # SUBTAB 0: DATA & KOMBINASI
    # -------------------------------------------------------------------------
    with tab0:
        group0 = st.selectbox(
            "Pilih grup konfigurasi:",
            options=["Data Teknis Lapangan", "Asumsi Sumur Idle", "Parameter Overlap", "CAPEX & OPEX BAU"],
            key="sb_group0",
        )
        st.markdown("---")

        if group0 == "Data Teknis Lapangan":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["q0"] = st.number_input(
                    "Laju Produksi Awal Minyak (q0) [bopd]:",
                    min_value=100.0, max_value=20000.0, value=float(cfg["q0"]), step=50.0,
                )
                cfg["wc0"] = st.number_input(
                    "Water Cut Awal Lapangan (wc0) [fraksi]:",
                    min_value=0.01, max_value=0.99, value=float(cfg["wc0"]), step=0.01,
                )
                cfg["d0"] = st.number_input(
                    "Decline Rate Tahunan Lapangan (d0) [fraksi/thn]:",
                    min_value=0.01, max_value=0.50, value=float(cfg["d0"]), step=0.005, format="%.3f",
                )
                cfg["lc0"] = st.number_input(
                    "Biaya Lifting Awal (lc0) [USD/bbl]:",
                    min_value=5.0, max_value=100.0, value=float(cfg["lc0"]), step=1.0,
                )
                cfg["n_total"] = st.number_input(
                    "Jumlah Sumur Total [sumur]:",
                    min_value=10, max_value=500, value=int(cfg["n_total"]), step=1,
                )
                cfg["n_active"] = st.number_input(
                    "Jumlah Sumur Aktif [sumur]:",
                    min_value=1, max_value=500, value=int(cfg["n_active"]), step=1,
                )
                cfg["n_idle"] = st.number_input(
                    "Jumlah Sumur Idle [sumur]:",
                    min_value=0, max_value=500, value=int(cfg["n_idle"]), step=1,
                )
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown(f"- q0: `2.000 bopd` (0.Existing Data!B9) {'[diubah]' if cfg['q0'] != 2000 else ''}")
                st.markdown(f"- wc0: `0,910` (0.Existing Data!B10) {'[diubah]' if cfg['wc0'] != 0.91 else ''}")
                st.markdown(f"- d0: `0,075/thn` (0.Existing Data!B8) {'[diubah]' if cfg['d0'] != 0.075 else ''}")
                st.markdown(f"- lc0: `31,0 USD/bbl` (0.Existing Data!B11) {'[diubah]' if cfg['lc0'] != 31.0 else ''}")
                st.markdown(f"- Total: `145 sumur` (0.Existing Data!B13)")
                st.markdown(f"- Aktif: `58 sumur` (0.Existing Data!B14)")
                st.markdown(f"- Idle: `87 sumur` (0.Existing Data!B15)")

            # Validasi silang: n_active + n_idle == n_total (Addendum §10.3)
            if cfg["n_active"] + cfg["n_idle"] != cfg["n_total"]:
                st.error(
                    f"Validasi Silang Gagal: Jumlah sumur aktif ({cfg['n_active']}) + idle ({cfg['n_idle']}) "
                    f"= {cfg['n_active'] + cfg['n_idle']}, tidak sama dengan Total Sumur ({cfg['n_total']})."
                )

        elif group0 == "Asumsi Sumur Idle":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["react_cost"] = st.number_input(
                    "Biaya Reaktivasi per Sumur Idle [USD/sumur]:",
                    min_value=10000.0, max_value=1000000.0, value=float(cfg["react_cost"]), step=10000.0,
                )
                st.write("Preset Biaya Cepat (Riset Excel V6):")
                p_c1, p_c2, p_c3 = st.columns(3)
                if p_c1.button("Rendah ($50k)"):
                    cfg["react_cost"] = 50000.0
                    st.rerun()
                if p_c2.button("Dasar ($159k)"):
                    cfg["react_cost"] = 159279.0
                    st.rerun()
                if p_c3.button("Tinggi ($421k)"):
                    cfg["react_cost"] = 420692.0
                    st.rerun()
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- Dasar: `$159.279 USD/sumur` (B71/B76)")
                st.markdown("- Rentang: Rendah `$50.000` (B75) s/d Tinggi `$420.692` (B77)")

        elif group0 == "Parameter Overlap":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["overlap_same_func"] = st.number_input(
                    "Bobot Overlap: Fungsi Sama (AN20) [fraksi]:",
                    min_value=0.0, max_value=1.0, value=float(cfg["overlap_same_func"]), step=0.05,
                )
                cfg["overlap_same_class"] = st.number_input(
                    "Bobot Overlap: Kelas Sama (Beda Fungsi) (AN21) [fraksi]:",
                    min_value=0.0, max_value=1.0, value=float(cfg["overlap_same_class"]), step=0.05,
                )
                cfg["overlap_diff_class"] = st.number_input(
                    "Bobot Overlap: Kelas Berbeda (AN22) [fraksi]:",
                    min_value=0.0, max_value=1.0, value=float(cfg["overlap_diff_class"]), step=0.05,
                )
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- Fungsi Sama: `0,80` (AN20)")
                st.markdown("- Kelas Sama: `0,40` (AN21)")
                st.markdown("- Kelas Beda: `0,15` (AN22)")

            # Validasi urutan overlap: AN20 >= AN21 >= AN22
            if not (cfg["overlap_same_func"] >= cfg["overlap_same_class"] >= cfg["overlap_diff_class"]):
                st.error("Validasi Urutan Gagal: Harus berlaku `Fungsi Sama (0.8) >= Kelas Sama (0.4) >= Kelas Beda (0.15)`.")

        elif group0 == "CAPEX & OPEX BAU":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["capex_annual_field"] = st.number_input(
                    "Anggaran CAPEX Rutin Tahunan BAU [USD Juta/thn]:",
                    min_value=0.5, max_value=20.0, value=float(cfg["capex_annual_field"]), step=0.5,
                )
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- Anggaran Tahunan: `4,0 USD Juta/thn` (0.Existing Data!B21)")

    # -------------------------------------------------------------------------
    # SUBTAB 1: MODEL FINANSIAL
    # -------------------------------------------------------------------------
    with tab1:
        group1 = st.selectbox(
            "Pilih grup konfigurasi:",
            options=["Harga Minyak & Discount Rate", "Pajak & Split Kontrak", "Periode & Eskalasi", "Produksi & Treatment", "Farm-In"],
            key="sb_group1",
        )
        st.markdown("---")

        if group1 == "Harga Minyak & Discount Rate":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["price_low"] = st.number_input(
                    "Harga Minyak Acuan Low [USD/bbl]:",
                    min_value=20.0, max_value=200.0, value=float(cfg["price_low"]), step=1.0,
                )
                cfg["price_base"] = st.number_input(
                    "Harga Minyak Acuan Base [USD/bbl]:",
                    min_value=20.0, max_value=200.0, value=float(cfg["price_base"]), step=1.0,
                )
                cfg["price_high"] = st.number_input(
                    "Harga Minyak Acuan High [USD/bbl]:",
                    min_value=20.0, max_value=250.0, value=float(cfg["price_high"]), step=1.0,
                )
                cfg["dr_main"] = st.number_input(
                    "Discount Rate Utama (dr_main) [fraksi]:",
                    min_value=0.01, max_value=0.30, value=float(cfg["dr_main"]), step=0.01, format="%.2f",
                )
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown(f"- Low: `64 USD/bbl` (B39) {'[diubah]' if cfg['price_low'] != 64 else ''}")
                st.markdown(f"- Base: `80 USD/bbl` (B40) {'[diubah]' if cfg['price_base'] != 80 else ''}")
                st.markdown(f"- High: `117 USD/bbl` (B41) {'[diubah]' if cfg['price_high'] != 117 else ''}")
                st.markdown(f"- Discount Rate: `10,0%` (B45) {'[diubah]' if cfg['dr_main'] != 0.10 else ''}")

        elif group1 == "Pajak & Split Kontrak":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["split_c"] = st.number_input(
                    "Gross Split Kontraktor (PNE) [fraksi]:",
                    min_value=0.10, max_value=0.90, value=float(cfg["split_c"]), step=0.05,
                )
                cfg["tax"] = st.number_input(
                    "Tarif Pajak Penghasilan (Income Tax) [fraksi]:",
                    min_value=0.0, max_value=0.60, value=float(cfg["tax"]), step=0.05,
                )
                gov_split = 1.0 - cfg["split_c"]
                st.text_input("Gross Split Pemerintah (Gov. Take) [Turunan]:", value=f"{gov_split*100:.1f}%", disabled=True)
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- Split Kontraktor: `55,0%` (0.Existing Data!B42)")
                st.markdown("- Pajak Penghasilan: `40,0%` (0.Existing Data!B44)")
                st.markdown("- Split Pemerintah: `45,0%` (turunan 1 - Split)")

        elif group1 == "Periode & Eskalasi":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["eval_period"] = st.number_input(
                    "Periode Evaluasi Finansial [tahun]:",
                    min_value=5, max_value=30, value=int(cfg["eval_period"]), step=1,
                )
                cfg["lc_esc"] = st.number_input(
                    "Eskalasi Biaya Lifting Tahunan [fraksi/thn]:",
                    min_value=-0.05, max_value=0.20, value=float(cfg["lc_esc"]), step=0.01,
                )
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- Periode Evaluasi: `15 tahun` (B38)")
                st.markdown("- Eskalasi Biaya: `3,0%/thn` (B49)")

        elif group1 == "Produksi & Treatment":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["alpha"] = st.number_input(
                    "Alpha Sensitivitas Decline Lapangan (alpha) [fraksi]:",
                    min_value=0.0, max_value=1.0, value=float(cfg["alpha"]), step=0.05,
                )
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- Alpha: `0,50` (1.Contoh Perhitungan!B23)")

        elif group1 == "Farm-In":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["wi_xyz"] = st.number_input(
                    "Working Interest Partner XYZ [fraksi]:",
                    min_value=0.05, max_value=0.80, value=float(cfg["wi_xyz"]), step=0.05,
                )
                cfg["carry"] = st.number_input(
                    "Porsi CAPEX Carry XYZ (t=0) [fraksi]:",
                    min_value=0.0, max_value=1.0, value=float(cfg["carry"]), step=0.05,
                )
                wi_pne = 1.0 - cfg["wi_xyz"]
                st.text_input("Working Interest PNE [Turunan]:", value=f"{wi_pne*100:.1f}%", disabled=True)
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- WI XYZ: `40,0%` (B24)")
                st.markdown("- Carry XYZ: `70,0%` (B26)")
                st.markdown("- WI PNE: `60,0%` (turunan)")

    # -------------------------------------------------------------------------
    # SUBTAB 2: MULTI-KRITERIA
    # -------------------------------------------------------------------------
    with tab2:
        group2 = st.selectbox(
            "Pilih grup konfigurasi:",
            options=[
                "Saklar & GWP Lingkungan",
                "Faktor Emisi Scope 1 & 2",
                "Harga Karbon & Kurs",
                "Rig Workover",
                "Ambang & Skala FMEA",
                "Parameter Skala Teknis",
            ],
            key="sb_group2",
        )
        st.markdown("---")

        if group2 == "Saklar & GWP Lingkungan":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                gwp_choice = st.radio("Set Protokol GWP 100-Thn:", options=["AR5 (CH4=30)", "AR6 (CH4=29.8)"], index=1)
                cfg["gwp_set"] = 2 if "AR6" in gwp_choice else 1
                cfg["gwp_ch4"] = 29.8 if cfg["gwp_set"] == 2 else 30.0
                cfg["scale_factor"] = st.number_input(
                    "Faktor Skala Metana & Flaring [faktor]:",
                    min_value=0.1, max_value=3.0, value=float(cfg["scale_factor"]), step=0.1,
                )
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- Protokol Terpilih: `AR6 (B100=2)`")
                st.markdown("- GWP CH4: `29,8` (B113)")
                st.markdown("- Faktor Skala: `1,0` (B104)")

        elif group2 == "Faktor Emisi Scope 1 & 2":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                st.caption("Status: Faktor emisi Scope 1 ditandai UNVERIFIED di Excel V6.")
                cfg["s1_fugitive_ch4"] = st.number_input("Fugitive CH4 [t/m3]:", value=float(cfg["s1_fugitive_ch4"]), format="%.5f")
                cfg["s1_venting_ch4"] = st.number_input("Venting CH4 [t/m3]:", value=float(cfg["s1_venting_ch4"]), format="%.5f")
                cfg["grid_factor_sumatera"] = st.number_input("Faktor Grid Sumatera [tCO2e/MWh]:", value=float(cfg["grid_factor_sumatera"]), step=0.01)
                cfg["lift_kwh_per_bbl"] = st.number_input("Listrik Artificial Lift [kWh/bbl]:", value=float(cfg["lift_kwh_per_bbl"]), step=0.05)
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- Fugitive: `0,00295 t/m3` (B120)")
                st.markdown("- Venting: `0,01035 t/m3` (B121)")
                st.markdown("- Grid Sumatera: `0,805 tCO2e/MWh` (B127)")
                st.markdown("- Listrik Lift: `0,52 kWh/bbl` (B128)")

        elif group2 == "Harga Karbon & Kurs":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["carbon_price_rp"] = st.number_input("Tarif Pajak Karbon [Rp/tCO2e]:", value=float(cfg["carbon_price_rp"]), step=5000.0)
                cfg["usd_rate"] = st.number_input("Kurs Nilai Tukar [Rp/USD]:", value=float(cfg["usd_rate"]), step=100.0)
                price_usd = cfg["carbon_price_rp"] / cfg["usd_rate"]
                st.text_input("Tarif Pajak Karbon [USD/tCO2e] (Turunan):", value=f"${price_usd:.2f}", disabled=True)
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- Pajak Karbon: `Rp30.000 / tCO2e` (B144)")
                st.markdown("- Kurs: `Rp17.669 / USD` (B96)")

        elif group2 == "Rig Workover":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["rig_days_idle"] = st.number_input("Durasi Rig Sumur Idle [hari]:", min_value=1.0, max_value=60.0, value=float(cfg["rig_days_idle"]), step=1.0)
                cfg["rig_days_active"] = st.number_input("Durasi Rig Sumur Aktif [hari] (PLACEHOLDER):", min_value=1.0, max_value=30.0, value=float(cfg["rig_days_active"]), step=1.0)
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- Hari Rig Idle: `17 hari` (B159)")
                st.markdown("- Hari Rig Aktif: `5 hari` [PLACEHOLDER] (B160)")

        elif group2 == "Ambang & Skala FMEA":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["fmea_critical"] = st.number_input("Ambang Batas Critical (RPN >=):", min_value=100, max_value=1000, value=int(cfg["fmea_critical"]), step=25)
                cfg["fmea_high"] = st.number_input("Ambang Batas High (RPN >=):", min_value=50, max_value=500, value=int(cfg["fmea_high"]), step=25)
                cfg["fmea_medium"] = st.number_input("Ambang Batas Medium (RPN >=):", min_value=10, max_value=200, value=int(cfg["fmea_medium"]), step=10)
                cfg["fmea_esc_severity"] = st.number_input("Eskalasi Khusus Severity (S >=):", min_value=7, max_value=10, value=int(cfg["fmea_esc_severity"]), step=1)
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- Critical: `>= 200` (B64)")
                st.markdown("- High: `>= 100` (B65)")
                st.markdown("- Medium: `>= 50` (B66)")
                st.markdown("- Low: `< 50` (B67)")
                st.markdown("- Eskalasi: `S >= 9` (B68)")

            # Validasi urutan ambang FMEA
            if not (cfg["fmea_critical"] > cfg["fmea_high"] > cfg["fmea_medium"] > 0):
                st.error("Validasi Ambang Gagal: Ambang FMEA harus bertingkat menurun (`Critical > High > Medium > Low`).")

        elif group2 == "Parameter Skala Teknis":
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                cfg["tech_score_min"] = st.number_input("Skor Skala Minimum:", value=float(cfg["tech_score_min"]), step=1.0)
                cfg["tech_score_max"] = st.number_input("Skor Skala Maksimum:", value=float(cfg["tech_score_max"]), step=1.0)
                cfg["tech_trl_max"] = st.number_input("Skala TRL Maksimum:", value=int(cfg["tech_trl_max"]), step=1)
                cfg["tech_local_cases_full"] = st.number_input("Kasus Lokal untuk Skor Penuh:", value=int(cfg["tech_local_cases_full"]), step=1)
            with col_b:
                st.caption("Nilai Acuan Excel V6:")
                st.markdown("- Skor: `1` s/d `5` (B35:B36)")
                st.markdown("- TRL Maks: `7` (B37)")
                st.markdown("- Kasus Penuh: `3 kasus` (B38)")

    # -------------------------------------------------------------------------
    # SUBTAB 3: AHP & TOPSIS (UI KHUSUS SLIDER DISKRET SAATY §10.4)
    # -------------------------------------------------------------------------
    with tab3:
        group3 = st.selectbox(
            "Pilih grup konfigurasi:",
            options=[
                "AHP Level 1 — Bobot Kriteria Utama",
                "AHP Level 2 — Environmental",
                "AHP Level 2 — Technical",
                "AHP Level 2 — Risk",
                "AHP Level 2 — Financial",
                "TOPSIS — Cakupan & Arah Kriteria",
            ],
            key="sb_group3",
        )
        st.markdown("---")

        if group3 == "AHP Level 1 — Bobot Kriteria Utama":
            st.markdown("#### Matriks Perbandingan Berpasangan Level 1 (4x4)")
            st.caption("Pilih preferensi Saaty 17 titik untuk 6 pasangan segitiga atas. Segitiga bawah otomatis resiprok.")

            pairs_l1 = [
                ("Environmental", "Technical", ("E", "T"), 0.5),
                ("Environmental", "Risk", ("E", "R"), 1/3),
                ("Environmental", "Financial", ("E", "F"), 1/3),
                ("Technical", "Risk", ("T", "R"), 0.5),
                ("Technical", "Financial", ("T", "F"), 0.5),
                ("Risk", "Financial", ("R", "F"), 1.0),
            ]

            pw_dict = st.session_state["ahp_pairwise_l1"]
            for name_a, name_b, key_pair, def_val in pairs_l1:
                cur_v = pw_dict.get(key_pair, def_val)
                closest_idx = int(np.argmin([abs(v - cur_v) for v in SAATY_SCALE_VALUES]))
                
                c_lbl, c_slider, c_text = st.columns([1.2, 2, 2])
                with c_lbl:
                    st.markdown(f"**{name_a}** vs **{name_b}**")
                with c_slider:
                    sel_val = st.select_slider(
                        f"Skala {name_a}-{name_b}",
                        options=SAATY_SCALE_VALUES,
                        value=SAATY_SCALE_VALUES[closest_idx],
                        format_func=lambda x: f"{x:.2f}" if x >= 1 else f"1/{round(1/x)}",
                        key=f"slider_l1_{key_pair[0]}_{key_pair[1]}",
                        label_visibility="collapsed",
                    )
                    pw_dict[key_pair] = sel_val
                with c_text:
                    st.caption(get_saaty_text(sel_val, name_a, name_b))

            # Susun matriks 4x4
            names_4 = ["E", "T", "R", "F"]
            idx_map = {n: i for i, n in enumerate(names_4)}
            mat_4 = np.ones((4, 4))
            for (k1, k2), val in pw_dict.items():
                i, j = idx_map[k1], idx_map[k2]
                mat_4[i, j] = val
                mat_4[j, i] = 1.0 / val

            weights_l1, lmax_l1, ci_l1, cr_l1, is_ok_l1 = calculate_ahp_matrix(mat_4)
            # Simpan bobot level 1 terhitung ke staged config
            cfg["ahp_l1_weights"] = {
                "Environmental": float(weights_l1[0]),
                "Technical": float(weights_l1[1]),
                "Risk": float(weights_l1[2]),
                "Financial": float(weights_l1[3]),
            }

            # Live CR Badge tanpa emoticon
            cr_limit = 0.08  # '1.AHP'!C81
            if cr_l1 <= cr_limit:
                badge_html = (
                    f'<div style="background: #ECFDF5; border: 1px solid #059669; border-radius: 6px; padding: 8px 14px; margin: 12px 0;">'
                    f'<span style="color: #059669; font-weight: 700;">STATUS: KONSISTEN (CR = {cr_l1:.4f} <= {cr_limit})</span> — '
                    f'<span style="font-size: 0.82rem; color: #065F46;">Judgment matriks Level 1 memenuhi syarat konsistensi Saaty.</span></div>'
                )
            else:
                badge_html = (
                    f'<div style="background: #FEF2F2; border: 1px solid #DC2626; border-radius: 6px; padding: 8px 14px; margin: 12px 0;">'
                    f'<span style="color: #DC2626; font-weight: 700;">STATUS: TINJAU ULANG (CR = {cr_l1:.4f} > {cr_limit})</span> — '
                    f'<span style="font-size: 0.82rem; color: #991B1B;">Inkonsistensi judgment terlampaui. Tetap diizinkan, namun pertimbangkan merevisi preferensi pasangan.</span></div>'
                )
            st.markdown(badge_html, unsafe_allow_html=True)

            # Bobot Hasil vs Excel
            df_w = pd.DataFrame([
                {"Kriteria": "Environmental (E)", "Bobot Saat Ini": f"{weights_l1[0]*100:.2f}%", "Bobot Excel V6": "10.93%"},
                {"Kriteria": "Technical (T)", "Bobot Saat Ini": f"{weights_l1[1]*100:.2f}%", "Bobot Excel V6": "18.92%"},
                {"Kriteria": "Risk (R)", "Bobot Saat Ini": f"{weights_l1[2]*100:.2f}%", "Bobot Excel V6": "35.07%"},
                {"Kriteria": "Financial (F)", "Bobot Saat Ini": f"{weights_l1[3]*100:.2f}%", "Bobot Excel V6": "35.07%"},
            ])
            st.dataframe(df_w, use_container_width=True, hide_index=True)

        elif group3 in ["AHP Level 2 — Environmental", "AHP Level 2 — Technical", "AHP Level 2 — Risk", "AHP Level 2 — Financial"]:
            crit_name = group3.split("—")[-1].strip()
            l2_info = AHP_LEVEL2_MATRICES.get(crit_name)

            st.markdown(f"#### Matriks Perbandingan Berpasangan Level 2 ({crit_name} 5×5)")
            st.caption(
                f"Matriks preferensi berpasangan 5×5 untuk sub-kriteria {crit_name} dari sheet '1.AHP'. "
                f"Seluruh bobot lokal dan global otomatis terhubung ke perhitungan TOPSIS."
            )

            # Badge konsistensi tanpa emoticon
            cr_val = l2_info["cr"]
            st.markdown(
                f'<div style="background: #ECFDF5; border: 1px solid #059669; border-radius: 6px; padding: 8px 14px; margin: 10px 0;">'
                f'<span style="color: #059669; font-weight: 700;">STATUS: KONSISTEN (CR = {cr_val:.4f} <= 0.10)</span> — '
                f'<span style="font-size: 0.82rem; color: #065F46;">Matriks Level 2 {crit_name} memenuhi syarat konsistensi Saaty.</span></div>',
                unsafe_allow_html=True,
            )

            # Tampilkan Matriks 5x5
            df_mat = pd.DataFrame(
                l2_info["matrix"],
                index=[f"{sub_id}" for sub_id in l2_info["ids"]],
                columns=[f"{sub_id}" for sub_id in l2_info["ids"]],
            )
            st.write("**Matriks Perbandingan Berpasangan 5×5:**")
            st.dataframe(df_mat.style.format("{:.2f}"), use_container_width=True)

            # Hitung bobot lokal dan global terhubung ke Level 1 aktif
            l1_weight = float(cfg.get("ahp_l1_weights", {}).get(crit_name, EXCEL_V6_DEFAULTS["ahp_l1_weights"][crit_name]))
            sub_configs = get_renormalized_weights(cfg.get("ahp_l1_weights"))
            sub_dict = {sc["id"]: sc for sc in sub_configs}

            st.write(f"**Rincian Bobot Sub-Kriteria {crit_name} & Tab Asal:**")
            df_l2_summary = pd.DataFrame([
                {
                    "ID": sub_id,
                    "Nama Sub-Kriteria": sub_dict[sub_id]["name"],
                    "Arah": sub_dict[sub_id]["direction"],
                    "Bobot Level 1 (Induk)": f"{l1_weight*100:.2f}%",
                    "Bobot Lokal Level 2": f"{sub_dict[sub_id]['level2_weight']*100:.2f}%",
                    "Bobot Global (L1 × L2)": f"{sub_dict[sub_id]['raw_global_weight']*100:.2f}%",
                    "Bobot Normalisasi TOPSIS": f"{sub_dict[sub_id]['normalized_weight']*100:.2f}%" if sub_dict[sub_id]["is_active"] else "0.00% (Redistribusi)",
                    "Status": "Aktif" if sub_dict[sub_id]["is_active"] else "Nonaktif (Redistribusi)",
                    "Tab Asal Data": sub_dict[sub_id]["source_tab"],
                }
                for sub_id in l2_info["ids"]
            ])
            st.dataframe(df_l2_summary, use_container_width=True, hide_index=True)

        elif group3 == "TOPSIS — Cakupan & Arah Kriteria":
            st.markdown("#### Cakupan 20 Sub-Kriteria & Arah Optimasi TOPSIS")
            st.caption(
                "Daftar lengkap 20 sub-kriteria beserta bobot Level 1, Level 2, bobot efektif normalisasi TOPSIS, "
                "dan tautan ke tab asalnya masing-masing. Bobot terupdate otomatis mengikuti preferensi AHP."
            )

            sub_configs = get_renormalized_weights(custom_l1_weights=cfg.get("ahp_l1_weights"))
            topsis_config = [
                {
                    "ID": sc["id"],
                    "Sub-Kriteria": sc["name"],
                    "Dimensi (Level 1)": sc["parent"],
                    "Arah": sc["direction"],
                    "Bobot Level 1": f"{sc['level1_weight']*100:.2f}%",
                    "Bobot Level 2": f"{sc['level2_weight']*100:.2f}%",
                    "Bobot Global Mentah": f"{sc['raw_global_weight']*100:.2f}%",
                    "Bobot Efektif TOPSIS": f"{sc['normalized_weight']*100:.2f}%" if sc["is_active"] else "0.00% (Redistribusi)",
                    "Status": "Aktif" if sc["is_active"] else "Nonaktif (Redistribusi)",
                    "Tab Asal Data": sc["source_tab"],
                }
                for sc in sub_configs
            ]
            st.dataframe(pd.DataFrame(topsis_config), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # 4. PARAMETER YANG DIKUNCI (PRD Addendum §10.6)
    # -------------------------------------------------------------------------
    st.markdown("---")
    with st.expander("Tidak Dapat Diubah di Versi Ini (Parameter Struktural)", expanded=False):
        locked_info = [
            {"Komponen": "Matriks Kompatibilitas 18x18", "Alamat Excel": "0.Combination!U5:AM23", "Alasan Penguncian": "Menentukan validitas kombinasi; mengubahnya mengubah 453 kombinasi dasar"},
            {"Komponen": "Hard Constraint Aquifer / Heterogeneity", "Alamat Excel": "0.Introduction!E22:H39", "Alasan Penguncian": "Menentukan 13 metode lolos teknis dasar lapangan"},
            {"Komponen": "Daftar & Jumlah 18 Metode Intervensi", "Alamat Excel": "0.Introduction!B5:C22", "Alasan Penguncian": "Basis data referensi intervensi industri"},
            {"Komponen": "Pool Biaya & Aturan Pool (Sekali/Jumlah)", "Alamat Excel": "0.CAPEX OPEX Breakdown!M-N", "Alasan Penguncian": "Mengubah struktur cost-pooling fasilitas bersama"},
            {"Komponen": "Tabel Random Index (RI) Saaty", "Alamat Excel": "1.AHP!C68:C77", "Alasan Penguncian": "Konstanta matematis literatur baku"},
            {"Komponen": "Cakupan Failure Mode Generik (run/well)", "Alamat Excel": "1.Risk!B144:B150", "Alasan Penguncian": "Struktur formula probabilitas multi-run 1 - (1-P)^n"},
        ]
        st.dataframe(pd.DataFrame(locked_info), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # 5. TOMBOL AKSI GLOBAL & JEJAK AUDIT (PRD Addendum §10.2 & §10.7)
    # -------------------------------------------------------------------------
    st.markdown("### Eksekusi & Jejak Audit Asumsi")
    col_act1, col_act2, col_act3, col_act4 = st.columns([1.5, 1.5, 1.2, 1.2])

    with col_act1:
        num_changes = len(staged_diffs)
        btn_label = f"Terapkan & Hitung Ulang ({num_changes} perubahan)" if num_changes > 0 else "Terapkan & Hitung Ulang Semua"
        if st.button(btn_label, type="primary", use_container_width=True):
            with st.spinner("Menerapkan asumsi kustom dan menghitung ulang seluruh pipeline..."):
                st.session_state["active_config"] = dict(st.session_state["staged_config"])
                # Pemicu agar radio harga global di sidebar tersinkron jika harga diubah
                if "price_base" in st.session_state["active_config"]:
                    st.session_state["selected_price"] = int(st.session_state["active_config"]["price_base"])
                st.success("Perubahan berhasil diterapkan ke seluruh halaman!")
                st.rerun()

    with col_act2:
        if st.button("Kembalikan Semua ke Nilai Excel", use_container_width=True):
            st.session_state["staged_config"] = dict(EXCEL_V6_DEFAULTS)
            st.session_state["active_config"] = dict(EXCEL_V6_DEFAULTS)
            st.success("Seluruh asumsi telah dikembalikan ke nilai default Excel V6.")
            st.rerun()

    with col_act3:
        json_str = ConfigManager.export_json(st.session_state["active_config"])
        st.download_button(
            label="Unduh .json",
            data=json_str,
            file_name="Athena_Scenario_Config.json",
            mime="application/json",
            use_container_width=True,
        )

    with col_act4:
        uploaded_json = st.file_uploader("Muat .json", type=["json"], label_visibility="collapsed")
        if uploaded_json is not None:
            try:
                loaded_cfg = ConfigManager.import_json(uploaded_json.read().decode("utf-8"))
                st.session_state["staged_config"].update(loaded_cfg)
                st.session_state["active_config"].update(loaded_cfg)
                st.success("Konfigurasi JSON berhasil dimuat!")
                st.rerun()
            except Exception as e:
                st.error(f"Gagal memuat file JSON: {e}")

    # Tabel Perubahan Aktif
    if len(diffs) > 0:
        st.markdown("#### Tabel Parameter yang Mengalami Perubahan (Custom Diffs)")
        df_diff = pd.DataFrame([
            {
                "Parameter": d["label"],
                "Alamat Sel": d["cell"],
                "Nilai Excel V6": d["excel_val"],
                "Nilai Kustom Aktif": d["current_val"],
                "Satuan": d["unit"],
                "Selisih": d["diff"],
            }
            for d in diffs
        ])
        st.dataframe(df_diff, use_container_width=True, hide_index=True)

    render_footnote()
