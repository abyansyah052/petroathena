"""
UI Tab 4: Financial Projection (Stand-Alone), Ranking & Sensitivitas (uiux.md compliant)
Titik Keputusan #1: "Dari 453 skenario, mana yang paling baik secara finansial — dan kenapa?"
"""

import streamlit as st
import pandas as pd
import numpy as np
from athena_app.ui.components import (
    render_kpi_card,
    render_insight_callout,
    render_compact_table,
    render_scenario_picker,
    render_footnote,
    set_selected_scenario,
    get_selected_scenario,
)
from athena_app.ui.charts import (
    create_top10_comparison_chart,
    create_spider_line_chart,
    create_tornado_chart,
    create_heatmap_3x3,
    create_all_scenarios_scatter,
    create_rank_breakdown_chart,
)


from athena_app.core.worked_example import get_worked_example_for_scenario


def render_tab4(engine_results: dict):
    st.subheader("4. Financial Projection (Stand-Alone), Ranking & Sensitivitas ★")
    st.markdown(
        "*Dari 453 skenario, mana yang paling unggul secara finansial — dan apa alasan teknis di baliknya?*"
    )

    df_tab4 = engine_results["df_tab4"]
    sa_scenarios = engine_results["sa_scenarios"]
    bau_data = engine_results["bau_data"]
    top10_sa = engine_results["top10_sa"]

    # Active price dari session_state sebagai single source of truth (Addendum §5.3)
    active_price = int(st.session_state.get("selected_price", 80))
    if active_price not in [64, 80, 117]:
        active_price = 80

    best_scenario = top10_sa[0]
    best_no = best_scenario["no"]

    # 1. Empat KPI Card Skenario Rank 1 (uiux.md §4 Tab 4)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            label="🏆 Skenario Rekomendasi (Rank 1)",
            value=f"#{best_no}",
            delta=f"{best_scenario['kombinasi'][:22]}..",
            help_text=f"Kombinasi lengkap: {best_scenario['kombinasi']}",
            is_gold=True,
        )
    with k2:
        render_kpi_card(
            label="Skor Rata-Rata Rank",
            value=f"{best_scenario['sa_score']:.4f}",
            delta="Peringkat 1 dari 453",
            help_text="Rata-rata dari 15 peringkat metrik finansial pada harga 64$, 80$, 117$ USD/bbl",
        )
    with k3:
        npv10_val = best_scenario["metrics"]["prices"][active_price]["npv10"] / 1e6
        pne_take_val = best_scenario["metrics"]["prices"][active_price]["pne_take"] / 1e6
        render_kpi_card(
            label=f"NPV,10% @{active_price}$ (Rank 1)",
            value=f"{npv10_val:,.2f} M USD",
            delta=f"PNE Take: {pne_take_val:,.1f} M USD",
            help_text=f"Net Present Value pada discount rate 10% dan harga minyak acuan {active_price}$ USD/bbl",
        )
    with k4:
        irr_val = best_scenario["metrics"]["prices"][active_price]["irr"]
        irr_str = f"{irr_val*100:.2f} %" if isinstance(irr_val, (int, float)) else str(irr_val)
        render_kpi_card(
            label=f"IRR @{active_price}$ (Rank 1)",
            value=irr_str,
            delta=f"Total CAPEX: {best_scenario['flows']['total_cpx']/1e6:,.2f} M USD",
            help_text=f"Internal Rate of Return arus kas inkremental terhadap baseline BAU pada harga {active_price}$",
        )

    # 2. 💡 Automated Insight Callout (uiux.md §1 Prinsip 6 & §4 Tab 4)
    other_capex = np.mean([s["flows"]["total_cpx"] for s in top10_sa[1:]])
    diff_capex_pct = (best_scenario["flows"]["total_cpx"] - other_capex) / other_capex * 100
    capex_comp_word = "lebih hemat" if diff_capex_pct < 0 else "lebih tinggi"

    insight_text = (
        f"Skenario <strong>#{best_no} ({best_scenario['kombinasi']})</strong> kokoh menempati <strong>Rank 1 dari 453</strong> "
        f"dengan Skor <strong>{best_scenario['sa_score']:.4f}</strong>. Dibandingkan rata-rata Top-10 lainnya, "
        f"kebutuhan CAPEX-nya <strong>{abs(diff_capex_pct):.1f}% {capex_comp_word}</strong> "
        f"({best_scenario['flows']['total_cpx']/1e6:,.2f}M vs {other_capex/1e6:,.2f}M USD) "
        f"dengan IRR @{active_price}$ mencapai <strong>{irr_str}</strong> dan NPV,10% sebesar <strong>{npv10_val:,.2f} M USD</strong>."
    )
    render_insight_callout(insight_text)

    # 3. Scenario Picker Global (uiux.md §2.3 d & §4 Tab 4)
    label_map = {
        s["no"]: f"Skenario #{s['no']} (Rank {df_tab4.loc[df_tab4['No']==s['no'], 'RANK (1 = terbaik)'].values[0]}) — {s['kombinasi']}"
        for s in sa_scenarios
    }
    sorted_options = df_tab4.sort_values("RANK (1 = terbaik)")["No"].tolist()

    st.markdown("##### 🎯 Pilih Skenario Fokus Analisis:")
    selected_no = render_scenario_picker(
        options=sorted_options,
        label_map=label_map,
        key="tab4_scenario_picker",
        label="Skenario Terpilih (Otomatis Tersinkronisasi ke Tab 5 & Contoh Perhitungan):",
    )

    selected_row = df_tab4[df_tab4["No"] == selected_no].iloc[0]
    selected_scenario = next(s for s in sa_scenarios if s["no"] == selected_no)

    # ==========================================================================
    # SECTION CONTOH PERHITUNGAN DETAIL (Addendum §5.4: SEBELUM SEMUA CHART)
    # ==========================================================================
    with st.expander("📊 Lihat Contoh Perhitungan Lengkap untuk Skenario Terpilih", expanded=False):
        st.markdown(
            f"**Audit Trail Akuntansi & Volumetrik 15 Tahun: Skenario #{selected_no} — {selected_row['Kombinasi']} "
            f"(@{active_price}$ USD/bbl)**"
        )
        st.caption(
            "Rincian ini menghitung dinamis untuk skenario terpilih di Scenario Picker (kondisi awal: Rank 1). "
            "Mencakup 34 baris akuntansi PSC cash flow dan tabel parameter perlakuan sumur."
        )

        we_data = get_worked_example_for_scenario(selected_no, float(active_price), engine_results)
        dec = we_data["block"]["decision_metrics"]

        # Mini KPI untuk skenario terpilih
        w_k1, w_k2, w_k3, w_k4 = st.columns(4)
        with w_k1:
            render_kpi_card("PNE Take (SA)", f"{dec['SA']['Take']/1e6:,.2f} M USD", help_text="Total Net Income 15 tahun Stand-Alone")
        with w_k2:
            render_kpi_card("NPV,10% (SA)", f"{dec['SA']['NPV,10']/1e6:,.2f} M USD", help_text=f"Net Present Value pada DR 10% (@{active_price}$)")
        with w_k3:
            irr_sa_disp = f"{dec['SA']['IRR']*100:.2f}%" if isinstance(dec['SA']['IRR'], (int, float)) else str(dec['SA']['IRR'])
            render_kpi_card("IRR (SA)", irr_sa_disp, help_text="Internal Rate of Return inkremental vs BAU")
        with w_k4:
            render_kpi_card("Gov. Take", f"{dec['SA']['Gov. Take']/1e6:,.2f} M USD", help_text="Total bagian pemerintah")

        # Tabel Parameter Perlakuan
        st.markdown(f"##### 1. Parameter Teknis & Asumsi Perlakuan: Skenario #{selected_no} vs BAU")
        df_param = pd.DataFrame(we_data["param_table"])
        def _fmt_p(val):
            if isinstance(val, (int, float)):
                return f"{val:,.0f}" if abs(val) >= 1000 else (f"{val:.4f}" if abs(val) > 0 else "0")
            return str(val)
        df_param_fmt = df_param.map(_fmt_p) if hasattr(df_param, "map") else df_param.applymap(_fmt_p)
        st.dataframe(df_param_fmt, use_container_width=True)

        # Tabel Audit 34 Baris
        st.markdown(f"##### 2. Tabel Audit Trail 34 Baris Akuntansi Permodelan (@{active_price}$ USD/bbl)")
        rows_data = we_data["block"]["rows"]
        years = rows_data["Year"]
        year_cols = [str(y) for y in years]
        line_keys = [k for k in rows_data.keys() if k not in ["Year", "Year no"]]

        def _fmt_c(val):
            if isinstance(val, (int, float)):
                if abs(val) >= 10000:
                    return f"{val:,.0f}"
                elif abs(val) >= 1:
                    return f"{val:,.2f}"
                elif abs(val) > 0:
                    return f"{val:,.4f}"
                return "0"
            return str(val)

        audit_rows = []
        for line_name in line_keys:
            line_vals = np.array(rows_data[line_name])
            lower_name = line_name.lower()
            if "cut" in lower_name or "lifting cost (usd" in lower_name or line_name == "DF":
                eval_val = "-"
            elif "cum." in lower_name:
                eval_val = float(line_vals[-1])
            else:
                eval_val = float(np.sum(line_vals))

            row_dict = {"Komponen Akuntansi / Arus": str(line_name)}
            for idx, y_col in enumerate(year_cols):
                row_dict[y_col] = _fmt_c(line_vals[idx])
            row_dict["Total / Evaluasi"] = _fmt_c(eval_val) if eval_val != "-" else "-"
            audit_rows.append(row_dict)

        df_audit_34 = pd.DataFrame(audit_rows)
        st.dataframe(
            df_audit_34,
            use_container_width=True,
            hide_index=True,
            height=380,
            column_config={
                "Komponen Akuntansi / Arus": st.column_config.TextColumn(
                    "Komponen Akuntansi / Arus",
                    pinned=True,
                )
            },
        )

        csv_audit = df_audit_34.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"⬇️ Unduh Audit Trail Skenario #{selected_no} ({active_price}$ USD) (CSV)",
            data=csv_audit,
            file_name=f"Athena_AuditTrail_Skenario_{selected_no}_{active_price}USD.csv",
            mime="text/csv",
            key=f"tab4_dl_audit_{selected_no}_{active_price}",
        )

    # 4. Chart Utama: Grouped Bar Top-10 dengan outline gold dinamis
    st.markdown("---")
    fig_top10 = create_top10_comparison_chart(top10_sa, selected_no=selected_no)
    st.plotly_chart(fig_top10, use_container_width=True)

    # Expander 1: Analisis Sensitivitas untuk Skenario Terpilih (Dinamis thd selected_no)
    with st.expander(f"📈 Analisis Sensitivitas Skenario #{selected_no} (Spider, Tornado & Heatmap 3×3)", expanded=False):
        st.caption(f"Parameter sensitivitas diperbarui otomatis untuk Skenario #{selected_no} ({selected_scenario['kombinasi']}).")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.plotly_chart(create_spider_line_chart(selected_scenario, bau_data), use_container_width=True)
        with col_g2:
            st.plotly_chart(create_tornado_chart(selected_scenario), use_container_width=True)

        st.plotly_chart(create_heatmap_3x3(selected_scenario), use_container_width=True)

    # Expander 2: Transparansi Skor (15 Peringkat Metrik)
    with st.expander(f"🔍 Transparansi Skor: Mengapa Skenario #{selected_no} Mendapat Skor {selected_row['Skor (Rata-rata rank)']:.4f}?", expanded=False):
        st.markdown(
            "Skor dihitung objektif tanpa bobot subjektif sebagai **rata-rata dari 15 peringkat metrik finansial** "
            "(PNE Take, NPV,8, NPV,10, NPV,12, dan IRR pada harga 64$, 80$, dan 117$ USD/bbl). "
            "Peringkat 1 = terbaik di antara seluruh 453 skenario."
        )
        st.plotly_chart(create_rank_breakdown_chart(selected_scenario, selected_row), use_container_width=True)

    # Expander 3: Peta Seluruh 453 Skenario (Scatter)
    with st.expander("🌐 Peta Lanskap Seluruh 453 Skenario (Scatter Plot CAPEX vs NPV,10%)", expanded=False):
        scatter_price = st.radio(
            "Tingkat Harga Minyak untuk Lanskap Scatter:",
            options=[64, 80, 117],
            index=1,
            horizontal=True,
            format_func=lambda x: f"{x}$ USD/bbl",
            key="tab4_scatter_price",
        )
        st.plotly_chart(create_all_scenarios_scatter(df_tab4, price=scatter_price), use_container_width=True)

    st.markdown("---")

    # 5. Tabel Ringkas Master (uiux.md §4 Tab 4: <=12 kolom di layar)
    st.markdown("#### Tabel Peringkat Proyeksi Finansial Stand-Alone")
    st.caption("Pilih tingkat harga minyak untuk menyesuaikan kolom NPV, Take, dan IRR pada tabel ringkas.")

    col_t_price, col_t_sort = st.columns([1, 1])
    with col_t_price:
        price_opts = [64, 80, 117]
        p_idx = price_opts.index(active_price) if active_price in price_opts else 1

        def _on_tab4_price_change():
            st.session_state["selected_price"] = st.session_state["tab4_table_price"]

        tbl_price = st.radio(
            "Tingkat Harga Minyak Ditampilkan:",
            options=price_opts,
            index=p_idx,
            horizontal=True,
            format_func=lambda x: f"{x}$ USD/bbl (Acuan)",
            key="tab4_table_price",
            on_change=_on_tab4_price_change,
        )
        if tbl_price != active_price:
            st.session_state["selected_price"] = tbl_price
            active_price = tbl_price

    with col_t_sort:
        sort_by = st.selectbox("Urutan Baris:", ["RANK (1 = terbaik)", "Nomor Skenario (No)"], index=0, key="tab4_sort_order")

    # Filter lanjutan di dalam expander
    with st.expander("⚙️ Filter Lanjutan (Pencarian Nama & Filter Ukuran)", expanded=False):
        f_s1, f_s2 = st.columns([1, 2])
        with f_s1:
            size_filter = st.multiselect("Filter Ukuran:", [1, 2, 3, 4], default=[1, 2, 3, 4], key="tab4_adv_size")
        with f_s2:
            search_name = st.text_input("Cari nama metode/kombinasi:", value="", placeholder="Ketik kata kunci...", key="tab4_adv_search")

    display_df = df_tab4.copy()
    if sort_by == "RANK (1 = terbaik)":
        display_df = display_df.sort_values(["RANK (1 = terbaik)", "No"])
    else:
        display_df = display_df.sort_values("No")

    if size_filter:
        display_df = display_df[display_df["Ukuran"].isin(size_filter)]
    if search_name:
        display_df = display_df[display_df["Kombinasi"].str.contains(search_name, case=False, na=False)]

    if len(display_df) == 0:
        st.warning(f"Tidak ada skenario yang cocok dengan pencarian '{search_name}'. Coba kata kunci lain atau reset filter.")
    else:
        st.caption(f"Menampilkan {len(display_df)} dari 453 skenario.")

        # Core columns for compact view (<= 12 cols)
        core_cols = [
            "RANK (1 = terbaik)",
            "No",
            "Ukuran",
            "Kombinasi",
            "Skor (Rata-rata rank)",
            "Total CAPEX",
            f"{active_price}$ PNE Take",
            f"{active_price}$ NPV,10",
            f"{active_price}$ IRR",
        ]

        all_cols = list(df_tab4.columns)

        # Formatter
        format_dict = {
            "Contingency Rate": "{:.4f}",
            "Total Production": "{:,.0f} bbl",
            "Remaining Oil": "{:,.0f} bbl",
            "Total Water": "{:,.0f} bbl",
            "Total CAPEX": "{:,.0f} $",
            "Total OPEX": "{:,.0f} $",
            "Skor (Rata-rata rank)": "{:.4f}",
        }
        for P in [64, 80, 117]:
            format_dict[f"{P}$ PNE Take"] = "{:,.0f} $"
            format_dict[f"{P}$ Gov. Take"] = "{:,.0f} $"
            format_dict[f"{P}$ NPV,8"] = "{:,.0f} $"
            format_dict[f"{P}$ NPV,10"] = "{:,.0f} $"
            format_dict[f"{P}$ NPV,12"] = "{:,.0f} $"

        # View copy with IRR formatted as %
        df_view_formatted = display_df.copy()
        for P in [64, 80, 117]:
            c_irr = f"{P}$ IRR"
            df_view_formatted[c_irr] = df_view_formatted[c_irr].apply(
                lambda x: f"{float(x)*100:.2f}%" if isinstance(x, (int, float)) and np.isfinite(x) else str(x)
            )

        render_compact_table(
            df=df_view_formatted,
            core_cols=core_cols,
            all_cols=all_cols,
            download_filename="Athena_Tab4_Financial_Projection_SA.csv",
            key_prefix="tab4_table",
            height=440,
            format_dict=format_dict,
        )

    render_footnote()
