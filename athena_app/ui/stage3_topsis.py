"""
Module ui/stage3_topsis.py: Halaman AHP & TOPSIS (Tahap 3 · Keputusan).
Sesuai PRD Addendum v4.1 §3, §9.4 dan UI/UX Guidelines §12.3.
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
from athena_app.core.topsis import calculate_topsis
from athena_app.core.environmental import calculate_all_environmental
from athena_app.core.risk import calculate_all_top10_risks
from athena_app.core.technical import calculate_all_top10_technical
from athena_app.core.contract_simulations import calculate_contract_simulations
from athena_app.core.config_manager import calculate_ahp_matrix, DEFAULT_AHP_LEVEL1


def render_stage3_topsis(engine_results: dict):
    st.subheader("12. Keputusan Multi-Kriteria (AHP & TOPSIS)")
    st.markdown(
        "*Sintesis pengambilan keputusan akhir: Mengintegrasikan 10 sub-kriteria berbobot terbesar "
        "dari 4 dimensi strategis (Lingkungan, Teknis, Risiko FMEA, dan Finansial) menggunakan pembobotan AHP "
        "dan algoritma TOPSIS sesuai Excel V6_1 sheet '3.TOPSIS'.*"
    )

    top10_sa = engine_results["top10_sa"]
    ed = engine_results.get("existing_data", {})
    bau_data = engine_results.get("bau_data", {})
    summary_rows = engine_results.get("summary_rows", [])

    # Dependensi Multi-Kriteria
    env_res = calculate_all_environmental(top10_sa, ed, bau_data)
    risk_res = calculate_all_top10_risks(top10_sa, config=ed)
    tech_res = calculate_all_top10_technical(top10_sa, config=ed)
    cs_res = calculate_contract_simulations(top10_sa, summary_rows, ed)

    # Ambil matriks AHP jika ada kustomisasi di session_state
    custom_l1 = st.session_state.get("ahp_matrix_l1")
    custom_l2 = st.session_state.get("ahp_matrix_l2")

    topsis_res = calculate_topsis(
        top10_sa=top10_sa,
        env_results=env_res,
        risk_results=risk_res,
        tech_results=tech_res,
        contract_results={"summary": cs_res["reserves_summary"]},
        pairwise_l1=custom_l1,
        pairwise_l2=custom_l2,
    )

    # 1. Pengecekan Blocking TOPSIS (§3.3)
    if topsis_res["is_blocked"]:
        st.error(
            f"🚫 **TOPSIS Tidak Dapat Dihitung:**\n\n"
            f"{topsis_res['block_message']}\n\n"
            f"*Silakan sesuaikan kembali bobot perbandingan AHP di menu 🔒 Pengaturan Lanjutan.*"
        )
        return

    # 2. Pengecekan Sumber Perluasan (§3.3)
    ext_used = topsis_res.get("extensions_used", [])
    if ext_used:
        st.info(
            f"ℹ️ **Pemberitahuan Perluasan:** Dengan bobot yang disesuaikan, sub-kriteria "
            f"**{', '.join(ext_used)}** ikut dinilai menggunakan kolom ekstensi sheet model. "
            f"Kolom ini tidak ada di sheet `3.TOPSIS` Excel asli, sehingga hasil ini tidak dapat dicocokkan langsung dengan Excel."
        )

    # Uji Konsistensi CR Level 1
    w_l1, lmax_l1, ci_l1, cr_l1, ok_l1 = calculate_ahp_matrix(custom_l1 if custom_l1 is not None else DEFAULT_AHP_LEVEL1)
    if not ok_l1:
        st.warning(
            f"⚠️ **Perhatian Konsistensi Judgment:** Bobot AHP Level 1 memiliki rasio konsistensi CR = {cr_l1:.4f} "
            f"(di atas ambang batas 0.08). Konsistensi perbandingan berpasangan perlu ditinjau ulang."
        )

    summary = topsis_res["summary"]
    summary_sorted = topsis_res["summary_sorted"]
    top_sc = topsis_res["top_scenario"]
    top10_sub = topsis_res["top10_sub"]

    # Cari pergeseran terbesar
    max_rise_sc = max(summary, key=lambda x: x["rank_diff"])
    max_drop_sc = min(summary, key=lambda x: x["rank_diff"])
    largest_mover = max_rise_sc if abs(max_rise_sc["rank_diff"]) >= abs(max_drop_sc["rank_diff"]) else max_drop_sc

    # 3. Tiga Kartu KPI Utama
    k1, k2, k3 = st.columns(3)
    with k1:
        render_kpi_card(
            label="🏆 Peringkat 1 TOPSIS",
            value=f"#{top_sc['scenario_no']}",
            delta=f"Closeness Ci = {top_sc['ci']:.4f} (Rank SA #{top_sc['rank_sa']})",
            help_text="Skenario dengan nilai kedekatan relatif tertinggi terhadap solusi ideal multi-kriteria",
            is_gold=True,
        )
    with k2:
        render_kpi_card(
            label="Uji Konsistensi AHP Level 1",
            value="Konsisten" if ok_l1 else "Tinjau Ulang",
            delta=f"CR = {cr_l1:.4f} (Ambang: 0.08)",
            help_text="Rasio konsistensi pembobotan matriks perbandingan berpasangan Level 1",
        )
    with k3:
        diff_str = f"+{largest_mover['rank_diff']}" if largest_mover['rank_diff'] > 0 else f"{largest_mover['rank_diff']}"
        render_kpi_card(
            label="Perubahan Rank Terbesar",
            value=f"{diff_str} Posisi",
            delta=f"#{largest_mover['scenario_no']} (SA #{largest_mover['rank_sa']} → TOPSIS #{largest_mover['rank_topsis']})",
            help_text="Pergeseran peringkat terbesar setelah kriteria lingkungan, risiko, dan teknis diintegrasikan",
        )

    # 4. Insight Callout Otomatis (Template PRD §9.4)
    tetap_atau_menjadi = "tetap" if top_sc["rank_sa"] == 1 else "menjadi"
    n_naik = sum(1 for r in summary if r["rank_diff"] > 0)
    n_turun = sum(1 for r in summary if r["rank_diff"] < 0)
    sama_atau_beda = "tetap sama" if topsis_res["is_consistent_with_equal"] else "berbeda"

    top3_subs = top10_sub[:3]
    sub1, sub2, sub3 = top3_subs[0], top3_subs[1], top3_subs[2]

    narrative = (
        f"Setelah aspek lingkungan, risiko, dan teknis ikut dinilai, <strong>#{top_sc['scenario_no']} ({top_sc['name']})</strong> "
        f"<strong>{tetap_atau_menjadi}</strong> peringkat 1 dengan skor kedekatan <strong>{top_sc['ci']:.4f}</strong>. "
        f"<strong>{n_naik} strategi naik peringkat</strong> dibanding ranking finansial murni dan <strong>{n_turun} turun</strong>; "
        f"perubahan terbesar adalah <strong>#{largest_mover['scenario_no']} ({largest_mover['name']})</strong> "
        f"({largest_mover['rank_sa']} → {largest_mover['rank_topsis']}). "
        f"Dengan bobot sama rata, peringkat 1 <strong>{sama_atau_beda}</strong>. "
        f"Bobot terbesar yang dipakai: <strong>{sub1['id']} ({sub1['norm_weight']*100:.1f}%)</strong>, "
        f"<strong>{sub2['id']} ({sub2['norm_weight']*100:.1f}%)</strong>, <strong>{sub3['id']} ({sub3['norm_weight']*100:.1f}%)</strong>."
    )
    render_insight_callout(narrative)

    # 5. Tabel Peringkat Final (Urut Rank TOPSIS)
    st.markdown("#### Tabel Peringkat Rekomendasi Akhir AHP-TOPSIS Top-10")
    df_rows = []
    for r in summary_sorted:
        diff = r["rank_diff"]
        diff_label = f"▲ +{diff}" if diff > 0 else (f"▼ {diff}" if diff < 0 else "— 0")
        df_rows.append({
            "Rank TOPSIS": r["rank_topsis"],
            "No": r["scenario_no"],
            "Skenario": r["name"],
            "Rank SA": r["rank_sa"],
            "Pergeseran (Δ)": diff_label,
            "NPV,10 @80$ (USD)": r["npv10_80"],
            "D+ (Jarak Positif)": r["d_plus"],
            "D- (Jarak Negatif)": r["d_minus"],
            "Kedekatan Relatif (Ci)": r["ci"],
            "Rank Bobot Sama": r["rank_equal_weights"],
            "Jenis Perpanjangan": r["contract_extension_type"],
            "Tambah kontrak (th)": r["contract_extra_years"],
        })
    df_table = pd.DataFrame(df_rows)

    core_cols = [
        "Rank TOPSIS", "Skenario", "Rank SA", "Pergeseran (Δ)", "Kedekatan Relatif (Ci)",
        "Rank Bobot Sama", "Jenis Perpanjangan", "Tambah kontrak (th)"
    ]
    all_cols = list(df_table.columns)

    fmt_topsis = {
        "NPV,10 @80$ (USD)": "{:,.0f}",
        "D+ (Jarak Positif)": "{:.6f}",
        "D- (Jarak Negatif)": "{:.6f}",
        "Kedekatan Relatif (Ci)": "{:.6f}",
    }

    render_compact_table(
        df=df_table,
        core_cols=core_cols,
        all_cols=all_cols,
        download_filename="Athena_AHP_TOPSIS_Final_Ranking.csv",
        key_prefix="topsis_rank_table",
        height=380,
        format_dict=fmt_topsis,
    )

    st.markdown("---")

    # 6. Chart A: Slope Chart (Rank SA -> Rank TOPSIS)
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("##### Chart A: Pergeseran Peringkat (Finansial SA → Multi-Kriteria TOPSIS)")
        fig_slope = go.Figure()
        for r in summary:
            diff = r["rank_diff"]
            # Garis yang naik/turun >= 2 dipertebal
            width = 4.0 if abs(diff) >= 2 else 1.8
            color = "#2E7D32" if diff > 0 else ("#C62828" if diff < 0 else "#78909C")

            fig_slope.add_trace(go.Scatter(
                x=["Rank SA (Finansial)", "Rank TOPSIS"],
                y=[r["rank_sa"], r["rank_topsis"]],
                mode="lines+markers+text",
                name=f"#{r['scenario_no']}",
                line=dict(color=color, width=width),
                marker=dict(size=8),
                text=[f"SA {r['rank_sa']}", f"#{r['scenario_no']} (Rank {r['rank_topsis']})"],
                textposition=["middle left", "middle right"],
                hoverinfo="text",
                hovertext=f"Skenario #{r['scenario_no']} ({r['name'][:24]}..): SA #{r['rank_sa']} → TOPSIS #{r['rank_topsis']} (Δ: {diff:+d})",
                showlegend=False,
            ))

        fig_slope.update_layout(
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=400,
            yaxis=dict(title="Peringkat (1 = Terbaik)", autorange="reversed", tickvals=list(range(1, 11))),
            margin=dict(l=60, r=90, t=30, b=30),
        )
        st.plotly_chart(fig_slope, use_container_width=True)

    with col_g2:
        st.markdown("##### Chart B: Skor Kedekatan Relatif Solusi Ideal (Ci)")
        labels_ci = [f"Rank {r['rank_topsis']}<br>#{r['scenario_no']}" for r in summary_sorted]
        ci_vals = [r["ci"] for r in summary_sorted]
        ci_colors = ["#FFB300" if r["rank_topsis"] == 1 else "#1E88E5" for r in summary_sorted]

        fig_ci = go.Figure(go.Bar(
            x=labels_ci,
            y=ci_vals,
            marker_color=ci_colors,
            text=[f"{v:.4f}" for v in ci_vals],
            textposition="outside",
            hovertemplate="%{x}<br>Koefisien Ci: %{y:.4f}<extra></extra>",
        ))
        fig_ci.update_layout(
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=400,
            yaxis=dict(title="Skor Kedekatan Ci (0–1)", range=[0, 1.05]),
            margin=dict(l=30, r=20, t=30, b=30),
        )
        st.plotly_chart(fig_ci, use_container_width=True)

    # 7. Chart C: Bobot 10 Sub-Kriteria Terpilih
    st.markdown("##### Chart C: Komposisi Bobot Ternormalisasi 10 Sub-Kriteria TOPSIS")
    crit_colors = {
        "Financial": "#FFB300",
        "Risk": "#E53935",
        "Technical": "#1E88E5",
        "Environmental": "#43A047",
    }
    sub_labels = [f"{s['id']}: {s['name'][:24]}.." for s in top10_sub]
    sub_weights = [s["norm_weight"] * 100 for s in top10_sub]
    sub_c = [crit_colors.get(s["criteria"], "#757575") for s in top10_sub]

    fig_w = go.Figure(go.Bar(
        x=sub_weights,
        y=sub_labels,
        orientation="h",
        marker_color=sub_c,
        text=[f"{w:.2f}%" for w in sub_weights],
        textposition="outside",
        hovertemplate="%{y}<br>Bobot: %{x:.2f}%<extra></extra>",
    ))
    fig_w.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=360,
        xaxis=dict(title="Bobot (%)", range=[0, max(sub_weights) * 1.2]),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=140, r=30, t=20, b=30),
    )
    st.plotly_chart(fig_w, use_container_width=True)

    # 8. Expander Matriks & Langkah Perhitungan TOPSIS
    with st.expander("🔍 Lihat Matriks Keputusan & Langkah Perhitungan Detail TOPSIS", expanded=False):
        st.markdown("###### Matriks Keputusan Asli (10 Skenario × 10 Sub-Kriteria)")
        sub_headers = [s["id"] for s in top10_sub]
        df_x = pd.DataFrame(topsis_res["matrix_X"], columns=sub_headers, index=[f"#{s['no']}" for s in top10_sa])
        st.dataframe(df_x.style.format("{:,.2f}"), use_container_width=True)

        st.markdown("###### Matriks Terbobot (V = R × w)")
        df_v = pd.DataFrame(topsis_res["matrix_V"], columns=sub_headers, index=[f"#{s['no']}" for s in top10_sa])
        st.dataframe(df_v.style.format("{:.6f}"), use_container_width=True)

    render_footnote()
