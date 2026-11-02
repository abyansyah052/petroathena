"""
Module metrics.py: kalkulasi metrik finansial (Take, NPV 8/10/12%, IRR)
per tingkat harga minyak (64, 80, 117 USD/bbl) sesuai PRD §4.4.
"""

import numpy as np
from typing import Dict, Any, List
from athena_app.core.irr import calculate_irr


def calculate_scenario_financial_metrics(
    flows: Dict[str, Any],
    existing_data: Dict[str, Any],
    bau_data: Dict[str, Any],
    prices: List[float] = None,
) -> Dict[str, Any]:
    """
    Menghitung 15 metrik finansial dan arus tahunan finansial untuk skenario Stand-Alone.
    """
    if prices is None:
        prices = [64.0, 80.0, 117.0]

    ed = existing_data
    split_c = ed["split_c"]
    split_g = ed["split_g"]
    tax = ed["tax"]
    t_arr = bau_data["t_arr"]
    lif = bau_data["lif"]
    prd = flows["prd"]
    cpx = flows["cpx"]
    opx = flows["opx"]

    result = {
        "prices": {},
        "annual_ni": {},
        "annual_inc": {},
    }

    for P in prices:
        P_key = int(P)
        # Net Income tahunan: (prd * P * split_c - cpx - opx - prd * lif) * (1 - tax)
        # Pajak boleh negatif
        ni = (prd * P * split_c - cpx - opx - prd * lif) * (1.0 - tax)
        inc = ni - bau_data["nib"][P]

        pne_take = float(np.sum(ni))
        gov_take = float(np.sum(prd * P * split_g) + np.sum(ni * (tax / (1.0 - tax))))
        dr_low = float(ed.get("dr_low", 0.08))
        dr_main = float(ed.get("dr_main", 0.10))
        dr_high = float(ed.get("dr_high", 0.12))
        npv8 = float(np.sum(ni / ((1.0 + dr_low) ** t_arr)))
        npv10 = float(np.sum(ni / ((1.0 + dr_main) ** t_arr)))
        npv12 = float(np.sum(ni / ((1.0 + dr_high) ** t_arr)))
        irr = calculate_irr(inc)

        result["annual_ni"][P_key] = ni
        result["annual_inc"][P_key] = inc
        result["prices"][P_key] = {
            "pne_take": pne_take,
            "gov_take": gov_take,
            "npv8": npv8,
            "npv10": npv10,
            "npv12": npv12,
            "irr": irr,
        }

    return result
