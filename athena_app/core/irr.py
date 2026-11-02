"""
Module irr.py: fungsi mandiri perhitungan Internal Rate of Return (IRR)
mengikuti aturan Excel V5 dan PRD §4.4 secara presisi.
TIDAK memakai library pihak ketiga (numpy_financial, scipy, dll).
"""

from typing import Union, Sequence
import numpy as np


def _sign(x: float) -> int:
    if x > 0:
        return 1
    elif x < 0:
        return -1
    return 0


def _newton_irr(cash_flows: Sequence[float], guess: float, max_iter: int = 100, tol: float = 1e-12) -> Union[float, None]:
    """
    Newton-Raphson untuk f(r) = sum(c_t / (1+r)^t) = 0.
    Mengembalikan r (float) jika konvergen, atau None jika gagal.
    """
    r = float(guess)
    for _ in range(max_iter):
        if r <= -1.0:
            return None
        
        # Hitung NPV dan turunan NPV'
        npv = 0.0
        d_npv = 0.0
        
        # t = 0
        npv += cash_flows[0]
        
        # t >= 1
        denom = 1.0 + r
        factor = 1.0
        for t in range(1, len(cash_flows)):
            factor *= denom
            c = cash_flows[t]
            npv += c / factor
            d_npv -= (t * c) / (factor * denom)

        if abs(npv) < tol:
            return r

        if abs(d_npv) < 1e-14:
            return None

        step = npv / d_npv
        r -= step

        if abs(step) < tol:
            return r

        if not np.isfinite(r) or abs(r) > 1e6:
            return None

    return None


def calculate_irr(inc_cash_flows: Sequence[float]) -> Union[float, str]:
    """
    Menghitung IRR dari deret arus kas inkremental tahunan (panjang N, t=0..N-1)
    mengikuti aturan Excel V5 di sel Contoh Perhitungan!B242 dan Financial Projection (SA)!N10:

    1. cum(t) = sum_{s<=t} inc(s); prv(t) = cum(t-1), prv(0) = 0
    2. Jika sum(inc) <= 0 -> 'n/a'
    3. Hitung banyaknya pergantian tanda kumulatif pada t >= 1:
       count(sign(cum(t)) != sign(cum(t-1))) untuk t = 1..N-1.
       Jika count != 1 -> 'n/m'
    4. Jika count == 1:
       Coba Newton-Raphson dengan tebakan 0.30;
       Jika gagal atau <= 0, coba 0.05;
       Jika gagal atau <= 0, coba 0.005;
       Ambil hasil pertama yang > 0;
       Jika tidak ada -> 'n/m'
    """
    cf = list(inc_cash_flows)
    total_inc = sum(cf)
    if total_inc <= 0.0:
        return "n/a"

    # Hitung cumulative cash flows
    n = len(cf)
    cum = []
    running = 0.0
    for val in cf:
        running += val
        cum.append(running)

    # Cek pergantian tanda kumulatif untuk t = 1..n-1
    sign_changes = 0
    for t in range(1, n):
        if _sign(cum[t]) != _sign(cum[t - 1]):
            sign_changes += 1

    if sign_changes != 1:
        return "n/m"

    # Coba bertingkat 0.30 -> 0.05 -> 0.005
    for guess in [0.30, 0.05, 0.005]:
        result = _newton_irr(cf, guess)
        if result is not None and result > 0.0:
            return result

    return "n/m"
