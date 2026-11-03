"""
Module ui/stage2_secondary_recovery.py: Halaman Secondary Recovery (Tahap 2 · Simulasi Lanjutan).
Sesuai PRD Addendum v4.1 §6 dan UI/UX Guidelines §12.1.
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
    render_scenario_picker,
)
from athena_app.core.secondary_recovery import calculate_secondary_recovery


def render_stage2_secondary_recovery(engine_results: dict):
    st.subheader("10. Secondary Recovery & Analisis EOR")
    st.markdown(
        "*Evaluasi kebutuhan implementasi secondary recovery / EOR setelah kontrak awal 15 tahun (2026–2040) "
        "berakhir: pemilihan skema optimal, profil produksi tambahan, dan kelayakan keekonomian.*"
    )

    top10_sa = engine_results["top10_sa"]
    existing_data = engine_results.get("existing_data", {})
    sr_res = calculate_secondary_recovery(top10_sa, existing_data)

    kpi = sr_res["kpi"]
    summary = sr_res["summary"]
    schemes = sr_res["schemes"]
    annual_details = sr_res["annual_details"]

    # 1. Pertanyaan Strategis (Banner)
    st.info(
        "**Pertanyaan Strategis:** Setelah kontrak 15 tahun habis, perlukah secondary recovery / EOR? "
        "Skema apa yang paling efisien, dan apakah keekonomiannya layak pada harga minyak acuan?"
    )

    # 2. 4 Kartu KPI Utama
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            label="Kebutuhan Secondary Recovery",
            value=f"{kpi['n_need_sr']} / {kpi['total_scenarios']}",
            delta=f"Sisa cadangan > {kpi['gate_threshold_pct']:.0f}% 2P",
            help_text="Jumlah skenario yang memiliki sisa minyak di atas ambang setelah 15 tahun",
        )
    with k2:
        render_kpi_card(
            label="Komposisi Skema Terpilih",
            value="Infill (9)",
            delta=kpi["scheme_composition"],
            help_text="Skema paling murah yang cukup menyerap sisa cadangan minyak",
        )
    with k3:
        render_kpi_card(
            label="Tambah Kontrak SR",
            value=f"{kpi['extra_years_range']} thn",
            delta="Durasi operasional SR",
            help_text="Rentang tahun tambahan yang diperlukan untuk menyelesaikan produksi secondary recovery",
        )
    with k4:
        render_kpi_card(
            label="Skenario Layak Ekonomi",
            value=f"{kpi['n_feasible']} / {kpi['n_need_sr']}",
            delta=f"Pada harga {kpi['active_price']:.0f} USD/bbl",
            help_text="Jumlah skenario yang menghasilkan NPV tambahan inkremental positif",
        )

    # 3. Insight Callout (Template PRD §6.3)
    periode = int(existing_data.get("eval_period", 15))
    narrative = (
        f"Setelah kontrak awal <strong>{periode} tahun</strong>, <strong>{kpi['n_need_sr']} dari 10 strategi</strong> masih menyisakan "
        f"minyak di atas ambang <strong>{kpi['gate_threshold_pct']:.0f}%</strong> dari cadangan 2P, sehingga perlu secondary recovery. "
        f"Skema yang terpilih: <strong>{kpi['scheme_composition']}</strong>. Hanya <strong>{kpi['n_feasible']} di antaranya</strong> yang menghasilkan NPV "
        f"tambahan positif pada harga <strong>{kpi['active_price']:.0f} USD/bbl</strong>. Sisa minyak terbesar setelah secondary "
        f"recovery adalah <strong>{kpi['max_rem_oil_after']:,.0f} bbl</strong> dari cadangan 2P <strong>{kpi['reserve_2p']:,.0f} bbl</strong>."
    )
    render_insight_callout(narrative)

    # 4. Tabel Ringkasan (10 Skenario)
    st.markdown("#### Tabel Ringkasan Gate & Evaluasi Secondary Recovery Top-10")
    df_rows = []
    for r in summary:
        df_rows.append({
            "Rank SA": r["rank_sa"],
            "No": r["scenario_no"],
            "Skenario": r["name"],
            "Contingency Rate": f"{r['contingency_rate']:.4f}",
            "Produksi 15 th (bbl)": r["prod_15_bbl"],
            "Sisa 2P (bbl)": r["rem_oil_bbl"],
            "Sisa 2P (%)": f"{r['rem_oil_pct']*100:.2f}%",
            "Perlu SR?": r["need_sr"],
            "Skema Dipakai": r["scheme_used"],
            "CAPEX Tambahan (USD)": r["add_capex"],
            "OPEX Tambahan (USD)": r["add_opex"],
            "Lifting Tambahan (USD)": r["add_lifting"],
            "Tambah kontrak SR (th)": r["extra_contract_years"],
            "Produksi Tambahan (bbl)": r["add_prod_bbl"],
            "Total Produksi Akhir (bbl)": r["total_final_prod_bbl"],
            "Sisa Oil Pasca SR (bbl)": r["rem_oil_after_sr_bbl"],
            "NPV Awal 15 th (USD)": r["npv_initial_usd"],
            "NPV Tambahan SR (USD)": r["npv_sr_usd"],
            "New NPV Total (USD)": r["new_npv_total_usd"],
            "Kelayakan SR": r["econ_status"],
        })
    df_sr = pd.DataFrame(df_rows)

    core_cols = [
        "Rank SA", "Skenario", "Sisa 2P (%)", "Perlu SR?", "Skema Dipakai",
        "CAPEX Tambahan (USD)", "Tambah kontrak SR (th)", "Produksi Tambahan (bbl)",
        "NPV Tambahan SR (USD)", "Kelayakan SR"
    ]
    all_cols = list(df_sr.columns)

    fmt_sr = {
        "Produksi 15 th (bbl)": "{:,.0f}",
        "Sisa 2P (bbl)": "{:,.0f}",
        "CAPEX Tambahan (USD)": lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else str(x),
        "OPEX Tambahan (USD)": lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else str(x),
        "Lifting Tambahan (USD)": lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else str(x),
        "Produksi Tambahan (bbl)": lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else str(x),
        "Total Produksi Akhir (bbl)": "{:,.0f}",
        "Sisa Oil Pasca SR (bbl)": "{:,.0f}",
        "NPV Awal 15 th (USD)": "{:,.0f}",
        "NPV Tambahan SR (USD)": lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else str(x),
        "New NPV Total (USD)": "{:,.0f}",
    }

    render_compact_table(
        df=df_sr,
        core_cols=core_cols,
        all_cols=all_cols,
        download_filename="Athena_Secondary_Recovery_Analysis.csv",
        key_prefix="sr_table",
        height=380,
        format_dict=fmt_sr,
    )

    st.markdown("---")

    # 5. Visualisasi Analisis Secondary Recovery
    col_ch1, col_ch2 = st.columns(2)
    with col_ch1:
        st.markdown("##### Chart A: Akumulasi Produksi 15 Tahun vs Tambahan SR")
        labels_bar = [f"#{r['scenario_no']}" for r in summary]
        p15_vals = [r["prod_15_bbl"] / 1e6 for r in summary]
        psr_vals = [r["add_prod_bbl"] / 1e6 if isinstance(r["add_prod_bbl"], (int, float)) else 0.0 for r in summary]

        fig_prod = go.Figure()
        fig_prod.add_trace(go.Bar(
            x=labels_bar,
            y=p15_vals,
            name="Produksi 15 Tahun Awal",
            marker_color="#1E88E5",
        ))
        fig_prod.add_trace(go.Bar(
            x=labels_bar,
            y=psr_vals,
            name="Produksi Tambahan SR",
            marker_color="#43A047",
        ))
        fig_prod.add_hline(y=38.0, line_dash="dash", line_color="#D32F2F", annotation_text="Cadangan 2P (38 MMbbl)")
        fig_prod.update_layout(
            barmode="stack",
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=360,
            margin=dict(l=30, r=20, t=30, b=30),
            yaxis_title="Volume Produksi (MMbbl)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_prod, use_container_width=True)

    with col_ch2:
        st.markdown("##### Chart B: Dampak NPV Awal vs Tambahan SR")
        npv_init_vals = [r["npv_initial_usd"] / 1e6 for r in summary]
        npv_add_vals = [r["npv_sr_usd"] / 1e6 if isinstance(r["npv_sr_usd"], (int, float)) else 0.0 for r in summary]
        npv_tot_vals = [r["new_npv_total_usd"] / 1e6 for r in summary]

        fig_npv = go.Figure()
        fig_npv.add_trace(go.Bar(
            x=labels_bar,
            y=npv_init_vals,
            name="NPV Awal 15 Tahun",
            marker_color="#90CAF9",
        ))
        fig_npv.add_trace(go.Bar(
            x=labels_bar,
            y=npv_add_vals,
            name="NPV Tambahan SR",
            marker_color=["#E53935" if v < 0 else "#43A047" for v in npv_add_vals],
        ))
        fig_npv.update_layout(
            barmode="group",
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=360,
            margin=dict(l=30, r=20, t=30, b=30),
            yaxis_title="USD Juta",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_npv, use_container_width=True)

    # 6. Profil Detail Skenario (Picker Lokal)
    st.markdown("---")
    st.markdown("##### 🔍 Profil Produksi & Biaya Tahunan Secondary Recovery per Skenario")
    label_map_sr = {r["scenario_no"]: f"Skenario #{r['scenario_no']} (Rank SA {r['rank_sa']}) — {r['name']}" for r in summary}
    selected_sr_no = st.selectbox(
        "Pilih Skenario untuk Profil Detail SR:",
        options=[r["scenario_no"] for r in summary],
        format_func=lambda x: label_map_sr.get(x, f"#{x}"),
        key="sr_detail_picker",
    )

    if selected_sr_no in annual_details:
        ann = annual_details[selected_sr_no]
        cal_years = np.arange(2026, 2026 + 50)
        fig_ann = go.Figure()
        fig_ann.add_trace(go.Scatter(
            x=cal_years,
            y=ann["prod"] / 1e3,
            name="Produksi SR (kbbl/thn)",
            line=dict(color="#1E88E5", width=2.5),
            yaxis="y1",
        ))
        fig_ann.add_trace(go.Bar(
            x=cal_years,
            y=ann["capex"] / 1e6,
            name="Inkremental CAPEX (USD Juta)",
            marker_color="rgba(255, 179, 0, 0.4)",
            yaxis="y2",
        ))
        fig_ann.add_vline(x=2040, line_dash="dash", line_color="#757575", annotation_text="Akhir Kontrak Awal (2040)")
        fig_ann.update_layout(
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=380,
            yaxis=dict(title="Produksi Tambahan (kbbl/tahun)"),
            yaxis2=dict(title="CAPEX (USD Juta)", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=30, b=30),
        )
        st.plotly_chart(fig_ann, use_container_width=True)
    else:
        st.info("Skenario ini tidak memerlukan Secondary Recovery / EOR.")

    # 7. Expander Asumsi Skema (Read-only)
    with st.expander("⚙️ Parameter Skema Secondary Recovery (Workover, Infill, EOR)", expanded=False):
        st.caption("Nilai referensi dari Excel sheet '2.Secondary Recovery Analysis'. Disesuaikan di menu Pengaturan Lanjutan.")
        scheme_rows = []
        for sid, sc in schemes.items():
            scheme_rows.append({
                "Skema": sc["name"],
                "Metode": sc["method"],
                "Incremental RF": f"{sc['rf_selected']*100:.2f}%",
                "Incremental EUR (MMbbl)": f"{sc['eur']/1e6:.2f}",
                "Tahun Respons (S)": sc["S"],
                "Tahun Penuh (F)": sc["F"],
                "Decline": f"{sc['decline']*100:.1f}%",
                "Total CAPEX (USD Juta)": f"{sc['total_capex']/1e6:.2f}",
                "OPEX Tetap (USD/thn)": f"{sc['total_fixed_opex']:,.0f}",
                "Biaya Variabel (USD/bbl)": f"{sc['variable_cost']:.2f}",
            })
        st.dataframe(pd.DataFrame(scheme_rows), use_container_width=True, hide_index=True)

    render_footnote()

