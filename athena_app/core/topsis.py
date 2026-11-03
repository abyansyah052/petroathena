"""
Module core/topsis.py: Implementasi Algoritma TOPSIS (Technique for Order Preference
by Similarity to Ideal Solution) persis sesuai Excel V6_1 sheet '3.TOPSIS'.
Sesuai PRD Addendum v4.1 §3.1, §3.2, §3.3 dan UI/UX Guidelines §12.3.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

from athena_app.config.topsis_sources import (
    TOPSIS_SOURCE_REGISTRY,
    BLOCKED_SUB_IDS,
    ALL_AHP_SUBCRITERIA,
)
from athena_app.core.config_manager import (
    calculate_ahp_matrix,
    DEFAULT_AHP_LEVEL1,
    DEFAULT_AHP_LEVEL2,
)


def compute_all_ahp_global_weights(
    pairwise_l1: Optional[np.ndarray] = None,
    pairwise_l2: Optional[Dict[str, np.ndarray]] = None,
) -> List[Dict[str, Any]]:
    """
    Menghitung bobot global untuk ke-20 sub-kriteria AHP:
    Bobot Global = Bobot Level 1 (Kriteria Induk) * Bobot Lokal Level 2.
    """
    mat_l1 = pairwise_l1 if pairwise_l1 is not None else DEFAULT_AHP_LEVEL1
    w_l1, lmax_l1, ci_l1, cr_l1, ok_l1 = calculate_ahp_matrix(mat_l1)

    crit_order = ["Environmental", "Technical", "Risk", "Financial"]
    results = []

    mats_l2 = pairwise_l2 if pairwise_l2 is not None else DEFAULT_AHP_LEVEL2

    for i, crit in enumerate(crit_order):
        mat_l2 = mats_l2[crit]
        w_l2, lmax_l2, ci_l2, cr_l2, ok_l2 = calculate_ahp_matrix(mat_l2)
        prefix = crit[0]
        for j in range(len(w_l2)):
            sub_id = f"{prefix}{j+1}"
            meta = next((item for item in ALL_AHP_SUBCRITERIA if item["id"] == sub_id), None)
            name = meta["name"] if meta else sub_id
            direction = meta["direction"] if meta else "Benefit"

            gw = float(w_l1[i] * w_l2[j])
            results.append({
                "id": sub_id,
                "name": name,
                "criteria": crit,
                "direction": direction,
                "parent_weight": float(w_l1[i]),
                "local_weight": float(w_l2[j]),
                "global_weight": gw,
            })

    # Urutkan berdasarkan bobot global terbesar (descending)
    results.sort(key=lambda x: x["global_weight"], reverse=True)
    for rank, item in enumerate(results, 1):
        item["rank"] = rank

    return results


def validate_top10_subcriteria(top10_sub: List[Dict[str, Any]]) -> Tuple[bool, Optional[str], List[str]]:
    """
    Validasi 10 sub-kriteria berbobot terbesar:
    1. Cek apakah ada ID terlarang (E2, E3, E4, E5, R5) yang masuk Top-10.
    2. Cek apakah ada ID ekstensi (T2, T3, T5, F4, F5) yang masuk Top-10.
    """
    blocked_found = []
    extensions_found = []

    for sub in top10_sub:
        sid = sub["id"]
        if sid in BLOCKED_SUB_IDS:
            blocked_found.append((sid, sub["name"]))
        elif sid in TOPSIS_SOURCE_REGISTRY:
            if TOPSIS_SOURCE_REGISTRY[sid]["origin"] == "Perluasan (disetujui user)":
                extensions_found.append(sid)
        else:
            blocked_found.append((sid, sub.get("name", sid)))

    if blocked_found:
        first_id, first_name = blocked_found[0]
        reason = BLOCKED_SUB_IDS.get(first_id, "nilainya belum tersedia di Excel")
        msg = (
            f"Sub-kriteria {first_id} ({first_name}) masuk 10 bobot terbesar, "
            f"tetapi nilainya belum tersedia di Excel ({reason}). Kembalikan bobot AHP, "
            f"atau tambahkan nilainya di Excel lebih dulu."
        )
        return False, msg, extensions_found

    return True, None, extensions_found


def extract_decision_matrix(
    top10_sa: List[Dict[str, Any]],
    top10_sub: List[Dict[str, Any]],
    env_results: Dict[str, Any],
    risk_results: List[Dict[str, Any]],
    tech_results: List[Dict[str, Any]],
    price_low: float = 64.0,
    price_base: float = 80.0,
) -> Tuple[np.ndarray, Optional[str]]:
    """
    Mengekstrak nilai x_ij (10 skenario x 10 sub-kriteria) berdasarkan ID sumber.
    Memeriksa validitas numerik IRR (F2).
    """
    n_scenarios = len(top10_sa)
    n_criteria = len(top10_sub)
    X = np.zeros((n_scenarios, n_criteria), dtype=float)

    for i, s in enumerate(top10_sa):
        # 1. Cek IRR numerik untuk F2
        irr_val = s["metrics"]["prices"][price_base].get("irr")
        if irr_val is None or (isinstance(irr_val, str) and irr_val.lower() in ["n/a", "n/m", "nan", "#value!", "#num!"]):
            return X, (
                f"Skenario #{s['no']} ({s['kombinasi']}) memiliki nilai IRR non-numerik ({irr_val}) pada ICP {price_base}. "
                f"TOPSIS tidak dapat dihitung dengan IRR tidak valid."
            )
        try:
            irr_float = float(irr_val)
            if np.isnan(irr_float) or np.isinf(irr_float):
                raise ValueError()
        except Exception:
            return X, (
                f"Skenario #{s['no']} ({s['kombinasi']}) memiliki nilai IRR non-numerik ({irr_val}) pada ICP {price_base}. "
                f"TOPSIS tidak dapat dihitung dengan IRR tidak valid."
            )

        # Nilai-nilai sumber
        npv_low = s["metrics"]["prices"][price_low]["npv10"]
        npv_base = s["metrics"]["prices"][price_base]["npv10"]
        # ICP Breakeven interpolasi linear:
        if abs(npv_base - npv_low) > 1e-9:
            icp_be = price_low - npv_low * (price_base - price_low) / (npv_base - npv_low)
        else:
            icp_be = price_base

        source_values = {
            # 10 Asli Excel
            "F1": float(npv_base),
            "R1": float(risk_results[i]["rpn_efficacy"]),
            "R4": float(icp_be),
            "T1": float(tech_results[i]["t1"]),
            "F2": float(irr_float),
            "F3": float(s["metrics"]["prices"][price_base]["pne_take"]),
            "R2": float(risk_results[i]["rpn_total"] - risk_results[i]["rpn_efficacy"]),
            "R3": float(s["flows"]["total_cpx"]),
            "T4": float(tech_results[i]["t4"]),
            "E1": float(env_results["strategies"][i]["int_s12"]),
            # 5 Perluasan
            "T2": float(tech_results[i]["t2"]),
            "T3": float(tech_results[i]["t3"]),
            "T5": float(tech_results[i]["t5"]),
            "F4": float(s["flows"]["total_opx"]),
            "F5": float(s["flows"]["total_prod"]),
        }

        for j, sub in enumerate(top10_sub):
            sid = sub["id"]
            if sid in source_values:
                X[i, j] = source_values[sid]
            else:
                return X, f"Sub-kriteria {sid} tidak memiliki pemetaan nilai yang valid."

    return X, None


def calculate_topsis(
    top10_sa: List[Dict[str, Any]],
    env_results: Dict[str, Any],
    risk_results: List[Dict[str, Any]],
    tech_results: List[Dict[str, Any]],
    contract_results: Optional[Dict[str, Any]] = None,
    pairwise_l1: Optional[np.ndarray] = None,
    pairwise_l2: Optional[Dict[str, np.ndarray]] = None,
    price_low: float = 64.0,
    price_base: float = 80.0,
) -> Dict[str, Any]:
    """
    Menghitung TOPSIS Top-10 persis sesuai alur Excel V6_1 sheet '3.TOPSIS'.
    """
    # 1. Hitung bobot AHP untuk ke-20 sub-kriteria
    all_ahp = compute_all_ahp_global_weights(pairwise_l1, pairwise_l2)

    # 2. Ambil 10 sub-kriteria teratas
    top10_sub = all_ahp[:10]

    # 3. Validasi blocking E2/E3/E4/E5/R5
    is_valid, block_msg, extensions = validate_top10_subcriteria(top10_sub)
    if not is_valid:
        return {
            "is_blocked": True,
            "block_message": block_msg,
            "all_ahp": all_ahp,
            "top10_sub": top10_sub,
            "extensions_used": extensions,
        }

    # 4. Normalisasi ulang bobot hanya di antara 10 sub-kriteria tersebut (sum = 1.0)
    sum_top10_gw = sum(s["global_weight"] for s in top10_sub)
    for s in top10_sub:
        s["norm_weight"] = s["global_weight"] / sum_top10_gw

    # 5. Ekstrak matriks keputusan X (10 x 10)
    X, irr_error = extract_decision_matrix(
        top10_sa=top10_sa,
        top10_sub=top10_sub,
        env_results=env_results,
        risk_results=risk_results,
        tech_results=tech_results,
        price_low=price_low,
        price_base=price_base,
    )
    if irr_error:
        return {
            "is_blocked": True,
            "block_message": irr_error,
            "all_ahp": all_ahp,
            "top10_sub": top10_sub,
            "extensions_used": extensions,
        }

    # 6. Norma kolom: ||x_j|| = SQRT(SUMSQ(x_1j..x_10j))
    col_norms = np.sqrt(np.sum(X**2, axis=0))
    col_norms = np.where(col_norms == 0, 1.0, col_norms)

    # 7. Normalisasi: r_ij = x_ij / ||x_j||
    R = X / col_norms

    # 8. Sensitivitas tak berbobot (bobot sama)
    directions = [s["direction"] for s in top10_sub]
    A_plus_unw = np.zeros(10)
    A_minus_unw = np.zeros(10)
    for j in range(10):
        if directions[j] == "Benefit":
            A_plus_unw[j] = np.max(R[:, j])
            A_minus_unw[j] = np.min(R[:, j])
        else:
            A_plus_unw[j] = np.min(R[:, j])
            A_minus_unw[j] = np.max(R[:, j])

    D_plus_unw = np.sqrt(np.sum((R - A_plus_unw)**2, axis=1))
    D_minus_unw = np.sqrt(np.sum((R - A_minus_unw)**2, axis=1))
    denom_unw = D_plus_unw + D_minus_unw
    Ci_unw = np.where(denom_unw == 0, 0.0, D_minus_unw / denom_unw)
    rank_unw = pd.Series(Ci_unw).rank(ascending=False, method="first").astype(int).to_numpy()

    # 9. Matriks terbobot: v_ij = r_ij * w_j
    weights = np.array([s["norm_weight"] for s in top10_sub], dtype=float)
    V = R * weights

    # 10. Solusi ideal A+ dan A-
    A_plus = np.zeros(10)
    A_minus = np.zeros(10)
    for j in range(10):
        if directions[j] == "Benefit":
            A_plus[j] = np.max(V[:, j])
            A_minus[j] = np.min(V[:, j])
        else:
            A_plus[j] = np.min(V[:, j])
            A_minus[j] = np.max(V[:, j])

    # 11. Jarak ke solusi ideal D+ dan D-
    D_plus = np.sqrt(np.sum((V - A_plus)**2, axis=1))
    D_minus = np.sqrt(np.sum((V - A_minus)**2, axis=1))

    # 12. Kedekatan relatif Ci
    denom = D_plus + D_minus
    Ci = np.where(denom == 0, 0.0, D_minus / denom)

    # 13. Peringkat TOPSIS (tie breaker: urutan baris / rank SA)
    rank_topsis = pd.Series(Ci).rank(ascending=False, method="first").astype(int).to_numpy()

    # 14. Susun ringkasan per skenario
    summary = []
    contract_recs = []
    if contract_results:
        contract_recs = contract_results.get("reserves_summary", contract_results.get("summary", []))

    for i, s in enumerate(top10_sa):
        c_scheme = "-"
        c_ext_yrs = 0
        if i < len(contract_recs):
            c_scheme = contract_recs[i].get("selected_scheme", contract_recs[i].get("extension_type", "-"))
            c_ext_yrs = contract_recs[i].get("extra_contract_years", 0)

        rank_sa = i + 1
        t_rank = int(rank_topsis[i])
        diff_rank = rank_sa - t_rank  # Positif jika TOPSIS lebih baik dari SA

        summary.append({
            "scenario_no": s["no"],
            "name": s["kombinasi"],
            "rank_sa": rank_sa,
            "npv10_80": float(s["metrics"]["prices"][price_base]["npv10"]),
            "d_plus": float(D_plus[i]),
            "d_minus": float(D_minus[i]),
            "ci": float(Ci[i]),
            "rank_topsis": t_rank,
            "rank_equal_weights": int(rank_unw[i]),
            "rank_diff": diff_rank,
            "contract_extension_type": c_scheme,
            "contract_extra_years": c_ext_yrs,
        })

    # Ranking berdasarkan TOPSIS
    summary_sorted = sorted(summary, key=lambda x: x["rank_topsis"])
    top_scenario = summary_sorted[0]

    # Cek konsistensi pemenang sama rata
    unw_top = min(summary, key=lambda x: x["rank_equal_weights"])
    is_consistent_with_equal = (top_scenario["scenario_no"] == unw_top["scenario_no"])

    return {
        "is_blocked": False,
        "block_message": None,
        "all_ahp": all_ahp,
        "top10_sub": top10_sub,
        "extensions_used": extensions,
        "matrix_X": X,
        "norms": col_norms,
        "matrix_R": R,
        "matrix_V": V,
        "ideal_plus": A_plus,
        "ideal_minus": A_minus,
        "summary": summary,
        "summary_sorted": summary_sorted,
        "top_scenario": top_scenario,
        "is_consistent_with_equal": is_consistent_with_equal,
    }
