"""
Athena Scenario Generator
Aplikasi Pemodelan Finansial & Optimasi Skenario Intervensi Sumur Lapangan Athena
PetroAthena 2026 Business Case Competition
Sesuai PRD Addendum v3.1 & Panduan UI/UX (UIUX_Guidelines §9)
"""

import os
import sys

# Tambahkan direktori root workspace ke sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import json
from athena_app.core.engine import AthenaEngine
from athena_app.core.config_manager import ConfigManager
from athena_app.ui.components import (
    set_selected_scenario,
    get_selected_scenario,
    FOOTNOTE_TEXT,
    render_stage_stepper,
    render_assumption_banner,
    init_session_state,
)
from athena_app.ui.tab1_kombinasi import render_tab1
from athena_app.ui.tab2_kompatibilitas import render_tab2
from athena_app.ui.tab3_variabel import render_tab3
from athena_app.ui.tab4_projection_sa import render_tab4
from athena_app.ui.tab5_projection_fi import render_tab5
from athena_app.ui.tab6_summary import render_tab6
from athena_app.ui.stage2_environmental import render_stage2_environmental
from athena_app.ui.stage2_risk import render_stage2_risk
from athena_app.ui.stage2_technical import render_stage2_technical
from athena_app.ui.stage3_topsis import render_stage3_topsis
from athena_app.ui.page_settings import render_settings_page

# Path ke file Excel V6 di data/ (didukung otomatis oleh loader)
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "data", "Bismillah_Angker_BCC_Excel_Calculations_V6.xlsx")
if not os.path.exists(EXCEL_PATH):
    EXCEL_PATH = os.path.join(os.path.dirname(__file__), "data", "Angker_BCC_Excel_Calculations_V5.xlsx")


st.set_page_config(
    page_title="Athena Scenario Generator | PetroAthena 2026",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inisialisasi session state awal
init_session_state()

# Custom Styling (uiux.md §2.1 Color Tokens, Light Data Theme & §9 Sidebar Navigation)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #0D1B2A;
        --bg-secondary: #F7F9FB;
        --accent-primary: #1E88E5;
        --accent-secondary: #00897B;
        --accent-gold: #FFB300;
        --text-primary: #1B1F23;
        --text-muted: #5A6A80;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Background area kerja terang dan nyaman untuk membaca data finansial berjam-jam */
    .stApp {
        background-color: var(--bg-secondary);
        color: var(--text-primary);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-primary);
        color: #E0E1DD;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] strong {
        color: #E0E1DD !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.15) !important;
    }

    /* Styling Navigasi Radio Bertahap di Sidebar (UIUX Guidelines §9.2) */
    section[data-testid="stSidebar"] div[role="radiogroup"] input {
        display: none !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 6px 12px !important;
        border-radius: 6px !important;
        border-left: 3px solid transparent !important;
        margin-bottom: 2px !important;
        transition: background-color 120ms ease !important;
        cursor: pointer !important;
        color: #CBD5E1 !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(30, 136, 229, 0.06) !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: rgba(30, 136, 229, 0.14) !important;
        border-left-color: #1E88E5 !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
    }
    /* Section Group Headers (0 / 1 / 2 / 3) */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(1)::before {
        content: "0 · DATA & KOMBINASI";
        display: block;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        color: #94A3B8;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
        pointer-events: none;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(4)::before {
        content: "1 · MODEL FINANSIAL";
        display: block;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        color: #94A3B8;
        margin-top: 14px;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
        pointer-events: none;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(7)::before {
        content: "2 · MULTI-KRITERIA";
        display: block;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        color: #94A3B8;
        margin-top: 14px;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
        pointer-events: none;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(10)::before {
        content: "3 · KEPUTUSAN";
        display: block;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        color: #94A3B8;
        margin-top: 14px;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
        pointer-events: none;
    }
    /* Item Pengaturan Lanjutan dipisah garis tipis di atasnya */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(11) {
        border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
        margin-top: 8px !important;
        padding-top: 8px !important;
    }

    /* Header Banner Eksekutif */
    .main-header, div.main-header {
        background: linear-gradient(135deg, #0D1B2A 0%, #1B263B 55%, #273A52 100%) !important;
        padding: 24px 32px;
        border-radius: 12px;
        margin-bottom: 14px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 4px 20px rgba(13, 27, 42, 0.25);
    }
    .main-header h1, h1.main-title, .main-title {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        letter-spacing: -0.5px !important;
    }
    .main-subtitle {
        color: #E0E1DD !important;
        -webkit-text-fill-color: #E0E1DD !important;
        font-size: 1.02rem;
        margin-top: 6px;
        margin-bottom: 0;
        opacity: 0.95;
    }

    /* Metric card value & styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        font-weight: 700 !important;
        color: var(--text-primary);
        font-feature-settings: 'tnum';
    }

    /* Expander card styling */
    div[data-testid="stExpander"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        margin-bottom: 12px;
    }

    /* Dataframe wrapper border */
    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
        background: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Menghitung seluruh 453 skenario & optimasi finansial V6...")
def load_and_calculate_engine(config_json: str = ""):
    engine = AthenaEngine(EXCEL_PATH)
    overrides = json.loads(config_json) if config_json else None
    return engine.run_all(config_overrides=overrides)


def main():
    # Periksa konfigurasi aktif dan deteksi modifikasi (Addendum §10)
    active_cfg = st.session_state.get("active_config", {})
    cfg_diffs = ConfigManager.get_diffs(active_cfg) if active_cfg else []
    cfg_json = json.dumps(active_cfg, sort_keys=True) if cfg_diffs else ""

    # Eksekusi engine terpadu (di-cache berdasarkan state konfigurasi aktif)
    results = load_and_calculate_engine(cfg_json)

    top10_sa = results["top10_sa"]
    sa_scenarios = results["sa_scenarios"]

    # Inisialisasi scenario fokus global ke Rank 1 jika belum ditentukan
    if "selected_scenario" not in st.session_state and len(top10_sa) > 0:
        set_selected_scenario(top10_sa[0]["no"])

    # ==========================================================================
    # SIDEBAR: KONTROL GLOBAL & NAVIGASI BERTAHAP (UI/UX Guidelines §9.2 & Addendum §11)
    # ==========================================================================
    with st.sidebar:
        st.markdown(
            '<div style="font-size: 1.25rem; font-weight: 700; color: #FFFFFF !important; margin-bottom: 2px;">'
            '🛢️ Athena Scenario Generator</div>',
            unsafe_allow_html=True,
        )
        st.caption("PetroAthena 2026 Business Case Competition")

        st.markdown("---")
        # Global Control Tunggal: Radio ICP (Addendum §11)
        st.markdown(
            '<div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: #94A3B8; margin-bottom: 4px;">'
            'Harga Minyak Acuan (ICP)</div>',
            unsafe_allow_html=True,
        )
        ed = results["existing_data"]
        p_low = int(ed.get("price_low", 64))
        p_base = int(ed.get("price_base", 80))
        p_high = int(ed.get("price_high", 117))
        p_opts = [p_low, p_base, p_high]
        cur_p = int(st.session_state.get("selected_price", p_base))
        if cur_p not in p_opts:
            cur_p = p_base
            st.session_state["selected_price"] = cur_p

        def _on_sidebar_price_change():
            st.session_state["selected_price"] = st.session_state["sb_icp_radio"]

        st.radio(
            "Tingkat Harga Minyak Global:",
            options=p_opts,
            index=p_opts.index(cur_p),
            horizontal=True,
            format_func=lambda x: f"{x}$ USD",
            key="sb_icp_radio",
            on_change=_on_sidebar_price_change,
            label_visibility="collapsed",
        )

        st.markdown("---")

        # Navigasi 11 Halaman Berjenjang (Tahap 0 / 1 / 2 / 3) + Pengaturan Lanjutan
        nav_pages = [
            "Kombinasi Strategi",
            "Hard Constraint & Kompatibilitas",
            "Variabel Inti",
            "Proyeksi Stand-Alone",
            "Skenario Farm-In",
            "Ringkasan SA vs FI",
            "Dampak Lingkungan",
            "Risiko (FMEA)",
            "Implementasi Teknis",
            "AHP & TOPSIS",
            "Pengaturan Lanjutan",
        ]

        if "selected_page" not in st.session_state:
            st.session_state["selected_page"] = "Proyeksi Stand-Alone"

        current_nav_idx = nav_pages.index(st.session_state["selected_page"]) if st.session_state["selected_page"] in nav_pages else 3

        def _on_nav_change():
            st.session_state["selected_page"] = st.session_state["main_nav_radio"]

        selected_page = st.radio(
            "Navigasi Halaman:",
            options=nav_pages,
            index=current_nav_idx,
            key="main_nav_radio",
            on_change=_on_nav_change,
            label_visibility="collapsed",
        )

        st.markdown("---")
        # Parameter Lapangan Ringkas
        st.caption(f"**Produksi Awal (q0):** {ed['q0']:,.0f} bopd")
        st.caption(f"**Water Cut Awal (wc0):** {ed['wc0']*100:.1f}%")
        st.caption(f"**Decline Rate (d0):** {ed['d0']*100:.2f}%/thn")
        st.caption(f"**Sumur Aktif / Idle:** {ed['n_active']} / {ed['n_idle']}")
        st.caption(f"⏱️ Waktu Hitung: **{results['duration_sec']:.3f} dtk**")
        st.caption(f"🛡️ *{FOOTNOTE_TEXT}*")

    # ==========================================================================
    # MAIN AREA: HEADER, STEPPER NAVIGASI, BANNER ASUMSI & KONTEN HALAMAN
    # ==========================================================================
    header_html = (
        '<div class="main-header" style="background: linear-gradient(135deg, #0D1B2A 0%, #1B263B 55%, #273A52 100%) !important; padding: 22px 28px; border-radius: 12px; margin-bottom: 14px; border: 1px solid rgba(255, 255, 255, 0.12); box-shadow: 0 4px 20px rgba(13, 27, 42, 0.25);">'
        '<h1 class="main-title" style="color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-size: 2.1rem; font-weight: 700; margin: 0; letter-spacing: -0.5px;">🛢️ Athena Scenario Generator</h1>'
        '<p class="main-subtitle" style="color: #E0E1DD !important; -webkit-text-fill-color: #E0E1DD !important; font-size: 0.98rem; margin-top: 5px; margin-bottom: 0;">'
        'Sistem Optimasi Portofolio Intervensi Sumur & Evaluasi Multi-Kriteria Lapangan Athena — '
        '<strong style="color: #FFB300 !important; -webkit-text-fill-color: #FFB300 !important;">PetroAthena 2026 Business Case Competition</strong></p>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Stepper Header Tipis Informatif (UIUX Guidelines §9.3)
    render_stage_stepper(selected_page)

    # Banner Status Asumsi Kustom (UIUX Guidelines §10.5 & PRD Addendum §10.7)
    render_assumption_banner(len(cfg_diffs))

    # Render Halaman Terpilih
    if selected_page == "Kombinasi Strategi":
        render_tab1(results)
    elif selected_page == "Hard Constraint & Kompatibilitas":
        render_tab2(results)
    elif selected_page == "Variabel Inti":
        render_tab3(results)
    elif selected_page == "Proyeksi Stand-Alone":
        render_tab4(results)
    elif selected_page == "Skenario Farm-In":
        render_tab5(results)
    elif selected_page == "Ringkasan SA vs FI":
        render_tab6(results)
    elif selected_page == "Dampak Lingkungan":
        render_stage2_environmental(results)
    elif selected_page == "Risiko (FMEA)":
        render_stage2_risk(results)
    elif selected_page == "Implementasi Teknis":
        render_stage2_technical(results)
    elif selected_page == "AHP & TOPSIS":
        render_stage3_topsis(results)
    elif selected_page == "Pengaturan Lanjutan":
        render_settings_page(results)


if __name__ == "__main__":
    main()

