"""
Module ui/stage2_environmental.py: Halaman Dampak Lingkungan (Tahap 2 · Multi-Kriteria).
Menyajikan analisis Scope 1, Scope 2, Scope 3, Produced Water, Intensitas Emisi,
dua kartu sorotan terbaik-terburuk, dan narasi otomatis sesuai PRD Addendum v3.2 §9.2.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from athena_app.ui.components import (
    render_insight_callout,
    render_footnote,
    render_compact_table,
)
from athena_app.core.environmental import calculate_all_environmental


def render_stage2_environmental(engine_results: dict):
    st.subheader("7. Dampak Lingkungan (Scope 1, 2, 3 & Air Terproduksi)")
    st.markdown(
        "*Evaluasi komparatif jejak karbon operasional, rantai nilai, dan beban air terproduksi "
        "untuk 10 skenario teratas SA terhadap baseline BAU (2026–2040).*"
    )

    top10_sa = engine_results["top10_sa"]
    existing_data = engine_results["existing_data"]
    bau_data = engine_results["bau_data"]

    env_data = calculate_all_environmental(top10_sa, existing_data, bau_data)
    bau = env_data["bau"]
    strats = env_data["strategies"]

    best_strat = min(strats, key=lambda x: x["int_s12"])
    worst_strat = max(strats, key=lambda x: x["int_s12"])

    j_min = best_strat["int_s12"]
    j_max = worst_strat["int_s12"]
    j_bau = bau["int_s12"]
    ogci = 17.9  # 0.Existing Data!B140

    pct_vs_bau = ((j_min - j_bau) / j_bau) * 100
    selisih_vs_terbaik = ((j_max - j_min) / j_min) * 100
    rentang_pct = selisih_vs_terbaik

    # 1. Dua Kartu Sorotan Bersebelahan: Terbaik vs Terburuk (UIUX Guidelines §10.1 & Addendum §9.2)
    col_card_best, col_card_worst = st.columns(2)
    with col_card_best:
        best_full_name = best_strat["name"]
        short_best_name = (best_full_name[:38] + "..") if len(best_full_name) > 40 else best_full_name
        html_best = (
            f'<div style="background: #FAFCF9; border-left: 4px solid #15803D; border-radius: 8px; '
            f'padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">'
            f'<div style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #15803D; letter-spacing: 0.5px; margin-bottom: 4px;">'
            f'▍ DAMPAK LINGKUNGAN TERENDAH</div>'
            f'<div style="font-size: 1.02rem; font-weight: 700; color: #1B1F23; margin-bottom: 4px;" title="{best_full_name}">'
            f'#{best_strat["no"]} {short_best_name}</div>'
            f'<div style="font-size: 1.45rem; font-weight: 700; color: #15803D; font-feature-settings: \'tnum\';">{j_min:.2f} kg CO2e/boe</div>'
            f'<div style="font-size: 0.82rem; color: #5A6A80; margin-top: 4px;">{pct_vs_bau:+.1f}% dibanding BAU ({j_bau:.2f} kg/boe)</div>'
            f'</div>'
        )
        st.markdown(html_best, unsafe_allow_html=True)

    with col_card_worst:
        worst_full_name = worst_strat["name"]
        short_worst_name = (worst_full_name[:38] + "..") if len(worst_full_name) > 40 else worst_full_name
        html_worst = (
            f'<div style="background: #FDF9F9; border-left: 4px solid #B91C1C; border-radius: 8px; '
            f'padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">'
            f'<div style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #B91C1C; letter-spacing: 0.5px; margin-bottom: 4px;">'
            f'▍ DAMPAK LINGKUNGAN TERTINGGI</div>'
            f'<div style="font-size: 1.02rem; font-weight: 700; color: #1B1F23; margin-bottom: 4px;" title="{worst_full_name}">'
            f'#{worst_strat["no"]} {short_worst_name}</div>'
            f'<div style="font-size: 1.45rem; font-weight: 700; color: #B91C1C; font-feature-settings: \'tnum\';">{j_max:.2f} kg CO2e/boe</div>'
            f'<div style="font-size: 0.82rem; color: #5A6A80; margin-top: 4px;">+{selisih_vs_terbaik:.1f}% lebih tinggi dari strategi terbaik</div>'
            f'</div>'
        )
        st.markdown(html_worst, unsafe_allow_html=True)


    # 2. Blok Narasi Otomatis (Template Persis Addendum §9.2)
    # Tentukan naik/turun emisi absolut Scope 1+2+3
    delta_total_pct_val = best_strat["delta_total_vs_bau"] * 100
    naik_atau_turun = "naik" if delta_total_pct_val >= 0 else "turun"

    water_vals = [s["water_mmbbl"] for s in strats]
    water_min = min(water_vals)
    water_max = max(water_vals)
    water_bau = bau["water_mmbbl"]

    best_wor_strat = min(strats, key=lambda x: x["wor"])

    narrative_text = (
        f"Dari 10 strategi teratas, <strong>#{best_strat['no']} {best_strat['name'][:28]}..</strong> memiliki jejak karbon operasional "
        f"paling rendah (<strong>{j_min:.2f} kg CO2e/boe</strong>) dan <strong>#{worst_strat['no']} {worst_strat['name'][:28]}..</strong> paling tinggi "
        f"(<strong>{j_max:.2f} kg CO2e/boe</strong>) — rentang <strong>{rentang_pct:.1f}%</strong> antar keduanya. Sebagai "
        f"pembanding, BAU tanpa treatment berada di <strong>{j_bau:.2f} kg CO2e/boe</strong> dan rata-rata "
        f"anggota OGCI di <strong>{ogci:.1f} kg CO2e/boe</strong>.<br><br>"
        f"Perlu dicatat: intensitas emisi turun bukan karena emisi absolutnya berkurang, "
        f"melainkan karena produksi minyak naik lebih cepat daripada emisinya. Total "
        f"Scope 1+2+3 justru <strong>{naik_atau_turun} {abs(delta_total_pct_val):.1f}%</strong> dibanding BAU, karena "
        f"tambahan produksi berarti tambahan minyak yang dibakar di hilir (Scope 3).<br><br>"
        f"Beban air terproduksi berkisar <strong>{water_min:.1f}–{water_max:.1f} MMbbl</strong> selama 15 tahun "
        f"(BAU: <strong>{water_bau:.1f} MMbbl</strong>). Strategi dengan WOR terendah adalah <strong>#{best_wor_strat['no']} {best_wor_strat['name'][:24]}..</strong> "
        f"pada <strong>{best_wor_strat['wor']:.2f} bbl air per bbl minyak</strong>."
    )
    render_insight_callout(narrative_text)

    # 3. Chart 1: Perbandingan Intensitas Scope 1+2 Top-10 vs BAU
    labels = [f"Rank SA #{s['rank_sa']}<br>#{s['no']}" for s in strats]
    int_s12_vals = [s["int_s12"] for s in strats]

    fig_int = go.Figure()
    bar_colors = ["#15803D" if s["no"] == best_strat["no"] else ("#B91C1C" if s["no"] == worst_strat["no"] else "#1E88E5") for s in strats]
    
    fig_int.add_trace(go.Bar(
        x=labels,
        y=int_s12_vals,
        name="Intensitas Scope 1+2 (kg CO2e/boe)",
        marker_color=bar_colors,
        text=[f"{v:.1f}" for v in int_s12_vals],
        textposition="outside",
        hovertemplate="%{x}<br>Intensitas S1+2: %{y:.2f} kg/boe<extra></extra>",
    ))
    fig_int.add_hline(
        y=bau["int_s12"],
        line_dash="dash",
        line_color="#B91C1C",
        annotation_text=f"BAU: {bau['int_s12']:.1f} kg/boe",
        annotation_position="top right",
    )
    fig_int.add_hline(
        y=ogci,
        line_dash="dot",
        line_color="#15803D",
        annotation_text=f"Target OGCI: {ogci:.1f} kg/boe",
        annotation_position="bottom right",
    )
    fig_int.update_layout(
        title="<b>Intensitas Emisi Operasional Scope 1+2 Top-10 vs Baseline BAU (Hijau: Terbaik, Merah: Terburuk)</b>",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFAFC",
        height=380,
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis=dict(title="Intensitas (kg CO2e/boe)"),
    )
    st.plotly_chart(fig_int, use_container_width=True)

    # 4. Chart 2: Stacked Bar Total Emisi Scope 1, 2, 3 (kt CO2e)
    fig_stack = go.Figure()
    fig_stack.add_trace(go.Bar(
        x=["BAU"] + labels,
        y=[bau["scope1_kt"]] + [s["scope1_kt"] for s in strats],
        name="Scope 1 (Direct & Flaring)",
        marker_color="#D97706",
    ))
    fig_stack.add_trace(go.Bar(
        x=["BAU"] + labels,
        y=[bau["scope2_kt"]] + [s["scope2_kt"] for s in strats],
        name="Scope 2 (Electricity)",
        marker_color="#2563EB",
    ))
    fig_stack.add_trace(go.Bar(
        x=["BAU"] + labels,
        y=[bau["scope3_kt"]] + [s["scope3_kt"] for s in strats],
        name="Scope 3 (Kat. 11 Combustion)",
        marker_color="#059669",
    ))
    fig_stack.update_layout(
        barmode="stack",
        title="<b>Komposisi Kumulatif Emisi 15 Tahun: Scope 1, Scope 2, dan Scope 3 (kt CO2e)</b>",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFAFC",
        height=380,
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis=dict(title="Emisi Kumulatif (kt CO2e)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    # 5. Tabel Ringkas Master
    st.markdown("#### Tabel Dampak Lingkungan (10 Skenario Teratas + BAU)")
    st.caption("Baris hijau menandai intensitas emisi terendah (terbaik), baris merah menandai intensitas tertinggi.")

    all_rows = [
        {
            "Strategi": bau["name"],
            "Rank SA": "-",
            "Env. Rank": "-",
            "p Gabungan": "-",
            "Minyak (MMbbl)": bau["oil_mmbbl"],
            "Air (MMbbl)": bau["water_mmbbl"],
            "Scope 1+2 (kt)": bau["scope12_kt"],
            "Scope 3 (kt)": bau["scope3_kt"],
            "Scope 1+2+3 (kt)": bau["scope123_kt"],
            "Int. S1+2 (kg/boe)": bau["int_s12"],
            "WOR (bbl/bbl)": bau["wor"],
            "Carbon Cost (M USD)": bau["carbon_cost_usd_mn"],
            "NPV10@80 (M USD)": np.nan,
            "Highlight": "BAU",
        }
    ]
    for s in strats:
        hl = "BEST" if s["no"] == best_strat["no"] else ("WORST" if s["no"] == worst_strat["no"] else "NORMAL")
        all_rows.append({
            "Strategi": f"#{s['no']} {s['name']}",
            "Rank SA": str(s["rank_sa"]),
            "Env. Rank": str(s["env_rank"]),
            "p Gabungan": f"{s['contingency_p']*100:.1f}%",
            "Minyak (MMbbl)": s["oil_mmbbl"],
            "Air (MMbbl)": s["water_mmbbl"],
            "Scope 1+2 (kt)": s["scope12_kt"],
            "Scope 3 (kt)": s["scope3_kt"],
            "Scope 1+2+3 (kt)": s["scope123_kt"],
            "Int. S1+2 (kg/boe)": s["int_s12"],
            "WOR (bbl/bbl)": s["wor"],
            "Carbon Cost (M USD)": s["carbon_cost_usd_mn"],
            "NPV10@80 (M USD)": s["npv10_80"],
            "Highlight": hl,
        })


    df_env = pd.DataFrame(all_rows)
    core_cols = [
        "Env. Rank", "Rank SA", "Strategi", "Minyak (MMbbl)", "Air (MMbbl)",
        "Scope 1+2 (kt)", "Int. S1+2 (kg/boe)", "WOR (bbl/bbl)", "Carbon Cost (M USD)"
    ]
    all_cols = [c for c in df_env.columns if c != "Highlight"]

    fmt_env = {
        "Minyak (MMbbl)": "{:,.2f}",
        "Air (MMbbl)": "{:,.2f}",
        "Scope 1+2 (kt)": "{:,.1f}",
        "Scope 3 (kt)": "{:,.1f}",
        "Scope 1+2+3 (kt)": "{:,.1f}",
        "Int. S1+2 (kg/boe)": "{:.2f}",
        "WOR (bbl/bbl)": "{:.2f}",
        "Carbon Cost (M USD)": "{:,.2f}",
        "NPV10@80 (M USD)": "{:,.2f}",
    }

    # Style highlighter 8% opacity untuk baris terbaik dan terburuk (UIUX §10.1)
    def highlight_best_worst(row):
        hl = row.get("Highlight")
        if hl == "BEST":
            return ["background-color: rgba(21, 128, 61, 0.08); font-weight: 600;"] * len(row)
        elif hl == "WORST":
            return ["background-color: rgba(185, 28, 28, 0.08);"] * len(row)
        return [""] * len(row)

    styled_df = df_env[core_cols].style.format(fmt_env).apply(
        lambda _: [
            "background-color: rgba(21, 128, 61, 0.08); font-weight: 600;" if df_env.loc[i, "Highlight"] == "BEST"
            else ("background-color: rgba(185, 28, 28, 0.08);" if df_env.loc[i, "Highlight"] == "WORST" else "")
            for i in df_env.index
        ],
        axis=0
    )

    col_ctrl, col_dl = st.columns([1, 1])
    with col_ctrl:
        show_all = st.checkbox(f"Tampilkan semua kolom ({len(all_cols)} kolom)", value=False, key="env_table_show_all")
    with col_dl:
        csv_data = df_env[all_cols].to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"⬇️ Unduh Seluruh Data Lingkungan ({len(df_env)} baris)",
            data=csv_data,
            file_name="Athena_Environmental_Impact_Top10.csv",
            mime="text/csv",
            key="env_table_download",
            use_container_width=True,
        )

    cols_to_disp = all_cols if show_all else core_cols
    disp_styled = df_env[cols_to_disp].style.format(fmt_env).apply(
        lambda _: [
            "background-color: rgba(21, 128, 61, 0.08); font-weight: 600;" if df_env.loc[i, "Highlight"] == "BEST"
            else ("background-color: rgba(185, 28, 28, 0.08);" if df_env.loc[i, "Highlight"] == "WORST" else "")
            for i in df_env.index
        ],
        axis=0
    )

    st.dataframe(
        disp_styled,
        use_container_width=True,
        hide_index=True,
        height=400,
    )

    render_footnote()
