"""
Module core/topsis.py: Implementasi Algoritma TOPSIS (Technique for Order Preference
by Similarity to Ideal Solution) dari awal untuk 10 Skenario Top-10 SA.
Sesuai PRD Addendum v3.1 §2, §3, §3.1, §3.1.1, dan §3.2.2.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from athena_app.core.derived_metrics import calculate_icp_breakeven, calculate_payback_period


# 20 Sub-kriteria AHP dari '1.AHP'!A281:K300
# Format: (ID, Nama, Kriteria Induk, Bobot Level 1, Bobot Level 2, Bobot Global Mentah, Arah Cost/Benefit)
RAW_AHP_SUBCRITERIA = [
    ("E1", "GHG operasional (Scope 1+2)", "Environmental", 0.10932857991681522, 0.3610324461907233, 0.03947116464592578, "Cost"),
    ("E2", "GHG rantai nilai (Scope 3)", "Environmental", 0.10932857991681522, 0.06539797859984679, 0.007149868129751521, "Cost"),
    ("E3", "Air terproduksi", "Environmental", 0.10932857991681522, 0.3610324461907233, 0.03947116464592578, "Cost"),
    ("E4", "Toksisitas bahan kimia", "Environmental", 0.10932857991681522, 0.1428838312699236, 0.015621286365814583, "Cost"),
    ("E5", "Tumpahan, limbah B3, jejak lahan", "Environmental", 0.10932857991681522, 0.06965329774878296, 0.007615096129397543, "Cost"),
    ("T1", "Kecocokan reservoir & masalah air", "Technical", 0.18924539512774807, 0.39388888888888884, 0.07454165841420743, "Benefit"),
    ("T2", "Kematangan teknologi", "Technical", 0.18924539512774807, 0.1238888888888889, 0.023445401729715456, "Benefit"),
    ("T3", "Kompleksitas operasional", "Technical", 0.18924539512774807, 0.1238888888888889, 0.023445401729715456, "Benefit"),
    ("T4", "Durabilitas vs umur fasilitas", "Technical", 0.18924539512774807, 0.2344444444444444, 0.04436753152439426, "Benefit"),
    ("T5", "Skalabilitas lintas sumur", "Technical", 0.18924539512774807, 0.1238888888888889, 0.023445401729715456, "Benefit"),
    ("R1", "Ketidakpastian bawah permukaan", "Risk", 0.3507130124777184, 0.29762237762237764, 0.10438004063672515, "Cost"),
    ("R2", "Risiko teknis & eksekusi (Proksi RPN)", "Risk", 0.3507130124777184, 0.15790209790209792, 0.05537832043179638, "Cost"),
    ("R3", "Eksposur capex", "Risk", 0.3507130124777184, 0.15790209790209792, 0.05537832043179638, "Cost"),
    ("R4", "Risiko pasar & harga minyak (ICP Breakeven)", "Risk", 0.3507130124777184, 0.29762237762237764, 0.10438004063672515, "Cost"),
    ("R5", "Risiko regulasi & tenor (Payback Period)", "Risk", 0.3507130124777184, 0.08895104895104895, 0.03119629034067537, "Cost"),
    ("F1", "NPV 10% @ICP80", "Financial", 0.3507130124777184, 0.4355555555555556, 0.15275500099029515, "Benefit"),
    ("F2", "IRR @ICP80", "Financial", 0.3507130124777184, 0.1807407407407407, 0.06338812966263946, "Benefit"),
    ("F3", "PNE Take @ICP80", "Financial", 0.3507130124777184, 0.1807407407407407, 0.06338812966263946, "Benefit"),
    ("F4", "Total OPEX 15 th", "Financial", 0.3507130124777184, 0.09777777777777777, 0.034291938997821354, "Cost"),
    ("F5", "Produksi kumulatif 15 th", "Financial", 0.3507130124777184, 0.10518518518518519, 0.03688981316432297, "Benefit"),
]

# Sub-kriteria aktif (16 dari 20): E4, E5, R1 dinonaktifkan sesuai Addendum §3.2.2
ACTIVE_SUB_IDS = [
    "E1", "E2", "E3",
    "T1", "T2", "T3", "T4", "T5",
    "R2", "R3", "R4", "R5",
    "F1", "F2", "F3", "F4", "F5"
]


# Mapping Sub-kriteria ke Tab Asal Data Model
SOURCE_TAB_MAP: Dict[str, str] = {
    "E1": "Dampak Lingkungan (Scope 1+2)",
    "E2": "Dampak Lingkungan (Scope 3)",
    "E3": "Dampak Lingkungan (Air Terproduksi)",
    "E4": "Penilaian Kualitatif (Nonaktif)",
    "E5": "Penilaian Kualitatif (Nonaktif)",
    "T1": "Implementasi Teknis (Kecocokan Reservoir)",
    "T2": "Implementasi Teknis (Kematangan TRL)",
    "T3": "Implementasi Teknis (Kompleksitas Operasional)",
    "T4": "Implementasi Teknis (Durabilitas Fasilitas)",
    "T5": "Implementasi Teknis (Skalabilitas Sumur)",
    "R1": "Penilaian Kualitatif (Nonaktif)",
    "R2": "Risiko & FMEA (Proksi RPN Total)",
    "R3": "Proyeksi Stand-Alone (Total CAPEX)",
    "R4": "Proyeksi Stand-Alone (ICP Breakeven)",
    "R5": "Proyeksi Stand-Alone (Payback Period)",
    "F1": "Proyeksi Stand-Alone (NPV 10% @Base)",
    "F2": "Proyeksi Stand-Alone (IRR @Base)",
    "F3": "Proyeksi Stand-Alone (PNE Take @Base)",
    "F4": "Proyeksi Stand-Alone (Total OPEX)",
    "F5": "Proyeksi Stand-Alone (Kumulatif Produksi)",
}

# Matriks Level 2 (5x5) dari sheet '1.AHP'
AHP_LEVEL2_MATRICES: Dict[str, Dict[str, Any]] = {
    "Environmental": {
        "ids": ["E1", "E2", "E3", "E4", "E5"],
        "names": [
            "GHG operasional (Scope 1 + 2)",
            "GHG rantai nilai (Scope 3)",
            "Air terproduksi: volume & pengelolaan",
            "Penggunaan & toksisitas bahan kimia",
            "Tumpahan, limbah B3, jejak lahan",
        ],
        "matrix": [
            [1.0, 5.0, 1.0, 3.0, 5.0],
            [0.2, 1.0, 0.2, 1/3, 1.0],
            [1.0, 5.0, 1.0, 3.0, 5.0],
            [1/3, 3.0, 1/3, 1.0, 2.0],
            [0.2, 1.0, 0.2, 0.5, 1.0],
        ],
        "local_weights": [0.3610, 0.0654, 0.3610, 0.1429, 0.0697],
        "cr": 0.0084,
        "is_consistent": True,
    },
    "Technical": {
        "ids": ["T1", "T2", "T3", "T4", "T5"],
        "names": [
            "Kecocokan reservoir & masalah air",
            "Kematangan teknologi & rekam jejak",
            "Kompleksitas operasional & sumber daya",
            "Durabilitas terhadap umur fasilitas",
            "Skalabilitas lintas sumur & interaksi",
        ],
        "matrix": [
            [1.0, 3.0, 3.0, 2.0, 3.0],
            [1/3, 1.0, 1.0, 0.5, 1.0],
            [1/3, 1.0, 1.0, 0.5, 1.0],
            [0.5, 2.0, 2.0, 1.0, 2.0],
            [1/3, 1.0, 1.0, 0.5, 1.0],
        ],
        "local_weights": [0.3939, 0.1239, 0.1239, 0.2344, 0.1239],
        "cr": 0.0022,
        "is_consistent": True,
    },
    "Risk": {
        "ids": ["R1", "R2", "R3", "R4", "R5"],
        "names": [
            "Ketidakpastian bawah permukaan",
            "Risiko teknis & eksekusi (RPN)",
            "Eksposur capex & pembengkakan biaya",
            "Risiko pasar & harga minyak (ICP)",
            "Risiko regulasi, kontrak & tenor",
        ],
        "matrix": [
            [1.0, 2.0, 2.0, 1.0, 3.0],
            [0.5, 1.0, 1.0, 0.5, 2.0],
            [0.5, 1.0, 1.0, 0.5, 2.0],
            [1.0, 2.0, 2.0, 1.0, 3.0],
            [1/3, 0.5, 0.5, 1/3, 1.0],
        ],
        "local_weights": [0.2976, 0.1579, 0.1579, 0.2976, 0.0890],
        "cr": 0.0030,
        "is_consistent": True,
    },
    "Financial": {
        "ids": ["F1", "F2", "F3", "F4", "F5"],
        "names": [
            "NPV 10% @ICP80",
            "IRR proyek @ICP80",
            "PNE Take @ICP80",
            "Total OPEX 15 tahun",
            "Produksi minyak kumulatif 15 th",
        ],
        "matrix": [
            [1.0, 3.0, 3.0, 4.0, 3.0],
            [1/3, 1.0, 1.0, 2.0, 2.0],
            [1/3, 1.0, 1.0, 2.0, 2.0],
            [0.25, 0.5, 0.5, 1.0, 1.0],
            [1/3, 0.5, 0.5, 1.0, 1.0],
        ],
        "local_weights": [0.4356, 0.1807, 0.1807, 0.0978, 0.1052],
        "cr": 0.0124,
        "is_consistent": True,
    },
}


def get_renormalized_weights(custom_l1_weights: Dict[str, float] = None) -> List[Dict[str, Any]]:
    """
    Menghitung bobot ternormalisasi w'_j untuk 16 sub-kriteria aktif
    dengan redistribusi bobot proporsional di dalam kriteria induk masing-masing:
        w'_j = w_j * ( bobot_Level1_induk / sum_{k in induk, aktif} w_k )
    Memastikan bobot Level 1 setiap kriteria (E, T, R, F) tetap utuh dan sum(w') = 1.0.
    """
    parents = dict(custom_l1_weights) if custom_l1_weights else {
        "Environmental": 0.10932857991681522,
        "Technical": 0.18924539512774807,
        "Risk": 0.3507130124777184,
        "Financial": 0.3507130124777184,
    }
    
    # Hitung jumlah bobot lokal sub-kriteria aktif per kriteria induk
    active_local_sum_by_parent: Dict[str, float] = {p: 0.0 for p in parents}
    for item in RAW_AHP_SUBCRITERIA:
        sub_id, _, parent, _, l2_w, _, _ = item
        if sub_id in ACTIVE_SUB_IDS:
            active_local_sum_by_parent[parent] += l2_w

    renormalized_list = []
    for item in RAW_AHP_SUBCRITERIA:
        sub_id, name, parent, _, l2_w, _, direction = item
        is_active = sub_id in ACTIVE_SUB_IDS
        l1_w_curr = float(parents.get(parent, 0.25))
        raw_global_w = l1_w_curr * l2_w

        if is_active and active_local_sum_by_parent[parent] > 0:
            w_norm = l1_w_curr * (l2_w / active_local_sum_by_parent[parent])
        else:
            w_norm = 0.0

        renormalized_list.append({
            "id": sub_id,
            "name": name,
            "parent": parent,
            "level1_weight": l1_w_curr,
            "level2_weight": l2_w,
            "raw_global_weight": raw_global_w,
            "normalized_weight": w_norm,
            "direction": direction,
            "is_active": is_active,
            "source_tab": SOURCE_TAB_MAP.get(sub_id, "Model"),
        })

    return renormalized_list


def coerce_metric(val: Any) -> Tuple[float, Optional[str]]:
    """
    Menangani nilai non-numerik seperti IRR 'n/a' atau 'n/m' (Addendum §3.1.1).
    - 'n/a' atau 'n/m' disubstitusi dengan 0.0 dan dicatat di peringatan UI.
    """
    if isinstance(val, (int, float)) and np.isfinite(val):
        return float(val), None
    if isinstance(val, str):
        v_low = val.lower().strip()
        if v_low == "n/a":
            return 0.0, "IRR 'n/a' disubstitusi 0.0 (arus kas inkremental tidak positif)"
        if v_low == "n/m":
            return 0.0, "IRR 'n/m' disubstitusi 0.0 (arus kas berubah tanda > 1 kali)"
    return 0.0, f"Nilai non-numerik '{val}' disubstitusi 0.0"


def run_topsis_analysis(
    top10_sa: List[Dict[str, Any]],
    env_results: Dict[str, Any],
    risk_results: List[Dict[str, Any]],
    tech_results: List[Dict[str, Any]],
    existing_data: Dict[str, Any],
    bau_data: Dict[str, Any],
    custom_l1_weights: Dict[str, float] = None,
) -> Dict[str, Any]:
    """
    Eksekusi penuh algoritma TOPSIS untuk 10 skenario Top-10 Stand-Alone.
    """
    sub_configs = get_renormalized_weights(custom_l1_weights=custom_l1_weights)
    active_configs = [sc for sc in sub_configs if sc["is_active"]]
    weights = np.array([sc["normalized_weight"] for sc in active_configs], dtype=float)
    directions = [sc["direction"] for sc in active_configs]
    
    n_scenarios = len(top10_sa)
    n_criteria = len(active_configs)
    warnings_list = []

    # 1. Matriks Keputusan X (10 x 16)
    X = np.zeros((n_scenarios, n_criteria), dtype=float)
    raw_table_rows = []

    for i in range(n_scenarios):
        s = top10_sa[i]
        env_s = env_results["strategies"][i]
        risk_s = risk_results[i]
        tech_s = tech_results[i]

        p_base = int(existing_data.get("price_base", 80))
        available_prices = list(s["metrics"]["prices"].keys())
        p_eval = p_base if p_base in available_prices else (80 if 80 in available_prices else available_prices[0])

        p_star, _ = calculate_icp_breakeven(s, existing_data, bau_data["lif"])
        pb = calculate_payback_period(s, float(p_eval), existing_data, bau_data)
        
        irr_raw = s["metrics"]["prices"][p_eval]["irr"]
        irr_coerced, irr_warn = coerce_metric(irr_raw)
        if irr_warn and irr_warn not in warnings_list:
            warnings_list.append(irr_warn)

        # Mapping nilai 16 sub-kriteria
        val_map = {
            "E1": env_s["scope12_kt"],
            "E2": env_s["scope3_kt"],
            "E3": env_s["water_mmbbl"],
            "T1": tech_s["t1"],
            "T2": tech_s["t2"],
            "T3": tech_s["t3"],
            "T4": tech_s["t4"],
            "T5": tech_s["t5"],
            "R2": float(risk_s["rpn_total"]),
            "R3": s["flows"]["total_cpx"] / 1e6,
            "R4": p_star if p_star is not None else 100.0,
            "R5": pb,
            "F1": s["metrics"]["prices"][p_eval]["npv10"] / 1e6,
            "F2": irr_coerced,
            "F3": s["metrics"]["prices"][p_eval]["pne_take"] / 1e6,
            "F4": s["flows"]["total_opx"] / 1e6,
            "F5": float(np.sum(s["flows"]["prd"]) / 1e6),
        }

        row_vals = [val_map[sc["id"]] for sc in active_configs]
        X[i, :] = row_vals

        row_meta = {
            "no": s["no"],
            "name": s["kombinasi"],
            "rank_sa": i + 1,
        }
        for sc in active_configs:
            row_meta[sc["id"]] = val_map[sc["id"]]
        raw_table_rows.append(row_meta)

    # Cek kolom konstan (§3.1.1 poin 2)
    for j in range(n_criteria):
        col = X[:, j]
        if np.allclose(col, col[0]):
            warnings_list.append(
                f"Kriteria {active_configs[j]['id']} ({active_configs[j]['name']}) memiliki nilai konstan ({col[0]}) "
                f"untuk seluruh Top-10 — tidak diskriminatif dalam pemeringkatan."
            )

    # Langkah 1: Normalisasi Euclidean r_ij = x_ij / sqrt(sum_k x_kj^2)
    norms = np.sqrt(np.sum(X**2, axis=0))
    # Pembagi nol (§3.1.1 poin 3)
    zero_mask = (norms == 0)
    norms[zero_mask] = 1.0
    R = X / norms
    R[:, zero_mask] = 0.0

    # Langkah 2: Matriks Terbobot v_ij = w_j * r_ij
    V = R * weights

    # Langkah 3: Solusi Ideal Positif (A+) dan Solusi Ideal Negatif (A-)
    A_plus = np.zeros(n_criteria)
    A_minus = np.zeros(n_criteria)
    for j in range(n_criteria):
        if directions[j] == "Benefit":
            A_plus[j] = np.max(V[:, j])
            A_minus[j] = np.min(V[:, j])
        else:
            A_plus[j] = np.min(V[:, j])
            A_minus[j] = np.max(V[:, j])

    # Langkah 4: Jarak Euclidean D+ dan D-
    D_plus = np.sqrt(np.sum((V - A_plus)**2, axis=1))
    D_minus = np.sqrt(np.sum((V - A_minus)**2, axis=1))

    # Langkah 5: Closeness Coefficient C_i = D- / (D+ + D-)
    denom = D_plus + D_minus
    C = np.zeros(n_scenarios)
    for i in range(n_scenarios):
        if denom[i] == 0:
            C[i] = 0.5
            warnings_list.append(f"Skenario #{top10_sa[i]['no']} memiliki D+ + D- = 0 (nilai identik di semua kriteria). C_i diset 0.5.")
        else:
            C[i] = D_minus[i] / denom[i]

    # Langkah 6: Ranking (C_i menurun, tie-break: rank SA lebih kecil)
    ranked_indices = sorted(
        range(n_scenarios),
        key=lambda idx: (-C[idx], idx)
    )

    topsis_results = []
    for topsis_rank, orig_idx in enumerate(ranked_indices, start=1):
        s = top10_sa[orig_idx]
        rank_sa = orig_idx + 1
        delta = rank_sa - topsis_rank  # Positif = naik peringkat, Negatif = turun

        topsis_results.append({
            "rank_topsis": topsis_rank,
            "rank_sa": rank_sa,
            "no": s["no"],
            "name": s["kombinasi"],
            "d_plus": float(D_plus[orig_idx]),
            "d_minus": float(D_minus[orig_idx]),
            "closeness": float(C[orig_idx]),
            "rank_delta": delta,
            "npv10_80": s["metrics"]["prices"][p_eval]["npv10"] / 1e6,
            "irr_80": s["metrics"]["prices"][p_eval]["irr"],
            "capex": s["flows"]["total_cpx"] / 1e6,
        })

    # Urutkan berdasarkan rank_topsis (1..10)
    topsis_results_sorted = sorted(topsis_results, key=lambda x: x["rank_topsis"])

    return {
        "results": topsis_results_sorted,
        "active_subcriteria": active_configs,
        "all_subcriteria": sub_configs,
        "raw_matrix": raw_table_rows,
        "normalized_matrix": R,
        "weighted_matrix": V,
        "a_plus": A_plus,
        "a_minus": A_minus,
        "warnings": warnings_list,
    }
