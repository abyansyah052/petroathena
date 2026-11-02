"""
Module ui/stage2_technical.py: Halaman Implementasi Teknis T1-T5 (Tahap 2 · Multi-Kriteria).
Menyajikan skor teknis: Kecocokan Reservoir (T1), Kematangan TRL (T2),
Kompleksitas (T3), Durabilitas (T4), dan Skalabilitas Sumur (T5) untuk Top-10 SA.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from athena_app.ui.components import (
    render_kpi_card,
    render_insight_callout,
    render_footnote,
    render_compact_table,
)
from athena_app.core.technical import calculate_all_top10_technical


def render_stage2_technical(engine_results: dict):
    st.subheader("9. Implementasi Teknis (Kriteria T1–T5)")
    st.markdown(
        "*Audit kelayakan teknis lapangan Athena: Kecocokan Reservoir & Masalah Air (T1), "
        "Kematangan Teknologi & Rekam Jejak (T2), Kompleksitas Operasional (T3), "
        "Durabilitas terhadap Umur Fasilitas 5 Tahun (T4), dan Skalabilitas Sumur (T5).*"
    )

    top10_sa = engine_results["top10_sa"]
    ed = engine_results.get("existing_data")
    tech_data = calculate_all_top10_technical(top10_sa, config=ed)

    avg_t1 = np.mean([t["t1"] for t in tech_data])
    avg_t2 = np.mean([t["t2"] for t in tech_data])
    avg_t4 = np.mean([t["t4"] for t in tech_data])
    avg_t5 = np.mean([t["t5"] for t in tech_data])

    # 1. Empat KPI Card
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            label="Kecocokan Reservoir (T1)",
            value=f"{avg_t1:.2f} / 5.0",
            delta="Rata-rata Top-10 (Aquifer Drive & Hetero)",
            help_text="T1: Rata-rata kecocokan metode terhadap reservoir kuat",
        )
    with k2:
        render_kpi_card(
            label="Kematangan Teknologi (T2)",
            value=f"{avg_t2:.2f} / 5.0",
            delta="Batas Terlemah (Minimum)",
            help_text="T2: Mengambil TRL terendah dalam kombinasi sebagai bottleneck",
        )
    with k3:
        render_kpi_card(
            label="Durabilitas Fasilitas (T4)",
            value=f"{avg_t4:.2f} / 5.0",
            delta=f"Umur Rata-rata: {np.mean([t['effective_life_yr'] for t in tech_data]):.1f} thn",
            help_text="T4: Ketahanan perlakuan terhadap sisa umur fasilitas 5 tahun",
        )
    with k4:
        render_kpi_card(
            label="Skalabilitas Sumur (T5)",
            value=f"{avg_t5:.2f} / 5.0",
            delta=f"Cakupan: {np.mean([t['wells_covered'] for t in tech_data]):.1f} / 145 sumur",
            help_text="T5: Jumlah sumur aktif & idle yang layak di-treat",
            is_gold=True,
        )

    # 2. Automated Insight Callout
    top1 = tech_data[0]
    insight_text = (
        f"Skenario <strong>#{top1['no']} ({top1['name']})</strong> menonjol dengan skor Durabilitas <strong>T4 = {top1['t4']:.2f}</strong> "
        f"(umur perlakuan rata-rata {top1['effective_life_yr']:.1f} tahun) dan Skalabilitas <strong>T5 = {top1['t5']:.2f}</strong> "
        f"yang mampu menjangkau <strong>{top1['wells_covered']:.1f} dari 145 sumur</strong>. "
        f"Penerapan metode mekanis (Bridge Plug + Re-perforation) memberikan keunggulan eksekusi (T3 = 4.0) tanpa dependensi bahan kimia cair."
    )
    render_insight_callout(insight_text)

    # 3. Chart 1: Grouped Bar Skor T1–T5 untuk 10 Skenario
    labels = [f"Rank SA #{t['rank_sa']}<br>#{t['no']}" for t in tech_data]
    fig_pillars = go.Figure()
    fig_pillars.add_trace(go.Bar(x=labels, y=[t["t1"] for t in tech_data], name="T1 Kecocokan", marker_color="#1E88E5"))
    fig_pillars.add_trace(go.Bar(x=labels, y=[t["t2"] for t in tech_data], name="T2 Kematangan", marker_color="#00897B"))
    fig_pillars.add_trace(go.Bar(x=labels, y=[t["t3"] for t in tech_data], name="T3 Kompleksitas", marker_color="#D97706"))
    fig_pillars.add_trace(go.Bar(x=labels, y=[t["t4"] for t in tech_data], name="T4 Durabilitas", marker_color="#7C3AED"))
    fig_pillars.add_trace(go.Bar(x=labels, y=[t["t5"] for t in tech_data], name="T5 Skalabilitas", marker_color="#059669"))

    fig_pillars.update_layout(
        barmode="group",
        title="<b>Perbandingan 5 Dimensi Evaluasi Teknis (Skala 1.0–5.0)</b>",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFAFC",
        height=380,
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis=dict(title="Skor Teknis (1-5)", range=[0, 5.5]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_pillars, use_container_width=True)

    # 4. Chart 2: Dual Axis Umur Efektif vs Sumur Tercakup
    fig_dual = go.Figure()
    fig_dual.add_trace(go.Bar(
        x=labels,
        y=[t["effective_life_yr"] for t in tech_data],
        name="Umur Efektif Perlakuan (Tahun)",
        marker_color="#2563EB",
        yaxis="y1",
    ))
    fig_dual.add_trace(go.Scatter(
        x=labels,
        y=[t["wells_covered"] for t in tech_data],
        name="Sumur Tercakup (Wells)",
        marker=dict(color="#FFB300", size=10),
        line=dict(color="#FFB300", width=2.5),
        mode="lines+markers",
        yaxis="y2",
    ))
    fig_dual.update_layout(
        title="<b>Umur Efektif Perlakuan vs Jumlah Sumur Terjangkau (Aktif + Idle)</b>",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFAFC",
        height=350,
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis=dict(title="Umur Efektif (Tahun)", side="left", range=[0, 6]),
        yaxis2=dict(title="Jumlah Sumur", side="right", overlaying="y", range=[100, 155]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_dual, use_container_width=True)

    # 5. Tabel Ringkas Teknis
    st.markdown("#### Tabel Evaluasi Parameter Teknis Top-10 Stand-Alone")
    st.caption("Nilai dinormalisasi dalam rentang 1.0 (terendah) hingga 5.0 (tertinggi).")

    df_tech = pd.DataFrame([
        {
            "Rank SA": t["rank_sa"],
            "Nomor": t["no"],
            "Strategi": t["name"],
            "p Gabungan": f"{t['p_gabungan']*100:.1f}%",
            "Jml Metode": t["n_methods"],
            "T1 Kecocokan": t["t1"],
            "T2 Kematangan": t["t2"],
            "T3 Kompleksitas": t["t3"],
            "T4 Durabilitas": t["t4"],
            "T5 Skalabilitas": t["t5"],
            "Umur Efektif (th)": t["effective_life_yr"],
            "Sumur Tercakup": t["wells_covered"],
            "NPV10@80 (M USD)": t["npv10_80"],
        }
        for t in tech_data
    ])

    core_cols = [
        "Rank SA", "Strategi", "p Gabungan", "Jml Metode",
        "T1 Kecocokan", "T2 Kematangan", "T3 Kompleksitas", "T4 Durabilitas", "T5 Skalabilitas"
    ]
    all_cols = list(df_tech.columns)

    fmt_tech = {
        "T1 Kecocokan": "{:.2f}",
        "T2 Kematangan": "{:.3f}",
        "T3 Kompleksitas": "{:.1f}",
        "T4 Durabilitas": "{:.2f}",
        "T5 Skalabilitas": "{:.3f}",
        "Umur Efektif (th)": "{:.1f}",
        "Sumur Tercakup": "{:.1f}",
        "NPV10@80 (M USD)": "{:,.2f}",
    }

    render_compact_table(
        df=df_tech,
        core_cols=core_cols,
        all_cols=all_cols,
        download_filename="Athena_Technical_Implementation_Top10.csv",
        key_prefix="tech_table",
        height=400,
        format_dict=fmt_tech,
    )

    # Expander Rubrik
    with st.expander("📖 Rubrik Penilaian Kualitatif T1–T5 (PRD Addendum §4.2)", expanded=False):
        st.markdown(
            "- **T1 (Kecocokan Reservoir):** Skor 1–5 berdasarkan kesesuaian mekanisme aquifer drive dan heterogenitas tinggi (Rata-rata metode).\n"
            "- **T2 (Kematangan TRL):** Skor 1–5 berbasis skala TRL (0–7) dan rekam jejak implementasi di Indonesia (Bottleneck: Minimum metode).\n"
            "- **T3 (Kompleksitas Operasional):** Skor 1–5 menilai ketiadaan bahan kimia berbahaya, eksekusi satu langkah, ketersediaan alat lokal, dan tanpa prasyarat diagnosis rumit (Minimum metode).\n"
            "- **T4 (Durabilitas vs Fasilitas):** Normalisasi umur perlakuan terhadap sisa umur fasilitas 5 tahun: $1 + 4 \\times \\min(\\text{umur}/5, 1)$.\n"
            "- **T5 (Skalabilitas Sumur):** Normalisasi rasio sumur aktif dan idle yang dapat di-treat terhadap 145 sumur: $1 + 4 \\times (\\text{sumur}/145)$."
        )

    render_footnote()
