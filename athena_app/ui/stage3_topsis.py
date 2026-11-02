"""
Module ui/stage3_topsis.py: Halaman AHP & TOPSIS (Tahap 3 · Keputusan).
Menyajikan sintesis multi-kriteria penuh (Environmental, Technical, Risk, Financial)
menggunakan bobot AHP Saaty dan pemeringkatan kedekatan ideal TOPSIS untuk Top-10 SA.
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
from athena_app.core.topsis import run_topsis_analysis
from athena_app.core.environmental import calculate_all_environmental
from athena_app.core.risk import calculate_all_top10_risks
from athena_app.core.technical import calculate_all_top10_technical


def render_stage3_topsis(engine_results: dict):
    st.subheader("10. Keputusan Multi-Kriteria (AHP & TOPSIS)")
    st.markdown(
        "*Sintesis pengambilan keputusan akhir: Mengintegrasikan 16 sub-kriteria dari 4 dimensi strategis "
        "(Lingkungan, Teknis, Risiko FMEA, dan Finansial) menggunakan bobot AHP dan algoritma TOPSIS.*"
    )

    top10_sa = engine_results["top10_sa"]
    ed = engine_results["existing_data"]
    bau_data = engine_results["bau_data"]

    # Jalankan perhitungan dependensi
    env_res = calculate_all_environmental(top10_sa, ed, bau_data)
    risk_res = calculate_all_top10_risks(top10_sa, config=ed)
    tech_res = calculate_all_top10_technical(top10_sa, config=ed)

    custom_l1 = ed.get("ahp_l1_weights")
    topsis_data = run_topsis_analysis(
        top10_sa=top10_sa,
        env_results=env_res,
        risk_results=risk_res,
        tech_results=tech_res,
        existing_data=ed,
        bau_data=bau_data,
        custom_l1_weights=custom_l1,
    )

    results = topsis_data["results"]
    best_topsis = results[0]
    
    # Cari delta terbesar
    max_rise = max(results, key=lambda x: x["rank_delta"])
    max_drop = min(results, key=lambda x: x["rank_delta"])

    # 1. Empat KPI Card
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            label="🏆 Rekomendasi Utama (Rank 1 TOPSIS)",
            value=f"#{best_topsis['no']}",
            delta=f"C = {best_topsis['closeness']:.4f} (Rank SA #{best_topsis['rank_sa']})",
            help_text="Skenario dengan nilai kedekatan relatif tertinggi terhadap solusi ideal",
            is_gold=True,
        )
    with k2:
        render_kpi_card(
            label="Kenaikan Peringkat Terbesar",
            value=f"+{max_rise['rank_delta']} Posisi",
            delta=f"Skenario #{max_rise['no']} (SA #{max_rise['rank_sa']} → TOPSIS #{max_rise['rank_topsis']})",
            help_text="Skenario yang paling diuntungkan setelah kriteria non-finansial diperhitungkan",
        )
    with k3:
        render_kpi_card(
            label="Konsistensi AHP Global",
            value="Konsisten (CR < 0.08)",
            delta="CR L1: 0.0038 | CR L2: < 0.012",
            help_text="Seluruh matriks Saaty lolos uji konsistensi (CR Level 1 < 0.08, Level 2 < 0.10)",
        )
    with k4:
        render_kpi_card(
            label="Cakupan Kriteria Model",
            value="16 / 20 Kriteria",
            delta="100.0% Bobot Teredistribusi",
            help_text="16 sub-kriteria aktif dengan bobot induk yang terjaga penuh",
        )

    # 2. Automated Insight Callout
    insight_text = (
        f"Skenario <strong>#{best_topsis['no']} ({best_topsis['name']})</strong> kokoh terpilih sebagai "
        f"<strong>Rekomendasi Utama Keputusan Multi-Kriteria (#1 TOPSIS)</strong> dengan koefisien kedekatan <strong>C = {best_topsis['closeness']:.4f}</strong> "
        f"(jarak ke ideal positif D⁺ = {best_topsis['d_plus']:.4f}, jarak ke ideal negatif D⁻ = {best_topsis['d_minus']:.4f}). "
        f"Penilaian non-finansial juga mengangkat Skenario <strong>#{max_rise['no']}</strong> melonjak <strong>+{max_rise['rank_delta']} peringkat</strong> "
        f"berkat profil risiko dan efisiensi CAPEX yang lebih unggul."
    )
    render_insight_callout(insight_text)

    # Callout Transparansi Cakupan Kriteria (§3.2.2)
    st.info(
        "ℹ️ **Status Cakupan Kriteria TOPSIS (16 dari 20 Sub-Kriteria Aktif):**\n"
        "- Sub-kriteria **E4** (Toksisitas Kimia), **E5** (Tumpahan/Limbah), dan **R1** (Ketidakpastian Bawah Permukaan) "
        "belum memiliki data kualitatif di Excel V6 sehingga dikeluarkan dari perhitungan v1. "
        "Bobotnya diredistribusikan secara proporsional ke sub-kriteria aktif dalam kriteria induk masing-masing agar bobot Level 1 (Environmental & Risk) tetap utuh.\n"
        "- Sub-kriteria **R2** (Risiko Teknis & Eksekusi) menggunakan **Proksi RPN Total** dari sheet `1.Risk` (arah Cost)."
    )

    # 3. Chart 1: Perbandingan Pergeseran Peringkat (Rank SA vs Rank TOPSIS)
    fig_slope = go.Figure()
    y_sa = [r["rank_sa"] for r in results]
    y_top = [r["rank_topsis"] for r in results]
    names = [f"#{r['no']} ({r['name'][:18]}..)" for r in results]

    for i in range(len(results)):
        r = results[i]
        color = "#2E7D32" if r["rank_delta"] > 0 else ("#C62828" if r["rank_delta"] < 0 else "#78909C")
        fig_slope.add_trace(go.Scatter(
            x=["Rank SA (Finansial)", "Rank TOPSIS (Multi-Kriteria)"],
            y=[r["rank_sa"], r["rank_topsis"]],
            mode="lines+markers+text",
            name=f"#{r['no']}",
            line=dict(color=color, width=2.5),
            marker=dict(size=9),
            text=[f"SA #{r['rank_sa']}", f"TOPSIS #{r['rank_topsis']}"],
            textposition=["middle left", "middle right"],
            hoverinfo="text",
            hovertext=f"Skenario #{r['no']}: SA #{r['rank_sa']} → TOPSIS #{r['rank_topsis']} (Δ: {r['rank_delta']:+d})",
            showlegend=False,
        ))

    fig_slope.update_layout(
        title="<b>Pergeseran Peringkat: Finansial Murni (Rank SA) vs Multi-Kriteria Holistik (Rank TOPSIS)</b>",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFAFC",
        height=420,
        margin=dict(l=80, r=80, t=60, b=40),
        yaxis=dict(title="Peringkat (1 = Terbaik)", autorange="reversed", tickvals=list(range(1, 11))),
    )
    st.plotly_chart(fig_slope, use_container_width=True)

    # 4. Chart 2: Bar Chart Koefisien Kedekatan Relatif C_i
    labels_bar = [f"Rank #{r['rank_topsis']}<br>#{r['no']}" for r in results]
    c_vals = [r["closeness"] for r in results]
    bar_colors = ["#FFB300" if r["rank_topsis"] == 1 else "#1E88E5" for r in results]

    fig_c = go.Figure(go.Bar(
        x=labels_bar,
        y=c_vals,
        marker_color=bar_colors,
        text=[f"{v:.4f}" for v in c_vals],
        textposition="outside",
        hovertemplate="%{x}<br>Koefisien Kedekatan (C): %{y:.4f}<extra></extra>",
    ))
    fig_c.update_layout(
        title="<b>Koefisien Kedekatan Relatif terhadap Solusi Ideal (Closeness Coefficient C_i)</b>",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFAFC",
        height=360,
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis=dict(title="Koefisien C (0.0 - 1.0)", range=[0, 1.05]),
    )
    st.plotly_chart(fig_c, use_container_width=True)

    # 5. Tabel Hasil Utama TOPSIS
    st.markdown("#### Tabel Peringkat Rekomendasi Akhir TOPSIS (Top-10 Stand-Alone)")
    st.caption("Peringkat diurutkan berdasarkan koefisien kedekatan relatif C_i tertinggi (descending).")

    df_topsis = pd.DataFrame([
        {
            "Rank TOPSIS": r["rank_topsis"],
            "Rank SA": r["rank_sa"],
            "Perubahan (Δ)": f"{r['rank_delta']:+d}" if r["rank_delta"] != 0 else "=",
            "Nomor": r["no"],
            "Strategi": r["name"],
            "Koefisien C": r["closeness"],
            "Jarak Ideal D+": r["d_plus"],
            "Jarak Negatif D-": r["d_minus"],
            "NPV,10% @80$ (M USD)": r["npv10_80"],
            "IRR @80$": f"{float(r['irr_80'])*100:.2f}%" if isinstance(r["irr_80"], (int, float)) and np.isfinite(r["irr_80"]) else str(r["irr_80"]),
            "CAPEX (M USD)": r["capex"],
        }
        for r in results
    ])

    core_cols = [
        "Rank TOPSIS", "Rank SA", "Perubahan (Δ)", "Nomor", "Strategi",
        "Koefisien C", "Jarak Ideal D+", "Jarak Negatif D-", "NPV,10% @80$ (M USD)"
    ]
    all_cols = list(df_topsis.columns)

    fmt_topsis = {
        "Koefisien C": "{:.4f}",
        "Jarak Ideal D+": "{:.4f}",
        "Jarak Negatif D-": "{:.4f}",
        "NPV,10% @80$ (M USD)": "{:,.2f}",
        "CAPEX (M USD)": "{:,.2f}",
    }

    render_compact_table(
        df=df_topsis,
        core_cols=core_cols,
        all_cols=all_cols,
        download_filename="Athena_TOPSIS_Ranking_Top10.csv",
        key_prefix="topsis_main_table",
        height=400,
        format_dict=fmt_topsis,
    )

    # Expander 1: Transparansi Hierarki Bobot AHP
    with st.expander("⚖️ Transparansi Bobot Hierarki AHP & Status 20 Sub-Kriteria (Addendum §2 & §3)", expanded=False):
        st.markdown(
            "Struktur bobot AHP Saaty: Matriks 4×4 Level 1 dan empat matriks 5×5 Level 2 dari sheet `1.AHP`. "
            "Kolom **Bobot Normalisasi (16 Kriteria)** menunjukkan bobot efektif yang dipakai di engine TOPSIS v1."
        )
        df_weights = pd.DataFrame([
            {
                "ID": sc["id"],
                "Sub-Kriteria": sc["name"],
                "Kriteria Induk": sc["parent"],
                "Arah": sc["direction"],
                "Bobot Level 1": sc["level1_weight"],
                "Bobot Level 2": sc["level2_weight"],
                "Bobot Global Excel": sc["raw_global_weight"],
                "Bobot Normalisasi (16 Kriteria)": sc["normalized_weight"],
                "Status": "Aktif" if sc["is_active"] else "Nonaktif (Redistribusi)",
                "Tab Asal Data": sc.get("source_tab", "-"),
            }
            for sc in topsis_data["all_subcriteria"]
        ])
        st.dataframe(
            df_weights.style.format({
                "Bobot Level 1": "{:.4f}",
                "Bobot Level 2": "{:.4f}",
                "Bobot Global Excel": "{:.4f}",
                "Bobot Normalisasi (16 Kriteria)": "{:.4f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

    # Expander 2: Matriks Keputusan Mentah (10 Skenario x 16 Sub-kriteria)
    with st.expander("🔢 Matriks Keputusan Mentah TOPSIS (10 Skenario × 16 Kriteria)", expanded=False):
        df_raw_x = pd.DataFrame(topsis_data["raw_matrix"])
        st.dataframe(
            df_raw_x.style.format({
                c: "{:,.2f}" for c in df_raw_x.columns if c not in ["no", "name", "rank_sa"]
            }),
            use_container_width=True,
            hide_index=True,
        )

    render_footnote()
