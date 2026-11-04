"""
Module ui/components.py: Reusable UI components according to UI/UX guidelines and PRD Addendum v4.1.
- KPI Cards with clean typography and optional delta/tooltip
- Compact Table with "Tampilkan semua kolom" toggle and full CSV download
- Dynamic Insight Callout (💡)
- Best vs Worst Highlight Cards (§9.1)
- Risk Class Legend Chips (§9.3)
- Pool Biaya display names mapping (cost_type, pool_code) (§5.1)
- Stage Stepper indicator (Stage 0 to Stage 3)
- Standardized footnote
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple


FOOTNOTE_TEXT = "Seluruh nilai dihitung dengan implementasi Python yang divalidasi 100% cocok terhadap cache Excel V6_1."


POOL_DISPLAY_NAMES: Dict[Tuple[str, str], str] = {
    ("CAPEX", "DIAG"): "Diagnosis & Desain",
    ("CAPEX", "SPEC"): "Material & Peralatan Khusus Metode",
    ("OPEX", "SPEC"): "Inspeksi & Servis Komplesi",
    ("CAPEX", "EXEC"): "Eksekusi & Intervensi Sumur",
    ("CAPEX", "TEST"): "Pengujian",
    ("OPEX", "TEST"): "Pengujian",
    ("CAPEX", "CONT"): "Kontinjensi",
    ("CAPEX", "REAK"): "Reaktivasi Sumur Idle",
    ("OPEX", "SURV"): "Surveilans Produksi & Water Cut",
    ("OPEX", "LAB"): "Laboratorium",
    ("OPEX", "REVIEW"): "Tinjauan Engineering",
}

POOL_FILTER_CAPTION = (
    "Pool Biaya mengelompokkan item menurut jenis pekerjaan. "
    "Item 'Sekali' dalam pool yang sama hanya dihitung satu kali per kombinasi "
    "(diambil yang termahal antar metode), karena sumber dayanya dipakai bersama — "
    "misalnya satu mobilisasi rig. Item 'Jumlah' dihitung untuk setiap metode."
)

ATURAN_FILTER_CAPTION = (
    "'Sekali' = biaya pool dihitung satu kali untuk seluruh kombinasi "
    "(nilai maksimum antar metode, karena fasilitas/sumber daya bisa dipakai bersama). "
    "'Jumlah' = biaya dijumlah penuh untuk setiap metode dalam kombinasi. "
    "Aturan ini selalu sama untuk semua item dalam satu pool."
)


def get_pool_display_name(cost_type: str, pool_code: str) -> str:
    """Mengembalikan nama tampilan pool biaya berdasarkan pasangan (tipe_biaya, kode_pool)."""
    ctype = cost_type.upper().strip() if cost_type else "CAPEX"
    pcode = pool_code.upper().strip() if pool_code else ""
    return POOL_DISPLAY_NAMES.get((ctype, pcode), f"{pcode} ({ctype})")


def render_footnote():
    """Footnote dihapus sesuai permintaan user."""
    pass


def render_insight_callout(text: str):
    """
    Renders an automated, dynamic 1-2 sentence executive insight callout.
    """
    html = (
        f'<div class="athena-insight-callout" style="background: #EBF3FA; border-left: 4px solid #1E88E5; padding: 12px 18px; '
        f'border-radius: 6px; margin: 12px 0 16px 0; color: #1B1F23; font-size: 0.95rem; '
        f'line-height: 1.45; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">'
        f'<span style="font-size: 1.15rem; margin-right: 6px;">💡</span>'
        f'<strong>Insight Eksekutif:</strong> {text}</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_kpi_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    help_text: Optional[str] = None,
    is_gold: bool = False,
):
    """
    Renders a clean KPI card with high contrast, large numeric font, and clear label.
    Includes semantic CSS class hooks for responsive mobile layouts.
    """
    gold_border = "border: 2px solid #FFB300;" if is_gold else "border: 1px solid #E2E8F0;"
    gold_bg = "background: #FFFDF5;" if is_gold else "background: #FFFFFF;"
    delta_html = f'<div class="athena-kpi-delta" style="font-size: 0.8rem; color: #2E7D32; font-weight: 500; margin-top: 4px;">{delta}</div>' if delta else ""
    help_html = f' <span title="{help_text}" style="cursor: help; color: #757575; font-size: 0.8rem;">ⓘ</span>' if help_text else ""

    html = (
        f'<div class="athena-kpi-card" style="{gold_bg} {gold_border} border-radius: 8px; padding: 14px 18px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); margin-bottom: 8px;">'
        f'<div class="athena-kpi-label" style="font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #5A6A80; margin-bottom: 4px;">{label}{help_html}</div>'
        f'<div class="athena-kpi-val" style="font-size: 1.65rem; font-weight: 700; color: #1B1F23; font-feature-settings: \'tnum\'; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_best_worst_cards(
    best_title: str,
    best_name: str,
    best_metric: str,
    best_detail: str,
    worst_title: str,
    worst_name: str,
    worst_metric: str,
    worst_detail: str,
):
    """
    Renders two side-by-side highlight cards per PRD Addendum v4.1 §9.1:
    Left: Best (green background 8% opacity, green border).
    Right: Worst (red background 8% opacity, red border).
    Includes responsive CSS hooks (.athena-bw-card, .athena-bw-best, .athena-bw-worst).
    """
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div class="athena-bw-card athena-bw-best" style="background: rgba(46, 125, 50, 0.08); border-left: 4px solid #2E7D32; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #1B5E20; text-transform: uppercase; letter-spacing: 0.5px;">🟢 {best_title}</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #1B1F23; margin: 4px 0 2px 0;">{best_name}</div>
                <div class="athena-bw-metric" style="font-size: 1.25rem; font-weight: 700; color: #2E7D32;">{best_metric}</div>
                <div style="font-size: 0.82rem; color: #2E7D32; margin-top: 2px;">{best_detail}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="athena-bw-card athena-bw-worst" style="background: rgba(198, 40, 40, 0.08); border-left: 4px solid #C62828; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #B71C1C; text-transform: uppercase; letter-spacing: 0.5px;">🔴 {worst_title}</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #1B1F23; margin: 4px 0 2px 0;">{worst_name}</div>
                <div class="athena-bw-metric" style="font-size: 1.25rem; font-weight: 700; color: #C62828;">{worst_metric}</div>
                <div style="font-size: 0.82rem; color: #C62828; margin-top: 2px;">{worst_detail}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_fmea_legend(b65: int = 200, b66: int = 100, b67: int = 50, b68: int = 0, b69: int = 9):
    """
    Renders risk class legend chips directly above the FMEA table (PRD §9.3).
    """
    html = f"""
    <div class="athena-fmea-legend" style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px; font-size: 0.83rem; line-height: 1.5; color: #1B1F23;">
        <div style="font-weight: 600; margin-bottom: 4px; color: #334155;">
            Kelas risiko dihitung dari RPN = Severity × Occurrence × Detection (skala 1–1000):
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 4px;">
            <span style="background: #FEE2E2; color: #991B1B; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Critical &ge; {b65}</span>
            <span style="color: #64748B;">Perlu mitigasi wajib sebelum eksekusi</span>
            <span style="color: #CBD5E1;">·</span>
            <span style="background: #FFEDD5; color: #9A3412; padding: 2px 8px; border-radius: 4px; font-weight: 600;">High {b66}&ndash;{b65-1}</span>
            <span style="color: #64748B;">Perlu rencana mitigasi & pemilik risiko</span>
            <span style="color: #CBD5E1;">·</span>
            <span style="background: #FEF9C3; color: #854D0E; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Medium {b67}&ndash;{b66-1}</span>
            <span style="color: #64748B;">Dipantau prosedur standar</span>
            <span style="color: #CBD5E1;">·</span>
            <span style="background: #DCFCE7; color: #166534; padding: 2px 8px; border-radius: 4px; font-weight: 600;">Low &lt; {b67}</span>
            <span style="color: #64748B;">Diterima tanpa tindakan</span>
        </div>
        <div style="font-size: 0.76rem; color: #64748B; font-style: italic;">
            Severity &ge; {b69} ditandai khusus walau RPN rendah (potensi well control / HSE).
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_compact_table(
    df: pd.DataFrame,
    core_cols: List[str],
    all_cols: List[str],
    download_filename: str,
    key_prefix: str,
    height: int = 420,
    format_dict: Optional[Dict[str, Any]] = None,
):
    """
    Renders a compact table showing core_cols by default (<= 12 cols).
    Includes a 'Tampilkan semua kolom' checkbox to reveal all_cols.
    """
    col_ctrl, col_dl = st.columns([1, 1])
    with col_ctrl:
        show_all = st.checkbox(
            f"Tampilkan semua kolom ({len(all_cols)} kolom)",
            value=False,
            key=f"{key_prefix}_show_all",
        )
    with col_dl:
        full_df = df[all_cols] if all(c in df.columns for c in all_cols) else df
        csv_data = full_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"⬇️ Unduh Seluruh Data ({len(full_df):,} baris, {len(all_cols)} kolom)",
            data=csv_data,
            file_name=download_filename,
            mime="text/csv",
            key=f"{key_prefix}_download",
            use_container_width=True,
        )

    cols_to_display = [c for c in all_cols if c in df.columns] if show_all else [c for c in core_cols if c in df.columns]
    view_df = df[cols_to_display].copy()

    if format_dict:
        active_fmt = {k: v for k, v in format_dict.items() if k in view_df.columns}
        styled_df = view_df.style.format(active_fmt, na_rep="")
    else:
        styled_df = view_df

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=height,
    )


def init_session_state():
    """Initializes global session states if not already present."""
    if "selected_scenario" not in st.session_state:
        st.session_state["selected_scenario"] = 60
    if "selected_price" not in st.session_state:
        st.session_state["selected_price"] = 80.0


def get_selected_scenario() -> int:
    """Returns currently selected scenario number from session_state."""
    init_session_state()
    return st.session_state["selected_scenario"]


def set_selected_scenario(no: int):
    """Sets currently selected scenario number in session_state."""
    st.session_state["selected_scenario"] = int(no)


def render_scenario_picker(
    options: List[int],
    label_map: Dict[int, str],
    key: str,
    label: str = "Pilih Skenario Fokus Analisis:",
    help_text: str = "Pilihan skenario untuk grafik detail dan worked example.",
) -> int:
    """
    Renders an in-page scenario picker synced to st.session_state['selected_scenario'].
    """
    init_session_state()
    current_val = st.session_state["selected_scenario"]
    if current_val not in options and len(options) > 0:
        current_val = options[0]
        st.session_state["selected_scenario"] = current_val

    default_idx = options.index(current_val) if current_val in options else 0

    selected = st.selectbox(
        label,
        options=options,
        index=default_idx,
        format_func=lambda x: label_map.get(x, f"Skenario #{x}"),
        key=key,
        help=help_text,
    )

    if selected != st.session_state["selected_scenario"]:
        st.session_state["selected_scenario"] = selected

    return selected


def render_stage_stepper(current_page: str = "Proyeksi Stand-Alone"):
    """
    Renders horizontal stage stepper according to PRD §5.6 & UI/UX Guidelines §9.
    Stages:
      0 · DATA & KOMBINASI
      1 · MODEL FINANSIAL & MULTI-KRITERIA
      2 · SIMULASI LANJUTAN
      3 · KEPUTUSAN
    """
    stage_map = {
        # Stage 0
        "Kombinasi Strategi": (0, "Tahap 0 · Data & Kombinasi"),
        "Hard Constraint & Kompatibilitas": (0, "Tahap 0 · Data & Kombinasi"),
        "Variabel Inti": (0, "Tahap 0 · Data & Kombinasi"),
        # Stage 1
        "Proyeksi Stand-Alone": (1, "Tahap 1 · Model Finansial"),
        "Skenario Farm-In": (1, "Tahap 1 · Model Finansial"),
        "Ringkasan SA vs Farm-In": (1, "Tahap 1 · Model Finansial"),
        "Ringkasan SA vs FI": (1, "Tahap 1 · Model Finansial"),
        "Dampak Lingkungan": (1, "Tahap 1 · Multi-Kriteria"),
        "Risiko (FMEA)": (1, "Tahap 1 · Multi-Kriteria"),
        "Implementasi Teknis": (1, "Tahap 1 · Multi-Kriteria"),
        # Stage 2
        "Secondary Recovery": (2, "Tahap 2 · Simulasi Lanjutan"),
        "Simulasi Kontrak": (2, "Tahap 2 · Simulasi Lanjutan"),
        # Stage 3
        "AHP & TOPSIS": (3, "Tahap 3 · Keputusan"),
        "Skenario Terpilih": (3, "Tahap 3 · Keputusan"),
        "Rencana Implementasi": (3, "Tahap 3 · Keputusan"),
        "Pengaturan Lanjutan": (3, "Pengaturan Asumsi Lanjutan"),
        "🔒 Pengaturan Lanjutan": (3, "Pengaturan Asumsi Lanjutan"),
    }
    stage_idx, stage_label = stage_map.get(current_page, (1, "Tahap 1 · Model Finansial"))

    dots = []
    for i in range(4):
        if i == stage_idx:
            dots.append('<span style="color:#1E88E5;font-size:1.15rem;font-weight:700;">●</span>')
        else:
            dots.append('<span style="color:#94A3B8;font-size:1.15rem;">○</span>')
    stepper_visual = '<span style="color:#CBD5E1;margin:0 3px;">──</span>'.join(dots)

    html = (
        f'<div class="athena-stepper" style="display:inline-flex;align-items:center;min-height:26px;padding:3px 14px;background:#FFFFFF;border-radius:14px;border:1px solid #E2E8F0;margin-bottom:12px;box-shadow:0 1px 2px rgba(0,0,0,0.02);">'
        f'<span class="athena-stepper-visual" style="margin-right:10px;line-height:1;">{stepper_visual}</span>'
        f'<span class="athena-stepper-label" style="font-size:0.75rem;font-weight:600;color:#64748B;letter-spacing:0.3px;">{stage_label}</span>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_assumption_banner(diff_count: int):
    """
    Renders subtle warm banner at top of content area when custom assumptions are active (§7.12, T24).
    """
    if diff_count <= 0:
        return
    html = (
        f'<div style="background: #FFF7E6; border: 1px solid #FFE58F; border-radius: 6px; '
        f'padding: 8px 16px; margin-bottom: 14px; font-size: 0.82rem; color: #873800; display: flex; align-items: center; justify-content: space-between;">'
        f'<span><strong>Hasil di halaman ini memakai asumsi kustom ({diff_count} parameter diubah)</strong>. Konfigurasi aktif berbeda dari acuan Excel V7.</span>'
        f'<span style="font-size: 0.78rem; color: #D46B08;">Buka Pengaturan Lanjutan untuk melihat detail atau mereset.</span>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_stepper(current_page: str = "Proyeksi Stand-Alone"):
    """Backward compatible alias."""
    render_stage_stepper(current_page)
