"""
Module costs.py: kalkulasi biaya per sumur (CAPEX & OPEX) per kombinasi
sesuai PRD §4 Tab 3 dan formula LET di Financial Projection (SA).
"""

from typing import List, Dict, Any, Tuple, Set


def calculate_costs_per_well(
    combination_method_ids: List[int],
    breakdown_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Menghitung CAPEX per sumur dan OPEX per sumur/thn untuk kombinasi metode tertentu.
    combination_method_ids: list ID baru metode dalam kombinasi (misal [1, 6])
    breakdown_items: list item dari CAPEX OPEX Breakdown (tanpa baris 'R')
    """
    # Filter hanya item metode (abaikan 'R' jika ada)
    method_items = [it for it in breakdown_items if it["method_id"] != "R"]

    # Cek okc: setiap metode dalam kombinasi harus punya >= 1 item biaya > 0
    okc = True
    for mid in combination_method_ids:
        has_cost = any(it["method_id"] == mid and it["value"] > 0 for it in method_items)
        if not has_cost:
            okc = False
            break

    result: Dict[str, Any] = {"okc": 1 if okc else 0}

    for cost_type in ["CAPEX", "OPEX"]:
        type_items = [it for it in method_items if it["cost_type"] == cost_type]

        # Pools dengan aturan "Sekali"
        pools_sekali: Set[str] = {it["pool"] for it in type_items if it["rule"] == "Sekali"}

        # Sekali: max per pool atas metode-metode dalam kombinasi
        sekali_total = 0.0
        for pool in pools_sekali:
            max_pool_val = 0.0
            for mid in combination_method_ids:
                val_i_pool = sum(
                    it["value"] for it in type_items
                    if it["method_id"] == mid and it["pool"] == pool
                )
                if val_i_pool > max_pool_val:
                    max_pool_val = val_i_pool
            sekali_total += max_pool_val

        # Jumlah: sum atas seluruh item aturan "Jumlah" dari metode-metode dalam kombinasi
        jumlah_total = sum(
            it["value"] for it in type_items
            if it["method_id"] in combination_method_ids and it["rule"] == "Jumlah"
        )

        per_well = sekali_total + jumlah_total
        result[f"{cost_type.lower()}_per_well"] = per_well

    result["capex_well"] = result["capex_per_well"]
    result["opex_well"] = result["opex_per_well"]
    return result


# Alias untuk kompatibilitas
calculate_capex_opex_per_well = calculate_costs_per_well
