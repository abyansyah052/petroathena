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
from athena_app.ui.stage2_secondary_recovery import render_stage2_secondary_recovery
from athena_app.ui.stage2_contract_simulations import render_stage2_contract_simulations
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
        color-scheme: light !important;
        --bg-primary: #FFFFFF;
        --bg-secondary: #F7F9FB;
        --accent-primary: #1E88E5;
        --accent-secondary: #00897B;
        --accent-gold: #FFB300;
        --text-primary: #1B1F23;
        --text-muted: #5A6A80;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color-scheme: light !important;
    }

    /* Background area kerja terang dan nyaman untuk membaca data finansial berjam-jam */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        color-scheme: light !important;
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
    }

    /* Sidebar Styling (Executive Petrol Dark Navbar dengan kontras tinggi) */
    section[data-testid="stSidebar"] {
        background-color: #0D1B2A !important;
        border-right: 1px solid #1E293B !important;
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] strong {
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.15) !important;
    }

    /* Styling Navigasi Radio Bertahap di Sidebar (UIUX Guidelines §9.2 - High Contrast) */
    section[data-testid="stSidebar"] div[role="radiogroup"] input {
        display: none !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 7px 12px !important;
        border-radius: 6px !important;
        border-left: 3px solid transparent !important;
        margin-bottom: 3px !important;
        transition: background-color 120ms ease !important;
        cursor: pointer !important;
        color: #CBD5E1 !important;
        background-color: transparent !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(30, 136, 229, 0.18) !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: rgba(30, 136, 229, 0.30) !important;
        border-left-color: #38BDF8 !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
    }
    /* Section Group Headers (0 / 1 / 1 / 2 / 3) dengan warna cerah kontras tinggi */
    div[data-testid="stRadio"]:has(input[value*="Kombinasi Strategi"]) div[role="radiogroup"] > label:nth-child(1)::before,
    div[role="radiogroup"][aria-label*="Navigasi"] > label:nth-child(1)::before {
        content: "0 · DATA & KOMBINASI";
        display: block;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        color: #38BDF8 !important;
        margin-bottom: 6px;
        letter-spacing: 0.6px;
        pointer-events: none;
    }
    div[data-testid="stRadio"]:has(input[value*="Kombinasi Strategi"]) div[role="radiogroup"] > label:nth-child(4)::before,
    div[role="radiogroup"][aria-label*="Navigasi"] > label:nth-child(4)::before {
        content: "1 · MODEL FINANSIAL";
        display: block;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        color: #38BDF8 !important;
        margin-top: 14px;
        margin-bottom: 6px;
        letter-spacing: 0.6px;
        pointer-events: none;
    }
    div[data-testid="stRadio"]:has(input[value*="Kombinasi Strategi"]) div[role="radiogroup"] > label:nth-child(7)::before,
    div[role="radiogroup"][aria-label*="Navigasi"] > label:nth-child(7)::before {
        content: "1 · MULTI-KRITERIA";
        display: block;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        color: #38BDF8 !important;
        margin-top: 14px;
        margin-bottom: 6px;
        letter-spacing: 0.6px;
        pointer-events: none;
    }
    div[data-testid="stRadio"]:has(input[value*="Kombinasi Strategi"]) div[role="radiogroup"] > label:nth-child(10)::before,
    div[role="radiogroup"][aria-label*="Navigasi"] > label:nth-child(10)::before {
        content: "2 · SIMULASI LANJUTAN";
        display: block;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        color: #38BDF8 !important;
        margin-top: 14px;
        margin-bottom: 6px;
        letter-spacing: 0.6px;
        pointer-events: none;
    }
    div[data-testid="stRadio"]:has(input[value*="Kombinasi Strategi"]) div[role="radiogroup"] > label:nth-child(12)::before,
    div[role="radiogroup"][aria-label*="Navigasi"] > label:nth-child(12)::before {
        content: "3 · KEPUTUSAN";
        display: block;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        color: #38BDF8 !important;
        margin-top: 14px;
        margin-bottom: 6px;
        letter-spacing: 0.6px;
        pointer-events: none;
    }
    /* Item Pengaturan Lanjutan dipisah garis tipis di atasnya */
    div[data-testid="stRadio"]:has(input[value*="Kombinasi Strategi"]) div[role="radiogroup"] > label:nth-child(13),
    div[role="radiogroup"][aria-label*="Navigasi"] > label:nth-child(13) {
        border-top: 1px solid rgba(255, 255, 255, 0.18) !important;
        margin-top: 10px !important;
        padding-top: 10px !important;
    }

    /* Header Banner Eksekutif Berwarna Elegan dengan Kontras Maksimal */
    .main-header, div.main-header {
        background: linear-gradient(135deg, #0A192F 0%, #112240 50%, #1B3A5A 100%) !important;
        padding: 24px 30px !important;
        border-radius: 12px !important;
        margin-bottom: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 4px 20px rgba(10, 25, 47, 0.3) !important;
    }
    .main-header h1, h1.main-title, .main-title {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-size: 2.15rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        letter-spacing: -0.5px !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4) !important;
    }
    .main-subtitle {
        color: #E2E8F0 !important;
        -webkit-text-fill-color: #E2E8F0 !important;
        font-size: 1.0rem !important;
        margin-top: 6px !important;
        margin-bottom: 0 !important;
        opacity: 0.95 !important;
    }

    /* Penegasan Visual Input Box & Form (Mencegah Input Box Tidak Terlihat di semua versi Streamlit) */
    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 10px !important;
        padding: 20px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    }
    div[data-testid="stTextInputRootElement"],
    div[data-testid="stTextInput"] div[data-testid="stTextInputRootElement"],
    div[data-testid="stTextInput"] div[data-baseweb="input"],
    div[data-testid="stTextInput"] div[data-baseweb="base-input"],
    div[data-baseweb="input"],
    div[data-baseweb="base-input"],
    .stTextInput > div > div {
        background-color: #FFFFFF !important;
        border: 2px solid #64748B !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06) inset !important;
        transition: border-color 150ms ease, box-shadow 150ms ease !important;
    }
    div[data-testid="stTextInputRootElement"]:focus-within,
    div[data-testid="stTextInput"] div[data-testid="stTextInputRootElement"]:focus-within,
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="base-input"]:focus-within,
    .stTextInput > div > div:focus-within {
        border-color: #1E88E5 !important;
        box-shadow: 0 0 0 3px rgba(30, 136, 229, 0.25) !important;
    }
    input[data-testid="stTextInputField"],
    div[data-testid="stTextInput"] input,
    .stTextInput input {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        background-color: transparent !important;
        font-size: 1.0rem !important;
        padding: 10px 14px !important;
        border: none !important;
        outline: none !important;
    }
    input[data-testid="stTextInputField"]::placeholder,
    div[data-testid="stTextInput"] input::placeholder,
    div[data-baseweb="input"] input::placeholder,
    input::placeholder {
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
        opacity: 0.70 !important; /* Opacity placeholder diturunkan 30% */
    }
    div[data-testid="stTextInput"] label {
        color: #0F172A !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 6px !important;
    }
    div[data-testid="stTextInput"] svg,
    div[data-testid="stTextInput"] button {
        fill: #475569 !important;
        color: #475569 !important;
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

    /* =========================================================================
       RESPONSIVE & MOBILE-FRIENDLY SYSTEM (DESKTOP UI/UX 100% PRESERVED)
       ========================================================================= */

    /* Ensure horizontal smoothness and prevent accidental body x-scroll */
    html, body {
        max-width: 100vw;
        overflow-x: hidden;
    }

    /* Tablet Viewport (<= 992px) */
    @media (max-width: 992px) {
        .main-header, div.main-header {
            padding: 20px 22px !important;
        }
        .main-header h1, h1.main-title, .main-title {
            font-size: 1.75rem !important;
        }
    }

    /* Mobile & Tablet Portrait Viewport (<= 768px) */
    @media (max-width: 768px) {
        /* 1. Page container padding optimization for mobile */
        .block-container,
        div.block-container,
        section.main > div {
            padding: 1.0rem 0.85rem 2.5rem 0.85rem !important;
            max-width: 100vw !important;
        }

        /* 2. Executive Hero Banner Responsive */
        .main-header, div.main-header {
            padding: 16px 16px !important;
            border-radius: 10px !important;
            margin-bottom: 12px !important;
        }
        .main-header h1, h1.main-title, .main-title {
            font-size: 1.40rem !important;
            line-height: 1.3 !important;
            letter-spacing: -0.3px !important;
        }
        .main-subtitle {
            font-size: 0.85rem !important;
            line-height: 1.4 !important;
            margin-top: 6px !important;
        }

        /* 3. Stage Stepper Responsive Wrapping */
        .athena-stepper {
            display: flex !important;
            flex-wrap: wrap !important;
            height: auto !important;
            min-height: 28px !important;
            padding: 6px 12px !important;
            line-height: 1.3 !important;
            gap: 6px !important;
            max-width: 100% !important;
        }
        .athena-stepper-visual {
            font-size: 0.95rem !important;
            margin-right: 6px !important;
        }
        .athena-stepper-label {
            font-size: 0.72rem !important;
        }

        /* 4. Intelligent Column Flow on Mobile */
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 10px 8px !important;
            width: 100% !important;
        }

        /* Default columns stack to 100% width on mobile (for charts, tables, forms, etc.) */
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            flex: 1 1 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
        }

        /* EXCEPT when columns contain KPI Cards: 2x2 Grid Layout */
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"] .athena-kpi-card) > div[data-testid="column"] {
            flex: 1 1 calc(50% - 6px) !important;
            min-width: calc(50% - 6px) !important;
            max-width: calc(50% - 6px) !important;
        }

        /* EXCEPT when columns contain Best/Worst Highlight Cards: 2 columns on tablet, stack on phone */
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"] .athena-bw-card) > div[data-testid="column"] {
            flex: 1 1 calc(50% - 6px) !important;
            min-width: calc(50% - 6px) !important;
            max-width: calc(50% - 6px) !important;
        }

        /* KPI Card typography adjustments on mobile */
        .athena-kpi-card {
            padding: 12px 14px !important;
            margin-bottom: 6px !important;
        }
        .athena-kpi-label {
            font-size: 0.68rem !important;
            letter-spacing: 0.3px !important;
        }
        .athena-kpi-val,
        div[data-testid="stMetricValue"] {
            font-size: 1.35rem !important;
            line-height: 1.25 !important;
        }
        .athena-kpi-delta {
            font-size: 0.75rem !important;
        }

        /* 5. Subtab Segmented Control Horizontal Scrolling */
        div[data-testid="stSegmentedControl"] {
            overflow-x: auto !important;
            white-space: nowrap !important;
            flex-wrap: nowrap !important;
            -webkit-overflow-scrolling: touch !important;
            padding-bottom: 6px !important;
            scrollbar-width: thin !important;
            gap: 6px !important;
        }
        div[data-testid="stSegmentedControl"] > div {
            display: inline-flex !important;
            flex-shrink: 0 !important;
            flex-wrap: nowrap !important;
        }
        div[data-testid="stSegmentedControl"] button,
        div[data-testid="stSegmentedControl"] label {
            flex-shrink: 0 !important;
            white-space: nowrap !important;
            font-size: 0.82rem !important;
            padding: 6px 12px !important;
        }

        /* 6. Mobile Plotly Charts & Modebar Handling */
        .js-plotly-plot,
        .plot-container {
            max-width: 100% !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }
        .modebar-container,
        .modebar {
            display: none !important; /* Sembunyikan modebar mengambang di mobile agar tidak menabrak judul graf */
        }

        /* 7. Tables & Dataframes Mobile Touch Scroll */
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            max-width: 100% !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }

        /* 8. Mobile Sidebar & Touch Targets */
        section[data-testid="stSidebar"] {
            max-width: 86vw !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: 10px 14px !important;
            min-height: 42px !important;
            display: flex !important;
            align-items: center !important;
            font-size: 0.90rem !important;
            margin-bottom: 4px !important;
        }

        /* Mobile Sidebar Collapse Toggle Button */
        button[data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapseButton"] {
            background-color: #0D1B2A !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.25) !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
            padding: 6px 8px !important;
        }
        button[data-testid="stSidebarCollapsedControl"] svg,
        [data-testid="stSidebarCollapseButton"] svg {
            fill: #FFFFFF !important;
            color: #FFFFFF !important;
        }

        /* 9. Buttons Touch Targets on Mobile */
        button[data-testid="stBaseButton-secondary"],
        button[data-testid="stBaseButton-primary"],
        div.stButton > button,
        div.stDownloadButton > button {
            min-height: 42px !important;
            font-size: 0.88rem !important;
            padding: 8px 14px !important;
            width: 100% !important;
        }

        /* 10. Callouts & Insights on Mobile */
        .athena-insight-callout {
            padding: 10px 14px !important;
            font-size: 0.88rem !important;
            line-height: 1.4 !important;
        }
    }

    /* Extra Narrow Mobile Screens (<= 480px) */
    @media (max-width: 480px) {
        .block-container,
        div.block-container {
            padding: 0.75rem 0.60rem 2.0rem 0.60rem !important;
        }

        .main-header h1, h1.main-title, .main-title {
            font-size: 1.25rem !important;
        }
        .main-subtitle {
            font-size: 0.80rem !important;
        }

        /* Stack Best/Worst cards on tiny screens */
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"] .athena-bw-card) > div[data-testid="column"] {
            flex: 1 1 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
        }

        /* In small screens, KPI card metric value */
        .athena-kpi-val,
        div[data-testid="stMetricValue"] {
            font-size: 1.20rem !important;
        }

        .athena-kpi-card {
            padding: 10px 12px !important;
        }
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
            '<div style="font-size: 1.25rem; font-weight: 800; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; margin-bottom: 2px; text-shadow: 0 1px 3px rgba(0,0,0,0.5);">'
            '🛢️ Athena Scenario Generator</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="color: #94A3B8 !important; font-size: 0.82rem; margin-bottom: 10px;">'
            'PetroAthena 2026 Business Case Competition</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        # Global Control Tunggal: Radio ICP (Addendum §11)
        st.markdown(
            '<div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: #38BDF8 !important; margin-bottom: 4px; letter-spacing: 0.6px;">'
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

        # Navigasi 12 Halaman Berjenjang (Tahap 0 / 1 / 2 / 3) + Pengaturan Lanjutan
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
            "Secondary Recovery",
            "Simulasi Kontrak",
            "AHP & TOPSIS",
            "🔒 Pengaturan Lanjutan",
        ]

        if "selected_page" not in st.session_state:
            st.session_state["selected_page"] = "Kombinasi Strategi"

        current_nav_idx = (
            nav_pages.index(st.session_state["selected_page"])
            if st.session_state["selected_page"] in nav_pages
            else 0
        )

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
        # Parameter Lapangan Ringkas (High Contrast pada Background Gelap)
        st.markdown(f'<div style="color: #CBD5E1; font-size: 0.82rem; margin-bottom: 4px;"><strong>Produksi Awal (q0):</strong> {ed["q0"]:,.0f} bopd</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #CBD5E1; font-size: 0.82rem; margin-bottom: 4px;"><strong>Water Cut Awal (wc0):</strong> {ed["wc0"]*100:.1f}%</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #CBD5E1; font-size: 0.82rem; margin-bottom: 4px;"><strong>Decline Rate (d0):</strong> {ed["d0"]*100:.2f}%/thn</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #CBD5E1; font-size: 0.82rem; margin-bottom: 4px;"><strong>Sumur Aktif / Idle:</strong> {ed["n_active"]} / {ed["n_idle"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color: #94A3B8; font-size: 0.80rem; margin-top: 8px;">⏱️ Waktu Hitung: <strong style="color: #FFFFFF;">{results["duration_sec"]:.3f} dtk</strong></div>', unsafe_allow_html=True)

    # ==========================================================================
    # MAIN AREA: HEADER, STEPPER NAVIGASI, BANNER ASUMSI & KONTEN HALAMAN
    # ==========================================================================
    # Hero Banner hanya ditampilkan di halaman awal (Kombinasi Strategi)
    if selected_page == "Kombinasi Strategi":
        header_html = (
            '<div class="main-header">'
            '<h1 class="main-title">🛢️ Athena Scenario Generator</h1>'
            '<p class="main-subtitle">'
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
    elif selected_page in ["Ringkasan SA vs FI", "Ringkasan SA vs Farm-In"]:
        render_tab6(results)
    elif selected_page == "Dampak Lingkungan":
        render_stage2_environmental(results)
    elif selected_page == "Risiko (FMEA)":
        render_stage2_risk(results)
    elif selected_page == "Implementasi Teknis":
        render_stage2_technical(results)
    elif selected_page == "Secondary Recovery":
        render_stage2_secondary_recovery(results)
    elif selected_page == "Simulasi Kontrak":
        render_stage2_contract_simulations(results)
    elif selected_page == "AHP & TOPSIS":
        render_stage3_topsis(results)
    elif selected_page in ["Pengaturan Lanjutan", "🔒 Pengaturan Lanjutan"]:
        render_settings_page(results)


if __name__ == "__main__":
    main()

