"""
UI Tab 3: Variabel Inti (uiux.md compliant)
Tujuan: "Ini angka-angka dasar (teknis, biaya, probabilitas) yang jadi bahan baku semua perhitungan finansial."
Layout: Scroll vertikal tunggal dengan 4 seksi (A, B, C, D) — tanpa sub-tab bersarang.
"""

import streamlit as st
import pandas as pd
from athena_app.ui.components import (
    render_kpi_card,
    render_compact_table,
    render_footnote,
    get_pool_display_name,
)
from athena_app.config.v5_cell_map import EXISTING_DATA_MAP, CONTOH_PERHITUNGAN_MAP
from athena_app.core.costs import calculate_costs_per_well


def render_tab3(engine_results: dict):
    st.subheader("3. Variabel Inti")
    st.markdown(
        "*Ini angka-angka dasar (teknis, biaya, probabilitas) yang jadi bahan baku semua perhitungan finansial Lapangan Athena.*"
    )

    ed = engine_results["existing_data"]
    cp = engine_results["contoh_perhitungan"]
    methods_18 = engine_results["methods_18"]
    breakdown_items = engine_results["breakdown_items"]
    combos_453 = engine_results["combos_453"]
    contingency_list = engine_results["contingency_list"]
    costs_list = engine_results["costs_list"]

    # ==========================================================================
    # SEKSI A — PROFIL LAPANGAN (8 KPI CARDS + EXPANDER AUDIT)
    # ==========================================================================
    st.markdown("#### Seksi A — Profil Lapangan Athena (Data Existing & Asumsi PSC)")
    st.caption("Parameter geologi, operasional, dan fiskal kontrak bagi hasil PSC (2026–2040).")

    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    with r1_c1:
        render_kpi_card("Produksi Minyak Awal (q0)", f"{ed['q0']:,.0f} bopd", help_text="Existing Data!C3")
    with r1_c2:
        render_kpi_card("Water Cut Awal (wc0)", f"{ed['wc0']*100:.1f} %", help_text="Existing Data!C4")
    with r1_c3:
        render_kpi_card("Decline Baseline (d0)", f"{ed['d0']*100:.2f} %/thn", help_text="Existing Data!C5")
    with r1_c4:
        render_kpi_card("Cadangan 2P Tersisa", f"{ed['reserve_2p']/1e6:,.1f} MMbbl", help_text="Existing Data!C9")

    r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
    with r2_c1:
        render_kpi_card("Sumur Aktif / Idle", f"{ed['n_active']} / {ed['n_idle']}", help_text="Existing Data!C7:C8")
    with r2_c2:
        render_kpi_card("Lifting Cost (lc0)", f"{ed['lc0']:,.0f} USD/bbl", delta="+3.0%/thn inflasi", help_text="Existing Data!C11")
    with r2_c3:
        render_kpi_card("Split Kontraktor : Gov", f"{ed['split_c']*100:.0f}% : {ed['split_g']*100:.0f}%", help_text="Existing Data!C13:C14")
    with r2_c4:
        render_kpi_card("Pajak Penghasilan", f"{ed['tax']*100:.0f} %", delta="Discount Rate: 10%", help_text="Existing Data!C15 & C17")

    with st.expander("🔍 Lihat Semua Parameter Lapangan & Alamat Sel V5 (Tabel Audit)", expanded=False):
        table_rows = []
        for k, info in EXISTING_DATA_MAP.items():
            val = ed.get(k, info["expected"])
            table_rows.append({
                "Parameter": k,
                "Deskripsi": info["desc"],
                "Nilai": val,
                "Satuan": info["unit"],
                "Alamat Sel V5": f"Existing Data!{info['cell']}",
            })
        for k, info in CONTOH_PERHITUNGAN_MAP.items():
            val = cp.get(k, info["expected"])
            table_rows.append({
                "Parameter": k,
                "Deskripsi": info["desc"],
                "Nilai": val,
                "Satuan": info["unit"],
                "Alamat Sel V5": f"Contoh Perhitungan!{info['cell']}",
            })
        df_params = pd.DataFrame(table_rows)
        st.dataframe(df_params, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ==========================================================================
    # SEKSI B — PARAMETER 13 METODE (p, r, u + BIAYA) — WAJIB SELALU TERLIHAT
    # ==========================================================================
    st.markdown("#### Seksi B — Parameter 13 Metode Terpilih (p, r, u & Biaya per Sumur)")
    st.caption(
        "Tabel rujukan utama: Probabilitas Sukses (p), Penurunan Water Cut (r), Uplift Produksi (u), "
        "serta biaya CAPEX dan OPEX per sumur untuk setiap metode mandiri."
    )

    methods_13 = engine_results["methods_13"]
    rows_m13 = []
    for m in methods_13:
        id_new = m["id_new"]
        costs_single = calculate_costs_per_well([id_new], breakdown_items)
        rows_m13.append({
            "ID (Baru)": id_new,
            "ID (Lama)": m["id_old"],
            "Method": m["name"],
            "Class": m["class"],
            "p (Probabilitas Sukses)": m["p"],
            "r (Penurunan WC)": m["r"],
            "u (Uplift Produksi)": m["u"],
            "CAPEX/sumur (USD)": costs_single["capex_well"],
            "OPEX/sumur/thn (USD)": costs_single["opex_well"],
        })

    df_m13 = pd.DataFrame(rows_m13)
    fmt_m13 = {
        "p (Probabilitas Sukses)": "{:.2%}",
        "r (Penurunan WC)": "{:.2%}",
        "u (Uplift Produksi)": "{:.2%}",
        "CAPEX/sumur (USD)": "{:,.0f} $",
        "OPEX/sumur/thn (USD)": "{:,.0f} $",
    }
    st.dataframe(
        df_m13.style.format(fmt_m13),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    # ==========================================================================
    # SEKSI C — RINCIAN BIAYA PER ITEM (108 BARIS) — DALAM EXPANDER
    # ==========================================================================
    with st.expander("💰 Seksi C — Lihat Rincian 108 Item Biaya (CAPEX/OPEX Breakdown per Pool)", expanded=False):
        st.markdown(
            "Rincian item biaya dari sheet `CAPEX OPEX Breakdown`. "
            "Item bertanda aturan **'Sekali'** memakai nilai maksimum per pool (max pooling), "
            "sedangkan item bertanda **'Jumlah'** dijumlahkan langsung."
        )

        all_unique_pools = sorted(list(set(it["pool"] for it in breakdown_items if it.get("pool"))))

        st.caption(
            "Pool Biaya mengelompokkan item menurut jenis pekerjaan. Item 'Sekali' dalam pool yang sama hanya dihitung satu kali per kombinasi (diambil yang termahal antar metode), karena sumber dayanya dipakai bersama — misalnya satu mobilisasi rig. Item 'Jumlah' dihitung untuk setiap metode."
        )
        col_f1, col_f2, col_f3 = st.columns([1, 1.8, 1.2])
        with col_f1:
            sel_type = st.multiselect("Filter Tipe Biaya:", ["CAPEX", "OPEX"], default=["CAPEX", "OPEX"], key="tab3_c_type")
        with col_f2:
            sel_pool = st.multiselect(
                "Filter Pool Biaya:",
                all_unique_pools,
                default=all_unique_pools,
                format_func=lambda p: f"{p} — {get_pool_display_name('CAPEX' if 'CAPEX' in sel_type and 'OPEX' not in sel_type else ('OPEX' if 'OPEX' in sel_type and 'CAPEX' not in sel_type else ''), p)}",
                key="tab3_c_pool"
            )
        with col_f3:
            st.caption(
                "'Sekali' = biaya pool dihitung satu kali untuk seluruh kombinasi (nilai maksimum antar metode, karena fasilitas/sumber daya bisa dipakai bersama). 'Jumlah' = biaya dijumlah penuh untuk setiap metode dalam kombinasi. Aturan ini selalu sama untuk semua item dalam satu pool."
            )
            sel_rule = st.multiselect("Filter Aturan Pool:", ["Sekali", "Jumlah"], default=["Sekali", "Jumlah"], key="tab3_c_rule")

        df_brk = pd.DataFrame([
            {
                "Baris V6_1": it["row"],
                "ID Metode": str(it["method_id"]),
                "Tipe Biaya": it["cost_type"],
                "Nama Item": it["name"],
                "Kode Pool": it["pool"],
                "Nama Pool": get_pool_display_name(it["cost_type"], it["pool"]),
                "Aturan": it["rule"],
                "Volume (F)": str(it["vol"]) if it["vol"] is not None else "-",
                "Harga Satuan (H)": f"{it['unit_price']:,.0f}" if it["unit_price"] is not None else "-",
                "Frekuensi/thn (J)": str(it["freq"]) if it["freq"] is not None else "-",
                "Nilai (USD/sumur)": it["value"],
            }
            for it in breakdown_items
        ])

        filtered_brk = df_brk[
            df_brk["Tipe Biaya"].isin(sel_type) & 
            df_brk["Kode Pool"].isin(sel_pool) & 
            df_brk["Aturan"].isin(sel_rule)
        ]
        st.dataframe(
            filtered_brk.style.format({"Nilai (USD/sumur)": "{:,.0f}"}),
            use_container_width=True,
            hide_index=True,
            height=380,
        )

        csv_brk = filtered_brk.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Unduh 108 Item Biaya (CSV)",
            data=csv_brk,
            file_name="Athena_Tab3_CAPEX_OPEX_Breakdown_108.csv",
            mime="text/csv",
            key="tab3_dl_brk",
        )

    # ==========================================================================
    # SEKSI D — CONTINGENCY RATE COMBINATION (453 BARIS) — DALAM EXPANDER
    # ==========================================================================
    with st.expander("⚙️ Seksi D — Lihat Perhitungan Detail 453 Kombinasi (Contingency Rate Combination)", expanded=False):
        st.markdown(
            "Tabel teknis kalkulasi interaksi antar-metode: Overlap probabilitas, Contingency Rate (S), "
            "Penurunan Water Cut (V), Yield Uplift, Batas Fisik, Uplift Dipakai (AG), dan Biaya Gabungan per Sumur."
        )

        search_crc = st.text_input("Cari nama kombinasi di Tabel CRC:", value="", placeholder="Ketik nama skenario...", key="tab3_search_crc")

        crc_rows = []
        for i, c in enumerate(combos_453):
            cont = contingency_list[i]
            cst = costs_list[i]
            p_vals = cont["p_vals"]
            r_vals = cont["r_vals"]
            u_vals = cont["u_vals"]

            row = {
                "No": c["no"],
                "Kombinasi": c["name"],
                "Ukuran": c["size"],
                "Contingency Rate (S)": cont["contingency_rate"],
                "Penurunan WC (V)": cont["wc_reduction_success"],
                "WC Baru (Sukses)": cont["wc_new_success"],
                "Uplift Dipakai (AG)": cont["u_used"],
                "Yield u/r": cont["yield_ur"],
                "Batas Fisik (WC)": cont["physical_limit_wc"],
                "Kenaikan Minyak Ekspektasi": cont["oil_increase_expected"],
                "CAPEX/sumur (USD)": cst["capex_well"],
                "OPEX/sumur/thn (USD)": cst["opex_well"],
                # Detail internal
                "ID 1": str(c["id_1"]) if c["id_1"] is not None else "",
                "ID 2": str(c["id_2"]) if c["id_2"] is not None else "",
                "ID 3": str(c["id_3"]) if c["id_3"] is not None else "",
                "ID 4": str(c["id_4"]) if c["id_4"] is not None else "",
                "Rata-rata Overlap": cont["p_overlap"],
                "p Independen": cont["p_indep"],
                "p Tertinggi": cont["p_max"],
                "r Independen": cont["r_indep"],
                "r Tertinggi": cont["r_max"],
                "u Gabungan": cont["u_combined"],
            }
            crc_rows.append(row)

        df_crc = pd.DataFrame(crc_rows)
        if search_crc:
            display_df_crc = df_crc[df_crc["Kombinasi"].str.contains(search_crc, case=False, na=False)]
        else:
            display_df_crc = df_crc

        core_crc_cols = [
            "No", "Ukuran", "Kombinasi", "Contingency Rate (S)", "Penurunan WC (V)",
            "WC Baru (Sukses)", "Uplift Dipakai (AG)", "CAPEX/sumur (USD)", "OPEX/sumur/thn (USD)"
        ]
        all_crc_cols = list(df_crc.columns)

        fmt_crc = {
            "Contingency Rate (S)": "{:.4f}",
            "Penurunan WC (V)": "{:.4f}",
            "WC Baru (Sukses)": "{:.4f}",
            "Uplift Dipakai (AG)": "{:.4f}",
            "Yield u/r": "{:.4f}",
            "Batas Fisik (WC)": "{:.4f}",
            "Kenaikan Minyak Ekspektasi": "{:.4f}",
            "CAPEX/sumur (USD)": "{:,.0f} $",
            "OPEX/sumur/thn (USD)": "{:,.0f} $",
        }

        render_compact_table(
            df=display_df_crc,
            core_cols=core_crc_cols,
            all_cols=all_crc_cols,
            download_filename="Athena_Tab3_Contingency_Rate_Combination_453.csv",
            key_prefix="tab3_crc",
            height=400,
            format_dict=fmt_crc,
        )

    render_footnote()
