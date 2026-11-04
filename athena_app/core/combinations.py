"""
Module combinations.py: implementasi Tab 1 & Tab 2 sesuai PRD §4.
Membangkitkan 4.047 kombinasi mentah, melakukan penyaringan hard constraint (1.092),
dan penyaringan kompatibilitas (453 kombinasi lolos).
"""

import itertools
from typing import List, Dict, Any, Tuple


def generate_raw_combinations(methods_18: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Membangkitkan semua kombinasi ukuran 1..4 dari 18 metode (urutan Introduction!B10:B27).
    Total: 18 + 153 + 816 + 3060 = 4.047 kombinasi.
    """
    raw_list = []
    no = 1
    for k in (1, 2, 3, 4):
        for combo in itertools.combinations(methods_18, k):
            names = [m["name"] for m in combo]
            combo_name = " + ".join(names)
            raw_list.append({
                "no": no,
                "size": k,
                "methods": combo,
                "name": combo_name,
            })
            no += 1
    return raw_list


def filter_hard_constraints(methods_18: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Tuple[Dict[str, Any], ...]]]:
    """
    Langkah 1: Hard constraint geologi/reservoir (Combination!I6:J23).
    Lolos jika Drive(m) * Hetero(m) == 1.
    Menghasilkan 13 metode lolos dan 1.092 kombinasi yang hanya berisi metode lolos.
    """
    passed_methods = [m for m in methods_18 if m["drive_aquifer"] * m["hetero_high"] == 1]
    
    combos_1092 = []
    for k in (1, 2, 3, 4):
        for combo in itertools.combinations(passed_methods, k):
            combos_1092.append(combo)

    return passed_methods, combos_1092


def filter_compatibility(
    combos_1092: List[Tuple[Dict[str, Any], ...]],
    compat_matrix: List[List[Any]],
    name_to_old_id: Dict[str, int],
    name_to_new_id: Dict[str, int],
) -> List[Dict[str, Any]]:
    """
    Langkah 2: Kompatibilitas antar pasangan metode (Combination!V7:AM24).
    Kombinasi diterima iff untuk SETIAP pasangan (a, b) dalam kombinasi: compat[a][b] > 0.
    Kombinasi ukuran 1 otomatis diterima.
    Menghasilkan tepat 453 kombinasi lolos (13 / 65 / 161 / 214) berurutan leksikografis ID (Q3, T26).
    """
    passed_combos = []
    no = 1
    for combo in combos_1092:
        k = len(combo)
        if k == 1:
            is_valid = True
        else:
            is_valid = True
            for m_a, m_b in itertools.combinations(combo, 2):
                idx_a = name_to_old_id[m_a["name"]] - 1
                idx_b = name_to_old_id[m_b["name"]] - 1
                val = compat_matrix[idx_a][idx_b]
                # Kompatibel jika bernilai 1 atau 2; tidak kompatibel jika 0
                if val == 0:
                    is_valid = False
                    break

        if is_valid:
            names = [m["name"] for m in combo]
            combo_name = " + ".join(names)
            old_ids = [name_to_old_id[m["name"]] for m in combo]
            new_ids = [name_to_new_id[m["name"]] for m in combo]

            passed_combos.append({
                "no": no,
                "size": k,
                "name": combo_name,
                "methods": combo,
                "old_ids": old_ids,
                "new_ids": new_ids,
                "id_1": new_ids[0] if len(new_ids) >= 1 else None,
                "id_2": new_ids[1] if len(new_ids) >= 2 else None,
                "id_3": new_ids[2] if len(new_ids) >= 3 else None,
                "id_4": new_ids[3] if len(new_ids) >= 4 else None,
            })
            no += 1

    return passed_combos
