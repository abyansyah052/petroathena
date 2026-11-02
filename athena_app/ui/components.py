"""
Module ui/components.py: Reusable UI components according to UI/UX guidelines (uiux.md).
- KPI Cards with clean typography and optional delta/tooltip (single-line HTML to avoid Markdown indentation bugs)
- Compact Table with "Tampilkan semua kolom" toggle and full CSV download
- Dynamic Insight Callout (💡)
- Global Scenario Picker synced to st.session_state['selected_scenario']
- Stepper navigation indicator (① -> ⑦)
- Standardized footnote
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional


FOOTNOTE_TEXT = "Seluruh nilai dihitung dengan implementasi Python yang divalidasi 100% cocok terhadap 5 kombinasi pertama."


def render_footnote():
    """Renders the standard validated Python engine footnote."""
    st.caption(f"ℹ️ *{FOOTNOTE_TEXT}*")


def render_insight_callout(text: str):
    """
    Renders an automated, dynamic 1-2 sentence executive insight callout.
    Uses single-line HTML to prevent Markdown parser from treating indented text as code blocks.
    """
    html = (
        f'<div style="background: #EBF3FA; border-left: 4px solid #1E88E5; padding: 12px 18px; '
        f'border-radius: 6px; margin: 12px 0 16px 0; color: #0D1B2A; font-size: 0.95rem; '
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
    Uses single-line HTML to ensure zero leading indentation.
    """
    gold_border = "border: 2px solid #FFB300;" if is_gold else "border: 1px solid #E2E8F0;"
    gold_bg = "background: #FFFDF5;" if is_gold else "background: #FFFFFF;"
    delta_html = f'<div style="font-size: 0.8rem; color: #2E7D32; font-weight: 500; margin-top: 4px;">{delta}</div>' if delta else ""
    help_html = f' <span title="{help_text}" style="cursor: help; color: #757575; font-size: 0.8rem;">ⓘ</span>' if help_text else ""

    html = (
        f'<div style="{gold_bg} {gold_border} border-radius: 8px; padding: 14px 18px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); margin-bottom: 8px;">'
        f'<div style="font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #5A6A80; margin-bottom: 4px;">{label}{help_html}</div>'
        f'<div style="font-size: 1.65rem; font-weight: 700; color: #0D1B2A; font-feature-settings: \'tnum\'; font-variant-numeric: tabular-nums; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )
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
    Download CSV ALWAYS exports the full all_cols.
    """
    col_ctrl, col_dl = st.columns([1, 1])
    with col_ctrl:
        show_all = st.checkbox(
            f"Tampilkan semua kolom ({len(all_cols)} kolom)",
            value=False,
            key=f"{key_prefix}_show_all",
        )
    with col_dl:
        # Full CSV download
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

    # Formatter
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
        st.session_state["selected_price"] = 80


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
    label: str = "Pilih Skenario Fokus:",
    help_text: str = "Pilihan skenario ini tersinkronisasi otomatis di Tab 4, Tab 5, dan Tab 7.",
) -> int:
    """
    Renders a unified scenario picker connected to st.session_state['selected_scenario'].
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
    Renders a slim, non-clickable horizontal stage stepper (UI/UX Guidelines §9.3).
    Example: ○──●──○──○  Tahap 1 dari 3 · Model Finansial
    """
    stage_map = {
        "Kombinasi Strategi": (0, "Tahap 0 dari 3 · Data & Kombinasi"),
        "Hard Constraint": (0, "Tahap 0 dari 3 · Data & Kombinasi"),
        "Hard Constraint & Kompatibilitas": (0, "Tahap 0 dari 3 · Data & Kombinasi"),
        "Variabel Inti": (0, "Tahap 0 dari 3 · Data & Kombinasi"),
        "Proyeksi Stand-Alone": (1, "Tahap 1 dari 3 · Model Finansial"),
        "Skenario Farm-In": (1, "Tahap 1 dari 3 · Model Finansial"),
        "Ringkasan SA vs FI": (1, "Tahap 1 dari 3 · Model Finansial"),
        "Dampak Lingkungan": (2, "Tahap 2 dari 3 · Multi-Kriteria"),
        "Risiko (FMEA)": (2, "Tahap 2 dari 3 · Multi-Kriteria"),
        "Implementasi Teknis": (2, "Tahap 2 dari 3 · Multi-Kriteria"),
        "AHP & TOPSIS": (3, "Tahap 3 dari 3 · Keputusan"),
        "Pengaturan Lanjutan": (3, "Tahap 3 dari 3 · Generator Asumsi"),
    }
    stage_idx, stage_label = stage_map.get(current_page, (1, "Tahap 1 dari 3 · Model Finansial"))

    dots = []
    for i in range(4):
        if i == stage_idx:
            dots.append('<span style="color:#1E88E5;font-size:1.15rem;font-weight:700;">●</span>')
        else:
            dots.append('<span style="color:#94A3B8;font-size:1.15rem;">○</span>')
    stepper_visual = '<span style="color:#CBD5E1;margin:0 3px;">──</span>'.join(dots)

    html = (
        f'<div style="display:inline-flex;align-items:center;height:26px;padding:2px 14px;background:#FFFFFF;border-radius:14px;border:1px solid #E2E8F0;margin-bottom:12px;box-shadow:0 1px 2px rgba(0,0,0,0.02);">'
        f'<span style="margin-right:10px;line-height:1;">{stepper_visual}</span>'
        f'<span style="font-size:0.75rem;font-weight:600;color:#64748B;letter-spacing:0.3px;">{stage_label}</span>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_assumption_banner(diff_count: int):
    """
    Renders subtle orange banner at the top of content area (under stepper)
    ONLY when custom assumptions are active (UIUX Guidelines §10.5).
    """
    if diff_count <= 0:
        return
    html = (
        f'<div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 6px; '
        f'padding: 6px 14px; margin-bottom: 12px; font-size: 0.8rem; color: #92400E; display: flex; align-items: center; justify-content: space-between;">'
        f'<span>[PERHATIAN] <strong>Asumsi Kustom Aktif:</strong> Hasil di halaman ini memakai {diff_count} parameter yang disesuaikan dari acuan Excel V6.</span>'
        f'<span style="font-size: 0.75rem; color: #B45309;">(Lihat / Reset di menu Pengaturan Lanjutan)</span>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)



def render_stepper(current_page: str = "Proyeksi Stand-Alone"):
    """Backward compatible alias."""
    render_stage_stepper(current_page)

