"""
UI Tab 2: Hard Constraint & Kompatibilitas (uiux.md compliant)
Tujuan: "Begini cara 4.047 kombinasi disaring jadi 453 yang layak dihitung."
"""

import streamlit as st
import pandas as pd
from athena_app.ui.components import (
    render_compact_table,
    render_footnote,
)
from athena_app.ui.charts import create_horizontal_funnel, create_compat_heatmap


def render_tab2(engine_results: dict):
    st.subheader("2. Hard Constraint & Kompatibilitas")
    st.markdown(
        "*Begini cara 4.047 kombinasi disaring jadi 453 yang layak dihitung melalui validasi reservoir dan sinergi teknis.*"
    )

    methods_18 = engine_results["methods_18"]
    compat_matrix = engine_results["compat_matrix"]
    combos_453 = engine_results["combos_453"]

    # 1. Funnel Chart Horizontal (uiux.md §4 Tab 2: pengganti 3 kartu angka terpisah)
    fig_funnel = create_horizontal_funnel(raw_count=4047, hc_count=1092, final_count=453)
    st.plotly_chart(fig_funnel, use_container_width=True)

    # 2. Tabel Hard Constraint 18 Metode (tampil penuh, 18 baris)
    st.markdown("#### 1. Evaluasi Hard Constraint Geologi & Reservoir (18 Metode)")
    st.caption("Kriteria kelayakan: Metode harus kompatibel dengan Aquifer Drive DAN High Heterogeneity (G × H = 1).")

    df_hc = pd.DataFrame([
        {
            "ID": m["id_old"],
            "Method": m["name"],
            "Drive: Aquifer Drive (G)": m["drive_aquifer"],
            "Heterogeneity: High (H)": m["hetero_high"],
            "Status": "✅ Lolos" if m["lolos"] == 1 else "❌ Eliminasi",
            "Alasan Ringkas": f"Aquifer: {m['alasan_aquifer']} | Hetero: {m['alasan_hetero']}",
            # Detail penuh untuk CSV
            "Alasan (Aquifer Drive)": m["alasan_aquifer"],
            "Alasan (High Heterogeneity)": m["alasan_hetero"],
        }
        for m in methods_18
    ])

    # Tampilkan kolom ringkas di layar
    cols_hc_view = ["ID", "Method", "Drive: Aquifer Drive (G)", "Heterogeneity: High (H)", "Status", "Alasan Ringkas"]
    st.dataframe(df_hc[cols_hc_view], use_container_width=True, hide_index=True)

    # 3. Expander Matriks Kompatibilitas 18x18 dengan angka tercetak di setiap sel
    with st.expander("🧩 Lihat Matriks Kompatibilitas 18×18 (Heatmap Lengkap dengan Angka)", expanded=False):
        st.markdown(
            "Setiap pasangan metode dievaluasi: **2** = Sinergis Kuat, **1** = Layak, **0** = Bertentangan/Inkompatibel, **-** = Diagonal Sendiri. "
            "Suatu kombinasi hanya lolos jika **seluruh** pasangan metode di dalamnya bernilai > 0."
        )
        fig_heat = create_compat_heatmap(methods_18, compat_matrix)
        st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")

    # 4. Tabel 453 Kombinasi Lolos (Tampil ringkas, search box kontrol utama)
    st.markdown("#### 2. Daftar 453 Kombinasi Lolos Final (Yang Dilanjutkan ke Pemodelan Finansial)")
    st.caption("Komposisi ukuran: Ukuran 1 = 13 skenario, Ukuran 2 = 65 skenario, Ukuran 3 = 161 skenario, Ukuran 4 = 214 skenario.")

    # Kontrol utama: Pencarian nama kombinasi
    search_query = st.text_input(
        "Cari nama kombinasi / metode:",
        value="",
        placeholder="Contoh: Polymer, Water Shutoff, Gel, Infill...",
        key="tab2_search_query",
    )

    # Filter lanjutan di dalam expander
    with st.expander("⚙️ Filter Lanjutan (Ukuran Kombinasi)", expanded=False):
        filter_sz = st.multiselect(
            "Pilih Ukuran Kombinasi:",
            options=[1, 2, 3, 4],
            default=[1, 2, 3, 4],
            key="tab2_size_filter",
        )

    df_combos = pd.DataFrame([
        {
            "No": c["no"],
            "Ukuran": c["size"],
            "ID 1": str(c["id_1"]) if c["id_1"] is not None else "",
            "ID 2": str(c["id_2"]) if c["id_2"] is not None else "",
            "ID 3": str(c["id_3"]) if c["id_3"] is not None else "",
            "ID 4": str(c["id_4"]) if c["id_4"] is not None else "",
            "Kombinasi": c["name"],
        }
        for c in combos_453
    ])

    if filter_sz:
        df_combos = df_combos[df_combos["Ukuran"].isin(filter_sz)]
    if search_query:
        df_combos = df_combos[df_combos["Kombinasi"].str.contains(search_query, case=False, na=False)]

    if len(df_combos) == 0:
        st.warning(f"Tidak ada skenario yang cocok dengan pencarian '{search_query}'. Coba kata kunci lain atau reset filter.")
    else:
        st.caption(f"Menampilkan {len(df_combos)} dari 453 kombinasi lolos")
        render_compact_table(
            df=df_combos,
            core_cols=["No", "Ukuran", "Kombinasi"],
            all_cols=["No", "Ukuran", "ID 1", "ID 2", "ID 3", "ID 4", "Kombinasi"],
            download_filename="Athena_Tab2_453_Passed_Combinations.csv",
            key_prefix="tab2_combos",
            height=420,
        )

    render_footnote()
