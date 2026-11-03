"""
Module ui/stage2_risk.py: Halaman Risiko & FMEA (Tahap 2 · Multi-Kriteria).
Menyajikan analisis register kegagalan teknis, efikasi gabungan, risiko generik,
antarmuka (interface), legenda kelas risiko, dua kartu sorotan terbaik-terburuk,
stacked bar gradasi satu hue, dan narasi otomatis sesuai PRD Addendum v3.2 §9.3 & UIUX Guidelines §10.
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
from athena_app.core.risk import (
    calculate_all_top10_risks,
    get_fmea_register_summary,
    METHOD_FAILURE_MODES_REGISTER,
)


def render_stage2_risk(engine_results: dict):
    st.subheader("8. Risiko & Evaluasi FMEA (Failure Mode and Effects Analysis)")
    st.markdown(
        "*Audit register kegagalan operasional (Severity, Occurrence, Detection): RPN Metode, "
        "Efikasi Gabungan, Risiko Generik, dan Antarmuka (Interface) untuk 10 skenario teratas SA.*"
    )

    top10_sa = engine_results["top10_sa"]
    ed = engine_results.get("existing_data")
    risk_data = calculate_all_top10_risks(top10_sa, config=ed)
    reg_summary = get_fmea_register_summary()

    best_risk = min(risk_data, key=lambda x: x["rpn_total"])
    worst_risk = max(risk_data, key=lambda x: x["rpn_total"])

    j_min = best_risk["rpn_total"]
    j_max = worst_risk["rpn_total"]
    rasio = j_max / j_min if j_min > 0 else 1.0

    # 1. Dua Kartu Sorotan Bersebelahan: Risiko Terendah vs Risiko Tertinggi (UIUX Guidelines §10.1 & Addendum §9.3)
    col_card_best, col_card_worst = st.columns(2)
    with col_card_best:
        best_full_name = best_risk["name"]
        short_best_name = (best_full_name[:38] + "..") if len(best_full_name) > 40 else best_full_name
        html_best = (
            f'<div class="athena-bw-card athena-bw-best" style="background: #FAFCF9; border-left: 4px solid #15803D; border-radius: 8px; '
            f'padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">'
            f'<div style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #15803D; letter-spacing: 0.5px; margin-bottom: 4px;">'
            f'▍ RISIKO TERENDAH</div>'
            f'<div style="font-size: 1.02rem; font-weight: 700; color: #1B1F23; margin-bottom: 4px;" title="{best_full_name}">'
            f'#{best_risk["no"]} {short_best_name}</div>'
            f'<div class="athena-bw-metric" style="font-size: 1.45rem; font-weight: 700; color: #15803D; font-feature-settings: \'tnum\';">RPN Total: {j_min:,}</div>'
            f'<div style="font-size: 0.82rem; color: #5A6A80; margin-top: 4px;">{best_risk["fm_critical"]} failure mode Critical, {best_risk["fm_high"]} High</div>'
            f'</div>'
        )
        st.markdown(html_best, unsafe_allow_html=True)

    with col_card_worst:
        worst_full_name = worst_risk["name"]
        short_worst_name = (worst_full_name[:38] + "..") if len(worst_full_name) > 40 else worst_full_name
        html_worst = (
            f'<div class="athena-bw-card athena-bw-worst" style="background: #FDF9F9; border-left: 4px solid #B91C1C; border-radius: 8px; '
            f'padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">'
            f'<div style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #B91C1C; letter-spacing: 0.5px; margin-bottom: 4px;">'
            f'▍ RISIKO TERTINGGI</div>'
            f'<div style="font-size: 1.02rem; font-weight: 700; color: #1B1F23; margin-bottom: 4px;" title="{worst_full_name}">'
            f'#{worst_risk["no"]} {short_worst_name}</div>'
            f'<div class="athena-bw-metric" style="font-size: 1.45rem; font-weight: 700; color: #B91C1C; font-feature-settings: \'tnum\';">RPN Total: {j_max:,}</div>'
            f'<div style="font-size: 0.82rem; color: #5A6A80; margin-top: 4px;">{worst_risk["fm_critical"]} failure mode Critical, {worst_risk["fm_high"]} High</div>'
            f'</div>'
        )
        st.markdown(html_worst, unsafe_allow_html=True)


    # 2. Blok Narasi Otomatis (Template Persis Addendum §9.3)
    # Tentukan sumber dominan pada strategi terburuk
    w_comp = {
        "risiko bawaan metode yang dipakai": worst_risk["sum_rpn_metode"],
        "risiko efikasi gabungan tidak tercapai": worst_risk["rpn_efficacy"],
        "risiko generik yang berulang di tiap run": worst_risk["sum_rpn_generic"],
        "risiko interaksi antar metode": worst_risk["sum_rpn_interface"],
    }
    sumber_dominan = max(w_comp, key=w_comp.get)

    highest_fm = reg_summary["highest_fm"]
    n_crit_tot = reg_summary["n_critical_total"]
    n_high_tot = reg_summary["n_high_total"]
    pct_metode = reg_summary["pct_metode"]
    pct_efikasi = reg_summary["pct_efikasi"]
    pct_generik = reg_summary["pct_generik"]
    pct_interface = reg_summary["pct_interface"]

    narrative_text = (
        f"<strong>#{worst_risk['no']} {short_worst_name}</strong> adalah strategi paling berisiko di Top-10 dengan RPN total "
        f"<strong>{j_max:,}</strong>, yaitu <strong>{rasio:.1f}x lipat</strong> dari strategi paling aman "
        f"(<strong>#{best_risk['no']} {short_best_name}</strong>, RPN <strong>{j_min:,}</strong>). "
        f"Perbedaan ini terutama datang dari <em>{sumber_dominan}</em>.<br><br>"
        f"Failure mode dengan RPN tertinggi di seluruh register adalah "
        f"<strong>\"{highest_fm['fm']}\"</strong> (RPN <strong>{highest_fm['rpn']}</strong>, kelas <strong>{highest_fm['class']}</strong>) "
        f"pada metode <strong>{highest_fm['method']}</strong>. Secara keseluruhan ada <strong>{n_crit_tot}</strong> "
        f"failure mode berkelas Critical dan <strong>{n_high_tot}</strong> berkelas High di register metode.<br><br>"
        f"Kombinasi dengan lebih banyak metode tidak otomatis lebih berisiko per pekerjaan, tetapi menambah dua hal: "
        f"failure mode generik yang berulang tiap run (alat macet, well control, tumpahan) dan failure mode interface yang "
        f"hanya muncul ketika dua metode tertentu dipakai bersamaan. Pada Top-10 ini, "
        f"rata-rata <strong>{pct_metode:.1f}%</strong> RPN berasal dari risiko metode itu sendiri, "
        f"<strong>{pct_efikasi:.1f}%</strong> dari risiko efikasi gabungan, "
        f"<strong>{pct_generik:.1f}%</strong> dari risiko generik, dan "
        f"<strong>{pct_interface:.1f}%</strong> dari risiko interface."
    )
    render_insight_callout(narrative_text)

    # 3. Chart: Stacked Bar RPN per Strategi (UIUX Guidelines §10.3)
    # Satu keluarga warna (gradasi satu hue, gelap ke terang), urut RPN terendah ke tertinggi
    sorted_risk = sorted(risk_data, key=lambda x: x["rpn_total"])
    labels = [f"Rank SA #{r['rank_sa']}<br>#{r['no']}" for r in sorted_risk]

    fig_rpn = go.Figure()
    # Segmen 1: Σ RPN Metode (Paling Gelap)
    fig_rpn.add_trace(go.Bar(
        x=labels,
        y=[r["sum_rpn_metode"] for r in sorted_risk],
        name="Σ RPN Metode (Eksekusi)",
        marker_color="#0F2942",
        hovertemplate="%{x}<br>RPN Metode: %{y:,}<extra></extra>",
    ))
    # Segmen 2: RPN Efikasi
    fig_rpn.add_trace(go.Bar(
        x=labels,
        y=[r["rpn_efficacy"] for r in sorted_risk],
        name="RPN Efikasi Gabungan",
        marker_color="#1E5A99",
        hovertemplate="%{x}<br>RPN Efikasi: %{y:,}<extra></extra>",
    ))
    # Segmen 3: Σ RPN Generik
    fig_rpn.add_trace(go.Bar(
        x=labels,
        y=[r["sum_rpn_generic"] for r in sorted_risk],
        name="Σ RPN Generik (Rig/Fish/HSE)",
        marker_color="#3B82F6",
        hovertemplate="%{x}<br>RPN Generik: %{y:,}<extra></extra>",
    ))
    # Segmen 4: Σ RPN Interface (Paling Terang)
    fig_rpn.add_trace(go.Bar(
        x=labels,
        y=[r["sum_rpn_interface"] for r in sorted_risk],
        name="Σ RPN Interface Antar-Metode",
        marker_color="#93C5FD",
        hovertemplate="%{x}<br>RPN Interface: %{y:,}<extra></extra>",
    ))

    fig_rpn.update_layout(
        barmode="stack",
        title="<b>Struktur Akumulasi Risk Priority Number (RPN Total) 10 Skenario Teratas (Diurutkan dari Teraman)</b>",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFAFC",
        height=380,
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis=dict(title="Akumulasi RPN Total"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_rpn, use_container_width=True)

    # 4. Legenda Kelas Risiko (Wajib di atas tabel, UIUX Guidelines §10.2 & Addendum §9.3)
    st.markdown("#### Tabel Ringkasan Risiko & FMEA Top-10 Stand-Alone")
    legend_html = (
        f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px;">'
        f'<div style="font-size: 0.8rem; font-weight: 600; color: #1E293B; margin-bottom: 6px;">'
        f'Kelas risiko dihitung dari RPN = Severity × Occurrence × Detection (skala 1–1000):'
        f'</div>'
        f'<div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">'
        f'<span style="background: #B91C1C; color: #FFFFFF; font-size: 0.76rem; font-weight: 700; padding: 3px 10px; border-radius: 12px;">'
        f'Critical: RPN ≥ 200 — Perlu mitigasi wajib sebelum eksekusi</span>'
        f'<span style="background: #C2410C; color: #FFFFFF; font-size: 0.76rem; font-weight: 700; padding: 3px 10px; border-radius: 12px;">'
        f'High: RPN 100–199 — Perlu rencana mitigasi dan pemilik risiko</span>'
        f'<span style="background: #A16207; color: #FFFFFF; font-size: 0.76rem; font-weight: 700; padding: 3px 10px; border-radius: 12px;">'
        f'Medium: RPN 50–99 — Dipantau dalam prosedur standar</span>'
        f'<span style="background: #6B7280; color: #FFFFFF; font-size: 0.76rem; font-weight: 700; padding: 3px 10px; border-radius: 12px;">'
        f'Low: RPN < 50 — Diterima tanpa tindakan khusus</span>'
        f'</div>'
        f'<div style="font-size: 0.75rem; color: #64748B; margin-top: 6px;">'
        f'<em>Severity ≥ 9 ditandai khusus walau RPN rendah (potensi bahaya well control / HSE).</em>'
        f'</div>'
        f'</div>'
    )
    st.markdown(legend_html, unsafe_allow_html=True)

    # 5. Tabel Utama dengan Highlight Baris Terbaik (Hijau 8%) & Terburuk (Merah 8%)
    df_risk = pd.DataFrame([
        {
            "Rank Risiko": r["risk_rank"],
            "Rank SA": r["rank_sa"],
            "Nomor": r["no"],
            "Strategi": r["name"],
            "p Gabungan": f"{r['p_gabungan']*100:.1f}%",
            "Jml Metode": r["n_methods"],
            "FM Aktif": r["total_fm_active"],
            "Σ RPN Metode": r["sum_rpn_metode"],
            "RPN Efikasi": r["rpn_efficacy"],
            "Σ RPN Generik": r["sum_rpn_generic"],
            "Σ RPN Interface": r["sum_rpn_interface"],
            "RPN TOTAL": r["rpn_total"],
            "RPN Rata²": r["rpn_avg"],
            "RPN Maks": r["rpn_max"],
            "FM Critical": r["fm_critical"],
            "FM High": r["fm_high"],
            "Kelas": r["risk_class"],
            "Highlight": "BEST" if r["no"] == best_risk["no"] else ("WORST" if r["no"] == worst_risk["no"] else "NONE"),
        }
        for r in sorted(risk_data, key=lambda x: x["risk_rank"])
    ])

    core_cols = [
        "Rank Risiko", "Rank SA", "Strategi", "p Gabungan", "Jml Metode",
        "RPN TOTAL", "RPN Maks", "FM Critical", "FM High", "Kelas"
    ]
    all_cols = [c for c in df_risk.columns if c != "Highlight"]

    fmt_risk = {
        "Σ RPN Metode": "{:,.0f}",
        "RPN Efikasi": "{:,.0f}",
        "Σ RPN Generik": "{:,.0f}",
        "Σ RPN Interface": "{:,.0f}",
        "RPN TOTAL": "{:,.0f}",
        "RPN Rata²": "{:.1f}",
        "RPN Maks": "{:,.0f}",
    }

    col_ctrl, col_dl = st.columns([1, 1])
    with col_ctrl:
        show_all = st.checkbox(f"Tampilkan semua kolom ({len(all_cols)} kolom)", value=False, key="risk_table_show_all")
    with col_dl:
        csv_data = df_risk[all_cols].to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"⬇️ Unduh Ringkasan Risiko FMEA ({len(df_risk)} baris)",
            data=csv_data,
            file_name="Athena_Risk_FMEA_Top10.csv",
            mime="text/csv",
            key="risk_table_download",
            use_container_width=True,
        )

    cols_to_disp = all_cols if show_all else core_cols
    disp_styled = df_risk[cols_to_disp].style.format(fmt_risk).apply(
        lambda _: [
            "background-color: rgba(21, 128, 61, 0.08); font-weight: 600;" if df_risk.loc[i, "Highlight"] == "BEST"
            else ("background-color: rgba(185, 28, 28, 0.08);" if df_risk.loc[i, "Highlight"] == "WORST" else "")
            for i in df_risk.index
        ],
        axis=0
    )

    st.dataframe(
        disp_styled,
        use_container_width=True,
        hide_index=True,
        height=380,
    )

    # 6. Tabel Register Failure Mode per Metode (Addendum §9.3)
    st.markdown("---")
    st.markdown("#### Register Failure Mode Metode (FMEA Catalog)")
    
    crit_high_fms = [f for f in METHOD_FAILURE_MODES_REGISTER if f["class"] in ["Critical", "High"]]
    st.caption(
        f"Menampilkan **{len(crit_high_fms)}** failure mode berkelas Critical dan High dari total "
        f"**{len(METHOD_FAILURE_MODES_REGISTER)}** di register. Buka expander di bawah untuk melihat seluruh register termasuk Medium dan Low."
    )

    with st.expander("🔍 Lihat Seluruh Register Failure Mode (Termasuk Medium & Low)", expanded=False):
        show_all_reg = st.checkbox("Tampilkan seluruh 39 failure mode termasuk kelas Medium & Low", value=False)
    
    display_reg = METHOD_FAILURE_MODES_REGISTER if show_all_reg else crit_high_fms
    df_reg = pd.DataFrame([
        {
            "Failure Mode": item["fm"],
            "Metode": item["method"],
            "P (Gagal)": f"{item['p']:.2f}",
            "S": item["s"],
            "O": item["o"],
            "D": item["d"],
            "RPN": item["rpn"],
            "Kelas": item["class"],
            "Efek Operasional": item["effect"],
            "Penyebab Teknis": item["cause"],
            "Status": "Dihitung" if item["active"] == 1 else "Efikasi (Non-Aditif)",
        }
        for item in display_reg
    ])

    st.dataframe(
        df_reg,
        use_container_width=True,
        hide_index=True,
        height=320,
    )
    st.caption(
        "💡 *Catatan:* Baris efikasi per metode (akhiran .E) tidak dijumlahkan langsung ke RPN strategi — "
        "karena digantikan oleh risiko efikasi gabungan tingkat strategi."
    )

    # 7. Expander Metodologi
    with st.expander("📚 Catatan Metodologi & Ambang Batas FMEA (PRD Addendum §4.3)", expanded=False):
        st.markdown(
            "- **Severity (S: 1–10):** Menilai dampak teknis, finansial, dan keselamatan kerja.\n"
            "- **Occurrence (O: 1–10):** Dikonversi dari probabilitas kegagalan empiris $P$ via tabel LOOKUP ($P \\ge 0.5 \\rightarrow O=10$).\n"
            "- **Detection (D: 1–10):** Menilai kemudahan deteksi dini sebelum insiden terjadi (D=1 sangat mudah, D=10 mustahil).\n"
            "- **Kategori Risiko:** Critical ($RPN \\ge 200$), High ($100 \\le RPN < 200$), Medium ($50 \\le RPN < 100$), Low ($RPN < 50$)."
        )

    render_footnote()
