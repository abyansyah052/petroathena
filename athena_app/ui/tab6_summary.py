"""
UI Tab 6: Financial Summary (SA vs Farm-In, Top-10) (uiux.md compliant)
Titik Keputusan #2: "Standalone atau Farm-In — mana yang dipilih, dan apa trade-off-nya?"
"""

import streamlit as st
import pandas as pd
import numpy as np
from athena_app.ui.components import (
    render_insight_callout,
    render_compact_table,
    render_footnote,
)
from athena_app.ui.charts import create_summary_3party_chart


def render_tab6(engine_results: dict):
    st.subheader("6. Financial Summary (Stand-Alone vs Farm-In) ★")
    st.markdown(
        "*Keputusan Strategis: Mengevaluasi trade-off nilai absolut Stand-Alone (100% PNE) "
        "vs mitigasi risiko modal Farm-In (60% PNE : 40% XYZ dengan 70% Treatment Carry).* "
    )

    df_tab6 = engine_results["df_tab6"]
    top10_sa = engine_results["top10_sa"]
    top10_fi = engine_results["top10_fi"]

    # 1. Radio Harga Minyak di Atas Sendiri (uiux.md §4 Tab 6: kontrol utama tunggal)
    col_p, _ = st.columns([1, 1])
    with col_p:
        active_price = st.radio(
            "Tingkat Harga Minyak Acuan Evaluasi:",
            options=[64, 80, 117],
            index=1,
            horizontal=True,
            format_func=lambda x: f"{x}$ USD/bbl ({'Base' if x==80 else 'Low' if x==64 else 'High'})",
            key="tab6_active_price",
        )

    # 2. 💡 Automated Insight Callout (uiux.md §4 Tab 6)
    s1 = top10_sa[0]
    fi1 = next(fi for fi in top10_fi if fi["no_kombinasi"] == s1["no"])

    cpx_sa = s1["flows"]["total_cpx"]
    cpx_pne = fi1["cpx_pne"]
    pct_capex_cut = ((cpx_sa - cpx_pne) / cpx_sa) * 100

    npv_sa = s1["metrics"]["prices"][active_price]["npv10"]
    npv_pne = fi1["prices"][active_price]["npv10_pne"]
    pct_npv_cut = ((npv_sa - npv_pne) / npv_sa) * 100

    irr_sa = s1["metrics"]["prices"][active_price]["irr"]
    irr_pne = fi1["prices"][active_price]["irr_pne"]
    irr_sa_str = f"{irr_sa*100:.2f}%" if isinstance(irr_sa, (int, float)) else str(irr_sa)
    irr_pne_str = f"{irr_pne*100:.2f}%" if isinstance(irr_pne, (int, float)) else str(irr_pne)

    insight_summary_text = (
        f"Untuk skenario rekomendasi <strong>Rank 1 (#{s1['no']} {s1['kombinasi']})</strong> pada harga {active_price}$ USD/bbl, "
        f"skema Farm-In memangkas kebutuhan CAPEX PT PNE sebesar <strong>{pct_capex_cut:.1f}%</strong> "
        f"({cpx_pne/1e6:,.2f}M vs {cpx_sa/1e6:,.2f}M USD) dengan konsekuensi NPV,10% PNE berkurang "
        f"<strong>{pct_npv_cut:.1f}%</strong> ({npv_pne/1e6:,.2f}M vs {npv_sa/1e6:,.2f}M USD). "
        f"Namun, efisiensi per modal meningkat tajam di mana IRR PNE bergerak dari <strong>{irr_sa_str}</strong> "
        f"menjadi <strong>{irr_pne_str}</strong> berkat penanggungan 70% capex treatment oleh partner."
    )
    render_insight_callout(insight_summary_text)

    # 3. Grouped Bar 3-Pihak: SA vs PNE vs XYZ
    st.markdown("---")
    fig_3party = create_summary_3party_chart(df_tab6, price=active_price)
    st.plotly_chart(fig_3party, use_container_width=True)

    st.markdown("---")

    # 4. Toggle Urutan & Tabel Ringkas Komparasi Eksekutif (uiux.md §4 Tab 6: <=12 kolom)
    st.markdown("#### Tabel Komparasi Eksekutif (Top-10 Skenario)")
    sort_mode = st.radio(
        "Urutkan Tabel Berdasarkan:",
        options=["Peringkat Stand-Alone (RANK SA)", "Peringkat Farm-In (RANK FI)"],
        horizontal=True,
        key="tab6_sort_toggle",
    )

    display_df = df_tab6.copy()
    if "Farm-In" in sort_mode:
        display_df = display_df.sort_values("RANK (1 = terbaik)")
    else:
        display_df = display_df.sort_values("No")

    core_cols = [
        "No",
        "Kombinasi",
        "CAPEX SA",
        "CAPEX PNE",
        "CAPEX XYZ",
        f"{active_price}$ NPV,10 SA",
        f"{active_price}$ NPV,10 PNE",
        f"{active_price}$ NPV,10 XYZ",
        f"{active_price}$ IRR SA",
        f"{active_price}$ IRR PNE",
        f"{active_price}$ IRR XYZ",
        "RANK (1 = terbaik)",
    ]
    all_cols = list(df_tab6.columns)

    fmt_summary = {
        "Contingency Rate": "{:.4f}",
        "Total Production": "{:,.0f} bbl",
        "CAPEX SA": "{:,.0f} $",
        "CAPEX PNE": "{:,.0f} $",
        "CAPEX XYZ": "{:,.0f} $",
        "OPEX SA": "{:,.0f} $",
        "OPEX PNE": "{:,.0f} $",
        "OPEX XYZ": "{:,.0f} $",
    }
    for P in [64, 80, 117]:
        fmt_summary[f"{P}$ NPV,10 SA"] = "{:,.0f} $"
        fmt_summary[f"{P}$ NPV,10 PNE"] = "{:,.0f} $"
        fmt_summary[f"{P}$ NPV,10 XYZ"] = "{:,.0f} $"
        fmt_summary[f"{P}$ Take SA"] = "{:,.0f} $"
        fmt_summary[f"{P}$ Take PNE"] = "{:,.0f} $"
        fmt_summary[f"{P}$ Take XYZ"] = "{:,.0f} $"
        fmt_summary[f"{P}$ Gov. Take FI"] = "{:,.0f} $"

    df_view_summary = display_df.copy()
    for P in [64, 80, 117]:
        for entity in ["SA", "PNE", "XYZ"]:
            col_irr = f"{P}$ IRR {entity}"
            df_view_summary[col_irr] = df_view_summary[col_irr].apply(
                lambda x: f"{float(x)*100:.2f}%" if isinstance(x, (int, float)) and np.isfinite(x) else str(x)
            )

    render_compact_table(
        df=df_view_summary,
        core_cols=core_cols,
        all_cols=all_cols,
        download_filename="Athena_Tab6_Financial_Summary_Comparison.csv",
        key_prefix="tab6_table",
        height=420,
        format_dict=fmt_summary,
    )

    render_footnote()
