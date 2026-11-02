"""
UI Tab 1: Kombinasi Strategi (uiux.md compliant)
Tujuan: "Begini cara 18 metode intervensi digabung jadi 4.047 kemungkinan skenario."
"""

import streamlit as st
import pandas as pd
from athena_app.ui.components import render_kpi_card, render_footnote


def render_tab1(engine_results: dict):
    st.subheader("1. Kombinasi Strategi")
    st.markdown(
        "*Begini cara 18 metode intervensi digabung jadi 4.047 kemungkinan skenario untuk Lapangan Athena.*"
    )

    methods_18 = engine_results["methods_18"]
    raw_combos = engine_results["raw_combos"]

    # 1. Dua Kartu KPI Berdampingan (uiux.md §4 Tab 1)
    k1, k2 = st.columns(2)
    with k1:
        render_kpi_card(
            label="Jumlah Metode Awal",
            value="18 Metode",
            delta="5 Kelas Intervensi Sumur",
            help_text="Metode konvensional dan mutakhir untuk penanganan water cut dan uplift produksi",
        )
    with k2:
        render_kpi_card(
            label="Total Kombinasi Mentah",
            value="4.047 Kombinasi",
            delta="Breakdown: 1→18 | 2→153 | 3→816 | 4→3.060",
            help_text="Kombinasi matematis C(18,1) + C(18,2) + C(18,3) + C(18,4)",
        )

    st.markdown("---")

    # 2. Tabel 18 Metode (Selalu tampil penuh, 18 baris tanpa filter)
    st.markdown("#### Daftar 18 Metode Intervensi Awal (5 Kelas)")
    df_methods = pd.DataFrame([
        {
            "ID": m["id_old"],
            "Class": m["class"],
            "Method Name": m["name"],
        }
        for m in methods_18
    ])
    st.dataframe(df_methods, use_container_width=True, hide_index=True)

    # 3. Expander "Lihat 4.047 Kombinasi Mentah" (uiux.md §4 Tab 1)
    with st.expander("🔍 Lihat 4.047 Kombinasi Mentah (Data Referensi / Audit)", expanded=False):
        st.caption("Kombinasi mentah sebelum diterapkan filter kesesuaian geologi dan matriks kompatibilitas.")

        f_col1, f_col2 = st.columns([1, 2])
        with f_col1:
            size_filter = st.multiselect(
                "Filter Ukuran Kombinasi:",
                options=[1, 2, 3, 4],
                default=[1, 2, 3, 4],
                key="tab1_raw_size",
            )
        with f_col2:
            search_query = st.text_input(
                "Cari nama metode dalam kombinasi:",
                value="",
                placeholder="Ketik nama metode...",
                key="tab1_raw_search",
            )

        df_raw = pd.DataFrame([
            {
                "No": r["no"],
                "Ukuran": r["size"],
                "Kombinasi": r["name"],
            }
            for r in raw_combos
        ])

        if size_filter:
            df_raw = df_raw[df_raw["Ukuran"].isin(size_filter)]
        if search_query:
            df_raw = df_raw[df_raw["Kombinasi"].str.contains(search_query, case=False, na=False)]

        st.caption(f"Menampilkan {len(df_raw):,} dari 4.047 kombinasi")
        st.dataframe(df_raw, use_container_width=True, hide_index=True, height=420)

        csv_data = df_raw.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Unduh 4.047 Kombinasi Mentah (CSV)",
            data=csv_data,
            file_name="Athena_Tab1_Raw_Combinations.csv",
            mime="text/csv",
            key="tab1_download_raw",
        )

    render_footnote()
