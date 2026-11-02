"""
Module summary.py: penyusunan tabel komparasi eksekutif Tab 6
(Financial Summary: Stand-Alone vs Farm-In PNE vs Farm-In XYZ).
"""

from typing import List, Dict, Any


def build_financial_summary(
    top10_sa_scenarios: List[Dict[str, Any]],
    top10_fi_rows: List[Dict[str, Any]],
    prices: List[int] = None,
) -> List[Dict[str, Any]]:
    """
    Menggabungkan metrik dari Tab 4 (SA) dan Tab 5 (Farm-In) menjadi tabel ringkasan Tab 6.
    Mendukung harga dinamis (Addendum §10.3).
    """
    if prices is None:
        prices = [64, 80, 117]

    summary_rows = []
    for i in range(len(top10_sa_scenarios)):
        sa = top10_sa_scenarios[i]
        fi = top10_fi_rows[i]
        assert sa["sa_rank"] == fi["rank_sa"]

        row = {
            "No": fi["rank_sa"],
            "Kombinasi": fi["kombinasi"],
            "Contingency Rate": fi["contingency_rate"],
            "Total Production": fi["total_prod"],
            "CAPEX SA": fi["cpx_sa"],
            "CAPEX PNE": fi["cpx_pne"],
            "CAPEX XYZ": fi["cpx_xyz"],
            "OPEX SA": fi["opx_sa"],
            "OPEX PNE": fi["opx_pne"],
            "OPEX XYZ": fi["opx_xyz"],
        }

        for P in prices:
            row[f"{P}$ NPV,10 SA"] = sa.get(f"{P}_npv10", sa["metrics"]["prices"][P]["npv10"])
            row[f"{P}$ NPV,10 PNE"] = fi[f"{P}_npv10_pne"]
            row[f"{P}$ NPV,10 XYZ"] = fi[f"{P}_npv10_xyz"]
            row[f"{P}$ IRR SA"] = sa.get(f"{P}_irr", sa["metrics"]["prices"][P]["irr"])
            row[f"{P}$ IRR PNE"] = fi[f"{P}_irr_pne"]
            row[f"{P}$ IRR XYZ"] = fi[f"{P}_irr_xyz"]
            row[f"{P}$ Take SA"] = sa.get(f"{P}_take", sa["metrics"]["prices"][P]["pne_take"])
            row[f"{P}$ Take PNE"] = fi[f"{P}_take_pne"]
            row[f"{P}$ Take XYZ"] = fi[f"{P}_take_xyz"]
            row[f"{P}$ Gov. Take FI"] = fi[f"{P}_gov_take"]

        row["RANK (1 = terbaik)"] = fi["rank_fi"]
        summary_rows.append(row)

    return summary_rows
