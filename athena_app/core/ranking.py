"""
Module ranking.py: logika pemeringkatan dan kalkulasi Skor sesuai PRD §4.5 dan §4.7.
Mendukung 15 metrik untuk Tab 4 (Stand-Alone) dan 30 metrik untuk Tab 5 (Farm-In).
"""

from typing import List, Dict, Any, Tuple
import numpy as np


def compute_ranks_and_scores(
    scenario_rows: List[Dict[str, Any]],
    metric_keys: List[str],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Menghitung rank_m untuk setiap metrik, Skor (rata-rata rank_m), dan RANK global.

    Aturan PRD §4.5:
    - rank_m(x) = 1 + jumlah skenario dengan nilai numerik > x (jika x numerik)
                = 1 + jumlah nilai numerik pada metrik m (jika x = "n/a" / "n/m")
    - Skor      = (sum 15 rank_m) / 15
    - RANK      = 1 + jumlah Skor numerik < Skor ini + (jumlah Skor sama di baris sebelumnya)
                  (urut Skor naik, seri dipecah berdasarkan No asli / baris lebih dulu)

    Mengembalikan: (ranks_matrix, scores, global_ranks)
    """
    n_scenarios = len(scenario_rows)
    n_metrics = len(metric_keys)
    ranks_matrix = np.zeros((n_scenarios, n_metrics))

    for j, m_key in enumerate(metric_keys):
        vals = [row[m_key] for row in scenario_rows]
        num_vals = [v for v in vals if isinstance(v, (int, float)) and np.isfinite(v)]
        n_num = len(num_vals)

        for i, v in enumerate(vals):
            if isinstance(v, (int, float)) and np.isfinite(v):
                r = 1 + sum(1 for other in num_vals if other > v)
            else:
                r = 1 + n_num
            ranks_matrix[i, j] = r

    scores = np.mean(ranks_matrix, axis=1)

    global_ranks = np.zeros(n_scenarios, dtype=int)
    for i in range(n_scenarios):
        s_this = scores[i]
        lt_count = sum(1 for k in range(n_scenarios) if scores[k] < s_this)
        eq_prev_count = sum(1 for k in range(i) if scores[k] == s_this)
        global_ranks[i] = 1 + lt_count + eq_prev_count

    return ranks_matrix, scores, global_ranks
