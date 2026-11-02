"""
Module core/derived_metrics.py: Menghitung metrik turunan baru R4 (ICP Breakeven)
dan R5 (Payback Period) dari cashflow 15 tahun sesuai PRD Addendum v3.1 §3.2.1.
"""

from typing import Dict, Any, Optional, Tuple
import numpy as np


def calculate_icp_breakeven(
    scenario_info: Dict[str, Any],
    existing_data: Dict[str, Any],
    lif: np.ndarray,
    dr: float = 0.10,
) -> Tuple[Optional[float], Optional[float]]:
    """
    R4 — ICP Breakeven (USD/bbl), arah Cost:
    Mencari P* sedemikian sehingga NPV10(P*) = 0.
    Implementasi analitis:
        NPV10(P) = P * A - B
        A = sum_t [ prod_t * split_c * (1 - tax) / (1 + dr)^t ]
        B = sum_t [ (capex_t + opex_t + prod_t * lif_t) * (1 - tax) / (1 + dr)^t ]
        P* = B / A
    Verifikasi silang: memastikan |NPV10(P*)| < 1e-6.
    """
    flows = scenario_info["flows"]
    prd = flows["prd"]
    cpx = flows["cpx"]
    opx = flows["opx"]
    
    split_c = existing_data["split_c"]
    tax = existing_data["tax"]
    N = len(prd)
    t_arr = np.arange(N)
    df = 1.0 / ((1.0 + dr) ** t_arr)
    
    A = np.sum(prd * split_c * (1.0 - tax) * df)
    B = np.sum((cpx + opx + prd * lif) * (1.0 - tax) * df)
    
    if A <= 0:
        return None, None
        
    p_star = float(B / A)
    
    # Verifikasi silang
    gross_star = prd * p_star
    taxable_star = gross_star * split_c - (cpx + opx + prd * lif)
    ni_star = taxable_star * (1.0 - tax)
    npv_verify = float(np.sum(ni_star * df))
    
    return p_star, npv_verify


def calculate_payback_period(
    scenario_info: Dict[str, Any],
    price: float,
    existing_data: Dict[str, Any],
    bau_data: Dict[str, Any],
) -> float:
    """
    R5 — Payback Period (tahun), arah Cost:
    t_payback = tahun pertama di mana kumulatif arus kas inkremental (vs BAU) >= 0.
    Menggunakan arus kas inkremental inc = ni - ni_BAU pada tingkat harga acuan (80$ USD/bbl).
    Interpolasi linear dalam tahun untuk nilai pecahan.
    Jika tidak pernah >= 0 dalam 15 tahun, mengembalikan 16.0 (> 15 tahun).
    """
    flows = scenario_info["flows"]
    prd = flows["prd"]
    cpx = flows["cpx"]
    opx = flows["opx"]
    lif = bau_data["lif"]
    ni_bau = bau_data["nib"][price]
    
    split_c = existing_data["split_c"]
    tax = existing_data["tax"]
    
    gross = prd * price
    taxable = gross * split_c - (cpx + opx + prd * lif)
    ni = taxable * (1.0 - tax)
    inc = ni - ni_bau
    cum_inc = np.cumsum(inc)
    
    if cum_inc[0] >= 0:
        return 0.0
        
    for t in range(1, len(cum_inc)):
        if cum_inc[t] >= 0:
            frac = -cum_inc[t - 1] / (cum_inc[t] - cum_inc[t - 1])
            return float((t - 1) + frac)
            
    # Tidak pernah positif dalam 15 tahun
    return 16.0
