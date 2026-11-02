"""
Module ui/charts.py: Visualisasi interaktif Plotly sesuai PRD §4.6 & UI/UX Guidelines (uiux.md).
Menggunakan palette kontras tinggi yang ramah pembaca laporan finansial (latar bersih, angka jelas):
1. Funnel Chart Horizontal (Tab 2: 4.047 -> 1.092 -> 453)
2. Heatmap Kompatibilitas 18x18 dengan angka tercetak di setiap sel (Tab 2)
3. Grouped Bar Top-10 Stand-Alone dengan outline emas untuk skenario terpilih (Tab 4)
4. Spider / Line Chart NPV vs Harga Minyak (Tab 4)
5. Tornado Diagram Rentang Sensitivitas (Tab 4)
6. Heatmap 3x3 Sensitivitas Harga x DR (Tab 4)
7. Scatter Plot 453 Skenario CAPEX vs NPV10 (Tab 4)
8. Bar Chart Transparansi 15 Rank (Tab 4)
9. Grouped Bar Farm-In Top-10 PNE vs XYZ (Tab 5)
10. Bar Chart Transparansi 30 Rank Farm-In (Tab 5)
11. Grouped Bar Komparasi 3 Pihak SA vs PNE vs XYZ (Tab 6)
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


# Palette warna eksekutif kontras tinggi sesuai uiux.md
PALETTE = {
    "primary": "#1E88E5",      # Biru PNE / SA
    "secondary": "#00897B",    # Toska / XYZ
    "gold": "#FFB300",         # Emas Top-10 / Rank 1
    "danger": "#C62828",       # Merah Downside / Eliminasi
    "success": "#2E7D32",      # Hijau Upside / Lolos
    "neutral": "#757575",      # Abu-abu
    "dr8": "#0288D1",          # Cyan DR 8%
    "dr10": "#1E88E5",         # Biru DR 10%
    "dr12": "#5E35B1",         # Ungu DR 12%
    "bau": "#78909C",          # Abu-abu Garis BAU
    "bg_card": "#FFFFFF",
    "bg_canvas": "#F7F9FB",
    "text": "#1B1F23",
    "grid": "rgba(0, 0, 0, 0.08)",
}


def _apply_clean_layout(fig: go.Figure, title: str, subtitle: Optional[str] = None, height: int = 420):
    """Menerapkan layout bersih, kontras tinggi, background terang sesuai uiux.md."""
    full_title = f"<b>{title}</b>"
    if subtitle:
        full_title += f"<br><span style='font-size: 0.85rem; color: #5A6A80;'>{subtitle}</span>"

    fig.update_layout(
        title=full_title,
        paper_bgcolor=PALETTE["bg_card"],
        plot_bgcolor="#FAFAFC",
        font=dict(family="Inter, sans-serif", color=PALETTE["text"], size=12),
        margin=dict(l=45, r=30, t=65, b=45),
        height=height,
        xaxis=dict(
            gridcolor=PALETTE["grid"],
            zerolinecolor="rgba(0,0,0,0.15)",
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            gridcolor=PALETTE["grid"],
            zerolinecolor="rgba(0,0,0,0.15)",
            tickfont=dict(size=11),
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
    )
    return fig


# ==============================================================================
# TAB 2 CHARTS
# ==============================================================================

def create_horizontal_funnel(raw_count: int = 4047, hc_count: int = 1092, final_count: int = 453) -> go.Figure:
    """
    Funnel Chart Horizontal (Tab 2 §4.2): 4.047 -> 1.092 -> 453.
    """
    stages = [
        "1. Kombinasi Mentah",
        "2. Lolos Hard Constraint",
        "3. Lolos Kompatibilitas",
    ]
    values = [raw_count, hc_count, final_count]
    percents_raw = [f"{v/raw_count*100:.1f}% dari Awal" for v in values]
    labels = [
        f"<b>{s}</b><br>{v:,} skenario ({p})"
        for s, v, p in zip(stages, values, percents_raw)
    ]

    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        text=labels,
        textinfo="text",
        textposition="inside",
        textfont=dict(size=13, color="white", family="Inter, sans-serif"),
        marker=dict(
            color=["#455A64", "#1E88E5", "#00897B"],
            line=dict(width=1.5, color="#FFFFFF"),
        ),
        connector=dict(line=dict(color="#B0BEC5", width=1.5, dash="dot")),
        orientation="h",
    ))

    _apply_clean_layout(
        fig,
        "Funnel Penyaringan Skenario: 4.047 Mentah → 453 Skenario Layak",
        "Penyaringan dua tahap: Kesesuaian Reservoir (Aquifer & Heterogeneity) lalu Matriks Kompatibilitas Antar-Metode",
        height=320,
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return fig


def create_compat_heatmap(methods_18: List[Dict[str, Any]], compat_matrix: List[List[Any]]) -> go.Figure:
    """
    Heatmap 18x18 Kompatibilitas (Tab 2) dengan ANGKA TERLIHAT di tiap sel (accessibility compliant).
    """
    labels = [f"#{m['id_old']} {m['name'][:16]}.." for m in methods_18]
    z_vals = []
    text_vals = []

    for r in range(18):
        row_z = []
        row_t = []
        for c in range(18):
            val = compat_matrix[r][c]
            if val == "-":
                row_z.append(0.5)
                row_t.append("-")
            elif val == 0:
                row_z.append(0.0)
                row_t.append("0")
            elif val == 1:
                row_z.append(1.0)
                row_t.append("1")
            elif val == 2:
                row_z.append(2.0)
                row_t.append("2")
        z_vals.append(row_z)
        text_vals.append(row_t)

    fig = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=labels,
        y=labels,
        text=text_vals,
        texttemplate="<b>%{text}</b>",
        textfont=dict(size=10, color="white"),
        colorscale=[
            [0.0, "#C62828"],     # 0 = Merah
            [0.25, "#78909C"],    # - = Abu-abu
            [0.5, "#F57F17"],     # 1 = Kuning/Orange Layak
            [1.0, "#2E7D32"],     # 2 = Hijau Sinergis
        ],
        showscale=False,
        hoverongaps=False,
    ))

    _apply_clean_layout(
        fig,
        "Matriks Kompatibilitas 18×18 (Setiap Sel Memiliki Nilai Numerik)",
        "2 = Sinergis Kuat (Hijau), 1 = Layak (Oranye), 0 = Tidak Kompatibel (Merah), - = Diagonal Mandiri (Abu-abu)",
        height=620,
    )
    fig.update_layout(
        margin=dict(l=120, r=30, t=70, b=120),
        xaxis=dict(tickangle=-45, side="bottom"),
        yaxis=dict(autorange="reversed"),
    )
    return fig


# ==============================================================================
# TAB 4 CHARTS (STAND-ALONE)
# ==============================================================================

def create_top10_comparison_chart(
    top10_sa: List[Dict[str, Any]],
    selected_no: Optional[int] = None,
) -> go.Figure:
    """
    Grouped Bar Chart Top-10 Stand-Alone (Tab 4):
    Bar skenario yang sedang dipilih di Scenario Picker diberi outline gold tebal.
    """
    labels = [f"Rank {s['sa_rank']} (#{s['no']})<br>{s['kombinasi'][:18]}.." for s in top10_sa]
    val_64 = [s["metrics"]["prices"][64]["npv10"] / 1e6 for s in top10_sa]
    val_80 = [s["metrics"]["prices"][80]["npv10"] / 1e6 for s in top10_sa]
    val_117 = [s["metrics"]["prices"][117]["npv10"] / 1e6 for s in top10_sa]

    # Border width logic for selected scenario
    line_widths = [3.5 if s["no"] == selected_no else 0.8 for s in top10_sa]
    line_colors = ["#FFB300" if s["no"] == selected_no else "rgba(0,0,0,0.15)" for s in top10_sa]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=labels,
        y=val_64,
        name="64$ Low",
        marker=dict(color=PALETTE["dr8"], line=dict(width=line_widths, color=line_colors)),
        hovertemplate="%{x}<br>64$ NPV,10%: %{y:,.2f} M USD<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=labels,
        y=val_80,
        name="80$ Base",
        marker=dict(color=PALETTE["dr10"], line=dict(width=line_widths, color=line_colors)),
        hovertemplate="%{x}<br>80$ NPV,10%: %{y:,.2f} M USD<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=labels,
        y=val_117,
        name="117$ High",
        marker=dict(color=PALETTE["gold"], line=dict(width=line_widths, color=line_colors)),
        hovertemplate="%{x}<br>117$ NPV,10%: %{y:,.2f} M USD<extra></extra>",
    ))

    subtitle = "Membandingkan NPV,10% pada 64$, 80$, dan 117$ USD/bbl."
    if selected_no:
        subtitle += f" <b>Border emas tebal menandai Skenario #{selected_no} terpilih.</b>"

    _apply_clean_layout(
        fig,
        "Perbandingan NPV,10% untuk Top-10 Skenario Stand-Alone",
        subtitle,
        height=430,
    )
    fig.update_layout(
        barmode="group",
        xaxis=dict(title="Top-10 Skenario (Urutan Rank SA)", tickangle=-20),
        yaxis=dict(title="NPV,10% (Juta USD)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_spider_line_chart(
    selected_scenario: Dict[str, Any],
    bau_data: Dict[str, Any],
) -> go.Figure:
    """
    Spider/Line chart NPV vs harga minyak (sumbu-x: 64, 80, 117)
    Tiga garis DR: 8%, 10%, 12% + Garis putus-putus BAU.
    """
    prices = [64, 80, 117]
    metrics = selected_scenario["metrics"]["prices"]

    npv8_vals = [metrics[P]["npv8"] / 1e6 for P in prices]
    npv10_vals = [metrics[P]["npv10"] / 1e6 for P in prices]
    npv12_vals = [metrics[P]["npv12"] / 1e6 for P in prices]

    bau_metrics = bau_data["metrics"]
    bau_npv10 = [bau_metrics[float(P)]["npv10"] / 1e6 for P in prices]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=prices,
        y=npv8_vals,
        mode="lines+markers",
        name="DR 8%",
        line=dict(color=PALETTE["dr8"], width=2.5),
        marker=dict(size=8),
        hovertemplate="Harga: %{x}$<br>NPV,8%: %{y:,.2f} M USD<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=prices,
        y=npv10_vals,
        mode="lines+markers",
        name="DR 10% (Utama)",
        line=dict(color=PALETTE["dr10"], width=3.5),
        marker=dict(size=9),
        hovertemplate="Harga: %{x}$<br>NPV,10%: %{y:,.2f} M USD<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=prices,
        y=npv12_vals,
        mode="lines+markers",
        name="DR 12%",
        line=dict(color=PALETTE["dr12"], width=2.5),
        marker=dict(size=8),
        hovertemplate="Harga: %{x}$<br>NPV,12%: %{y:,.2f} M USD<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=prices,
        y=bau_npv10,
        mode="lines+markers",
        name="BAU (NPV,10%)",
        line=dict(color=PALETTE["bau"], width=2.5, dash="dash"),
        marker=dict(size=7, symbol="diamond"),
        hovertemplate="Harga: %{x}$<br>BAU NPV,10%: %{y:,.2f} M USD<extra></extra>",
    ))

    fig.add_hline(y=0, line_dash="dot", line_color="rgba(0,0,0,0.3)", annotation_text="Break-even (0 USD)")

    _apply_clean_layout(
        fig,
        f"NPV vs Harga Minyak — Skenario #{selected_scenario['no']} (Rank {selected_scenario['sa_rank']})",
        f"Kombinasi: {selected_scenario['kombinasi']}",
        height=400,
    )
    fig.update_layout(
        xaxis=dict(
            title="Harga Minyak (USD/bbl)",
            tickvals=prices,
            ticktext=["64$ (Low)", "80$ (Base)", "117$ (High)"],
        ),
        yaxis=dict(title="NPV (Juta USD)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_tornado_chart(
    selected_scenario: Dict[str, Any],
) -> go.Figure:
    """
    Tornado Diagram NPV,10 @80$ untuk skenario terpilih:
    Rentang Harga (64$ <-> 117$) vs Rentang Discount Rate (12% <-> 8%).
    """
    m = selected_scenario["metrics"]["prices"]
    base_val = m[80]["npv10"] / 1e6

    price_low = m[64]["npv10"] / 1e6
    price_high = m[117]["npv10"] / 1e6

    dr_low = m[80]["npv12"] / 1e6  # 12%
    dr_high = m[80]["npv8"] / 1e6   # 8%

    categories = ["Discount Rate (12% ↔ 8%)", "Harga Minyak (64$ ↔ 117$)"]
    low_diffs = [dr_low - base_val, price_low - base_val]
    high_diffs = [dr_high - base_val, price_high - base_val]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=categories,
        x=low_diffs,
        base=base_val,
        orientation="h",
        name="Sisi Turun (Downside)",
        marker=dict(color=PALETTE["danger"]),
        text=[f"{dr_low:,.1f}M", f"{price_low:,.1f}M"],
        textposition="inside",
        hovertemplate="%{y}<br>Nilai: %{x:,.2f} M USD<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        y=categories,
        x=high_diffs,
        base=base_val,
        orientation="h",
        name="Sisi Naik (Upside)",
        marker=dict(color=PALETTE["success"]),
        text=[f"{dr_high:,.1f}M", f"{price_high:,.1f}M"],
        textposition="inside",
        hovertemplate="%{y}<br>Nilai: %{x:,.2f} M USD<extra></extra>",
    ))

    fig.add_vline(
        x=base_val,
        line_width=2.5,
        line_color=PALETTE["gold"],
        annotation_text=f"Base: {base_val:,.1f}M",
        annotation_position="top",
    )

    _apply_clean_layout(
        fig,
        f"Tornado Sensitivitas NPV,10 — Skenario #{selected_scenario['no']}",
        f"Base Case: {base_val:,.2f} M USD (NPV,10 @80$)",
        height=320,
    )
    fig.update_layout(
        barmode="overlay",
        xaxis=dict(title="NPV (Juta USD)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_heatmap_3x3(
    selected_scenario: Dict[str, Any],
) -> go.Figure:
    """
    Heatmap 3x3 NPV (Baris: 64$, 80$, 117$ x Kolom: DR 8%, 10%, 12%) dengan angka terlihat.
    """
    m = selected_scenario["metrics"]["prices"]
    prices = [64, 80, 117]
    price_labels = ["64$ (Low)", "80$ (Base)", "117$ (High)"]
    dr_labels = ["DR 8%", "DR 10%", "DR 12%"]

    z_vals = []
    text_vals = []
    for P in prices:
        row_z = [m[P]["npv8"] / 1e6, m[P]["npv10"] / 1e6, m[P]["npv12"] / 1e6]
        row_text = [f"{v:,.2f} M" for v in row_z]
        z_vals.append(row_z)
        text_vals.append(row_text)

    fig = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=dr_labels,
        y=price_labels,
        text=text_vals,
        texttemplate="<b>%{text}</b>",
        textfont=dict(size=13, color="#1B1F23"),
        colorscale="Blues",
        colorbar=dict(title="Juta USD"),
        hoverongaps=False,
    ))

    _apply_clean_layout(
        fig,
        f"Matriks Sensitivitas NPV 3×3 — Skenario #{selected_scenario['no']}",
        "Nilai dalam Juta USD pada berbagai kombinasi Harga Minyak dan Discount Rate",
        height=320,
    )
    fig.update_layout(
        xaxis=dict(title="Discount Rate", side="top"),
        yaxis=dict(title="Harga Minyak", autorange="reversed"),
    )
    return fig


def create_all_scenarios_scatter(
    df_tab4: pd.DataFrame,
    price: int = 80,
) -> go.Figure:
    """
    Scatter Plot 453 Skenario: Total CAPEX vs NPV,10 pada harga yang dipilih.
    """
    df = df_tab4.copy()
    npv_col = f"{price}$ NPV,10"
    df["capex_m"] = df["Total CAPEX"] / 1e6
    df["npv_m"] = df[npv_col] / 1e6
    df["is_top10"] = df["RANK (1 = terbaik)"] <= 10

    df_normal = df[~df["is_top10"]]
    df_top = df[df["is_top10"]].sort_values("RANK (1 = terbaik)")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_normal["capex_m"],
        y=df_normal["npv_m"],
        mode="markers",
        name="Skenario (Rank 11-453)",
        marker=dict(
            size=6.5,
            color=df_normal["Skor (Rata-rata rank)"],
            colorscale="Viridis_r",
            showscale=True,
            colorbar=dict(title="Skor (Rata-rata)", x=1.02),
            opacity=0.65,
        ),
        text=df_normal["Kombinasi"],
        customdata=np.stack((df_normal["No"], df_normal["RANK (1 = terbaik)"], df_normal["Skor (Rata-rata rank)"]), axis=-1),
        hovertemplate="<b>No #%{customdata[0]} (Rank %{customdata[1]})</b><br>%{text}<br>Total CAPEX: %{x:,.2f} M USD<br>NPV,10 @"+str(price)+"$: %{y:,.2f} M USD<br>Skor: %{customdata[2]:.2f}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df_top["capex_m"],
        y=df_top["npv_m"],
        mode="markers+text",
        name="Top-10 Skenario",
        text=[f"R{r}" for r in df_top["RANK (1 = terbaik)"]],
        textposition="top center",
        textfont=dict(color="#FF8F00", size=11, family="Inter, sans-serif"),
        marker=dict(
            size=14,
            color="#FFB300",
            symbol="star",
            line=dict(color="#D84315", width=1.5),
        ),
        customdata=np.stack((df_top["No"], df_top["RANK (1 = terbaik)"], df_top["Skor (Rata-rata rank)"]), axis=-1),
        hovertemplate="<b>TOP-10: No #%{customdata[0]} (Rank %{customdata[1]})</b><br>%{text}<br>Total CAPEX: %{x:,.2f} M USD<br>NPV,10 @"+str(price)+"$: %{y:,.2f} M USD<br>Skor: %{customdata[2]:.2f}<extra></extra>",
    ))

    _apply_clean_layout(
        fig,
        f"Landscape Seluruh 453 Skenario: Total CAPEX vs NPV,10% @{price}$ USD/bbl",
        "Bintang emas menandai Top-10 skenario rekomendasi. Skenario di kuadran kiri-atas memiliki efisiensi modal tertinggi.",
        height=500,
    )
    fig.update_layout(
        xaxis=dict(title="Total CAPEX (Juta USD)"),
        yaxis=dict(title=f"NPV,10% @{price}$ (Juta USD)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=0.9),
    )
    return fig


def create_rank_breakdown_chart(
    selected_scenario: Dict[str, Any],
    selected_row: pd.Series,
) -> go.Figure:
    """
    Horizontal Bar Chart Transparansi 15 Rank Metrik untuk skenario terpilih (Tab 4).
    """
    rank_details = selected_scenario["sa_rank_details"]
    metric_labels = [
        "64$ Take", "64$ NPV,8", "64$ NPV,10", "64$ NPV,12", "64$ IRR",
        "80$ Take", "80$ NPV,8", "80$ NPV,10", "80$ NPV,12", "80$ IRR",
        "117$ Take", "117$ NPV,8", "117$ NPV,10", "117$ NPV,12", "117$ IRR",
    ]
    metric_keys = [
        "64_take", "64_npv8", "64_npv10", "64_npv12", "64_irr",
        "80_take", "80_npv8", "80_npv10", "80_npv12", "80_irr",
        "117_take", "117_npv8", "117_npv10", "117_npv12", "117_irr",
    ]
    rank_values = [rank_details[k] for k in metric_keys]

    fig = go.Figure(go.Bar(
        y=metric_labels,
        x=rank_values,
        orientation="h",
        marker=dict(
            color=rank_values,
            colorscale="Teal_r",
            showscale=True,
            colorbar=dict(title="Rank (1=Terbaik)"),
        ),
        text=[f"Rank {int(r)}" for r in rank_values],
        textposition="inside",
        hovertemplate="Metrik: %{y}<br>Peringkat: %{x} dari 453<extra></extra>",
    ))

    _apply_clean_layout(
        fig,
        f"Rincian 15 Peringkat Metrik — Skenario #{selected_scenario['no']} (Skor Rata-Rata = {selected_row['Skor (Rata-rata rank)']:.4f})",
        "Peringkat 1 menandai skenario dengan performa metrik tertinggi di antara seluruh 453 skenario",
        height=450,
    )
    fig.update_layout(
        xaxis=dict(title="Peringkat (1 = Terbaik, 453 = Terburuk)", range=[0, 460]),
        yaxis=dict(autorange="reversed"),
    )
    return fig


# ==============================================================================
# TAB 5 CHARTS (FARM-IN)
# ==============================================================================

def create_farmin_top10_chart(
    top10_fi: List[Dict[str, Any]],
    price: int = 80,
) -> go.Figure:
    """
    Grouped Bar Chart NPV,10 PNE vs Partner XYZ untuk Top-10 skenario pada harga tertentu.
    """
    labels = [f"Rank SA #{fi['rank_sa']} (#{fi['no_kombinasi']})<br>{fi['kombinasi'][:18]}.." for fi in top10_fi]
    pne_npvs = [fi["prices"][price]["npv10_pne"] / 1e6 for fi in top10_fi]
    xyz_npvs = [fi["prices"][price]["npv10_xyz"] / 1e6 for fi in top10_fi]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=pne_npvs,
        name="PNE (60% WI, 30% Capex Treatment)",
        marker=dict(color=PALETTE["primary"]),
        text=[f"{v:,.1f}M" for v in pne_npvs],
        textposition="inside",
        hovertemplate="%{x}<br>PNE NPV,10%: %{y:,.2f} M USD<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=labels,
        y=xyz_npvs,
        name="Partner XYZ (40% WI, 70% Carry Capex)",
        marker=dict(color=PALETTE["secondary"]),
        text=[f"{v:,.1f}M" for v in xyz_npvs],
        textposition="inside",
        hovertemplate="%{x}<br>XYZ NPV,10%: %{y:,.2f} M USD<extra></extra>",
    ))

    _apply_clean_layout(
        fig,
        f"Perbandingan NPV,10% PNE vs XYZ pada Tingkat Harga {price}$ USD/bbl",
        "Pembagian nilai ekonomi sesuai struktur kemitraan Farm-In (60:40 dengan 70% treatment carry)",
        height=430,
    )
    fig.update_layout(
        barmode="group",
        xaxis=dict(title="Top-10 Skenario (Urutan Rank SA)", tickangle=-20),
        yaxis=dict(title="NPV,10% (Juta USD)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_farmin_rank_breakdown_chart(
    selected_fi: Dict[str, Any],
) -> go.Figure:
    """
    Bar Chart Transparansi 30 Peringkat Metrik Farm-In (Tab 5).
    """
    rank_details_fi = selected_fi["rank_details"]
    metric_keys = list(rank_details_fi.keys())
    metric_values = [rank_details_fi[k] for k in metric_keys]

    fig = go.Figure(go.Bar(
        y=metric_keys,
        x=metric_values,
        orientation="h",
        marker=dict(
            color=metric_values,
            colorscale="Viridis_r",
            showscale=True,
            colorbar=dict(title="Rank (1=Terbaik)"),
        ),
        text=[f"Rank {int(r)}" for r in metric_values],
        textposition="inside",
    ))

    _apply_clean_layout(
        fig,
        f"Profil 30 Peringkat Metrik — Skenario #{selected_fi['no_kombinasi']} (Skor FI = {selected_fi['skor_fi']:.4f})",
        "Evaluasi 30 metrik finansial gabungan PNE dan XYZ pada 3 tingkat harga minyak",
        height=580,
    )
    fig.update_layout(
        xaxis=dict(title="Peringkat di Antara Top-10 (1 = Terbaik)", range=[0, 11]),
        yaxis=dict(autorange="reversed"),
    )
    return fig


# ==============================================================================
# TAB 6 CHARTS (SUMMARY)
# ==============================================================================

def create_summary_3party_chart(
    display_df: pd.DataFrame,
    price: int = 80,
) -> go.Figure:
    """
    Grouped Bar Chart 3 Pihak: SA (100% PNE) vs PNE (60% WI) vs XYZ (40% WI) pada harga tertentu.
    """
    labels = [f"#{row['No']} (FI Rank {row['RANK (1 = terbaik)']})<br>{row['Kombinasi'][:16]}.." for _, row in display_df.iterrows()]
    sa_npvs = [row[f"{price}$ NPV,10 SA"] / 1e6 for _, row in display_df.iterrows()]
    pne_npvs = [row[f"{price}$ NPV,10 PNE"] / 1e6 for _, row in display_df.iterrows()]
    xyz_npvs = [row[f"{price}$ NPV,10 XYZ"] / 1e6 for _, row in display_df.iterrows()]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=sa_npvs,
        name="Stand-Alone (100% PNE)",
        marker=dict(color=PALETTE["gold"]),
        text=[f"{v:,.1f}M" for v in sa_npvs],
        textposition="inside",
        hovertemplate="%{x}<br>SA NPV,10%: %{y:,.2f} M USD<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=labels,
        y=pne_npvs,
        name="Farm-In: PNE (60% WI)",
        marker=dict(color=PALETTE["primary"]),
        text=[f"{v:,.1f}M" for v in pne_npvs],
        textposition="inside",
        hovertemplate="%{x}<br>PNE NPV,10%: %{y:,.2f} M USD<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=labels,
        y=xyz_npvs,
        name="Farm-In: Partner XYZ (40% WI)",
        marker=dict(color=PALETTE["secondary"]),
        text=[f"{v:,.1f}M" for v in xyz_npvs],
        textposition="inside",
        hovertemplate="%{x}<br>XYZ NPV,10%: %{y:,.2f} M USD<extra></extra>",
    ))

    _apply_clean_layout(
        fig,
        f"Komparasi 3 Pihak NPV,10%: Stand-Alone vs Farm-In PNE vs Partner XYZ (@{price}$ USD/bbl)",
        "Memperlihatkan trade-off langsung antara nilai absolut Stand-Alone dan mitigasi risiko Farm-In",
        height=450,
    )
    fig.update_layout(
        barmode="group",
        xaxis=dict(title="Top-10 Skenario", tickangle=-20),
        yaxis=dict(title="NPV,10% (Juta USD)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
