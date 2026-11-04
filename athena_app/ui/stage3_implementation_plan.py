"""
UI Module stage3_implementation_plan.py: Halaman Rencana Implementasi (sheet 3.Implementation Plan).
Sesuai PRD + UI/UX Guidelines v5.3 §9.6 (Q12) dan Acceptance Tests T31-T33.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from athena_app.core.chosen_scenario import calculate_chosen_scenario
from athena_app.core.implementation_plan import (
    calculate_implementation_plan,
    get_gantt_dataframe,
    get_risk_matrix_dataframe,
    get_mitigation_register_dataframe,
)
from athena_app.ui.components import render_kpi_card, render_insight_callout


def render_stage3_implementation_plan(engine_results: dict):
    st.subheader("Rencana Implementasi: Jadwal, Manajemen Risiko & Transisi Energi (3.Implementation Plan)")
    st.markdown(
        "*Rencana aksi operasional dan eksekusi lapangan 2026-2045 untuk skenario terpilih (Kombinasi #8), "
        "mencakup Timeline Fase 0-3, Matriks Risiko 5x5, Register Mitigasi FMEA, dan Indikator Dekarbonisasi.*"
    )

    # Dapatkan hasil perhitungan dinamis
    cs = calculate_chosen_scenario(engine_results)
    plan = calculate_implementation_plan(engine_results, cs)

    # --------------------------------------------------------------------------
    # HEADER SKENARIO TERPILIH
    # --------------------------------------------------------------------------
    st.markdown(
        '<div style="background:#F8FAFC; border:1px solid #E2E8F0; border-left:4px solid #00897B; padding:10px 16px; border-radius:4px; margin:12px 0 16px 0;">'
        '<span style="font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px;">Skenario Acuan Eksekusi (Peringkat 1 TOPSIS)</span>'
        '<h4 style="margin:2px 0; color:#0F172A; font-weight:700;">Kombinasi #8: Polymer/Cross-linked Bulk Gel + Bridge Plug + Targeted Re-perforation</h4>'
        '<p style="margin:0; font-size:0.83rem; color:#475569;">Cakupan: 58 Sumur Aktif & 87 Sumur Idle (Total 145 Sumur) · Kontrak Awal 15 Th (2026-2040) + Perpanjangan Gross Split 4 Th (2041-2044)</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # RINGKASAN METRIK DINAMIS UTAMA (Q12)
    # --------------------------------------------------------------------------
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            label="OPEX Treatment Tahunan",
            value=f"${plan['opex_treatment']:,.0f}/th",
            delta="Surveilans berkelanjutan",
            help_text="Biaya operasional chemical injection dan monitoring rutin",
        )
    with k2:
        render_kpi_card(
            label="CAPEX Renewal Fasilitas",
            value=f"${plan['capex_renewal']/1e6:,.1f}M",
            delta=f"Tahun: {plan['renewal_years_str']}",
            help_text="Peremajaan fasilitas produksi di tahun ke-5, 10, dan 15",
        )
    with k3:
        render_kpi_card(
            label="Sisa 2P Akhir Kontrak Awal",
            value=f"{plan['sisa_2p_contract']/1e6:,.2f} MMbbl",
            delta=f"Porsi sisa: {plan['porsi_sisa_2p']*100:.1f}%",
            help_text="Cadangan minyak 2P yang tersisa setelah tahun 2040",
        )
    with k4:
        render_kpi_card(
            label="Perpanjangan Kontrak",
            value=f"{plan['jenis_perpanjangan']} +{plan['tambah_kontrak_th']} Th",
            delta=f"NPV Base: ${plan['npv_gs_base']/1e6:,.1f}M",
            help_text="Skema Gross Split 4 tahun tambahan (2041-2044) sampai cadangan habis",
        )

    # --------------------------------------------------------------------------
    # SECTION A: GANTT CHART TIMELINE FASE 0 - FASE 3 (2026-2045)
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### A. Timeline Implementasi Proyek (Gantt Chart 2026-2045)")
    st.markdown(
        "Eksekusi terbagi ke dalam empat fase utama untuk memitigasi risiko operasional dan menjaga batas anggaran modal korporat:"
    )

    df_gantt = get_gantt_dataframe()
    if not df_gantt.empty:
        # Tampilkan ringkasan milestone fase
        c_f0, c_f1, c_f2, c_f3 = st.columns(4)
        with c_f0:
            st.markdown(
                '<div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:6px; padding:10px; font-size:0.8rem;">'
                '<strong>FASE 0 (2026 H1-H2)</strong><br>'
                'Diagnostic Screening, Perizinan AMDAL & Procurement Rig (145 sumur).'
                '</div>',
                unsafe_allow_html=True,
            )
        with c_f1:
            st.markdown(
                '<div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:6px; padding:10px; font-size:0.8rem;">'
                '<strong>FASE 1 (2027)</strong><br>'
                'Pilot Batch-1: ~15 sumur aktif + 20 sumur idle kandidat utama.'
                '</div>',
                unsafe_allow_html=True,
            )
        with c_f2:
            st.markdown(
                '<div style="background:#FAF5FF; border:1px solid #E9D5FF; border-radius:6px; padding:10px; font-size:0.8rem;">'
                '<strong>FASE 2 (2028)</strong><br>'
                'Scale-Up Batch-2: sisa ~43 sumur aktif + 67 sumur idle.'
                '</div>',
                unsafe_allow_html=True,
            )
        with c_f3:
            st.markdown(
                '<div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:6px; padding:10px; font-size:0.8rem;">'
                '<strong>FASE 3 (2029-2045)</strong><br>'
                'Surveilans rutin, CAPEX renewal berkala (t=5,10,15), & perpanjangan PSC.'
                '</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        # Tabel Gantt Aktivitas
        df_g_display = df_gantt[["no", "aktivitas", "output", "mulai", "selesai", "jenis"]].copy()
        df_g_display.columns = ["No", "Aktivitas / Milestone", "Deliverable / Output", "Mulai", "Selesai", "Jenis"]
        st.dataframe(df_g_display, use_container_width=True, hide_index=True)
    else:
        st.info("Data timeline Gantt tidak tersedia.")

    # --------------------------------------------------------------------------
    # SECTION B: MATRIKS RISIKO 5x5 & REGISTER MITIGASI FMEA
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### B. Manajemen Risiko & Register Mitigasi FMEA (25 Mode Kegagalan)")

    # Peringatan Kritis G6 RPN 343
    st.error(
        "⚠️ **PERINGATAN KRITIS OPERASIONAL — Mode Kegagalan G6 (RPN 343):**\n\n"
        "**'Salah diagnosis sumber air'** memiliki Severity = 7, Occurrence = 7, Detection = 7 (RPN 343, status: Critical). "
        "Risiko ini memicu kegagalan total treatment kimia jika zona air salah diidentifikasi. "
        "**Mitigasi Wajib:** Terapkan diagnostik bertahap berbiaya rendah (analisis kimia air formasi, multi-rate testing, "
        "dan temperature logging) sebelum logging PLT lengkap untuk memangkas Occurrence ke ≤ 3 dan RPN ke ≤ 84."
    )

    c_m1, c_m2 = st.columns([1, 1])
    with c_m1:
        st.markdown("##### Matriks Risiko 5x5 (Impact vs Likelihood)")
        df_matriks = get_risk_matrix_dataframe()
        if not df_matriks.empty:
            df_m_clean = df_matriks[["A", "D", "F", "H", "J", "L"]].dropna(how="all")
            df_m_clean.columns = ["Impact \\ Likelihood", "1 Rare", "2 Unlikely", "3 Possible", "4 Likely", "5 Almost Certain"]
            st.dataframe(df_m_clean, use_container_width=True, hide_index=True)
        else:
            st.info("Matriks risiko tidak tersedia.")

    with c_m2:
        st.markdown("##### Profil Distribusi Risiko FMEA")
        st.markdown(
            f'<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:14px; font-size:0.85rem;">'
            f'<div style="margin-bottom:8px;"><strong>Total Failure Modes Teridentifikasi:</strong> {plan["active_fm"]} Mode</div>'
            f'<div style="margin-bottom:8px;"><strong>RPN Maksimum (Unmitigated):</strong> <span style="color:#DC2626; font-weight:700;">{plan["max_rpn"]} (Critical)</span></div>'
            f'<div style="margin-bottom:8px;"><strong>Ambang Batas Intervensi:</strong> RPN ≥ 100 wajib memiliki rencana mitigasi tertulis.</div>'
            f'<div style="color:#64748B; font-size:0.8rem;">Mitigasi difokuskan pada uji laboratorium kompatibilitas fluida, isolasi mekanis bridge plug sebelum injeksi gel, dan sensor pemantauan tekanan kepala sumur secara real-time.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("##### Register Mitigasi 25 Failure Modes (FMEA)")
    df_reg = get_mitigation_register_dataframe()
    if not df_reg.empty:
        df_r_clean = df_reg.iloc[1:][["A", "B", "D", "E", "F", "G", "H", "I", "J", "K"]].dropna(subset=["B"])
        df_r_clean.columns = ["No", "Mode Kegagalan", "Kategori", "S", "O", "D", "RPN Awal", "RPN Mitigasi", "Status", "Rencana Mitigasi Utama"]
        st.dataframe(df_r_clean, use_container_width=True, hide_index=True)

    # --------------------------------------------------------------------------
    # SECTION C: PRODUCED WATER & DEKARBONISASI TRANSISI ENERGI
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### C. Manajemen Air Terproduksi & Indikator Transisi Energi")

    col_w, col_e = st.columns(2)
    with col_w:
        st.markdown("##### 💧 Manajemen Air Terproduksi (Produced Water)")
        st.markdown(
            f'<div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:6px; padding:14px; font-size:0.85rem;">'
            f'<div style="display:flex; justify-content:space-between; margin-bottom:8px;">'
            f'<span>Total Volume Air Terproduksi (20 Th):</span><strong>{plan["tot_water_bbl"]/1e6:,.2f} MMbbl</strong>'
            f'</div>'
            f'<div style="display:flex; justify-content:space-between; margin-bottom:8px;">'
            f'<span>Peak Water Produksi (2026):</span><strong>{plan["peak_water"]/1e6:,.2f} MMbbl</strong>'
            f'</div>'
            f'<div style="display:flex; justify-content:space-between; margin-bottom:8px;">'
            f'<span>Laju Minimum Pasca-Treatment:</span><strong>{plan["water_min_post"]/1e3:,.1f} kbbl/th</strong>'
            f'</div>'
            f'<div style="display:flex; justify-content:space-between;">'
            f'<span>Laju Maksimum Pasca-Treatment:</span><strong>{plan["water_max_post"]/1e6:,.2f} MMbbl/th</strong>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_e:
        st.markdown("##### 🌱 Emisi Gas Rumah Kaca & Transisi Energi")
        st.markdown(
            f'<div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:6px; padding:14px; font-size:0.85rem;">'
            f'<div style="display:flex; justify-content:space-between; margin-bottom:8px;">'
            f'<span>Total Emisi GRK (Scope 1+2+3, 20 Th):</span><strong>{plan["tot_emisi_kt"]:,.1f} kt CO₂e</strong>'
            f'</div>'
            f'<div style="display:flex; justify-content:space-between; margin-bottom:8px;">'
            f'<span>Emisi Langsung Scope 1+2 (15 Th):</span><strong>{plan["s12_kt_15"]:,.1f} kt CO₂e</strong>'
            f'</div>'
            f'<div style="display:flex; justify-content:space-between; margin-bottom:8px;">'
            f'<span>Proporsi Emisi Scope 3 (End-Use):</span><strong>{plan["porsi_scope3"]*100:.1f}%</strong>'
            f'</div>'
            f'<div style="display:flex; justify-content:space-between;">'
            f'<span>Intensitas Dekarbonisasi:</span><strong style="color:#00897B;">Pengurangan 18.4% vs BAU</strong>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
