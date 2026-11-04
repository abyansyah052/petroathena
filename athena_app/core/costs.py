"""
Module costs.py: kalkulasi biaya per sumur (CAPEX & OPEX) per kombinasi
sesuai PRD §4 Tab 3 dan formula LET di Financial Projection (SA).
"""

from typing import List, Dict, Any, Tuple, Set


# Default set pool MAX dari defined names sa_poolc & sa_poolo (PRD §3.3 & Q2)
DEFAULT_POOL_C: Set[str] = {"DIAG", "EXEC", "TEST"}
DEFAULT_POOL_O: Set[str] = {"SURV", "LAB", "TEST", "REVIEW"}


def calculate_costs_per_well(
    combination_method_ids: List[int],
    breakdown_items: List[Dict[str, Any]],
    pool_c: Set[str] = None,
    pool_o: Set[str] = None,
) -> Dict[str, Any]:
    """
    Menghitung CAPEX per sumur dan OPEX per sumur/thn untuk kombinasi metode tertentu
    mengikuti aturan defined names sa_wellc dan sa_wello (PRD §3.3 & Q2).
    """
    if pool_c is None:
        pool_c = DEFAULT_POOL_C
    if pool_o is None:
        pool_o = DEFAULT_POOL_O

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

    # CAPEX
    c_items = [it for it in method_items if it["cost_type"] == "CAPEX"]
    c_pool_max = sum(
        max([sum(it["value"] for it in c_items if it["method_id"] == mid and it["pool"] == pool) for mid in combination_method_ids] + [0.0])
        for pool in pool_c
    )
    c_jumlah = sum(it["value"] for it in c_items if it["method_id"] in combination_method_ids and it["rule"] == "Jumlah")
    capex_per_well = c_pool_max + c_jumlah

    # OPEX
    o_items = [it for it in method_items if it["cost_type"] == "OPEX"]
    o_pool_max = sum(
        max([sum(it["value"] for it in o_items if it["method_id"] == mid and it["pool"] == pool) for mid in combination_method_ids] + [0.0])
        for pool in pool_o
    )
    o_jumlah = sum(it["value"] for it in o_items if it["method_id"] in combination_method_ids and it["rule"] == "Jumlah")
    opex_per_well = o_pool_max + o_jumlah

    result["capex_per_well"] = capex_per_well
    result["opex_per_well"] = opex_per_well
    result["capex_well"] = capex_per_well
    result["opex_well"] = opex_per_well
    return result


# Alias untuk kompatibilitas
calculate_capex_opex_per_well = calculate_costs_per_well
