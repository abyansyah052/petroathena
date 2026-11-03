
"""
Peta sel Excel V5 dan V6_1 (0efefd70-Bismillah_Angker_BCC_Excel_Calculations_V6_1.xlsx).
Sesuai PRD Addendum v4.1 §0.2, §2, §4, Lampiran G dan H.
"""

from typing import Dict, Any, Tuple, List

# ==============================================================================
# V5 (Legacy) Cell Mappings
# ==============================================================================
V5_EXISTING_DATA_MAP = {
    "stoiip": {"cell": "B4", "expected": 950.0, "unit": "MMbbl", "desc": "STOIIP (tampilan)"},
    "rf": {"cell": "B5", "expected": 0.21, "unit": "fraction", "desc": "Recovery Factor (tampilan)"},
    "cum_prod": {"cell": "B6", "expected": 200.0, "unit": "MMbbl", "desc": "Cumulative Production (tampilan)"},
    "reserve_2p_mmbbl": {"cell": "B7", "expected": 38.0, "unit": "MMbbl", "desc": "2P Reserves in MMbbl"},
    "d0": {"cell": "B8", "expected": 0.075, "unit": "fraction/yr", "desc": "Decline rate baseline"},
    "q0": {"cell": "B9", "expected": 2000.0, "unit": "bopd", "desc": "Initial oil production"},
    "wc0": {"cell": "B10", "expected": 0.91, "unit": "fraction", "desc": "Initial water cut"},
    "lc0": {"cell": "B11", "expected": 31.0, "unit": "USD/bbl", "desc": "Initial lifting cost"},
    "fac_life": {"cell": "B12", "expected": 5, "unit": "years", "desc": "Facility life / cycle carry-forward"},
    "n_total": {"cell": "B13", "expected": 145, "unit": "wells", "desc": "Total wells"},
    "n_active": {"cell": "B14", "expected": 58, "unit": "wells", "desc": "Active wells"},
    "n_idle": {"cell": "B15", "expected": 87, "unit": "wells", "desc": "Idle wells"},
    "capex_annual_field": {"cell": "B21", "expected": 4.0, "unit": "USD juta", "desc": "Annual field capex"},
    "capex_pool_corp": {"cell": "B22", "expected": 60.0, "unit": "USD juta", "desc": "Corporate capex pool"},
    "N": {"cell": "B38", "expected": 15, "unit": "years", "desc": "PSC projection years (t=0..14)"},
    "split_c": {"cell": "B42", "expected": 0.55, "unit": "fraction", "desc": "Contractor split"},
    "tax": {"cell": "B44", "expected": 0.40, "unit": "fraction", "desc": "Tax rate"},
    "dr_main": {"cell": "B45", "expected": 0.10, "unit": "fraction", "desc": "Discount rate main (10%)"},
    "dr_low": {"cell": "B46", "expected": 0.08, "unit": "fraction", "desc": "Discount rate low (8%)"},
    "dr_high": {"cell": "B47", "expected": 0.12, "unit": "fraction", "desc": "Discount rate high (12%)"},
    "lc_esc": {"cell": "B49", "expected": 0.03, "unit": "fraction/yr", "desc": "Lifting cost escalation"},
}

V5_ICP_CELLS = {
    "2016": "B26",  # 64 (price_low)
    "2017": "B27",  # 69
    "2018": "B28",  # 102
    "2019": "B29",  # 117 (price_high)
    "2020": "B30",  # 107
    "2021": "B31",  # 83
    "2022": "B32",  # 92
    "2023": "B33",  # 70
    "2024": "B34",  # 80 (price_base)
}

V5_PRICE_CELLS = {
    "price_low": "B39",   # =B26 = 64
    "price_base": "B40",  # =B34 = 80
    "price_high": "B41",  # =B29 = 117
}

V5_OPEX_BAU_ITEMS = [f"C{r}" for r in range(59, 64)]  # C59:C63 sum = 4,000,000

V5_CONTOH_PERHITUNGAN_MAP = {
    "alpha": {"cell": "B23", "expected": 0.5, "unit": "fraction", "desc": "Decline attenuation factor"},
    "wi_xyz": {"cell": "B24", "expected": 0.4, "unit": "fraction", "desc": "XYZ Working Interest"},
    "carry": {"cell": "B26", "expected": 0.7, "unit": "fraction", "desc": "XYZ CAPEX carry on treatment t=0"},
}

# ==============================================================================
# V6_1 (Excel V6.1) Cell Mappings — Lampiran G & H (PRD Addendum v4.1)
# ==============================================================================
V6_EXISTING_DATA_MAP = {
    "stoiip": {"cell": "B5", "expected": 950.0, "unit": "MMbbl", "desc": "STOIIP (Stock Tank Oil Initially In Place)"},
    "rf": {"cell": "B6", "expected": 0.21, "unit": "fraction", "desc": "Recovery Factor Terealisasi (REFERENSI)"},
    "cum_prod": {"cell": "B7", "expected": 200.0, "unit": "MMbbl", "desc": "Estimasi Produksi Kumulatif (REFERENSI)"},
    "reserve_2p_mmbbl": {"cell": "B8", "expected": 38.0, "unit": "MMbbl", "desc": "Cadangan 2P Tersisa"},
    "d0": {"cell": "B9", "expected": 0.075, "unit": "fraction/yr", "desc": "Laju Penurunan Produksi (Decline Rate)"},
    "q0": {"cell": "B10", "expected": 2000.0, "unit": "bopd", "desc": "Produksi Saat Ini (2026)"},
    "wc0": {"cell": "B11", "expected": 0.91, "unit": "fraction", "desc": "Water Cut Saat Ini (2026)"},
    "lc0": {"cell": "B12", "expected": 31.0, "unit": "USD/bbl", "desc": "Biaya Lifting"},
    "fac_life": {"cell": "B13", "expected": 5, "unit": "years", "desc": "Sisa Umur Desain Fasilitas"},
    "n_total": {"cell": "B14", "expected": 145, "unit": "wells", "desc": "Jumlah Sumur Total"},
    "n_active": {"cell": "B15", "expected": 58, "unit": "wells", "desc": "Jumlah Sumur Aktif"},
    "n_idle": {"cell": "B16", "expected": 87, "unit": "wells", "desc": "Jumlah Sumur Idle"},
    "capex_annual_field": {"cell": "B22", "expected": 4.0, "unit": "USD juta", "desc": "Anggaran Capex Tahunan (REFERENSI)"},
    "capex_pool_corp": {"cell": "B23", "expected": 60.0, "unit": "USD juta", "desc": "Kolam Capex Korporat"},
    "N": {"cell": "B39", "expected": 15, "unit": "years", "desc": "Periode evaluasi (DIKUNCI)"},
    "split_c": {"cell": "B43", "expected": 0.55, "unit": "fraction", "desc": "PSC Gross Split (Contr. Take)"},
    "tax": {"cell": "B45", "expected": 0.40, "unit": "fraction", "desc": "Pajak penghasilan kontraktor"},
    "dr_main": {"cell": "B46", "expected": 0.10, "unit": "fraction", "desc": "Discount rate utama (10%)"},
    "dr_low": {"cell": "B47", "expected": 0.08, "unit": "fraction", "desc": "Discount rate rendah (8%)"},
    "dr_high": {"cell": "B48", "expected": 0.12, "unit": "fraction", "desc": "Discount rate tinggi (12%)"},
    "lc_esc": {"cell": "B50", "expected": 0.03, "unit": "fraction/yr", "desc": "Eskalasi biaya lifting"},
}

V6_ICP_CELLS = {
    "2016": "B27",  # 64 (ICP Jan 2026)
    "2017": "B28",  # 69 (ICP Feb 2026)
    "2018": "B29",  # 102 (ICP Mar 2026)
    "2019": "B30",  # 117 (ICP Apr 2026 / Puncak)
    "2020": "B31",  # 107 (ICP Mei 2026)
    "2021": "B32",  # 83 (ICP Jun 2026)
    "2022": "B33",  # 92 (Rata-rata ICP Jan-Mei 2026)
    "2023": "B34",  # 70 (Asumsi APBN 2026)
    "2024": "B35",  # 80 (Asumsi Base Case)
}

V6_PRICE_CELLS = {
    "price_low": "B40",   # =B27 = 64
    "price_base": "B41",  # =B35 = 80
    "price_high": "B42",  # =B30 = 117
}

V6_OPEX_BAU_ITEMS = [f"C{r}" for r in range(60, 65)]  # C60:C64 sum = 4,000,000

V6_CONTOH_PERHITUNGAN_MAP = {
    "alpha": {"cell": "B24", "expected": 0.5, "unit": "fraction", "desc": "Decline attenuation factor"},
    "wi_xyz": {"cell": "B25", "expected": 0.4, "unit": "fraction", "desc": "XYZ Working Interest"},
    "carry": {"cell": "B27", "expected": 0.7, "unit": "fraction", "desc": "XYZ CAPEX carry on treatment t=0"},
}

# Alias default untuk V6_1
EXISTING_DATA_MAP = V6_EXISTING_DATA_MAP
ICP_CELLS = V6_ICP_CELLS
PRICE_CELLS = V6_PRICE_CELLS
OPEX_BAU_ITEMS = V6_OPEX_BAU_ITEMS
CONTOH_PERHITUNGAN_MAP = V6_CONTOH_PERHITUNGAN_MAP

# §3.3 Sheet 'Introduction' & 'Combination'
INTRO_CLASS_RANGE = ("A10", "A27")
INTRO_METHOD_RANGE = ("B10", "B27")

COMB_DRIVE_RANGE = ("G6", "G23")
COMB_HETERO_RANGE = ("H6", "H23")
COMB_REASON_AQUIFER_RANGE = ("M6", "M23")
COMB_REASON_HETERO_RANGE = ("N6", "N23")
COMB_COMPAT_MATRIX_RANGE = ("V6", "AM23")  # 18x18

COMB_RAW_4047_RANGE = ("B5", "B4051")
COMB_PASSED_453_RANGE = ("R5", "R457")

# V6 Combination ranges (+1 shift)
V6_COMB_DRIVE_RANGE = ("G7", "G24")
V6_COMB_HETERO_RANGE = ("H7", "H24")
V6_COMB_REASON_AQUIFER_RANGE = ("M7", "M24")
V6_COMB_REASON_HETERO_RANGE = ("N7", "N24")
V6_COMB_COMPAT_MATRIX_RANGE = ("V7", "AM24")  # 18x18
V6_COMB_RAW_4047_RANGE = ("B6", "B4052")
V6_COMB_PASSED_453_RANGE = ("R6", "R458")

# §3.4 Sheet 'Contingency Rate Combination'
CRC_ID_BARU_RANGE = ("BB4", "BB16")
CRC_METHOD_NAME_RANGE = ("AM4", "AM16")
CRC_P_RANGE = ("BC4", "BC16")
CRC_R_RANGE = ("BD4", "BD16")
CRC_DASAR_RANGE = ("BE4", "BE16")
CRC_CLASS_RANGE = ("BF4", "BF16")
CRC_F1_RANGE = ("BG4", "BG16")
CRC_F2_RANGE = ("BH4", "BH16")
CRC_U_RANGE = ("BJ4", "BJ16")

OVERLAP_WEIGHT_CELLS = {
    "same_function": {"cell": "AN20", "expected": 0.8},
    "same_class": {"cell": "AN21", "expected": 0.4},
    "diff_class": {"cell": "AN22", "expected": 0.15},
}

CRC_PASSED_IDS_RANGE = ("D5", "G457")  # 453 rows x 4 method ID columns

# §3.5 Sheet 'CAPEX OPEX Breakdown'
BREAKDOWN_ROW_START = 1
BREAKDOWN_ROW_END = 189
REACTIVATION_ROW = 188  # row 188 C188=159279, C189 = SUM(C188:C188)

# V6 Breakdown (+1 shift)
V6_BREAKDOWN_ROW_END = 190
V6_REACTIVATION_ROW = 189  # C189, total C190

# Lampiran A: Pemetaan Nama Metode ↔ ID Lama (1..18) ↔ ID Baru (1..13)
METHOD_MAPPINGS: List[Dict[str, Any]] = [
    {
        "id_old": 1,
        "id_new": 1,
        "name": "Polymer/Cross-linked Bulk Gel Treatment",
        "class": "Chemical Conformance / Selective Water Shutoff",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.60,
        "r": 0.60,
        "u": 0.40,
        "crc_class": "Chemical",
        "f1": "BLOK KIMIA",
        "f2": None,
        "dasar": "Literatur",
    },
    {
        "id_old": 2,
        "id_new": 2,
        "name": "Preformed Particle Gel (PPG)",
        "class": "Chemical Conformance / Selective Water Shutoff",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.70,
        "r": 0.10,
        "u": 0.10,
        "crc_class": "Chemical",
        "f1": "BLOK KIMIA",
        "f2": None,
        "dasar": "Literatur",
    },
    {
        "id_old": 3,
        "id_new": None,
        "name": "Relative Permeability Modifier (RPM)",
        "class": "Chemical Conformance / Selective Water Shutoff",
        "drive_aquifer": 0,
        "hetero_high": 0,
        "status": "Eliminasi",
        "p": None,
        "r": None,
        "u": None,
        "crc_class": None,
        "f1": None,
        "f2": None,
        "dasar": None,
    },
    {
        "id_old": 4,
        "id_new": None,
        "name": "Resin/Silicate-based Shutoff",
        "class": "Chemical Conformance / Selective Water Shutoff",
        "drive_aquifer": 0,
        "hetero_high": 1,
        "status": "Eliminasi",
        "p": None,
        "r": None,
        "u": None,
        "crc_class": None,
        "f1": None,
        "f2": None,
        "dasar": None,
    },
    {
        "id_old": 5,
        "id_new": 3,
        "name": "Gel + Cement Combination Squeeze",
        "class": "Chemical Conformance / Selective Water Shutoff",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.70,
        "r": 0.70,
        "u": 0.50,
        "crc_class": "Chemical",
        "f1": "BLOK KIMIA",
        "f2": "ISOLASI MEKANIS",
        "dasar": "Estimasi (analog)",
    },
    {
        "id_old": 6,
        "id_new": 4,
        "name": "Straddle Packer (termasuk HEX type)",
        "class": "Mechanical Isolation",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.75,
        "r": 0.60,
        "u": 0.30,
        "crc_class": "Mechanical",
        "f1": "ISOLASI MEKANIS",
        "f2": None,
        "dasar": "Literatur + estimasi",
    },
    {
        "id_old": 7,
        "id_new": 5,
        "name": "Swellable/Inflatable Packer",
        "class": "Mechanical Isolation",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.60,
        "r": 0.25,
        "u": 0.25,
        "crc_class": "Mechanical",
        "f1": "ISOLASI MEKANIS",
        "f2": None,
        "dasar": "Estimasi (analog)",
    },
    {
        "id_old": 8,
        "id_new": 6,
        "name": "Bridge Plug (mechanical/cast-iron)",
        "class": "Mechanical Isolation",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.85,
        "r": 0.70,
        "u": 0.50,
        "crc_class": "Mechanical",
        "f1": "ISOLASI MEKANIS",
        "f2": None,
        "dasar": "Literatur",
    },
    {
        "id_old": 9,
        "id_new": None,
        "name": "Cement Squeeze / Plug-Back",
        "class": "Mechanical Isolation",
        "drive_aquifer": 0,
        "hetero_high": 0,
        "status": "Eliminasi",
        "p": None,
        "r": None,
        "u": None,
        "crc_class": None,
        "f1": None,
        "f2": None,
        "dasar": None,
    },
    {
        "id_old": 10,
        "id_new": 7,
        "name": "Combined Mechanical Isolation + Gel Injection",
        "class": "Mechanical Isolation",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.80,
        "r": 0.75,
        "u": 0.55,
        "crc_class": "Mechanical",
        "f1": "ISOLASI MEKANIS",
        "f2": "BLOK KIMIA",
        "dasar": "Estimasi (kombinasi)",
    },
    {
        "id_old": 11,
        "id_new": 8,
        "name": "AS-1 Packer + CIBP",
        "class": "Mechanical Isolation",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.85,
        "r": 0.70,
        "u": 0.50,
        "crc_class": "Mechanical",
        "f1": "ISOLASI MEKANIS",
        "f2": None,
        "dasar": "Literatur",
    },
    {
        "id_old": 12,
        "id_new": 9,
        "name": "Inflow Control Device (ICD)",
        "class": "Smart/Flow-Control Completion",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.70,
        "r": 0.25,
        "u": 0.05,
        "crc_class": "Smart Completion",
        "f1": "KONTROL INFLOW",
        "f2": None,
        "dasar": "Literatur + estimasi",
    },
    {
        "id_old": 13,
        "id_new": 10,
        "name": "Autonomous Inflow Control Device/Valve (AICD/AICV)",
        "class": "Smart/Flow-Control Completion",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.75,
        "r": 0.50,
        "u": 0.25,
        "crc_class": "Smart Completion",
        "f1": "KONTROL INFLOW",
        "f2": None,
        "dasar": "Literatur + estimasi",
    },
    {
        "id_old": 14,
        "id_new": None,
        "name": "Production Rate Optimization / Choke Management",
        "class": "Reservoir/Well Management",
        "drive_aquifer": 1,
        "hetero_high": 0,
        "status": "Eliminasi",
        "p": None,
        "r": None,
        "u": None,
        "crc_class": None,
        "f1": None,
        "f2": None,
        "dasar": None,
    },
    {
        "id_old": 15,
        "id_new": None,
        "name": "Produced Water Reinjection / Surface Choking",
        "class": "Reservoir/Well Management",
        "drive_aquifer": 0,
        "hetero_high": 0,
        "status": "Eliminasi",
        "p": None,
        "r": None,
        "u": None,
        "crc_class": None,
        "f1": None,
        "f2": None,
        "dasar": None,
    },
    {
        "id_old": 16,
        "id_new": 11,
        "name": "Targeted Re-perforation (Zona Baru/Bypassed)",
        "class": "Diagnostic-Dependent Workover",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.60,
        "r": 0.30,
        "u": 0.50,
        "crc_class": "Workover",
        "f1": "REKOMPLESI",
        "f2": None,
        "dasar": "Literatur + estimasi",
    },
    {
        "id_old": 17,
        "id_new": 12,
        "name": "Selective Re-completion Guided by PLT",
        "class": "Diagnostic-Dependent Workover",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.70,
        "r": 0.35,
        "u": 0.60,
        "crc_class": "Workover",
        "f1": "REKOMPLESI",
        "f2": None,
        "dasar": "Literatur + estimasi",
    },
    {
        "id_old": 18,
        "id_new": 13,
        "name": "Selective Re-completion Guided by Saturation Log (RST/PNN)",
        "class": "Diagnostic-Dependent Workover",
        "drive_aquifer": 1,
        "hetero_high": 1,
        "status": "Lolos",
        "p": 0.70,
        "r": 0.35,
        "u": 0.60,
        "crc_class": "Workover",
        "f1": "REKOMPLESI",
        "f2": None,
        "dasar": "Estimasi (analog PLT)",
    },
]

# Lookup Maps
NAME_TO_OLD_ID = {m["name"]: m["id_old"] for m in METHOD_MAPPINGS}
OLD_ID_TO_NAME = {m["id_old"]: m["name"] for m in METHOD_MAPPINGS}
NAME_TO_NEW_ID = {m["name"]: m["id_new"] for m in METHOD_MAPPINGS if m["id_new"] is not None}
NEW_ID_TO_NAME = {m["id_new"]: m["name"] for m in METHOD_MAPPINGS if m["id_new"] is not None}
OLD_ID_TO_NEW_ID = {m["id_old"]: m["id_new"] for m in METHOD_MAPPINGS if m["id_new"] is not None}
NEW_ID_TO_OLD_ID = {m["id_new"]: m["id_old"] for m in METHOD_MAPPINGS if m["id_new"] is not None}

