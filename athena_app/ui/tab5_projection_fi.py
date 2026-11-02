"""
UI Tab 5: Financial Projection (Farm-In), Top-10 (uiux.md compliant)
Tujuan: "Kalau Top-10 skenario itu dikerjakan bareng partner (XYZ) dengan skema carry 70%, bagaimana hasilnya buat PNE vs XYZ?"
"""

import streamlit as st
import pandas as pd
import numpy as np
from athena_app.ui.components import (
    render_kpi_card,
    render_insight_callout,
    render_compact_table,
    render_scenario_picker,
    render_footnote,
    get_selected_scenario,
    set_selected_scenario,
)
from athena_app.ui.charts import create_farmin_top10_chart, create_farmin_rank_breakdown_chart


def render_tab5(engine_results: dict):
    st.subheader("5. Financial Projection (Farm-In) — Top 10 Skenario")
    st.markdown(
        "*Evaluasi dampak skema kemitraan Farm-In bersama Partner XYZ (60% PNE : 40% XYZ, 70% Treatment Carry) pada Top-10 skenario.*"
    )

    df_tab5 = engine_results["df_tab5"]
    top10_fi = engine_results["top10_fi"]
    sa_scenarios = engine_results["sa_scenarios"]

    # 1. Scenario Picker khusus Top-10 (membawa pilihan dari Tab 4)
    top10_nos = [fi["no_kombinasi"] for fi in top10_fi]
    current_selected = get_selected_scenario()
    if current_selected not in top10_nos:
        # Default ke Rank FI 1
        best_fi_default = sorted(top10_fi, key=lambda x: x["rank_fi"])[0]["no_kombinasi"]
        set_selected_scenario(best_fi_default)

    label_map_fi = {
        fi["no_kombinasi"]: f"Skenario #{fi['no_kombinasi']} (SA Rank {fi['rank_sa']} | FI Rank {fi['rank_fi']}) — {fi['kombinasi']}"
        for fi in top10_fi
    }

    st.markdown("##### 🎯 Pilih Skenario Top-10 Fokus:")
    selected_fi_no = render_scenario_picker(
        options=top10_nos,
        label_map=label_map_fi,
        key="tab5_scenario_picker",
        label="Skenario Fokus Farm-In (Tersinkronisasi dari Tab 4):",
    )

    selected_fi = next(fi for fi in top10_fi if fi["no_kombinasi"] == selected_fi_no)
    matching_sa = next(s for s in sa_scenarios if s["no"] == selected_fi_no)

    # 2. Empat Kartu KPI Skenario Terpilih (uiux.md §4 Tab 5)
    npv_pne_80 = selected_fi["prices"][80]["npv10_pne"] / 1e6
    npv_xyz_80 = selected_fi["prices"][80]["npv10_xyz"] / 1e6

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            label="Peringkat Farm-In (RANK FI)",
            value=f"Rank #{selected_fi['rank_fi']}",
            delta=f"Rank Stand-Alone: #{selected_fi['rank_sa']}",
            help_text="Peringkat di antara Top-10 berdasarkan evaluasi 30 metrik finansial Farm-In",
            is_gold=(selected_fi["rank_fi"] == 1),
        )
    with k2:
        render_kpi_card(
            label="Skor Farm-In (30 Metrik)",
            value=f"{selected_fi['skor_fi']:.4f}",
            delta=f"Skenario #{selected_fi_no}",
            help_text="Rata-rata 30 peringkat metrik (10 metrik finansial PNE & XYZ di 3 tingkat harga)",
        )
    with k3:
        render_kpi_card(
            label="NPV,10% PNE @80$",
            value=f"{npv_pne_80:,.2f} M USD",
            delta="60% WI (PNE)",
            help_text="Net Present Value untuk PT PNE setelah memperhitungkan 70% carry capex treatment awal",
        )
    with k4:
        render_kpi_card(
            label="NPV,10% XYZ @80$",
            value=f"{npv_xyz_80:,.2f} M USD",
            delta="40% WI (XYZ)",
            help_text="Net Present Value untuk Partner XYZ dengan imbalan menanggung 70% capex treatment awal",
        )

    # 3. 💡 Automated Insight Callout (uiux.md §4 Tab 5)
    sa_npv10_80 = matching_sa["metrics"]["prices"][80]["npv10"]
    sa_cpx = matching_sa["flows"]["total_cpx"]
    pne_cpx = selected_fi["cpx_pne"]
    pct_npv_retained = (selected_fi["prices"][80]["npv10_pne"] / sa_npv10_80) * 100
    pct_cpx_saved = ((sa_cpx - pne_cpx) / sa_cpx) * 100

    insight_fi_text = (
        f"Dengan skema Farm-In, untuk Skenario <strong>#{selected_fi_no} ({selected_fi['kombinasi']})</strong>, "
        f"PT PNE mempertahankan <strong>{pct_npv_retained:.1f}%</strong> dari NPV Stand-Alone "
        f"({npv_pne_80:,.2f}M vs {sa_npv10_80/1e6:,.2f}M USD) sambil memangkas kebutuhan modal sendiri sebesar "
        f"<strong>{pct_cpx_saved:.1f}%</strong> ({pne_cpx/1e6:,.2f}M vs {sa_cpx/1e6:,.2f}M USD)."
    )
    render_insight_callout(insight_fi_text)

    # 4. Chart Utama: Grouped Bar NPV,10 PNE vs XYZ untuk 10 skenario dengan radio harga
    st.markdown("---")
    sel_chart_price = st.radio(
        "Tingkat Harga Minyak untuk Diagram Farm-In:",
        options=[64, 80, 117],
        index=1,
        horizontal=True,
        format_func=lambda x: f"{x}$ USD/bbl",
        key="tab5_chart_price",
    )
    fig_fi_bar = create_farmin_top10_chart(top10_fi, price=sel_chart_price)
    st.plotly_chart(fig_fi_bar, use_container_width=True)

    # Expander Transparansi Skor Farm-In (30 Metrik)
    with st.expander(f"🔍 Transparansi Skor Farm-In: Rincian 30 Peringkat Metrik Skenario #{selected_fi_no}", expanded=False):
        st.markdown(
            "Pemeringkatan Farm-In dihitung secara transparan dari rata-rata **30 peringkat metrik finansial** "
            "(15 metrik untuk PT PNE dan 15 metrik untuk Partner XYZ pada harga 64$, 80$, dan 117$ USD/bbl)."
        )
        st.plotly_chart(create_farmin_rank_breakdown_chart(selected_fi), use_container_width=True)

    st.markdown("---")

    # 5. Tabel Ringkas Farm-In (uiux.md §4 Tab 5: <=12 kolom di layar)
    st.markdown("#### Tabel Master Analisis Finansial Farm-In (Top-10)")
    st.caption(
        "Tabel menampilkan komparasi pembagian modal (CAPEX) dan profitabilitas (NPV, IRR) antara PNE dan XYZ."
    )

    core_fi_cols = [
        "No",
        "Kombinasi",
        "Total CAPEX -> PNE",
        "Total CAPEX -> XYZ",
        f"{sel_chart_price}$ NPV,10 PNE",
        f"{sel_chart_price}$ NPV,10 XYZ",
        f"{sel_chart_price}$ IRR PNE",
        f"{sel_chart_price}$ IRR XYZ",
        "Rata-rata rank",
        "RANK (1 = terbaik)",
    ]
    all_fi_cols = list(df_tab5.columns)

    fmt_fi = {
        "Contingency Rate": "{:.4f}",
        "Total Production": "{:,.0f} bbl",
        "Remaining Oil": "{:,.0f} bbl",
        "Total Water": "{:,.0f} bbl",
        "Total CAPEX -> PNE": "{:,.0f} $",
        "Total CAPEX -> XYZ": "{:,.0f} $",
        "Total OPEX -> PNE": "{:,.0f} $",
        "Total OPEX -> XYZ": "{:,.0f} $",
        "Rata-rata rank": "{:.4f}",
    }
    for P in [64, 80, 117]:
        for partner in ["PNE", "XYZ"]:
            fmt_fi[f"{P}$ {partner} Take"] = "{:,.0f} $"
            fmt_fi[f"{P}$ NPV,8 {partner}"] = "{:,.0f} $"
            fmt_fi[f"{P}$ NPV,10 {partner}"] = "{:,.0f} $"
            fmt_fi[f"{P}$ NPV,12 {partner}"] = "{:,.0f} $"
        fmt_fi[f"{P}$ Gov. Take"] = "{:,.0f} $"

    df_view_fi = df_tab5.copy()
    for P in [64, 80, 117]:
        for partner in ["PNE", "XYZ"]:
            c_irr = f"{P}$ IRR {partner}"
            df_view_fi[c_irr] = df_view_fi[c_irr].apply(
                lambda x: f"{float(x)*100:.2f}%" if isinstance(x, (int, float)) and np.isfinite(x) else str(x)
            )

    render_compact_table(
        df=df_view_fi,
        core_cols=core_fi_cols,
        all_cols=all_fi_cols,
        download_filename="Athena_Tab5_Financial_Projection_FarmIn_Top10.csv",
        key_prefix="tab5_table",
        height=400,
        format_dict=fmt_fi,
    )

    render_footnote()
