"""
Module ui/stage2_contract_simulations.py: Halaman Simulasi Kontrak (Tahap 2 · Simulasi Lanjutan).
Sesuai PRD Addendum v4.1 §7 dan UI/UX Guidelines §12.2.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from athena_app.ui.components import (
    render_kpi_card,
    render_insight_callout,
    render_compact_table,
    render_footnote,
)
from athena_app.core.contract_simulations import calculate_contract_simulations


def render_stage2_contract_simulations(engine_results: dict):
    st.subheader("11. Simulasi Kontrak & Penipisan Cadangan 2P")
    st.markdown(
        "*Analisis forecast produksi jangka panjang (60 tahun) untuk memprediksi penipisan cadangan 2P, "
        "kebutuhan durasi perpanjangan kontrak, serta komparasi NPV antara Gross Split, Cost Recovery, dan Exit.*"
    )

    top10_sa = engine_results["top10_sa"]
    summary_rows = engine_results["summary_rows"]
    existing_data = engine_results.get("existing_data", {})

    cs_res = calculate_contract_simulations(top10_sa, summary_rows, existing_data)

    reserves_summary = cs_res["reserves_summary"]
    npv_summary = cs_res["npv_summary"]
    scenario_details = cs_res["scenario_details"]
    kpi = cs_res["kpi"]

    # 1. Pertanyaan Strategis (Banner)
    st.info(
        "**Pertanyaan Strategis:** Apakah cadangan 2P habis di dalam sisa kontrak 15 tahun? "
        "Kalau tidak, perpanjangan dengan skema apa yang memberikan NPV kontraktor tertinggi: "
        "Gross Split, Cost Recovery, atau Exit (jual cadangan)?"
    )

    # 2. Tiga Kartu KPI Utama
    k1, k2, k3 = st.columns(3)
    with k1:
        render_kpi_card(
            label="Habis dalam Kontrak Awal",
            value=f"{kpi['n_depleted_in_contract']} / 10",
            delta="Cadangan 2P belum habis di thn ke-15",
            help_text="Jumlah skenario yang cadangan 2P-nya habis sebelum atau tepat di tahun ke-15",
        )
    with k2:
        render_kpi_card(
            label="Perlu Perpanjangan Kontrak",
            value=f"{kpi['n_need_extension']} / 10",
            delta="Tambahan 2–6 tahun kontrak",
            help_text="Durasi perpanjangan yang dibutuhkan agar seluruh cadangan 2P terserap",
        )
    with k3:
        render_kpi_card(
            label="Skema Perpanjangan Terpilih",
            value=f"{kpi['top_choice']} (10)",
            delta="Memberi NPV Kontraktor Tertinggi",
            help_text="Skema kontrak dengan nilai NPV Base kontraktor paling optimal",
            is_gold=True,
        )

    # 3. Insight Callout (Template PRD §7.3)
    # Default ke skenario Rank SA 1
    selected_idx = 0
    sc_res = reserves_summary[selected_idx]
    sc_npv = npv_summary[selected_idx]

    stable_word = "tetap sama" if sc_npv["is_stable"] else f"berbeda (Low: {sc_npv['best_low']}, High: {sc_npv['best_high']})"
    narrative = (
        f"Dengan decline setelah intervensi, cadangan 2P <strong>#{sc_res['scenario_no']} ({sc_res['name']})</strong> "
        f"habis dalam <strong>{sc_res['years_to_deplete']:.2f} tahun</strong> (<strong>tahun {sc_res['cal_year_deplete']}</strong>), "
        f"atau <strong>{sc_res['extra_contract_years']} tahun</strong> setelah kontrak awal berakhir. "
        f"Untuk perpanjangan, <strong>{sc_npv['selected_scheme']}</strong> memberi NPV kontraktor tertinggi pada harga Base "
        f"(<strong>{sc_npv['gs_base']:,.0f} USD</strong>), dibanding Cost Recovery (<strong>{sc_npv['cr_base']:,.0f} USD</strong>) "
        f"dan Exit (<strong>{sc_npv['exit_base']:,.0f} USD</strong>). Pilihan ini <strong>{stable_word}</strong> pada harga Low dan High."
    )
    render_insight_callout(narrative)

    # 4. Tabel A: Ringkasan Cadangan & Penipisan 2P
    st.markdown("#### Tabel A — Penipisan Cadangan 2P & Horizon Kontrak Top-10")
    df_res_rows = []
    for r in reserves_summary:
        df_res_rows.append({
            "Rank SA": r["rank_sa"],
            "No": r["scenario_no"],
            "Skenario": r["name"],
            "Contingency Rate": f"{r['contingency_rate']:.4f}",
            "Decline Efektif (/thn)": f"{r['decline_eff']*100:.2f}%",
            "Laju Th-15 (bopd)": r["rate_15_bopd"],
            "Produksi 15 Th (bbl)": r["cum_15_bbl"],
            "Sisa 2P Pasca 15 Th (bbl)": r["rem_2p_15_bbl"],
            "Ultimate Recovery (bbl)": r["ult_rec_bbl"],
            "Tahun 2P Habis": r["years_to_deplete"],
            "Tahun Kalender": r["cal_year_deplete"],
            "Tambah kontrak sampai 2P habis (th)": r["extra_contract_years"],
            "Status Kontrak": r["contract_status"],
            "Jenis Perpanjangan": r["selected_scheme"],
        })
    df_res = pd.DataFrame(df_res_rows)

    core_res_cols = [
        "Rank SA", "Skenario", "Tahun 2P Habis", "Tahun Kalender",
        "Tambah kontrak sampai 2P habis (th)", "Status Kontrak", "Jenis Perpanjangan"
    ]
    all_res_cols = list(df_res.columns)

    fmt_res = {
        "Laju Th-15 (bopd)": "{:,.0f}",
        "Produksi 15 Th (bbl)": "{:,.0f}",
        "Sisa 2P Pasca 15 Th (bbl)": "{:,.0f}",
        "Ultimate Recovery (bbl)": "{:,.0f}",
        "Tahun 2P Habis": lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else str(x),
    }

    render_compact_table(
        df=df_res,
        core_cols=core_res_cols,
        all_cols=all_res_cols,
        download_filename="Athena_Contract_Reserves_Summary.csv",
        key_prefix="cs_res_table",
        height=320,
        format_dict=fmt_res,
    )

    # 5. Tabel B: Ringkasan NPV Kontraktor (3 Skema x 3 Kasus Harga)
    st.markdown("#### Tabel B — Perbandingan NPV Kontraktor Skema Kontrak (USD)")
    df_npv_rows = []
    for r in npv_summary:
        df_npv_rows.append({
            "Rank SA": r["rank_sa"],
            "No": r["scenario_no"],
            "Skenario": r["name"],
            "Gross Split Low": r["gs_low"],
            "Gross Split Base": r["gs_base"],
            "Gross Split High": r["gs_high"],
            "Cost Recovery Low": r["cr_low"],
            "Cost Recovery Base": r["cr_base"],
            "Cost Recovery High": r["cr_high"],
            "Exit Low": r["exit_low"],
            "Exit Base": r["exit_base"],
            "Exit High": r["exit_high"],
            "Pilihan Skema (Base)": r["selected_scheme"],
            "GS Base (DR 8%)": r["gs_base_low_dr"],
            "GS Base (DR 12%)": r["gs_base_high_dr"],
            "CR Base (DR 8%)": r["cr_base_low_dr"],
            "CR Base (DR 12%)": r["cr_base_high_dr"],
        })
    df_npv = pd.DataFrame(df_npv_rows)

    core_npv_cols = [
        "Rank SA", "Skenario", "Gross Split Base", "Cost Recovery Base", "Exit Base", "Pilihan Skema (Base)"
    ]
    all_npv_cols = list(df_npv.columns)

    fmt_npv = {
        "Gross Split Low": "{:,.0f}",
        "Gross Split Base": "{:,.0f}",
        "Gross Split High": "{:,.0f}",
        "Cost Recovery Low": "{:,.0f}",
        "Cost Recovery Base": "{:,.0f}",
        "Cost Recovery High": "{:,.0f}",
        "Exit Low": "{:,.0f}",
        "Exit Base": "{:,.0f}",
        "Exit High": "{:,.0f}",
        "GS Base (DR 8%)": "{:,.0f}",
        "GS Base (DR 12%)": "{:,.0f}",
        "CR Base (DR 8%)": "{:,.0f}",
        "CR Base (DR 12%)": "{:,.0f}",
    }

    render_compact_table(
        df=df_npv,
        core_cols=core_npv_cols,
        all_cols=all_npv_cols,
        download_filename="Athena_Contract_NPV_Comparison.csv",
        key_prefix="cs_npv_table",
        height=320,
        format_dict=fmt_npv,
    )

    st.markdown("---")

    # 6. Chart A: Grouped Bar NPV 3 Skema
    st.markdown("##### Chart A: Perbandingan NPV Kontraktor (Gross Split vs Cost Recovery vs Exit)")
    p_choice = st.radio("Tingkat Harga Minyak Ditampilkan:", ["Low (64$)", "Base (80$)", "High (117$)"], index=1, horizontal=True)
    p_key = "Base" if "Base" in p_choice else ("Low" if "Low" in p_choice else "High")

    labels_cs = [f"#{r['scenario_no']}" for r in npv_summary]
    gs_vals = [r[f"gs_{p_key.lower()}"] / 1e6 for r in npv_summary]
    cr_vals = [r[f"cr_{p_key.lower()}"] / 1e6 for r in npv_summary]
    exit_val = npv_summary[0][f"exit_{p_key.lower()}"] / 1e6

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Bar(
        x=labels_cs,
        y=gs_vals,
        name="Gross Split",
        marker_color="#1E88E5",
    ))
    fig_cmp.add_trace(go.Bar(
        x=labels_cs,
        y=cr_vals,
        name="Cost Recovery",
        marker_color="#43A047",
    ))
    fig_cmp.add_hline(
        y=exit_val,
        line_dash="dot",
        line_color="#E53935",
        annotation_text=f"Exit Strategy ({exit_val:.1f} M USD)",
        annotation_position="bottom right",
    )
    fig_cmp.update_layout(
        barmode="group",
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=360,
        yaxis_title="NPV Kontraktor (USD Juta)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=30, r=20, t=30, b=30),
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

    # 7. Detail Skenario Terpilih (Picker Lokal): Waterfall & Kumulatif vs 2P
    st.markdown("---")
    st.markdown("##### 🔍 Analisis Detail Aliran Kas & Kurva Penipisan 2P Skenario Terpilih")
    label_map_cs = {r["scenario_no"]: f"Skenario #{r['scenario_no']} (Rank SA {r['rank_sa']}) — {r['name']}" for r in npv_summary}
    selected_cs_no = st.selectbox(
        "Pilih Skenario untuk Detail Kontrak:",
        options=[r["scenario_no"] for r in npv_summary],
        format_func=lambda x: label_map_cs.get(x, f"#{x}"),
        key="cs_detail_picker",
    )

    detail = scenario_details[selected_cs_no]
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.markdown(f"###### Kurva Penipisan Kumulatif Produksi 60 Tahun vs Cadangan 2P (#{selected_cs_no})")
        years_60 = np.arange(2026, 2026 + 60)
        fig_cum = go.Figure()
        fig_cum.add_trace(go.Scatter(
            x=years_60,
            y=detail["cum_60"] / 1e6,
            name="Kumulatif Produksi",
            line=dict(color="#1E88E5", width=2.5),
        ))
        fig_cum.add_hline(y=38.0, line_dash="dash", line_color="#D32F2F", annotation_text="Cadangan 2P (38 MMbbl)")
        fig_cum.add_vline(x=2040, line_dash="dot", line_color="#757575", annotation_text="Akhir Kontrak 15 Th (2040)")

        # Ambil tahun habis skenario ini
        sc_info = next(r for r in reserves_summary if r["scenario_no"] == selected_cs_no)
        if sc_info["cal_year_deplete"] != "-":
            fig_cum.add_vline(
                x=sc_info["cal_year_deplete"],
                line_dash="dashdot",
                line_color="#43A047",
                annotation_text=f"2P Habis ({sc_info['cal_year_deplete']})",
            )

        fig_cum.update_layout(
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=340,
            yaxis_title="Produksi Kumulatif (MMbbl)",
            margin=dict(l=30, r=20, t=30, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_cum, use_container_width=True)

    with col_d2:
        st.markdown(f"###### Waterfall Pembagian Hasil Gross Split (@80$ USD/bbl) (#{selected_cs_no})")
        prod_tot = np.sum(detail["prod_15"])
        rev_tot = prod_tot * 80.0
        gov_share = rev_tot * 0.45
        c_share = rev_tot * 0.55
        c_opex = np.sum(detail["opex_15"])
        c_capex = np.sum(detail["capex_15"])
        taxable = c_share - c_opex - c_capex
        c_tax = taxable * 0.40
        c_take = taxable - c_tax

        fig_wf = go.Figure(go.Waterfall(
            name="Gross Split Waterfall",
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "total"],
            x=["Gross Revenue", "Bag. Pemerintah", "Total OPEX", "Total CAPEX & Pajak", "Kontraktor Take"],
            textposition="outside",
            text=[f"{rev_tot/1e6:.1f}M", f"-{gov_share/1e6:.1f}M", f"-{c_opex/1e6:.1f}M", f"-{(c_capex+c_tax)/1e6:.1f}M", f"{c_take/1e6:.1f}M"],
            y=[rev_tot/1e6, -gov_share/1e6, -c_opex/1e6, -(c_capex+c_tax)/1e6, 0],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))
        fig_wf.update_layout(
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=340,
            yaxis_title="USD Juta",
            margin=dict(l=30, r=20, t=30, b=30),
        )
        st.plotly_chart(fig_wf, use_container_width=True)

    render_footnote()

