"""
Peta nama sheet Excel V5 dan V6.
Sesuai PRD Addendum v3.1 §0.1:
Nama semua sheet di V6 memiliki prefix tahap pipeline (0./1./2./3.).
"""

from typing import Dict, Any
import openpyxl

# Nama standar internal -> Nama sheet V6 (Default resmi)
V6_SHEET_NAMES: Dict[str, str] = {
    "introduction": "0.Introduction",
    "existing_data": "0.Existing Data",
    "combination": "0.Combination",
    "capex_opex_breakdown": "0.CAPEX OPEX Breakdown",
    "contingency_rate_combination": "0.Contingency Rate Combination",
    "financial_projection_sa": "1.Financial Projection (SA)",
    "financial_projection_farmin": "1.Financial Projection (FarmIn)",  # Tanpa tanda hubung di V6!
    "financial_summary": "1.Financial Summary",
    "contoh_perhitungan": "1.Contoh Perhitungan",
    "ahp": "1.AHP",
    "environmental_impact": "1.Environmental Impact",
    "risk": "1.Risk",
    "technical_implementation": "1.Technical Implementation",
    "secondary_recovery": "2.Secondary Recovery Analysis",
    "contract_simulations": "2.Contract Simulations",
    "topsis": "3.TOPSIS",
    "implementation_plan": "3.Implementation Plan",
    "chosen_scenario": "3. Chosen Scenario",  # Spasi setelah titik persis seperti di Excel V6_1!
}

# Nama sheet V5 (Legacy)
V5_SHEET_NAMES: Dict[str, str] = {
    "introduction": "Introduction",
    "existing_data": "Existing Data",
    "combination": "Combination",
    "capex_opex_breakdown": "CAPEX OPEX Breakdown",
    "contingency_rate_combination": "Contingency Rate Combination",
    "financial_projection_sa": "Financial Projection (SA)",
    "financial_projection_farmin": "Financial Projection (Farm-In)",
    "financial_summary": "Financial Summary",
    "contoh_perhitungan": "Contoh Perhitungan",
}


def get_sheet_names_for_wb(wb: openpyxl.Workbook) -> Dict[str, str]:
    """
    Mendeteksi secara otomatis apakah workbook merupakan V6 (memiliki prefix '0.')
    atau V5, dan mengembalikan mapping nama sheet yang sesuai.
    """
    sheet_list = wb.sheetnames
    if "0.Existing Data" in sheet_list or "0.Introduction" in sheet_list:
        return V6_SHEET_NAMES
    return V5_SHEET_NAMES
