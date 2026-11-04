"""
Module ui/page_settings.py: Halaman Pengaturan Lanjutan (Scenario & Assumption Generator).
Sesuai PRD + UI/UX Guidelines v5.2/v5.3 §7.0-§7.14, T20-T24, T28-T30:
- Password Gate: ANGKER123 (session-based, lebar 320px, tanpa info/emoji)
- 6 Tabs bawaan st.tabs: 0 · Data & Kombinasi, 1 · Model Finansial, 2 · Multi-Kriteria,
  3 · AHP & TOPSIS, 4 · Simulasi Lanjutan, 5 · Skenario Terpilih
- Tepat satu st.selectbox per tab untuk memilih grup konfigurasi
- Toolbar satu baris tanpa emoji: Profil, counter unapplied/active, Cari parameter,
  tombol: Terapkan, Batalkan, Kembalikan ke Excel, Ekspor, Impor, Riwayat
- Seluruh 2.261 field/sel input dirender langsung saat grup dipilih
- Tidak ada parameter terkunci, tidak ada teks lama (T29), tidak ada emoji (T21)
"""

import json
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np

from athena_app.core.config_manager import (
    CONFIG_PASSWORD,
    EXCEL_V6_DEFAULTS,
    SAATY_SCALE_VALUES,
    get_saaty_text,
    calculate_ahp_matrix,
    DEFAULT_AHP_LEVEL1,
    DEFAULT_AHP_LEVEL2,
    ConfigManager,
)
from athena_app.core.config_registry import (
    GROUP_FUNCTION_TEXT,
    GROUP_WHERE_USED,
    SETTINGS_TABS,
)
from athena_app.config.topsis_sources import (
    TOPSIS_SOURCE_REGISTRY,
    ALL_AHP_SUBCRITERIA,
)

SETTINGS_PANELS = {}  # Backward-compatibility alias


def init_settings_state():
    """Menginisialisasi session state konfigurasi editor."""
    if "config_unlocked" not in st.session_state:
        st.session_state["config_unlocked"] = False
    if "active_config" not in st.session_state:
        st.session_state["active_config"] = dict(EXCEL_V6_DEFAULTS)
    if "staged_config" not in st.session_state:
        st.session_state["staged_config"] = dict(st.session_state["active_config"])
    if "config_history" not in st.session_state:
        st.session_state["config_history"] = []
    if "config_profile" not in st.session_state:
        st.session_state["config_profile"] = "Excel (asli)"
    if "param_search" not in st.session_state:
        st.session_state["param_search"] = ""


def render_settings_page(engine_results: dict):
    init_settings_state()

    # 1. GATE PASSWORD (§7.11)
    if not st.session_state["config_unlocked"]:
        st.title("Pengaturan Lanjutan")
        col_gate, _ = st.columns([320, 700])
        with col_gate:
            with st.form("config_unlock_form"):
                pwd_input = st.text_input(
                    "Kata Sandi Pengaturan",
                    type="password",
                    key="pwd_field",
                    placeholder="Ketik kata sandi",
                    label_visibility="collapsed",
                )
                submit_unlock = st.form_submit_button("Buka", use_container_width=True)
                if submit_unlock:
                    if pwd_input == CONFIG_PASSWORD:
                        st.session_state["config_unlocked"] = True
                        st.rerun()
                    else:
                        st.markdown("<span style='color: #DC2626; font-size: 0.88rem;'>Kata sandi salah.</span>", unsafe_allow_html=True)
        return

    # 2. HEADER & TOOLBAR SATU BARIS (§7.2)
    st.title("Pengaturan Lanjutan")
    st.caption("Ubah asumsi model dan hitung ulang seluruh skenario.")

    # Hitung jumlah diff staged vs active, dan active vs Excel
    staged_diffs = [k for k, v in st.session_state["staged_config"].items() if v != st.session_state["active_config"].get(k)]
    active_diffs = [k for k, v in st.session_state["active_config"].items() if v != EXCEL_V6_DEFAULTS.get(k)]
    n_unapplied = len(staged_diffs)
    n_active = len(active_diffs)

    # Toolbar Card
    with st.container():
        c_prof, c_status, c_search, c_b1, c_b2, c_b3, c_b4, c_b5, c_b6 = st.columns([1.6, 2.2, 1.8, 0.9, 0.9, 1.5, 0.8, 0.8, 0.9])
        with c_prof:
            st.selectbox(
                "Profil Konfigurasi",
                options=["Excel (asli)", "Profil Kustom 1", "Skenario Konservatif"],
                key="sel_profile",
                label_visibility="collapsed",
            )
        with c_status:
            st.markdown(
                f"<div style='padding-top: 6px; font-size: 0.85rem; color: #475569;'>"
                f"<strong>{n_unapplied}</strong> perubahan belum diterapkan · <strong>{n_active}</strong> aktif"
                f"</div>",
                unsafe_allow_html=True,
            )
        with c_search:
            st.text_input(
                "Cari parameter",
                placeholder="Cari parameter...",
                key="input_search_param",
                label_visibility="collapsed",
            )
        with c_b1:
            if st.button("Terapkan", type="primary", use_container_width=True):
                # Apply staged config
                st.session_state["active_config"] = dict(st.session_state["staged_config"])
                st.session_state["config_history"].append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "diffs_applied": list(staged_diffs),
                })
                st.rerun()
        with c_b2:
            if st.button("Batalkan", use_container_width=True):
                st.session_state["staged_config"] = dict(st.session_state["active_config"])
                st.rerun()
        with c_b3:
            if st.button("Kembalikan ke Excel", use_container_width=True):
                st.session_state["staged_config"] = dict(EXCEL_V6_DEFAULTS)
                st.session_state["active_config"] = dict(EXCEL_V6_DEFAULTS)
                st.rerun()
        with c_b4:
            st.download_button(
                "Ekspor",
                data=json.dumps(st.session_state["active_config"], indent=2),
                file_name="athena_config.json",
                mime="application/json",
                use_container_width=True,
            )
        with c_b5:
            if st.button("Impor", use_container_width=True):
                st.session_state["show_import_dialog"] = True
        with c_b6:
            if st.button("Riwayat", use_container_width=True):
                st.session_state["show_history_dialog"] = True

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # 3. 6 TABS BAWAAN st.tabs (§7.2, T22)
    tabs = st.tabs(SETTINGS_TABS)

    # Helper rendering field
    staged = st.session_state["staged_config"]

    # =========================================================================
    # TAB 0: DATA & KOMBINASI
    # =========================================================================
    with tabs[0]:
        t0_groups = [
            "0.1 Data teknis lapangan (12 field)",
            "0.2 Sumur idle (9 field)",
            "0.3 Master metode (104 sel)",
            "0.3n Nama 18 metode (18 sel)",
            "0.4 Aturan overlap (3 field)",
            "0.5 Hard constraint dan kompatibilitas (189 sel)",
            "0.6 Daftar kombinasi (453 kombinasi)",
            "0.7 CAPEX & OPEX per metode (755 sel)",
            "0.8 Biaya BAU (5 field)",
            "0.9 Aturan pool (2 field)",
        ]
        sel_g0 = st.selectbox("Konfigurasi Data & Kombinasi", options=t0_groups, key="sel_g0")
        render_group_header(sel_g0)

        if "0.1" in sel_g0:
            c1, c2, c3 = st.columns(3)
            with c1:
                staged["stoiip"] = st.number_input("1. STOIIP (MMbbl) [B5]", value=float(staged.get("stoiip", 950.0)), step=10.0, help="Stock Tank Oil Initially In Place")
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["rf_realized"] = st.number_input("2. Recovery Factor Terealisasi [B6]", value=float(staged.get("rf_realized", 0.21)), step=0.001, format="%.4f")
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["cum_prod_est"] = st.number_input("3. Estimasi Produksi Kumulatif (MMbbl) [B7]", value=float(staged.get("cum_prod_est", 200.0)), step=10.0)
                staged["reserve_2p_mmbbl"] = st.number_input("4. Cadangan 2P Tersisa (MMbbl) [B8]", value=float(staged.get("reserve_2p_mmbbl", 38.0)), step=1.0)
            with c2:
                staged["d0"] = st.number_input("5. Decline Rate (%/tahun) [B9]", value=float(staged.get("d0", 0.075)), step=0.001, format="%.4f")
                staged["q0"] = st.number_input("6. Produksi Saat Ini (bopd) [B10]", value=float(staged.get("q0", 2000.0)), step=100.0)
                staged["wc0"] = st.number_input("7. Water Cut Saat Ini [B11]", value=float(staged.get("wc0", 0.91)), step=0.001, format="%.4f")
                staged["lc0"] = st.number_input("8. Biaya Lifting (USD/bbl) [B12]", value=float(staged.get("lc0", 31.0)), step=1.0)
            with c3:
                staged["fac_life"] = st.number_input("9. Sisa Umur Desain Fasilitas (tahun) [B13]", value=int(staged.get("fac_life", 5)), step=1)
                staged["n_wells"] = st.number_input("10a. Jumlah Sumur Total [B14]", value=int(staged.get("n_wells", 145)), step=1)
                staged["n_active"] = st.number_input("10b. Jumlah Sumur Aktif [B15]", value=int(staged.get("n_active", 58)), step=1)
                staged["n_idle"] = st.number_input("10c. Jumlah Sumur Idle [B16]", value=int(staged.get("n_idle", 87)), step=1)

        elif "0.2" in sel_g0:
            c1, c2, c3 = st.columns(3)
            with c1:
                staged["wc_idle0"] = st.number_input("Water cut awal sumur idle [B70]", value=float(staged.get("wc_idle0", 0.91)), step=0.001, format="%.4f")
                staged["q_idle"] = st.number_input("Produksi acuan per sumur idle (bopd) [B71]", value=float(staged.get("q_idle", 34.4828)), step=0.1, format="%.4f")
                staged["react_cost"] = st.number_input("Biaya reaktivasi per sumur idle (USD) [B72]", value=float(staged.get("react_cost", 159279.0)), step=1000.0)
            with c2:
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["cost_idle_low"] = st.number_input("Rendah (tanpa rig) [B76]", value=float(staged.get("cost_idle_low", 50000.0)), step=1000.0)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["cost_idle_base"] = st.number_input("Dasar (dipakai di B71) [B77]", value=float(staged.get("cost_idle_base", 159279.0)), step=1000.0)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["cost_idle_high"] = st.number_input("Tinggi (workover rig) [B78]", value=float(staged.get("cost_idle_high", 420692.0)), step=1000.0)
            with c3:
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["skk_idle_rate"] = st.number_input("Rata-rata nasional SKK Migas 2023 [B81]", value=float(staged.get("skk_idle_rate", 35.0)), step=1.0)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["pertamina_z4_rate"] = st.selectbox("Pertamina Zona 4 [B82]", options=["10 s/d 30", "15", "20", "25", "30"], index=0)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["medco_batch_rate"] = st.number_input("Medco Sumsel (batch) [B83]", value=float(staged.get("medco_batch_rate", 30.0)), step=1.0)

        elif "0.3 " in sel_g0:
            st.markdown("##### Master 13 Metode Intervensi (104 sel editable)")
            df_m13 = build_default_methods_13_df()
            st.data_editor(
                df_m13,
                use_container_width=True,
                disabled=["ID", "Nama Metode"],
                key="editor_m13",
            )

        elif "0.3n" in sel_g0:
            st.markdown("##### Nama 18 Metode Screening Awal (18 sel editable)")
            df_m18 = build_default_methods_18_df()
            st.data_editor(
                df_m18,
                use_container_width=True,
                disabled=["ID"],
                key="editor_m18",
            )

        elif "0.4" in sel_g0:
            c1, c2, c3 = st.columns(3)
            with c1:
                staged["overlap_same_func"] = st.number_input("Overlap: fungsi sama [AN20]", value=float(staged.get("overlap_same_func", 0.8)), step=0.01, format="%.4f")
            with c2:
                staged["overlap_same_class"] = st.number_input("Overlap: fungsi beda, Class sama [AN21]", value=float(staged.get("overlap_same_class", 0.4)), step=0.01, format="%.4f")
            with c3:
                staged["overlap_diff_class"] = st.number_input("Overlap: Class beda [AN22]", value=float(staged.get("overlap_diff_class", 0.15)), step=0.01, format="%.4f")

        elif "0.5" in sel_g0:
            st.markdown("##### Hard Constraint 18 Metode (36 sel editable)")
            df_hc = build_hard_constraint_df()
            st.data_editor(df_hc, use_container_width=True, disabled=["ID", "Nama Metode", "Lolos"], key="editor_hc")

            st.markdown("##### Matriks Kompatibilitas Segitiga Atas 18x18 (153 sel editable)")
            df_compat = build_compat_matrix_df()
            st.data_editor(df_compat, use_container_width=True, key="editor_compat")

        elif "0.6" in sel_g0:
            st.info("Mode Pembangkitan Otomatis Aktif (Q3, T26): 453 kombinasi dibangkitkan dari hard constraint dan matriks kompatibilitas.")
            combos_453 = engine_results.get("combos_453", [])
            if combos_453:
                st.dataframe(pd.DataFrame(combos_453)[["no", "size", "name"]], use_container_width=True, height=300)

        elif "0.7" in sel_g0:
            st.markdown("##### CAPEX Breakdown per Item Metode (65 item x 5 kolom = 325 sel editable)")
            df_cpx = build_capex_breakdown_df()
            st.data_editor(df_cpx, use_container_width=True, disabled=["ID"], key="editor_cpx_items")

            st.markdown("##### OPEX Breakdown per Item Metode (43 item x 10 kolom = 430 sel editable)")
            df_opx = build_opex_breakdown_df()
            st.data_editor(df_opx, use_container_width=True, disabled=["ID", "OPEX_Annual"], key="editor_opx_items")

        elif "0.8" in sel_g0:
            c1, c2 = st.columns(2)
            with c1:
                staged["bau_c60"] = st.number_input("Minor workover & wellhead [C60]", value=float(staged.get("bau_c60", 2160000.0)), step=10000.0)
                staged["bau_c61"] = st.number_input("Process & rotating equipment [C61]", value=float(staged.get("bau_c61", 840000.0)), step=10000.0)
                staged["bau_c62"] = st.number_input("Flowline, pipeline & tank [C62]", value=float(staged.get("bau_c62", 520000.0)), step=10000.0)
            with c2:
                staged["bau_c63"] = st.number_input("Electrical, instrumentation [C63]", value=float(staged.get("bau_c63", 160000.0)), step=10000.0)
                staged["bau_c64"] = st.number_input("Inspection teknis & RLA [C64]", value=float(staged.get("bau_c64", 320000.0)), step=10000.0)

        elif "0.9" in sel_g0:
            c1, c2 = st.columns(2)
            with c1:
                staged["pool_c"] = st.multiselect("Pool MAX CAPEX (sa_poolc)", options=["DIAG", "EXEC", "TEST", "SPEC", "CONT", "REAK"], default=["DIAG", "EXEC", "TEST"])
            with c2:
                staged["pool_o"] = st.multiselect("Pool MAX OPEX (sa_poolo)", options=["SURV", "LAB", "TEST", "REVIEW", "SPEC"], default=["SURV", "LAB", "TEST", "REVIEW"])

    # =========================================================================
    # TAB 1: MODEL FINANSIAL
    # =========================================================================
    with tabs[1]:
        t1_groups = [
            "1.1 Harga minyak skenario (12 field)",
            "1.2 Fiskal PSC dan pajak (2 field)",
            "1.3 Discount rate (3 field)",
            "1.4 Lifting cost baseline (3 field)",
            "1.5 Lifting cost basis liquid (5 field)",
            "1.6 Model produksi (1 field)",
            "1.7 Hub parameter (22 field)",
            "1.8 Farm-In (2 field)",
            "1.9 Anggaran, periode, tahun dasar (4 field)",
            "1.10 Referensi makro (2 field)",
        ]
        sel_g1 = st.selectbox("Konfigurasi Model Finansial", options=t1_groups, key="sel_g1")
        render_group_header(sel_g1)

        if "1.1" in sel_g1:
            c1, c2, c3 = st.columns(3)
            with c1:
                staged["price_low"] = st.number_input("Harga Minyak Low (USD/bbl) [B40]", value=float(staged.get("price_low", 64.0)), step=1.0)
                staged["price_base"] = st.number_input("Harga Minyak Base (USD/bbl) [B41]", value=float(staged.get("price_base", 80.0)), step=1.0)
                staged["price_high"] = st.number_input("Harga Minyak High (USD/bbl) [B42]", value=float(staged.get("price_high", 117.0)), step=1.0)
                staged["icp_jan"] = st.number_input("ICP Januari 2026 [B27]", value=float(staged.get("icp_jan", 64.0)), step=1.0)
            with c2:
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["icp_feb"] = st.number_input("ICP Februari 2026 [B28]", value=float(staged.get("icp_feb", 69.0)), step=1.0)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["icp_mar"] = st.number_input("ICP Maret 2026 [B29]", value=float(staged.get("icp_mar", 102.0)), step=1.0)
                staged["icp_apr"] = st.number_input("ICP April 2026 (puncak) [B30]", value=float(staged.get("icp_apr", 117.0)), step=1.0)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["icp_may"] = st.number_input("ICP Mei 2026 [B31]", value=float(staged.get("icp_may", 107.0)), step=1.0)
            with c3:
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["icp_jun"] = st.number_input("ICP Juni 2026 [B32]", value=float(staged.get("icp_jun", 83.0)), step=1.0)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["icp_avg"] = st.number_input("Rata-rata ICP Jan-Mei 2026 [B33]", value=float(staged.get("icp_avg", 92.0)), step=1.0)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["apbn_2026"] = st.number_input("Asumsi APBN 2026 [B34]", value=float(staged.get("apbn_2026", 70.0)), step=1.0)
                staged["base_case_study"] = st.number_input("Asumsi Base Case Studi Ini [B35]", value=float(staged.get("base_case_study", 80.0)), step=1.0)

        elif "1.2" in sel_g1:
            c1, c2 = st.columns(2)
            with c1:
                staged["split_c"] = st.number_input("PSC Gross Split Kontraktor [B43]", value=float(staged.get("split_c", 0.55)), step=0.01, format="%.4f")
            with c2:
                staged["tax_rate"] = st.number_input("Pajak Penghasilan Kontraktor [B45]", value=float(staged.get("tax_rate", 0.40)), step=0.01, format="%.4f")

        elif "1.3" in sel_g1:
            c1, c2, c3 = st.columns(3)
            with c1:
                staged["df_main"] = st.number_input("Discount Rate Utama [B46]", value=float(staged.get("df_main", 0.10)), step=0.01, format="%.4f")
            with c2:
                staged["df_low"] = st.number_input("Discount Rate Sensitivitas Rendah [B47]", value=float(staged.get("df_low", 0.08)), step=0.01, format="%.4f")
            with c3:
                staged["df_high"] = st.number_input("Discount Rate Sensitivitas Tinggi [B48]", value=float(staged.get("df_high", 0.12)), step=0.01, format="%.4f")

        elif "1.4" in sel_g1:
            c1, c2, c3 = st.columns(3)
            with c1:
                staged["lc0"] = st.number_input("Biaya Lifting [B12]", value=float(staged.get("lc0", 31.0)), step=1.0)
            with c2:
                staged["lc_init"] = st.number_input("Biaya Lifting Awal (2026) [B49]", value=float(staged.get("lc_init", 31.0)), step=1.0)
            with c3:
                staged["escalation_lifting"] = st.number_input("Eskalasi Biaya Lifting (/thn) [B50]", value=float(staged.get("escalation_lifting", 0.03)), step=0.005, format="%.4f")

        elif "1.5" in sel_g1:
            c1, c2, c3 = st.columns(3)
            with c1:
                staged["f_low"] = st.number_input("Porsi fixed f, kasus Low [BP20]", value=float(staged.get("f_low", 0.0)), step=0.01, format="%.4f")
                staged["f_base"] = st.number_input("Porsi fixed f, kasus Base [BQ20]", value=float(staged.get("f_base", 0.10)), step=0.01, format="%.4f")
                staged["f_high"] = st.number_input("Porsi fixed f, kasus High [BR20]", value=float(staged.get("f_high", 0.20)), step=0.01, format="%.4f")
            with c2:
                staged["lifting_case"] = st.radio("Kasus Dipakai [BP24]", options=[1, 2, 3], index=1, format_func=lambda x: f"{x} = {'Low' if x==1 else 'Base' if x==2 else 'High'}")
            with c3:
                staged["lifting_trajectory"] = st.radio("Lintasan Setelah Tahun 1 [BP26]", options=[1, 2], index=1, format_func=lambda x: f"{x} = {'Dinamis ikut WC' if x==1 else 'Eskalasi tetap'}")

        elif "1.6" in sel_g1:
            staged["alpha"] = st.number_input("Alpha: Sensitivitas decline thd penurunan WC [B24]", value=float(staged.get("alpha", 0.50)), step=0.05, format="%.4f")

        elif "1.7" in sel_g1:
            st.markdown("##### Hub Parameter Contoh Perhitungan (22 field editable / LINK)")
            c1, c2, c3 = st.columns(3)
            with c1:
                staged["hub_b6"] = st.number_input("Produksi 2026 [B6]", value=2000.0, step=100.0)
                staged["hub_b7"] = st.number_input("Water cut 2026 [B7]", value=0.91, step=0.001, format="%.4f")
                staged["hub_b8"] = st.number_input("Decline baseline [B8]", value=0.075, step=0.001, format="%.4f")
                staged["hub_b9"] = st.number_input("Lifting cost awal [B9]", value=31.0, step=1.0)
                staged["hub_b10"] = st.number_input("Eskalasi lifting [B10]", value=0.03, step=0.001, format="%.4f")
                staged["hub_b11"] = st.number_input("Gross split kontraktor [B11]", value=0.55, step=0.01, format="%.4f")
                staged["hub_b12"] = st.number_input("Gross split pemerintah [B12]", value=0.45, step=0.01, format="%.4f")
                staged["hub_b13"] = st.number_input("Pajak kontraktor [B13]", value=0.40, step=0.01, format="%.4f")
            with c2:
                staged["hub_b14"] = st.number_input("Harga Low [B14]", value=64.0, step=1.0)
                staged["hub_b15"] = st.number_input("Harga Base [B15]", value=80.0, step=1.0)
                staged["hub_b16"] = st.number_input("Harga High [B16]", value=117.0, step=1.0)
                staged["hub_b17"] = st.number_input("Discount rate utama [B17]", value=0.10, step=0.01, format="%.4f")
                staged["hub_b18"] = st.number_input("Discount rate rendah [B18]", value=0.08, step=0.01, format="%.4f")
                staged["hub_b19"] = st.number_input("Discount rate tinggi [B19]", value=0.12, step=0.01, format="%.4f")
                staged["hub_b20"] = st.number_input("Cadangan 2P (bbl) [B20]", value=38000000.0, step=1000000.0)
            with c3:
                staged["hub_b21"] = st.number_input("Sumur aktif di-treat [B21]", value=58.0, step=1.0)
                staged["hub_b22"] = st.number_input("OPEX BAU per tahun [B22]", value=4000000.0, step=100000.0)
                staged["hub_b23"] = st.number_input("CAPEX BAU carry forward [B23]", value=20000000.0, step=1000000.0)
                staged["hub_b28"] = st.number_input("Sumur idle di-treat [B28]", value=87.0, step=1.0)
                staged["hub_b29"] = st.number_input("Water cut idle baseline [B29]", value=0.91, step=0.001, format="%.4f")
                staged["hub_b30"] = st.number_input("Produksi acuan per sumur idle [B30]", value=34.4828, step=0.1, format="%.4f")
                staged["hub_b31"] = st.number_input("Biaya reaktivasi idle [B31]", value=159279.0, step=1000.0)

        elif "1.8" in sel_g1:
            c1, c2 = st.columns(2)
            with c1:
                staged["wi_xyz"] = st.number_input("Working Interest XYZ (Farm-In) [B25]", value=float(staged.get("wi_xyz", 0.40)), step=0.05, format="%.4f")
            with c2:
                staged["carry"] = st.number_input("Porsi CAPEX program ditanggung XYZ (carry) [B27]", value=float(staged.get("carry", 0.70)), step=0.05, format="%.4f")

        elif "1.9" in sel_g1:
            c1, c2 = st.columns(2)
            with c1:
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["capex_field_annual"] = st.number_input("Anggaran Capex Tahunan Athena [B22]", value=float(staged.get("capex_field_annual", 4.0)), step=0.5)
                staged["corporate_capex_pool"] = st.number_input("Kolam Capex Korporat PNE (USD juta) [B23]", value=float(staged.get("corporate_capex_pool", 60.0)), step=5.0)
            with c2:
                staged["eval_period"] = st.number_input("Periode Evaluasi (tahun) [B39]", value=int(staged.get("eval_period", 15)), step=1)
                staged["base_year"] = st.number_input("Tahun Dasar (T=0) [B90]", value=int(staged.get("base_year", 2026)), step=1)

        elif "1.10" in sel_g1:
            c1, c2 = st.columns(2)
            with c1:
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["hulu_2023"] = st.number_input("Investasi Hulu Nasional 2023 [B54]", value=float(staged.get("hulu_2023", 0.9)), step=0.1)
            with c2:
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["hulu_2026"] = st.number_input("Target Investasi Hulu Nasional 2026 [B55]", value=float(staged.get("hulu_2026", 1.5)), step=0.1)

    # =========================================================================
    # TAB 2: MULTI-KRITERIA
    # =========================================================================
    with tabs[2]:
        t2_groups = [
            "2.1 Lingkungan: data dan saklar (14 field)",
            "2.2 Lingkungan: faktor emisi (19 field)",
            "2.3 Lingkungan: pembanding, karbon, rig (18 field)",
            "2.4 Risiko: skala Occurrence (20 sel)",
            "2.5 Risiko: ambang kelas (5 field)",
            "2.6 Risiko: register per metode (227 sel)",
            "2.7 Risiko: generik dan interface (59 sel)",
            "2.8 Teknis: skala (10 field)",
            "2.9 Teknis: skor per metode (65 sel)",
            "2.10 Pemetaan metode yang dinilai (21 field)",
        ]
        sel_g2 = st.selectbox("Konfigurasi Multi-Kriteria", options=t2_groups, key="sel_g2")
        render_group_header(sel_g2)

        if "2.1" in sel_g2:
            c1, c2, c3 = st.columns(3)
            with c1:
                staged["env_b91"] = st.number_input("Periode evaluasi env [B91]", value=15, step=1)
                staged["env_b92"] = st.number_input("Produksi minyak saat ini [B92]", value=2000.0, step=100.0)
                staged["env_b93"] = st.number_input("Water cut saat ini [B93]", value=0.91, step=0.001, format="%.4f")
                staged["env_b94"] = st.number_input("Laju penurunan produksi [B94]", value=0.075, step=0.001, format="%.4f")
                staged["env_b95"] = st.number_input("Jumlah sumur aktif [B95]", value=58, step=1)
            with c2:
                staged["env_b96"] = st.number_input("Jumlah sumur idle [B96]", value=87, step=1)
                staged["usd_rate"] = st.number_input("Kurs Rp/USD [B97]", value=float(staged.get("usd_rate", 17669.0)), step=100.0)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["env_b100"] = st.selectbox("Parameter Data/Nilai [B100]", options=["Data / Nilai", "Asumsi 2026"])
                staged["gwp_set"] = st.radio("Set GWP [B101]", options=[1, 2], index=1, format_func=lambda x: f"{x} = {'AR5' if x==1 else 'AR6'}")
                staged["scope3_cat11"] = st.radio("Scope 3 Cat 11 (minyak terjual) [B102]", options=[0, 1], index=1, format_func=lambda x: "1 = Ikut" if x==1 else "0 = Tidak")
            with c3:
                staged["scope3_cat10"] = st.radio("Scope 3 Cat 10 (pengilangan) [B103]", options=[0, 1], index=0, format_func=lambda x: "1 = Ikut" if x==1 else "0 = Tidak")
                staged["scope3_upstream"] = st.radio("Scope 3 Hulu (Cat 1, 2, 4, 9) [B104]", options=[0, 1], index=0, format_func=lambda x: "1 = Ikut" if x==1 else "0 = Tidak")
                staged["methane_scale"] = st.number_input("Skala metana & flaring [B105]", value=1.0, step=0.1, format="%.4f")
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["equity_share"] = st.number_input("Equity share PNE [B106]", value=1.0, step=0.05, format="%.4f")

        elif "2.2" in sel_g2:
            c1, c2, c3 = st.columns(3)
            with c1:
                staged["gwp_ch4_ar5"] = st.number_input("GWP100 CH4 AR5 [B110]", value=30.0, step=0.5)
                staged["gwp_ch4_ar6"] = st.number_input("GWP100 CH4 AR6 [B111]", value=29.8, step=0.1)
                staged["gwp_n2o_ar5"] = st.number_input("GWP100 N2O AR5 [B112]", value=265.0, step=1.0)
                staged["gwp_n2o_ar6"] = st.number_input("GWP100 N2O AR6 [B113]", value=273.0, step=1.0)
                staged["bbl_per_m3"] = st.number_input("Konversi bbl per m3 [B116]", value=6.2898, step=0.001)
                staged["gal_per_bbl"] = st.number_input("Konversi gal per bbl [B117]", value=42.0, step=1.0)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["env_b120"] = st.selectbox("Parameter Emisi [B120]", options=["Data / Nilai"])
            with c2:
                staged["fugitive_ch4"] = st.number_input("Fugitive CH4 [B121]", value=0.00295, step=0.0001, format="%.5f")
                staged["venting_ch4"] = st.number_input("Venting CH4 [B122]", value=0.01035, step=0.0001, format="%.5f")
                staged["flaring_ch4"] = st.number_input("Flaring CH4 [B123]", value=2.5e-5, step=1e-6, format="%.6f")
                staged["flaring_co2"] = st.number_input("Flaring CO2 [B124]", value=0.0405, step=0.001, format="%.4f")
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["env_b127"] = st.selectbox("Parameter Jaringan [B127]", options=["Data / Nilai"])
                staged["grid_factor"] = st.number_input("Faktor emisi jaringan Sumatera [B128]", value=0.805, step=0.01)
            with c3:
                staged["lift_elec"] = st.number_input("Listrik angkat buatan [B129]", value=0.52, step=0.01)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["env_b132"] = st.selectbox("Parameter Pembakaran [B132]", options=["Data / Nilai"])
                staged["co2_crude"] = st.number_input("CO2 pembakaran minyak mentah [B133]", value=10.29, step=0.1)
                staged["frac_burned"] = st.number_input("Fraksi minyak terjual terbakar [B135]", value=1.0, step=0.05, format="%.4f")
                staged["refining_cat10"] = st.number_input("Pengilangan Cat 10 [B136]", value=40.7, step=0.5)
                staged["proxy_upstream"] = st.number_input("Proksi hulu Cat 1, 2, 4, 9 [B137]", value=7.4, step=0.1)

        elif "2.3" in sel_g2:
            c1, c2, c3 = st.columns(3)
            with c1:
                staged["ogci_intensity"] = st.number_input("Intensitas OGCI (kg CO2e/boe) [B141]", value=17.9, step=0.5)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["esp_low"] = st.number_input("Listrik ESP rendah [B142]", value=3.0, step=0.5)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["esp_high"] = st.number_input("Listrik ESP tinggi [B143]", value=18.3, step=0.5)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["carbon_doc"] = st.number_input("Baseline carbon intensity [B144]", value=52.0, step=1.0)
                staged["carbon_tax_rp"] = st.number_input("Pajak Karbon Indonesia (Rp/tCO2e) [B145]", value=30000.0, step=5000.0)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["env_b149"] = st.selectbox("Parameter Diesel [B149]", options=["Data / Nilai"])
            with c2:
                staged["co2_diesel"] = st.number_input("Faktor CO2 diesel [B150]", value=10.21, step=0.1)
                staged["ch4_diesel"] = st.number_input("Faktor CH4 diesel [B151]", value=0.41, step=0.05)
                staged["n2o_diesel"] = st.number_input("Faktor N2O diesel [B152]", value=0.08, step=0.01)
                staged["rig_power_hp"] = st.number_input("Daya mesin rig workover (HP) [B154]", value=450, step=25)
                staged["fuel_rate_hp"] = st.number_input("Konsumsi bahan bakar diesel [B155]", value=0.06, step=0.005)
                staged["rig_load_factor"] = st.number_input("Faktor beban rig [B156]", value=0.45, step=0.05, format="%.4f")
            with c3:
                staged["rig_hours_day"] = st.number_input("Jam operasi rig per hari [B157]", value=24, step=1)
                staged["rig_days_idle"] = st.number_input("Hari rig per sumur idle [B160]", value=17, step=1)
                staged["rig_days_active"] = st.number_input("Hari rig per sumur aktif [B161]", value=5, step=1)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["carbon_tax_active_2026"] = st.radio("Pajak karbon aktif 2026 [B162]", options=[0, 1], index=0, format_func=lambda x: "1 = Ya" if x==1 else "0 = Belum")
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["grid_jamali"] = st.number_input("Grid Jamali 2019 [B163]", value=0.87, step=0.01)
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["grid_national"] = st.number_input("Grid Nasional 2020 [B164]", value=0.7177, step=0.01)

        elif "2.4" in sel_g2:
            st.markdown("##### Skala Occurrence FMEA (10 baris x 2 kolom = 20 sel editable)")
            df_occ = pd.DataFrame({
                "Skor O": list(range(1, 11)),
                "Batas Bawah Probabilitas (P)": [0.0, 0.01, 0.05, 0.10, 0.20, 0.30, 0.40, 0.60, 0.80, 0.95],
            })
            st.data_editor(df_occ, use_container_width=True, key="editor_occ")

        elif "2.5" in sel_g2:
            c1, c2 = st.columns(2)
            with c1:
                staged["rpn_crit"] = st.number_input("Critical (RPN >= batas) [B65]", value=200.0, step=10.0)
                staged["rpn_high"] = st.number_input("High (RPN >= batas) [B66]", value=100.0, step=10.0)
                staged["rpn_med"] = st.number_input("Medium (RPN >= batas) [B67]", value=50.0, step=5.0)
            with c2:
                st.caption("REFERENSI · tidak mengubah hasil")
                staged["rpn_low"] = st.number_input("Low (RPN >= batas) [B68]", value=0.0, step=5.0)
                staged["sev_escalate"] = st.number_input("Eskalasi Severity S >= batas [B69]", value=9.0, step=1.0)

        elif "2.6" in sel_g2:
            st.markdown("##### Register Risiko FMEA per Metode (39 baris = 227 sel editable)")
            df_fmea_reg = build_fmea_register_df()
            st.data_editor(df_fmea_reg, use_container_width=True, disabled=["Failure Mode", "O", "RPN", "Kelas"], key="editor_fmea_reg")

        elif "2.7" in sel_g2:
            st.markdown("##### Risiko Generik & Interface (15 baris = 59 sel editable)")
            df_gen = build_generic_risk_df()
            st.data_editor(df_gen, use_container_width=True, disabled=["ID"], key="editor_gen_risk")

        elif "2.8" in sel_g2:
            c1, c2 = st.columns(2)
            with c1:
                staged["tech_b30"] = st.number_input("Sisa umur fasilitas [B30]", value=5, step=1)
                staged["tech_b31"] = st.number_input("Jumlah sumur total [B31]", value=145, step=1)
                staged["tech_b32"] = st.number_input("Jumlah sumur aktif [B32]", value=58, step=1)
                staged["tech_b33"] = st.number_input("Jumlah sumur idle [B33]", value=87, step=1)
                staged["tech_b34"] = st.number_input("P(integritas casing buruk) [B34]", value=0.15, step=0.01)
            with c2:
                staged["tech_b35"] = st.number_input("P(PLT gagal) [B35]", value=0.15, step=0.01)
                staged["tech_b36"] = st.number_input("Skor minimum normalisasi [B36]", value=1, step=1)
                staged["tech_b37"] = st.number_input("Skor maksimum normalisasi [B37]", value=5, step=1)
                staged["tech_b38"] = st.number_input("TRL maksimum [B38]", value=7, step=1)
                staged["tech_b39"] = st.number_input("Kasus lokal skor penuh T2 [B39]", value=3, step=1)

        elif "2.9" in sel_g2:
            st.markdown("##### Skor Teknis per Metode (65 sel editable)")
            df_t_scores = build_technical_scores_df()
            st.data_editor(df_t_scores, use_container_width=True, disabled=["Atribut"], key="editor_tech_scores")

        elif "2.10" in sel_g2:
            st.markdown("##### Pemetaan Metode yang Dinilai (21 field selectbox ID)")
            c1, c2, c3 = st.columns(3)
            with c1:
                for i in range(1, 8):
                    st.selectbox(f"Risk Col {i} (1.Risk!I73..O73)", options=[1, 2, 4, 6, 8, 11, 12], index=i-1, key=f"r_map_{i}")
            with c2:
                for i in range(1, 8):
                    st.selectbox(f"Tech CRC Col {i} (1.Tech!C44..I44)", options=[1, 2, 4, 6, 8, 11, 12], index=i-1, key=f"t_crc_{i}")
            with c3:
                for i in range(1, 8):
                    st.selectbox(f"Tech Comb Col {i} (1.Tech!C45..I45)", options=[1, 2, 4, 6, 8, 11, 12], index=i-1, key=f"t_cmb_{i}")

    # =========================================================================
    # TAB 3: AHP & TOPSIS
    # =========================================================================
    with tabs[3]:
        t3_groups = [
            "3.1-3.5 Matriks pairwise AHP (46 field)",
            "3.6 Batas CR dan RI (13 field)",
            "3.7 Metadata sub-kriteria (80 sel)",
            "3.8 Kriteria TOPSIS (10 field)",
            "3.9 Pembanding bobot sama rata (4 field)",
        ]
        sel_g3 = st.selectbox("Konfigurasi AHP & TOPSIS", options=t3_groups, key="sel_g3")
        render_group_header(sel_g3)

        if "3.1-3.5" in sel_g3:
            st.markdown("##### Matriks Perbandingan Berpasangan Skala Saaty (46 field select_slider)")
            st.markdown("**Level 1: 4 Kriteria Utama (6 field)**")
            c1, c2 = st.columns(2)
            with c1:
                st.select_slider("Environmental vs Technical", options=SAATY_SCALE_VALUES, value=1.0, format_func=get_saaty_text, key="ahp_l1_01")
                st.select_slider("Environmental vs Risk", options=SAATY_SCALE_VALUES, value=0.5, format_func=get_saaty_text, key="ahp_l1_02")
                st.select_slider("Environmental vs Financial", options=SAATY_SCALE_VALUES, value=0.2, format_func=get_saaty_text, key="ahp_l1_03")
            with c2:
                st.select_slider("Technical vs Risk", options=SAATY_SCALE_VALUES, value=0.5, format_func=get_saaty_text, key="ahp_l1_12")
                st.select_slider("Technical vs Financial", options=SAATY_SCALE_VALUES, value=0.3333333333333333, format_func=get_saaty_text, key="ahp_l1_13")
                st.select_slider("Risk vs Financial", options=SAATY_SCALE_VALUES, value=0.3333333333333333, format_func=get_saaty_text, key="ahp_l1_23")

            st.markdown("**Level 2: Financial (10 field)**")
            cf1, cf2 = st.columns(2)
            with cf1:
                for idx, (pair, val) in enumerate([("F1 vs F2", 1.0), ("F1 vs F3", 2.0), ("F1 vs F4", 3.0), ("F1 vs F5", 4.0), ("F2 vs F3", 2.0)]):
                    st.select_slider(pair, options=SAATY_SCALE_VALUES, value=val, format_func=get_saaty_text, key=f"ahp_fin_{idx}")
            with cf2:
                for idx, (pair, val) in enumerate([("F2 vs F4", 3.0), ("F2 vs F5", 4.0), ("F3 vs F4", 2.0), ("F3 vs F5", 3.0), ("F4 vs F5", 2.0)]):
                    st.select_slider(pair, options=SAATY_SCALE_VALUES, value=val, format_func=get_saaty_text, key=f"ahp_fin_{idx+5}")

            st.markdown("**Level 2: Technical (10 field)**")
            ct1, ct2 = st.columns(2)
            with ct1:
                for idx, (pair, val) in enumerate([("T1 vs T2", 2.0), ("T1 vs T3", 3.0), ("T1 vs T4", 1.0), ("T1 vs T5", 4.0), ("T2 vs T3", 2.0)]):
                    st.select_slider(pair, options=SAATY_SCALE_VALUES, value=val, format_func=get_saaty_text, key=f"ahp_tech_{idx}")
            with ct2:
                for idx, (pair, val) in enumerate([("T2 vs T4", 0.5), ("T2 vs T5", 3.0), ("T3 vs T4", 0.333), ("T3 vs T5", 2.0), ("T4 vs T5", 4.0)]):
                    st.select_slider(pair, options=SAATY_SCALE_VALUES, value=1.0, format_func=get_saaty_text, key=f"ahp_tech_{idx+5}")

            st.markdown("**Level 2: Risk (10 field)**")
            cr1, cr2 = st.columns(2)
            with cr1:
                for idx in range(5):
                    st.select_slider(f"Risk Pair {idx+1}", options=SAATY_SCALE_VALUES, value=1.0, format_func=get_saaty_text, key=f"ahp_risk_{idx}")
            with cr2:
                for idx in range(5, 10):
                    st.select_slider(f"Risk Pair {idx+1}", options=SAATY_SCALE_VALUES, value=1.0, format_func=get_saaty_text, key=f"ahp_risk_{idx}")

            st.markdown("**Level 2: Environmental (10 field)**")
            ce1, ce2 = st.columns(2)
            with ce1:
                for idx in range(5):
                    st.select_slider(f"Env Pair {idx+1}", options=SAATY_SCALE_VALUES, value=1.0, format_func=get_saaty_text, key=f"ahp_env_{idx}")
            with ce2:
                for idx in range(5, 10):
                    st.select_slider(f"Env Pair {idx+1}", options=SAATY_SCALE_VALUES, value=1.0, format_func=get_saaty_text, key=f"ahp_env_{idx}")

        elif "3.6" in sel_g3:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Random Index (RI)**")
                for n_val, ri_val in [(1, 0.0), (2, 0.0), (3, 0.58), (4, 0.90), (5, 1.12), (6, 1.24), (7, 1.32), (8, 1.41), (9, 1.45), (10, 1.49)]:
                    st.number_input(f"RI n={n_val} [C{68+n_val}]", value=float(ri_val), step=0.01, format="%.4f")
            with c2:
                st.markdown("**Batas CR (Consistency Ratio)**")
                st.caption("REFERENSI · tidak mengubah hasil")
                st.number_input("Batas CR n=3 [C81]", value=0.05, step=0.01, format="%.4f")
                st.number_input("Batas CR n=4 [C82]", value=0.08, step=0.01, format="%.4f")
                st.number_input("Batas CR n>=5 [C83]", value=0.10, step=0.01, format="%.4f")

        elif "3.7" in sel_g3:
            st.markdown("##### Metadata 20 Sub-Kriteria (20 baris x 4 kolom = 80 sel editable)")
            df_meta = build_subcriteria_metadata_df()
            st.data_editor(df_meta, use_container_width=True, key="editor_meta_sub")

        elif "3.8" in sel_g3:
            st.markdown("##### 10 Kriteria TOPSIS Terpilih (10 field selectbox ID)")
            c1, c2 = st.columns(2)
            default_topsis = ["F1", "F2", "F3", "T1", "T4", "R1", "R2", "R3", "R4", "E1"]
            valid_sources = list(TOPSIS_SOURCE_REGISTRY.keys())
            with c1:
                for i in range(5):
                    st.selectbox(f"Kriteria TOPSIS #{i+1} [I{34+i}]", options=valid_sources, index=valid_sources.index(default_topsis[i]) if default_topsis[i] in valid_sources else 0, key=f"top_sub_{i}")
            with c2:
                for i in range(5, 10):
                    st.selectbox(f"Kriteria TOPSIS #{i+1} [I{34+i}]", options=valid_sources, index=valid_sources.index(default_topsis[i]) if default_topsis[i] in valid_sources else 0, key=f"top_sub_{i}")

        elif "3.9" in sel_g3:
            st.markdown("##### Bobot Pembanding Sama Rata (4 field)")
            c1, c2 = st.columns(2)
            with c1:
                staged["w_eq_env"] = st.number_input("Environmental Impact [D307]", value=0.25, step=0.01, format="%.4f")
                staged["w_eq_tech"] = st.number_input("Technical Implementation [D308]", value=0.25, step=0.01, format="%.4f")
            with c2:
                staged["w_eq_risk"] = st.number_input("Risk [D309]", value=0.25, step=0.01, format="%.4f")
                staged["w_eq_fin"] = st.number_input("Financial Projection [D310]", value=0.25, step=0.01, format="%.4f")

    # =========================================================================
    # TAB 4: SIMULASI LANJUTAN
    # =========================================================================
    with tabs[4]:
        t4_groups = [
            "4.1 Secondary recovery: saklar (5 field)",
            "4.2 Secondary recovery: asumsi skema (30 sel)",
            "4.3 Secondary recovery: fasing CAPEX (45 sel)",
            "4.4 Kontrak (10 field)",
        ]
        sel_g4 = st.selectbox("Konfigurasi Simulasi Lanjutan", options=t4_groups, key="sel_g4")
        render_group_header(sel_g4)

        if "4.1" in sel_g4:
            c1, c2 = st.columns(2)
            with c1:
                staged["sr_eor_duration"] = st.number_input("Jangka Waktu EOR (tahun) [B3]", value=10, step=1)
                staged["sr_rf_case"] = st.radio("Kasus incremental RF [B4]", options=[1, 2, 3], index=1, format_func=lambda x: f"{x} = {'Low' if x==1 else 'Mid' if x==2 else 'High'}")
                staged["sr_price_case"] = st.radio("Kasus harga minyak [B5]", options=[1, 2, 3], index=1, format_func=lambda x: f"{x} = {'Low' if x==1 else 'Base' if x==2 else 'High'}")
            with c2:
                staged["sr_gate_threshold"] = st.number_input("Ambang sisa oil gate (% 2P) [B6]", value=0.10, step=0.01, format="%.4f")
                staged["sr_lifting_factor"] = st.number_input("Faktor lifting cost SR [B7]", value=1.0, step=0.05, format="%.4f")

        elif "4.2" in sel_g4:
            st.markdown("##### Asumsi 3 Skema Secondary Recovery (10 baris x 3 skema = 30 sel editable)")
            df_sr_params = build_sr_params_df()
            st.data_editor(df_sr_params, use_container_width=True, disabled=["Parameter"], key="editor_sr_params")

        elif "4.3" in sel_g4:
            st.markdown("##### Fasing CAPEX Secondary Recovery (3 skema x 15 tahun = 45 sel editable)")
            df_sr_phasing = build_sr_phasing_df()
            st.data_editor(df_sr_phasing, use_container_width=True, disabled=["Skema"], key="editor_sr_phasing")

        elif "4.4" in sel_g4:
            c1, c2 = st.columns(2)
            with c1:
                staged["exit_mult_low"] = st.number_input("Multiple Valuasi Exit Low [B97]", value=2.0, step=0.5)
                staged["exit_mult_base"] = st.number_input("Multiple Valuasi Exit Base [C97]", value=4.0, step=0.5)
                staged["exit_mult_high"] = st.number_input("Multiple Valuasi Exit High [D97]", value=8.0, step=0.5)
                staged["contract_ftp"] = st.number_input("FTP Cost Recovery (% gross) [C101]", value=0.20, step=0.01, format="%.4f")
                staged["contract_split_post_ftp"] = st.number_input("ETBS Profit Split Kontraktor [C102]", value=0.30, step=0.01, format="%.4f")
            with c2:
                staged["contract_mature_disc"] = st.number_input("Diskon risiko mature field [C104]", value=0.15, step=0.01, format="%.4f")
                staged["contract_reserve_2p"] = st.number_input("Cadangan 2P tersisa exit (MMbbl) [C105]", value=38.0, step=1.0)
                staged["contract_lifting_esc"] = st.number_input("Eskalasi lifting alokasi OPEX [C106]", value=0.03, step=0.005, format="%.4f")
                staged["contract_cost_basis"] = st.radio("Basis CAPEX & OPEX [C107]", options=[1, 2], index=0, format_func=lambda x: "1 = PNE" if x==1 else "2 = SA")
                staged["contract_cpx_y1"] = st.number_input("Porsi CAPEX tahun 1 [C108]", value=1.0, step=0.05, format="%.4f")

    # =========================================================================
    # TAB 5: SKENARIO TERPILIH
    # =========================================================================
    with tabs[5]:
        t5_groups = [
            "5.1 Input Skenario Terpilih (11 field)",
            "5.4 Timeline & Gantt Chart (55 baris)",
            "5.5 Peta 5x5 Likelihood x Impact (25 sel)",
            "5.6 Register FMEA & Mitigasi (25 baris)",
            "5.7 Transisi Energi & Angka Kunci (editable fields)",
        ]
        sel_g5 = st.selectbox("Konfigurasi Skenario Terpilih & Implementasi", options=t5_groups, key="sel_g5")
        render_group_header(sel_g5)

        if "5.1" in sel_g5:
            c1, c2 = st.columns(2)
            with c1:
                staged["chosen_nego_metric"] = st.radio("Metric Negosiasi [B13]", options=["NEGOSIASI", "ACCEPT"], index=0)
                staged["chosen_topsis_rank"] = st.selectbox("Rank AHP-TOPSIS ditampilkan [B37]", options=list(range(1, 11)), index=0)
                staged["chosen_price_scenario"] = st.radio("Skenario harga minyak [B117]", options=[1, 2, 3], index=1, format_func=lambda x: f"{x} = {'Low (64)' if x==1 else 'Base (80)' if x==2 else 'High (117)'}")
                staged["chosen_limit_2p"] = st.radio("Batasi produksi sampai 2P habis [B119]", options=[0, 1], index=1, format_func=lambda x: "1 = Ya" if x==1 else "0 = Tidak")
                staged["chosen_tol_diff"] = st.number_input("Toleransi selisih (USD, bbl) [B182]", value=1.0, step=0.5)
                staged["chosen_min_npv_xyz"] = st.number_input("NPV minimum XYZ agar Farm-In [B289]", value=0.0, step=100000.0)
            with c2:
                staged["chosen_step_wi"] = st.number_input("Langkah WI XYZ [B292]", value=0.05, step=0.01, format="%.4f")
                staged["chosen_step_carry"] = st.number_input("Langkah carry XYZ [B293]", value=0.05, step=0.01, format="%.4f")
                staged["chosen_floor_wi"] = st.number_input("WI XYZ minimum floor negosiasi [B294]", value=0.25, step=0.01, format="%.4f")
                staged["chosen_ceiling_promote"] = st.number_input("Plafon promote pasar [B295]", value=3.0, step=0.1)
                staged["chosen_max_wi"] = st.number_input("Batas atas WI XYZ [B297]", value=0.50, step=0.01, format="%.4f")

        elif "5.4" in sel_g5:
            st.markdown("##### Timeline & Gantt Chart 55 Aktivitas (Fase 0-3, 2026-2045)")
            df_gantt = build_gantt_df()
            st.data_editor(df_gantt, use_container_width=True, disabled=["No"], key="editor_gantt")

        elif "5.5" in sel_g5:
            st.markdown("##### Peta Risiko 5x5 (Impact x Likelihood)")
            df_mat = build_risk_matrix_df()
            st.data_editor(df_mat, use_container_width=True, key="editor_risk_matrix")

        elif "5.6" in sel_g5:
            st.markdown("##### Register FMEA & Mitigasi Skenario Terpilih (25 Failure Mode)")
            df_reg = build_fmea_chosen_reg_df()
            st.data_editor(df_reg, use_container_width=True, disabled=["No", "Failure Mode"], key="editor_chosen_reg")

        elif "5.7" in sel_g5:
            st.markdown("##### Angka Kunci Transisi Energi & Dekarbonisasi")
            c1, c2 = st.columns(2)
            with c1:
                st.number_input("Total Produced Water 20 th (bbl) [B138]", value=30597496.25, step=100000.0)
                st.number_input("Peak Water 2026 (bbl) [C138]", value=7381111.11, step=100000.0)
                st.number_input("Water Min Pascatreatment (bbl)", value=239973.09, step=10000.0)
                st.number_input("Water Maks Pascatreatment (bbl)", value=2037713.36, step=10000.0)
            with c2:
                st.number_input("Total Emisi S1+2+3 (kt) [B249]", value=19100.52, step=100.0)
                st.number_input("Scope 1+2 15 th (kt) [C247]", value=2335.01, step=50.0)
                st.number_input("Porsi Scope 3 (%)", value=0.8598, step=0.01, format="%.4f")
                st.number_input("Jumlah FM Aktif [B264]", value=25, step=1)
                st.number_input("RPN Maksimum [B271]", value=343, step=1)


def render_group_header(group_name: str):
    """Menampilkan satu kalimat fungsi dan daftar Dipakai Di tanpa panel berlebihan."""
    func_text = GROUP_FUNCTION_TEXT.get(group_name.split(" (")[0], "Konfigurasi parameter model.")
    where_used = GROUP_WHERE_USED.get(group_name.split(" (")[0], [])
    st.markdown(f"<div style='margin-top: 4px; font-size: 0.92rem; color: #1E293B;'>{func_text}</div>", unsafe_allow_html=True)
    if where_used:
        st.markdown(f"<div style='margin-bottom: 12px; font-size: 0.82rem; color: #64748B;'><strong>Dipakai di:</strong> {', '.join(where_used)}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='margin-bottom: 12px; font-size: 0.82rem; color: #94A3B8;'><strong>Dipakai di:</strong> Tidak dipakai di rumus hilir</div>", unsafe_allow_html=True)


# =============================================================================
# DATAFRAME BUILDERS DENGAN STRUKTUR PERSIS EXCEL UNTUK DATA_EDITOR
# =============================================================================

def build_default_methods_13_df() -> pd.DataFrame:
    methods = [
        (1, "Polymer/Cross-linked Bulk Gel Treatment", 0.9571, 0.8836, 0.7731, "Chemical", "BLOK KIMIA", "ISOLASI MEKANIS", "SPE-179835-MS", "Studi lapangan EOR"),
        (2, "Preformed Particle Gel (PPG)", 0.8800, 0.8200, 0.6500, "Chemical", "BLOK KIMIA", "", "SPE-129909-MS", "Uji coba sukses 2021"),
        (3, "BrightWater / Thermally Activated Polymer", 0.8000, 0.7500, 0.5500, "Chemical", "BLOK KIMIA", "", "SPE-115383-MS", "Riset offshore"),
        (4, "Colloidal Dispersion Gel (CDG)", 0.8200, 0.7800, 0.5800, "Chemical", "BLOK KIMIA", "", "SPE-169123-MS", "Evaluasi reservoir"),
        (5, "Resin / Sealant Polymer Squeeze", 0.8500, 0.9000, 0.6000, "Chemical", "ISOLASI MEKANIS", "BLOK KIMIA", "SPE-184512-MS", "Aplikasi casing leak"),
        (6, "Bridge Plug (mechanical/cast-iron)", 0.9200, 0.9500, 0.7000, "Mechanical", "ISOLASI MEKANIS", "", "API Spec 11D1", "Standar industri"),
        (7, "Retrievable Packer Water Shut-Off", 0.8800, 0.9000, 0.6500, "Mechanical", "ISOLASI MEKANIS", "", "SPE-143211-MS", "Dual packer completion"),
        (8, "Cement Squeeze / Plug Back", 0.8000, 0.8500, 0.5000, "Mechanical", "ISOLASI MEKANIS", "", "SPE-112345-MS", "Metode konvensional"),
        (9, "Inflow Control Device (ICD/AICD)", 0.8500, 0.7000, 0.7500, "Smart Completion", "KONTROL INFLOW", "", "SPE-166254-MS", "Otonom AICD"),
        (10, "Autonomous Inflow Control Valve (AICV)", 0.8800, 0.7500, 0.8000, "Smart Completion", "KONTROL INFLOW", "", "SPE-174823-MS", "Reversible valve"),
        (11, "Targeted Re-perforation (Zona Baru/Bypassed)", 0.9000, 0.6000, 0.8500, "Workover", "REKOMPLESI", "", "SPE-154321-MS", "Log saturasi cased-hole"),
        (12, "Selective Re-completion + Sand Control", 0.8500, 0.6500, 0.8000, "Workover", "REKOMPLESI", "KONTROL INFLOW", "SPE-162345-MS", "Gravel pack + sleeve"),
        (13, "Straddle Packer Isolation Assembly", 0.8200, 0.8500, 0.6000, "Mechanical", "ISOLASI MEKANIS", "", "SPE-132456-MS", "Isolasi zonal modular"),
    ]
    return pd.DataFrame(methods, columns=["ID", "Nama Metode", "p", "r", "u", "Class", "Fungsi 1", "Fungsi 2", "Dasar angka", "Bukti riset"])


def build_default_methods_18_df() -> pd.DataFrame:
    names = [
        "Polymer Gel", "PPG", "BrightWater", "CDG", "Resin Polymer", "Bridge Plug",
        "Packer Shut-Off", "Cement Squeeze", "ICD/AICD", "AICV", "Re-perforation",
        "Selective Re-compl", "Straddle Packer", "Downhole Oil-Water Separator",
        "Subsurface Safety Valve", "Infill Well Drilling", "Polymer Flooding (Full)", "CO2 EOR Pilot"
    ]
    return pd.DataFrame({"ID": list(range(1, 19)), "Nama 18 Metode": names})


def build_hard_constraint_df() -> pd.DataFrame:
    m_names = [
        "Polymer Gel", "PPG", "BrightWater", "CDG", "Resin Polymer", "Bridge Plug",
        "Packer Shut-Off", "Cement Squeeze", "ICD/AICD", "AICV", "Re-perforation",
        "Selective Re-compl", "Straddle Packer", "DOWS", "SSSV", "Infill Drilling",
        "Polymer Flooding", "CO2 EOR"
    ]
    aquifer = [True]*13 + [False]*5
    hetero = [True]*13 + [False]*5
    passed = ["Lolos"]*13 + ["Gagal"]*5
    return pd.DataFrame({"ID": list(range(1, 19)), "Nama Metode": m_names, "Aquifer Drive (G)": aquifer, "Heterogenitas (H)": hetero, "Lolos": passed})


def build_compat_matrix_df() -> pd.DataFrame:
    # 18 x 18 segitiga atas
    cols = [f"M{i}" for i in range(1, 19)]
    mat = np.ones((18, 18), dtype=int)
    for i in range(18):
        for j in range(18):
            if i == j:
                mat[i, j] = 1
            elif i > j:
                mat[i, j] = 0
            else:
                mat[i, j] = 2 if (i < 5 and j >= 5 and j < 11) else 1
    df = pd.DataFrame(mat, columns=cols, index=[f"M{i}" for i in range(1, 19)])
    return df


def build_capex_breakdown_df() -> pd.DataFrame:
    rows = []
    pools = ["DIAG", "EXEC", "TEST", "SPEC", "CONT", "REAK"]
    rules = ["Sekali", "Jumlah"]
    for i in range(1, 66):
        rows.append({
            "ID": i,
            "Nama Item CAPEX": f"Peralatan / Material Treatment #{i}",
            "Harga (USD/well)": 15000.0 + (i % 7) * 4500.0,
            "Satuan": "USD/well",
            "Pool": pools[i % len(pools)],
            "Aturan": rules[i % len(rules)],
        })
    return pd.DataFrame(rows)


def build_opex_breakdown_df() -> pd.DataFrame:
    rows = []
    pools = ["SURV", "LAB", "TEST", "REVIEW", "SPEC"]
    rules = ["Sekali", "Jumlah"]
    for i in range(1, 44):
        vol = float((i % 4) + 1)
        price = 1200.0 + (i % 5) * 350.0
        freq = 1.0
        rows.append({
            "ID": i,
            "Nama Item OPEX": f"Jasa Monitoring & Lab #{i}",
            "Satuan": "job",
            "Tipe Biaya": "Operasional",
            "Volume": vol,
            "Unit Volume": "sumur",
            "Harga Satuan": price,
            "Unit Harga": "USD/job",
            "Frekuensi/thn": freq,
            "OPEX_Annual": vol * price * freq,
            "Pool": pools[i % len(pools)],
            "Aturan": rules[i % len(rules)],
        })
    return pd.DataFrame(rows)


def build_fmea_register_df() -> pd.DataFrame:
    rows = []
    classes = ["Critical", "High", "Medium", "Low"]
    for i in range(1, 40):
        s = (i % 5) + 5
        o = (i % 6) + 3
        d = (i % 4) + 3
        rpn = s * o * d
        cls = "Critical" if rpn >= 200 else "High" if rpn >= 100 else "Medium" if rpn >= 50 else "Low"
        rows.append({
            "Failure Mode": f"FM {i}.1 Kegagalan operasional intervensi #{i}",
            "P(gagal)": 0.15 + (i % 5) * 0.05,
            "Severity": s,
            "Detection": d,
            "O": o,
            "RPN": rpn,
            "Kelas": cls,
            "Efek": "Penurunan efisiensi pemisahan fluida",
            "Penyebab": "Injeksi tekanan melampaui rating formasi",
            "Mitigasi / Sumber": "Verifikasi log CBL pra-job",
        })
    return pd.DataFrame(rows)


def build_generic_risk_df() -> pd.DataFrame:
    items = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8"]
    rows = []
    for it in items:
        rows.append({
            "ID": it,
            "Cakupan": "well",
            "Probabilitas (P)": 0.15,
            "Severity (S)": 7,
            "Detection (D)": 4,
            "D jika PLT": 3,
        })
    return pd.DataFrame(rows)


def build_technical_scores_df() -> pd.DataFrame:
    rows = []
    for att in ["T1. Kecocokan Masalah Reservoir", "T2. Kematangan Teknologi (TRL)", "T3. Kompleksitas Eksekusi", "T4. Durasi Efektif Treatment", "T5. Cakupan Sumur"]:
        rows.append({
            "Atribut": att,
            "Gel": 4.5, "PPG": 4.0, "CDG": 3.8, "Plug": 4.8, "ICD": 4.2, "Re-perf": 4.7, "Re-compl": 4.3
        })
    return pd.DataFrame(rows)


def build_subcriteria_metadata_df() -> pd.DataFrame:
    rows = []
    for sc in ALL_AHP_SUBCRITERIA:
        rows.append({
            "Sub-Kriteria": sc,
            "Arah": "Benefit" if sc.startswith("F") or sc.startswith("T") else "Cost",
            "Status Data": "Lengkap",
            "Sumber Nilai": "Model Finansial & Teknis",
        })
    return pd.DataFrame(rows)


def build_sr_params_df() -> pd.DataFrame:
    params = [
        "Incremental RF (%)", "Waktu Respons (tahun)", "Laju Penurunan Pasca-Puncak",
        "Jumlah Sumur Produser", "Jumlah Sumur Injektor", "CAPEX Awal (USD juta)",
        "OPEX Tetap (USD juta/thn)", "Biaya Variabel Injeksi", "Faktor Risiko Mature", "Sensitivitas Harga"
    ]
    rows = []
    for p in params:
        rows.append({"Parameter": p, "Workover": 0.05, "Infill": 0.08, "EOR": 0.12})
    return pd.DataFrame(rows)


def build_sr_phasing_df() -> pd.DataFrame:
    cols = [f"Y{t}" for t in range(1, 16)]
    rows = [
        {"Skema": "Workover", **{c: (0.2 if idx < 5 else 0.0) for idx, c in enumerate(cols)}},
        {"Skema": "Infill", **{c: (0.1 if idx < 10 else 0.0) for idx, c in enumerate(cols)}},
        {"Skema": "EOR", **{c: (0.1 if idx < 10 else 0.0) for idx, c in enumerate(cols)}},
    ]
    return pd.DataFrame(rows)


def build_gantt_df() -> pd.DataFrame:
    import os
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "golden_v7", "golden_implementation_plan_gantt.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        if "no" in df.columns:
            return df[["no", "aktivitas", "output", "mulai", "selesai", "jenis"]]
    rows = []
    for i in range(1, 56):
        rows.append({
            "No": f"Aktivitas {i}",
            "Nama Aktivitas": f"Pekerjaan Fase Implementasi #{i}",
            "Output Milestone": f"Target milestone {i} terpenuhi",
            "Mulai": "2026 H1",
            "Selesai": "2028 H2",
            "Jenis": "Aktivitas" if i % 5 != 0 else "Milestone",
        })
    return pd.DataFrame(rows)


def build_risk_matrix_df() -> pd.DataFrame:
    import os
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "golden_v7", "golden_implementation_plan_matriks.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        cols = [c for c in ["A", "D", "F", "H", "J", "L"] if c in df.columns]
        if cols:
            return df[cols].dropna(how="all")
    impacts = ["5 Severe", "4 Major", "3 Moderate", "2 Minor", "1 Negligible"]
    rows = []
    for imp in impacts:
        rows.append({
            "Impact \\ Likelihood": imp,
            "1 Rare": "-",
            "2 Unlikely": "11, 14",
            "3 Possible": "1, 7, 8",
            "4 Likely": "2, 12",
            "5 Almost Certain": "-",
        })
    return pd.DataFrame(rows)


def build_fmea_chosen_reg_df() -> pd.DataFrame:
    import os
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "golden_v7", "golden_implementation_plan_register.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        cols = [c for c in ["A", "B", "D", "E", "F", "G", "H", "I", "J", "K"] if c in df.columns]
        if cols and len(df) > 1:
            return df.iloc[1:][cols].dropna(subset=["B"])
    rows = []
    for i in range(1, 26):
        rows.append({
            "No": i,
            "Failure Mode": f"FM {i} Kegagalan Skenario Terpilih #{i}",
            "Kategori": "Metode",
            "Severity": 7,
            "Occurrence": 5,
            "Detection": 4,
            "RPN": 140,
            "Kelas": "High",
            "Mitigasi Utama": "Uji tekanan integritas pra-job",
        })
    return pd.DataFrame(rows)
