"""
UI Tab 7: Contoh Perhitungan (Audit Trail Tahunan) (uiux.md compliant)
Tujuan: "Begini rincian hitungan tahun-per-tahun untuk satu skenario, bisa ditelusuri sampai ke rumus."
"""

import streamlit as st
import pandas as pd
import numpy as np
from athena_app.ui.components import (
    render_kpi_card,
    render_footnote,
    get_selected_scenario,
    set_selected_scenario,
)
from athena_app.core.worked_example import (
    generate_detailed_annual_block,
    build_parameter_comparison_table,
)


def render_tab7(engine_results: dict):
    st.subheader("7. Contoh Perhitungan (Audit Trail Tahunan)")
    st.markdown(
        "*Verifikasi transparansi matematis penuh: Pembuktian arus volumetrik dan finansial tahun-per-tahun (2026–2040) "
        "yang dapat diaudit hingga formula sel.*"
    )

    ed = engine_results["existing_data"]
    cp = engine_results["contoh_perhitungan"]
    bau_data = engine_results["bau_data"]
    sa_scenarios = engine_results["sa_scenarios"]

    # 1. Scenario Picker & Radio Harga (uiux.md §4 Tab 7)
    # Default otomatis mengikuti skenario terakhir di Tab 4/5/6
    current_selected = get_selected_scenario()
    sa_nos = [s["no"] for s in sa_scenarios]

    scenario_options = ["BAU"] + sa_nos
    label_map_tab7 = {"BAU": "🏢 Baseline BAU (Business-As-Usual — Tanpa Intervensi)"}
    for s in sa_scenarios:
        label_map_tab7[s["no"]] = f"Skenario #{s['no']} (Rank {s['sa_rank']}) — {s['kombinasi']}"

    default_idx = (1 + sa_nos.index(current_selected)) if current_selected in sa_nos else 1

    c_sel1, c_sel2 = st.columns([2.5, 1])
    with c_sel1:
        sel_choice = st.selectbox(
            "Pilih Skenario untuk Diaudit Rinci (Otomatis Tersinkronisasi dari Tab 4/5/6):",
            options=scenario_options,
            index=default_idx,
            format_func=lambda x: label_map_tab7.get(x, f"Skenario #{x}"),
            key="tab7_scenario_picker",
            help="Pilihan skenario ini otomatis mengikuti skenario terakhir yang dipilih pada Tab 4 atau Tab 5.",
        )
    with c_sel2:
        sel_price = st.radio(
            "Tingkat Harga Minyak:",
            options=[64.0, 80.0, 117.0],
            index=1,
            horizontal=True,
            format_func=lambda x: f"{int(x)}$ USD/bbl",
            key="tab7_price_radio",
        )

    is_bau = (sel_choice == "BAU")
    if not is_bau:
        set_selected_scenario(sel_choice)
        selected_scenario = next(s for s in sa_scenarios if s["no"] == sel_choice)
        block_result = generate_detailed_annual_block(selected_scenario, sel_price, ed, cp, bau_data, is_bau=False)
        scenario_title = f"Skenario #{sel_choice} (Rank {selected_scenario['sa_rank']})"
    else:
        selected_scenario = None
        block_result = generate_detailed_annual_block({}, sel_price, ed, cp, bau_data, is_bau=True)
        scenario_title = "Baseline BAU"

    dec = block_result["decision_metrics"]

    # 2. 7 KPI Card Ringkas di Atas (uiux.md §4 Tab 7)
    st.markdown("##### 📌 Metrik Keputusan Finansial Skenario Terpilih:")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("PNE Take (SA)", f"{dec['SA']['Take']/1e6:,.2f} M USD", help_text="Total Net Income 15 tahun Stand-Alone")
    with k2:
        render_kpi_card("NPV,10% (SA)", f"{dec['SA']['NPV,10']/1e6:,.2f} M USD", help_text="Net Present Value pada DR 10% Stand-Alone")
    with k3:
        irr_sa_disp = f"{dec['SA']['IRR']*100:.2f}%" if isinstance(dec['SA']['IRR'], (int, float)) else str(dec['SA']['IRR'])
        render_kpi_card("IRR (SA)", irr_sa_disp, help_text="Internal Rate of Return inkremental vs BAU")
    with k4:
        render_kpi_card("Government Take", f"{dec['SA']['Gov. Take']/1e6:,.2f} M USD", help_text="Total bagian pemerintah (split + pajak)")

    k5, k6, k7, _ = st.columns(4)
    with k5:
        render_kpi_card("NPV,10% PNE (FI)", f"{dec['PNE (FI)']['NPV,10']/1e6:,.2f} M USD", delta="60% WI", help_text="NPV PT PNE dalam skema Farm-In")
    with k6:
        render_kpi_card("NPV,10% XYZ (FI)", f"{dec['XYZ (FI)']['NPV,10']/1e6:,.2f} M USD", delta="40% WI", help_text="NPV Partner XYZ dalam skema Farm-In")
    with k7:
        irr_pne_disp = f"{dec['PNE (FI)']['IRR']*100:.2f}%" if isinstance(dec['PNE (FI)']['IRR'], (int, float)) else str(dec['PNE (FI)']['IRR'])
        render_kpi_card("IRR PNE (FI)", irr_pne_disp, help_text="IRR PT PNE dalam skema Farm-In")

    st.markdown("---")

    # 3. Tabel Parameter Teknis & Biaya Perlakuan (K-terpilih vs BAU)
    st.markdown(f"#### 1. Parameter Teknis & Asumsi Perlakuan: {scenario_title} vs BAU")
    st.caption("Perbandingan parameter perlakuan sumur (58 aktif, 87 idle) dan carry-forward capex.")

    if not is_bau:
        comp_data = build_parameter_comparison_table([selected_scenario], ed)
    else:
        comp_data = build_parameter_comparison_table([], ed)

    df_param = pd.DataFrame(comp_data)
    # Format baris
    def fmt_param_val(val):
        if isinstance(val, (int, float)):
            if abs(val) >= 1000:
                return f"{val:,.0f}"
            elif abs(val) > 0:
                return f"{val:.4f}"
            else:
                return "0"
    df_param_formatted = pd.DataFrame(comp_data)
    for c in df_param_formatted.columns:
        df_param_formatted[c] = df_param_formatted[c].apply(fmt_param_val)
    st.dataframe(df_param_formatted, use_container_width=True)

    st.markdown("---")

    # 4. Tabel Audit 34 Baris × 15 Tahun (uiux.md §4 Tab 7)
    st.markdown(f"#### 2. Tabel Audit Trail 34 Baris Akuntansi Permodelan: {scenario_title} (@{int(sel_price)}$ USD/bbl)")
    st.caption("Rincian tahunan 2026–2040 langkah-demi-langkah sesuai urutan baris sheet 'Contoh Perhitungan' V5.")

    rows_data = block_result["rows"]
    years = rows_data["Year"]
    year_cols = [str(y) for y in years]

    audit_rows = []
    # Daftar 34 baris sesuai PRD §4 Tab 7
    line_keys = [k for k in rows_data.keys() if k not in ["Year", "Year no"]]

    def format_audit_cell(val):
        if isinstance(val, (int, float)):
            if abs(val) >= 10000:
                return f"{val:,.0f}"
            elif abs(val) >= 1:
                return f"{val:,.2f}"
            elif abs(val) > 0:
                return f"{val:,.4f}"
            else:
                return "0"
        return str(val)

    for line_name in line_keys:
        line_vals = np.array(rows_data[line_name])
        # Hitung kolom evaluasi / total
        lower_name = line_name.lower()
        if "cut" in lower_name or "lifting cost (usd" in lower_name or line_name == "DF":
            eval_val = "-"
        elif "cum." in lower_name:
            eval_val = float(line_vals[-1])  # Nilai kumulatif akhir
        else:
            eval_val = float(np.sum(line_vals))

        row_dict = {"Komponen Akuntansi / Arus": str(line_name)}
        for idx, y_col in enumerate(year_cols):
            row_dict[y_col] = format_audit_cell(line_vals[idx])
        row_dict["Total / Evaluasi"] = format_audit_cell(eval_val) if eval_val != "-" else "-"
        audit_rows.append(row_dict)

    df_audit_34 = pd.DataFrame(audit_rows)

    st.dataframe(
        df_audit_34,
        use_container_width=True,
        hide_index=True,
        height=540,
        column_config={
            "Komponen Akuntansi / Arus": st.column_config.TextColumn(
                "Komponen Akuntansi / Arus",
                pinned=True,
            )
        },
    )

    csv_audit = df_audit_34.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"⬇️ Unduh Audit Trail Lengkap ({scenario_title}, {int(sel_price)}$ USD/bbl) (CSV)",
        data=csv_audit,
        file_name=f"Athena_Tab7_AuditTrail_{'BAU' if is_bau else f'Kombinasi_{sel_choice}'}_{int(sel_price)}USD.csv",
        mime="text/csv",
        key="tab7_download_audit",
    )

    render_footnote()
