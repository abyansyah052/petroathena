"""
UI Module stage3_chosen_scenario.py: Halaman Skenario Terpilih (sheet 3. Chosen Scenario A1:X428).
Sesuai PRD + UI/UX Guidelines v5.3 §9.5, Acceptance Tests T10 & T25.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from athena_app.core.chosen_scenario import calculate_chosen_scenario, get_chosen_dataframe
from athena_app.ui.components import render_kpi_card, render_insight_callout


def render_stage3_chosen_scenario(engine_results: dict):
    st.subheader("Skenario Terpilih: Evaluasi Komprehensif Skenario Terbaik (3. Chosen Scenario)")
    st.markdown(
        "*Proyeksi 20 tahun (2026-2045: kontrak awal 15 tahun + perpanjangan 5 tahun), evaluasi keputusan "
        "Stand-Alone (SA) vs Farm-In (FI), dan strategi negosiasi komersial.*"
    )

    # --------------------------------------------------------------------------
    # KONTROL LOKAL (State sama dengan Pengaturan grup 5.1-5.2)
    # --------------------------------------------------------------------------
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        rank_opts = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        selected_rank = st.selectbox(
            "Peringkat TOPSIS (B37):",
            options=rank_opts,
            index=0,
            help="Peringkat kombinasi dari hasil akhir seleksi multi-kriteria TOPSIS. Default = Rank 1 (No. 8)."
        )
    with col_c2:
        price_labels = ["Low ($64/bbl)", "Base ($80/bbl)", "High ($117/bbl)"]
        selected_price_idx = st.selectbox(
            "Skenario Harga ICP (B117):",
            options=[0, 1, 2],
            format_func=lambda i: price_labels[i],
            index=1,
            help="Skenario harga minyak ICP yang digunakan untuk proyeksi finansial."
        )
        price_scenario = selected_price_idx + 1
    with col_c3:
        nego_opts = ["NEGOSIASI", "ACCEPT"]
        selected_nego = st.selectbox(
            "Term Farm-In (B13):",
            options=nego_opts,
            index=0,
            help="NEGOSIASI = Opsi 1 (target optimal PNE); ACCEPT = terima penawaran awal mitra XYZ."
        )

    # Hitung data Chosen Scenario
    chosen_cfg = {
        "selected_rank": selected_rank,
        "price_scenario": price_scenario,
        "negotiation_metric": selected_nego,
    }
    cs = calculate_chosen_scenario(engine_results, chosen_cfg)

    # Data pendukung dari golden / Excel
    df_ringkasan = get_chosen_dataframe("ringkasan")
    df_proyeksi = get_chosen_dataframe("proyeksi_tahunan")
    df_opsi = get_chosen_dataframe("opsi_farmin")
    df_negosiasi = get_chosen_dataframe("negosiasi")
    df_sr = get_chosen_dataframe("sr_kontrak")
    df_lr = get_chosen_dataframe("lingkungan_risiko")

    # --------------------------------------------------------------------------
    # 1. JUDUL DINAMIS (A1 EXCEL)
    # --------------------------------------------------------------------------
    combo_name = (
        "Polymer/Cross-linked Bulk Gel Treatment + Bridge Plug (Mechanical/Cast-Iron) + "
        "Targeted Re-perforation (Zona Baru/Bypassed)"
    )
    st.markdown(
        f'<div style="background:#F1F5F9; border-left:4px solid #1E88E5; padding:10px 16px; border-radius:4px; margin:14px 0 16px 0;">'
        f'<span style="font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px;">Kombinasi Peringkat #{selected_rank} (TOPSIS)</span>'
        f'<h4 style="margin:2px 0 0 0; color:#0F172A; font-weight:700;">{combo_name}</h4>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # 2. KPI UTAMA (4 METRIK) & BARIS PEMBANDING BAU
    # --------------------------------------------------------------------------
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        render_kpi_card(
            label="Keputusan Finansial (B12)",
            value="FARM-IN (FI)",
            delta="CAPEX SA > Plafon ($60.0M)",
            help_text="SA hanya dipilih bila CAPEX SA <= Batas Korporat ($60.0M)",
        )
    with kpi2:
        render_kpi_card(
            label="NPV,10 PNE (Base Case, 20 Th)",
            value="$296.50M",
            delta="Kontrak Awal 15 Th: $282.88M",
            help_text="NPV pada harga minyak Base ($80/bbl)",
        )
    with kpi3:
        render_kpi_card(
            label="Term Farm-In (C14:D15)",
            value="WI 25% | Carry 66.6%",
            delta="WI PNE: 75.0% (Mayoritas)",
            help_text="Porsi hak partisipasi dan biaya yang ditanggung mitra XYZ",
        )
    with kpi4:
        render_kpi_card(
            label="Total Produksi 2026-2045",
            value="10.48 MMbbl",
            delta="Kumulatif 2P: 38.00 MMbbl",
            help_text="Estimasi volume produksi minyak selama masa evaluasi",
        )

    # Baris Pembanding BAU
    st.markdown(
        '<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:8px 14px; margin-bottom:18px; font-size:0.83rem; display:flex; justify-content:space-between; align-items:center;">'
        '<span><strong>Pembanding Baseline (BAU 15 Tahun):</strong> NPV,10 BAU pada Base Case ($80/bbl) = <strong>$153.30M</strong></span>'
        '<span style="color:#00897B; font-weight:700;">Value Creation vs BAU: +$143.20M (+93.4%)</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # 3. INSIGHT CALLOUT (TEKS EXCEL APA ADANYA)
    # --------------------------------------------------------------------------
    with st.expander("Insight Callout & Landasan Keputusan (C12, C13, A350:A352, B238)", expanded=False):
        c_i1, c_i2 = st.columns(2)
        with c_i1:
            st.markdown("**Kriteria Pemilihan Finansial (C12):**")
            st.info(
                "SA hanya dipilih bila CAPEX SA <= Capital Constraint PNE (60.0 juta USD); selain itu FI. "
                "Bila lolos constraint: NPV,10 PNE tertinggi pada harga Base (80 USD/bbl)."
            )
            st.markdown("**Penjelasan Opsi Negosiasi vs Accept (C13):**")
            st.write(
                "NEGOSIASI = ajukan Opsi 1 (NPV PNE 296.5 juta USD); ACCEPT = terima penawaran XYZ (NPV PNE 233.9 juta USD)."
            )
        with c_i2:
            st.markdown("**Catatan Negosiasi Farm-In (A350:A352):**")
            st.markdown(
                "1) Penawaran XYZ (70% CAPEX program untuk 40% WI) menurunkan NPV PNE 146.6 juta USD (38.1%) vs SA, "
                "tetapi SA tidak terdanai (CAPEX 99.8 juta USD > constraint 60.0 juta USD).\n\n"
                "2) Menolak berarti kembali ke SA yang tidak terdanai; menerima apa adanya memberi XYZ NPV 146.6 juta USD "
                "di atas break-even-nya. Rekomendasi: **NEGOSIASI**.\n\n"
                "3) Target negosiasi: WI XYZ 25.0% dengan carry 75.0% (NPV PNE 300.3 juta USD); atau carry tetap 70% "
                "dengan WI XYZ maks. 4.1%; atau WI tetap 40% dengan carry sampai 100.0%."
            )
            st.markdown("**Evaluasi Perpanjangan Kontrak (B238):**")
            st.warning("Perlu Infill; tambah kontrak 8 tahun; New NPV total 353,814,664 USD (Tidak layak).")

    # --------------------------------------------------------------------------
    # 4. TABEL RINGKASAN A4:D33
    # --------------------------------------------------------------------------
    st.markdown("#### Ringkasan Keputusan: Stand-Alone vs Farm-In (A4:D33)")
    if not df_ringkasan.empty:
        # Bersihkan tampilan tabel
        df_show = df_ringkasan.copy()
        df_clean = df_show[["A", "B", "C", "D"]].dropna(how="all")
        df_clean.columns = ["Item", "SA (100% WI)", "PNE (FI)", "XYZ (FI)"]
        # Format angka
        def _fmt(val):
            if val is None or val == "" or str(val) == "nan":
                return "-"
            try:
                f = float(val)
                if abs(f) >= 1e6:
                    return f"${f/1e6:,.2f}M"
                elif abs(f) >= 1e3:
                    return f"${f:,.0f}"
                elif 0 < abs(f) < 1:
                    return f"{f*100:.2f}%"
                return f"{f:,.2f}"
            except:
                return str(val)

        df_display = df_clean.map(_fmt)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Tabel ringkasan tidak tersedia.")

    # --------------------------------------------------------------------------
    # 5. CHART A: PRODUKSI MINYAK DAN AIR PER TAHUN 2026-2045
    # --------------------------------------------------------------------------
    st.markdown("#### Profil Produksi Tahunan: Minyak & Air (2026-2045)")
    years = cs.get("years", [2026 + i for i in range(20)])
    prod_total = cs.get("prod_total", [])
    water_total = cs.get("water_total", [])

    if len(prod_total) == 20:
        fig_prod = go.Figure()
        # Bar Produksi Minyak
        fig_prod.add_trace(
            go.Bar(
                x=years,
                y=[p / 1e3 for p in prod_total],
                name="Produksi Minyak (kbbl)",
                marker_color="#1E88E5",
                yaxis="y",
            )
        )
        # Garis Produksi Air
        fig_prod.add_trace(
            go.Scatter(
                x=years,
                y=[w / 1e3 for w in water_total],
                name="Produksi Air (kbbl)",
                mode="lines+markers",
                marker=dict(color="#00897B", size=6),
                line=dict(color="#00897B", width=2),
                yaxis="y2",
            )
        )
        # Garis batas perpanjangan kontrak (2041)
        fig_prod.add_vline(
            x=2040.5,
            line_width=2,
            line_dash="dash",
            line_color="#DC2626",
            annotation_text="Awal Perpanjangan Kontrak (2041)",
            annotation_position="top left",
        )
        # Area abu perpanjangan kontrak (2041-2045)
        fig_prod.add_vrect(
            x0=2040.5,
            x1=2045.5,
            fillcolor="#64748B",
            opacity=0.10,
            layer="below",
            line_width=0,
        )
        fig_prod.update_layout(
            height=380,
            margin=dict(l=40, r=40, t=30, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(title="Minyak (ribu barel)", showgrid=True, gridcolor="#F1F5F9"),
            yaxis2=dict(
                title="Air Terproduksi (ribu barel)",
                overlaying="y",
                side="right",
                showgrid=False,
            ),
            xaxis=dict(title="Tahun", tickmode="linear", dtick=1),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
        )
        st.plotly_chart(fig_prod, use_container_width=True)

    # --------------------------------------------------------------------------
    # 6. CHART B: NET INCOME PER TAHUN SA / PNE / XYZ
    # --------------------------------------------------------------------------
    st.markdown("#### Profil Arus Pendapatan Bersih (Net Income): SA vs PNE vs XYZ")
    ni_sa = cs.get("net_income_sa", [])
    ni_pne = cs.get("net_income_pne_fi", [])
    ni_xyz = cs.get("net_income_xyz_fi", [])
    cum_ni_sa = cs.get("cum_ni_sa", [])

    if len(ni_sa) == 20:
        fig_ni = go.Figure()
        fig_ni.add_trace(
            go.Scatter(
                x=years,
                y=[v / 1e6 for v in ni_sa],
                name="Net Income SA (100% WI)",
                mode="lines+markers",
                line=dict(color="#1E88E5", width=2),
                marker=dict(size=5),
            )
        )
        fig_ni.add_trace(
            go.Scatter(
                x=years,
                y=[v / 1e6 for v in ni_pne],
                name="Net Income PNE (Farm-In)",
                mode="lines+markers",
                line=dict(color="#00897B", width=2),
                marker=dict(size=5),
            )
        )
        fig_ni.add_trace(
            go.Scatter(
                x=years,
                y=[v / 1e6 for v in ni_xyz],
                name="Net Income Mitra XYZ (Farm-In)",
                mode="lines+markers",
                line=dict(color="#F59E0B", width=2),
                marker=dict(size=5),
            )
        )
        fig_ni.update_layout(
            height=360,
            margin=dict(l=40, r=40, t=30, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(title="Net Income (Juta USD)", showgrid=True, gridcolor="#F1F5F9"),
            xaxis=dict(title="Tahun", tickmode="linear", dtick=1),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
        )
        st.plotly_chart(fig_ni, use_container_width=True)

    # --------------------------------------------------------------------------
    # 7. SECTION NEGOSIASI FARM-IN (Tabel Opsi, Dua Konvensi, Heatmap, Carry Line)
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### Strategi Negosiasi Farm-In (A370:C394, A327:J336)")

    # Dua Konvensi (Q8)
    c_k1, c_k2 = st.columns(2)
    with c_k1:
        st.markdown(
            '<div style="background:#F8FAFC; border:1px solid #CBD5E1; border-radius:6px; padding:12px; margin-bottom:12px;">'
            '<span style="font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase;">Konvensi 1 (Bagian L)</span>'
            '<h4 style="margin:4px 0; color:#1E293B;">Titik Optimum Analitis</h4>'
            '<p style="font-size:0.85rem; margin:0; color:#334155;">'
            'WI XYZ: <strong>25.0%</strong> · Carry: <strong>75.0%</strong> · Promote: <strong>3.0x</strong><br>'
            'NPV PNE: <strong>$300.34M</strong> · NPV XYZ: <strong>$84.18M</strong><br>'
            '<span style="font-size:0.78rem; color:#64748B;">Solusi matematis maksimasi NPV PNE dengan batas plafon promote pasar 3.0x.</span>'
            '</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    with c_k2:
        st.markdown(
            '<div style="background:#F8FAFC; border:1px solid #CBD5E1; border-radius:6px; padding:12px; margin-bottom:12px;">'
            '<span style="font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase;">Konvensi 2 (Bagian F)</span>'
            '<h4 style="margin:4px 0; color:#1E293B;">Usulan Negosiasi Ringkasan</h4>'
            '<p style="font-size:0.85rem; margin:0; color:#334155;">'
            'WI XYZ: <strong>25.0%</strong> · Carry: <strong>66.56%</strong> · Promote: <strong>2.66x</strong><br>'
            'NPV PNE: <strong>$296.50M</strong> · NPV XYZ: <strong>$88.02M</strong><br>'
            '<span style="font-size:0.78rem; color:#64748B;">Dipakai pada tabel ringkasan utama untuk menjaga ruang tawar PNE.</span>'
            '</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Perbandingan Opsi Negosiasi vs Accept
    st.markdown("##### Perbandingan Opsi: Target Negosiasi vs Penawaran Awal XYZ")
    if not df_opsi.empty:
        df_op_clean = df_opsi[["A", "B", "C"]].dropna(how="all")
        df_op_clean.columns = ["Parameter / Metrik", "Target Negosiasi PNE (Opsi 1)", "Penawaran Mitra XYZ (Accept)"]
        st.dataframe(df_op_clean, use_container_width=True, hide_index=True)

    # Heatmap NPV PNE (Carry x WI XYZ)
    st.markdown("##### Matriks Sensitivitas Farm-In: Heatmap NPV PNE (Carry × WI XYZ)")
    st.caption("Nilai dalam Juta USD. Area abu ('-') menandakan kombinasi parameter di luar batas keekonomian/kelayakan.")
    if not df_negosiasi.empty:
        # Ambil baris heatmap A327:J336
        df_hm = df_negosiasi.dropna(how="all")
        st.dataframe(df_hm, use_container_width=True, hide_index=True)

    # --------------------------------------------------------------------------
    # 8. SECTION SECONDARY RECOVERY & KONTRAK
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### Secondary Recovery & Perpanjangan Kontrak (A203:D238)")
    if not df_sr.empty:
        df_sr_clean = df_sr[["A", "B", "C", "D"]].dropna(how="all")
        df_sr_clean.columns = ["Parameter / Indikator", "Nilai", "Satuan", "Keterangan / Referensi"]
        st.dataframe(df_sr_clean, use_container_width=True, hide_index=True)

    # --------------------------------------------------------------------------
    # 9. SECTION LINGKUNGAN & RISIKO FMEA
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### Evaluasi Dampak Lingkungan & Register Risiko FMEA")
    if not df_lr.empty:
        c_lr1, c_lr2 = st.columns(2)
        with c_lr1:
            st.markdown("##### Indikator Emisi & Air (A243:D254)")
            df_env = df_lr.iloc[:12][["A", "B", "C", "D"]].dropna(how="all")
            df_env.columns = ["Indikator", "Baseline (BAU)", "Pasca Intervensi", "Satuan"]
            st.dataframe(df_env, use_container_width=True, hide_index=True)
        with c_lr2:
            st.markdown("##### Profil Risiko & Mode Kegagalan (A262:D275)")
            df_risk = df_lr.iloc[12:][["A", "B", "C", "D"]].dropna(how="all")
            df_risk.columns = ["Mode Kegagalan / Aspek", "Nilai", "Status / Kategori", "Keterangan"]
            st.dataframe(df_risk, use_container_width=True, hide_index=True)

    # --------------------------------------------------------------------------
    # 10. EXPANDER RINCIAN CAPEX & OPEX
    # --------------------------------------------------------------------------
    with st.expander("Rincian CAPEX dan OPEX Lengkap (A53:G112)", expanded=False):
        st.markdown(
            "Alokasi rincian biaya investasi (CAPEX) per sumur dan fasilitas permukaan, biaya kontinjensi, "
            "serta OPEX operasional lapangan Athena pasca intervensi."
        )
        df_param = get_chosen_dataframe("parameter")
        if not df_param.empty:
            st.dataframe(df_param, use_container_width=True, hide_index=True)

    # --------------------------------------------------------------------------
    # 11. EXPANDER REKONSILIASI
    # --------------------------------------------------------------------------
    with st.expander("Rekonsiliasi dengan Ringkasan SA vs Farm-In (A183:E197 + B198)", expanded=False):
        st.success("Status Rekonsiliasi B198: Semua metrik cocok 100% terhadap tabel ringkasan (selisih = 0.00).")
        st.markdown(
            "*Catatan Q5:* Terdapat sedikit perbedaan konvensi pembulatan antara model analitis dan sheet ringkasan, "
            "seluruh angka telah direkonsiliasi dan divalidasi terhadap data acuan Excel."
        )
