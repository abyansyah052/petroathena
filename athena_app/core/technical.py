"""
Module core/technical.py: Evaluasi Implementasi Teknis (T1-T5) untuk Top-10 Skenario.
Sesuai PRD Addendum v3.1 §4.2 dan aturan audit Excel V6 ('1.Technical Implementation').
"""

from typing import Dict, Any, List
import numpy as np
from athena_app.core.risk import P_CASING_IDLE_BURUK, P_PLT_FAIL


# Parameter Lapangan & Skala ('1.Technical Implementation'!B29:B38)
FACILITY_DESIGN_LIFE = 5.0   # B29
N_WELLS_TOTAL = 145.0         # B30
N_WELLS_ACTIVE = 58.0        # B31
N_WELLS_IDLE = 87.0          # B32
SCORE_MIN = 1.0              # B35
SCORE_MAX = 5.0              # B36

# Nilai per Metode untuk 7 Metode yang Dinilai di Excel V6 (baris 96-115)
# CRC ID -> {T1, T2, T3, Life (th), Sumur Tercakup}
RATED_METHODS_TECH: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "Polymer Gel",
        "t1": 4.0,
        "t2": 4.333333333333333,
        "t3": 2.0,
        "life": 1.0,
        "cov_idle": 1.0,
        "wells_covered": 145.0,  # 58 + 1.0*87
    },
    2: {
        "name": "PPG",
        "t1": 3.0,
        "t2": 2.7142857142857144,
        "t3": 2.0,
        "life": 1.0,
        "cov_idle": 1.0,
        "wells_covered": 145.0,  # 58 + 1.0*87
    },
    4: {
        "name": "Straddle Pkr",
        "t1": 4.0,
        "t2": 2.7142857142857144,
        "t3": 2.0,
        "life": 3.0,
        "cov_idle": 1.0 - P_CASING_IDLE_BURUK,  # 0.85
        "wells_covered": 58.0 + (1.0 - P_CASING_IDLE_BURUK) * 87.0,  # 131.95
    },
    6: {
        "name": "Bridge Plug",
        "t1": 4.0,
        "t2": 3.6666666666666665,
        "t3": 4.0,
        "life": 5.0,
        "cov_idle": 1.0 - P_CASING_IDLE_BURUK,  # 0.85
        "wells_covered": 58.0 + (1.0 - P_CASING_IDLE_BURUK) * 87.0,  # 131.95
    },
    8: {
        "name": "AS-1 + CIBP",
        "t1": 4.0,
        "t2": 2.7142857142857144,
        "t3": 2.0,
        "life": 5.0,
        "cov_idle": 1.0 - P_CASING_IDLE_BURUK,  # 0.85
        "wells_covered": 58.0 + (1.0 - P_CASING_IDLE_BURUK) * 87.0,  # 131.95
    },
    11: {
        "name": "Re-perf",
        "t1": 4.0,
        "t2": 5.0,
        "t3": 4.0,
        "life": 3.0,
        "cov_idle": 1.0 - P_CASING_IDLE_BURUK,  # 0.85
        "wells_covered": 58.0 + (1.0 - P_CASING_IDLE_BURUK) * 87.0,  # 131.95
    },
    12: {
        "name": "PLT Recompl.",
        "t1": 4.0,
        "t2": 2.7142857142857144,
        "t3": 3.0,
        "life": 4.0,
        "cov_idle": (1.0 - P_CASING_IDLE_BURUK) * (1.0 - P_PLT_FAIL),  # 0.85 * 0.85 = 0.7225
        "wells_covered": 58.0 + ((1.0 - P_CASING_IDLE_BURUK) * (1.0 - P_PLT_FAIL)) * 87.0,  # 120.8575
    },
}


def calculate_scenario_technical(
    scenario_info: Dict[str, Any],
    rank_sa: int,
    config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Menghitung skor teknis T1-T5 untuk 1 skenario Top-10.
    Aturan agregasi sesuai Addendum §4.2:
      - T1: Rata-rata T1 metode
      - T2: Minimum T2 metode
      - T3: Minimum T3 metode
      - T4: Rata-rata Umur Efektif mentah -> dinormalisasi: 1 + 4 * min(umur / 5, 1)
      - T5: Minimum Sumur Tercakup mentah -> dinormalisasi: 1 + 4 * sumur / 145
    """
    combo = scenario_info["combo"]
    method_ids = [m for m in [combo.get("id_1"), combo.get("id_2"), combo.get("id_3"), combo.get("id_4")] if m is not None]
    n_methods = len(method_ids)
    p_gabungan = scenario_info["cont"]["contingency_rate"]

    # Validasi robustness §4.0b
    unrated = [m for m in method_ids if m not in RATED_METHODS_TECH]
    if unrated:
        raise ValueError(
            f"Skenario #{scenario_info['no']} memiliki metode CRC ID {unrated} yang belum memiliki data teknis T1-T5 di Excel V6. "
            f"Excel hanya menilai 7 metode: 1, 2, 4, 6, 8, 11, 12."
        )

    # Parameter skala dinamis dari config
    score_min = float(config.get("tech_score_min", SCORE_MIN)) if config else SCORE_MIN
    score_max = float(config.get("tech_score_max", SCORE_MAX)) if config else SCORE_MAX
    fac_life = float(config.get("fac_life", FACILITY_DESIGN_LIFE)) if config else FACILITY_DESIGN_LIFE
    n_wells = float(config.get("n_total", N_WELLS_TOTAL)) if config else N_WELLS_TOTAL

    # 1. T1: Rata-rata skor T1
    t1_avg = sum(RATED_METHODS_TECH[m]["t1"] for m in method_ids) / n_methods

    # 2. T2: Minimum skor T2
    t2_min = min(RATED_METHODS_TECH[m]["t2"] for m in method_ids)

    # 3. T3: Minimum skor T3
    t3_min = min(RATED_METHODS_TECH[m]["t3"] for m in method_ids)

    # 4. T4: Rata-rata umur efektif -> normalisasi
    raw_life_avg = sum(RATED_METHODS_TECH[m]["life"] for m in method_ids) / n_methods
    t4_score = score_min + (score_max - score_min) * min(raw_life_avg / fac_life, 1.0)

    # 5. T5: Minimum sumur tercakup -> normalisasi
    raw_wells_min = min(RATED_METHODS_TECH[m]["wells_covered"] for m in method_ids)
    t5_score = score_min + (score_max - score_min) * (raw_wells_min / n_wells)

    return {
        "no": scenario_info["no"],
        "name": scenario_info["kombinasi"],
        "rank_sa": rank_sa,
        "p_gabungan": p_gabungan,
        "n_methods": n_methods,
        "t1": t1_avg,
        "t2": t2_min,
        "t3": t3_min,
        "t4": t4_score,
        "t5": t5_score,
        "effective_life_yr": raw_life_avg,
        "wells_covered": raw_wells_min,
        "npv10_80": scenario_info["metrics"]["prices"][80]["npv10"] / 1e6,
    }


def calculate_all_top10_technical(
    top10_sa: List[Dict[str, Any]],
    config: Dict[str, Any] = None,
) -> List[Dict[str, Any]]:
    """
    Menghitung skor teknis T1-T5 untuk seluruh 10 skenario Top-10.
    """
    return [calculate_scenario_technical(s, rank_sa=i + 1, config=config) for i, s in enumerate(top10_sa)]

