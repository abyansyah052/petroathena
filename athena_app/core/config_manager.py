"""
Module core/config_manager.py: Manajemen Konfigurasi & Asumsi Aplikasi.
Menyimpan parameter default Excel V6, melacak perubahan kustom per sesi,
menghitung CR AHP secara live, serta menyediakan fungsi ekspor/impor JSON
sesuai PRD Addendum v3.2 §10.
"""

import json
import time
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

# Password gate sesi
CONFIG_PASSWORD = "ANGKER123"

# Saaty Random Index (RI) table (1.AHP!C68:C77)
RI_TABLE: Dict[int, float] = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}

# Ambang batas CR per ukuran matriks ('1.AHP'!C80:C82)
CR_LIMITS: Dict[int, float] = {
    3: 0.05,  # C80
    4: 0.08,  # C81 (Level 1)
    5: 0.10,  # C82 (Level 2)
}

# 17 Nilai diskret skala Saaty (Addendum §10.4)
SAATY_SCALE_VALUES: List[float] = [
    1/9, 1/8, 1/7, 1/6, 1/5, 1/4, 1/3, 1/2,
    1.0,
    2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0
]

SAATY_DESCRIPTIONS: Dict[float, str] = {
    1.0: "sama penting (1)",
    2.0: "mendekati sedikit lebih penting (2)",
    3.0: "sedikit lebih penting (3)",
    4.0: "mendekati lebih penting (4)",
    5.0: "lebih penting (5)",
    6.0: "mendekati jauh lebih penting (6)",
    7.0: "jauh lebih penting (7)",
    8.0: "mendekati mutlak lebih penting (8)",
    9.0: "mutlak lebih penting (9)",
}


def get_saaty_text(val: float, item_a: str, item_b: str) -> str:
    """Menerjemahkan nilai slider Saaty menjadi kalimat naratif."""
    if abs(val - 1.0) < 1e-4:
        return f"{item_a} dan {item_b} sama penting (1)"
    if val > 1.0:
        desc = SAATY_DESCRIPTIONS.get(round(val), f"skala {val:.2f}")
        return f"{item_a} {desc} dibanding {item_b}"
    recip = round(1.0 / val)
    desc = SAATY_DESCRIPTIONS.get(recip, f"skala {recip}")
    return f"{item_b} {desc} dibanding {item_a}"


DEFAULT_AHP_LEVEL1: np.ndarray = np.array([
    [1.0, 0.5, 1/3, 1/3],
    [2.0, 1.0, 0.5, 0.5],
    [3.0, 2.0, 1.0, 1.0],
    [3.0, 2.0, 1.0, 1.0],
], dtype=float)

DEFAULT_AHP_LEVEL2: Dict[str, np.ndarray] = {
    "Environmental": np.array([
        [1.0, 5.0, 1.0, 3.0, 5.0],
        [0.2, 1.0, 0.2, 1/3, 1.0],
        [1.0, 5.0, 1.0, 3.0, 5.0],
        [1/3, 3.0, 1/3, 1.0, 2.0],
        [0.2, 1.0, 0.2, 0.5, 1.0],
    ], dtype=float),
    "Technical": np.array([
        [1.0, 3.0, 3.0, 2.0, 3.0],
        [1/3, 1.0, 1.0, 0.5, 1.0],
        [1/3, 1.0, 1.0, 0.5, 1.0],
        [0.5, 2.0, 2.0, 1.0, 2.0],
        [1/3, 1.0, 1.0, 0.5, 1.0],
    ], dtype=float),
    "Risk": np.array([
        [1.0, 2.0, 2.0, 1.0, 3.0],
        [0.5, 1.0, 1.0, 0.5, 2.0],
        [0.5, 1.0, 1.0, 0.5, 2.0],
        [1.0, 2.0, 2.0, 1.0, 3.0],
        [1/3, 0.5, 0.5, 1/3, 1.0],
    ], dtype=float),
    "Financial": np.array([
        [1.0, 3.0, 3.0, 4.0, 3.0],
        [1/3, 1.0, 1.0, 2.0, 2.0],
        [1/3, 1.0, 1.0, 2.0, 2.0],
        [0.25, 0.5, 0.5, 1.0, 1.0],
        [1/3, 0.5, 0.5, 1.0, 1.0],
    ], dtype=float),
}


def calculate_ahp_matrix(pairwise_matrix: np.ndarray) -> Tuple[np.ndarray, float, float, float, bool]:
    """
    Menghitung bobot AHP dan CR menggunakan METODE YANG SAMA DENGAN EXCEL (Addendum §2.2 & §10.4):
    1. Normalisasi kolom: C96 = C88 / SUM(C$88:C$91)
    2. Bobot w_i: Rata-rata baris matriks ternormalisasi
    3. Aw = A * w
    4. lambda_i = Aw_i / w_i
    5. lambda_max = Rata-rata lambda_i
    6. CI = (lambda_max - n) / (n - 1)
    7. CR = CI / RI(n)
    """
    A = np.array(pairwise_matrix, dtype=float)
    n = len(A)
    col_sums = np.sum(A, axis=0)
    col_sums[col_sums == 0] = 1.0
    norm_A = A / col_sums
    weights = np.mean(norm_A, axis=1)

    Aw = np.dot(A, weights)
    # Hindari pembagian nol
    safe_w = np.where(weights == 0, 1.0, weights)
    lambda_i = Aw / safe_w
    lambda_max = float(np.mean(lambda_i))

    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    ri = RI_TABLE.get(n, 1.12)
    cr = ci / ri if ri > 0 else 0.0

    limit = CR_LIMITS.get(n, 0.10)
    is_consistent = (cr <= limit + 1e-6)

    return weights, lambda_max, ci, cr, is_consistent


# Default parameter inventory dari Excel V6 (Addendum §10.3)
EXCEL_V6_DEFAULTS: Dict[str, Any] = {
    # Subtab 0: Data & Kombinasi
    "stoiip": 950.0,             # B4
    "rf": 0.21,                  # B5
    "cum_prod": 200.0,           # B6
    "reserve_2p_mmbbl": 38.0,    # B7
    "d0": 0.075,                 # B8
    "q0": 2000.0,                # B9
    "wc0": 0.91,                 # B10
    "lc0": 31.0,                 # B11
    "fac_life": 5,               # B12
    "n_total": 145,              # B13
    "n_active": 58,              # B14
    "n_idle": 87,                # B15
    "wc_idle0": 0.91,            # B69
    "react_cost": 159279.0,      # B71 / B76
    "overlap_same_func": 0.80,   # AN20
    "overlap_same_class": 0.40,  # AN21
    "overlap_diff_class": 0.15,  # AN22
    "capex_annual_field": 4.0,   # B21

    # Subtab 1: Model Finansial
    "price_low": 64.0,           # B39
    "price_base": 80.0,          # B40
    "price_high": 117.0,         # B41
    "dr_main": 0.10,             # B45
    "dr_low": 0.08,              # B46
    "dr_high": 0.12,             # B47
    "split_c": 0.55,             # B42
    "tax": 0.40,                 # B44
    "eval_period": 15,           # B38
    "lc_esc": 0.03,              # B49
    "alpha": 0.50,               # B23 (Contoh Perhitungan)
    "wi_xyz": 0.40,              # B24
    "carry": 0.70,               # B26

    # Subtab 2: Multi-Kriteria
    "gwp_set": 2,                # B100 (2 = AR6)
    "gwp_ch4": 29.8,             # B113
    "scale_factor": 1.0,         # B104
    "scope3_kat11_active": True, # B101
    "s1_fugitive_ch4": 0.00295,  # B120
    "s1_venting_ch4": 0.01035,   # B121
    "s1_flaring_ch4": 2.5e-5,    # B122
    "s1_flaring_co2": 0.0405,    # B123
    "grid_factor_sumatera": 0.805, # B127
    "lift_kwh_per_bbl": 0.52,    # B128
    "s3_oil_combustion": 0.43218, # B133
    "carbon_price_rp": 30000.0,  # B144
    "usd_rate": 17669.0,         # B96
    "rig_hp": 450.0,             # B153
    "rig_load_factor": 0.45,     # B155
    "rig_emission_per_day": 2.9871673128, # B158
    "rig_days_idle": 17.0,       # B159
    "rig_days_active": 5.0,      # B160 (PLACEHOLDER)
    
    # Ambang FMEA (1.Risk!B64:B68)
    "fmea_critical": 200,        # B64
    "fmea_high": 100,            # B65
    "fmea_medium": 50,           # B66
    "fmea_low": 0,               # B67
    "fmea_esc_severity": 9,      # B68

    # Skala Teknis
    "tech_score_min": 1.0,       # B35
    "tech_score_max": 5.0,       # B36
    "tech_trl_max": 7,           # B37
    "tech_local_cases_full": 3,  # B38

    # Bobot AHP Level 1 Default (1.AHP!C96:F96)
    "ahp_l1_weights": {
        "Environmental": 0.1093,
        "Technical": 0.1892,
        "Risk": 0.3507,
        "Financial": 0.3507,
    },
}

# Metadata Parameter: Sel Excel, Label, Satuan, Rentang Valid
PARAM_METADATA: Dict[str, Dict[str, Any]] = {
    # Subtab 0
    "q0": {"cell": "0.Existing Data!B9", "label": "Laju Produksi Awal (q0)", "unit": "bopd", "min": 100.0, "max": 10000.0},
    "wc0": {"cell": "0.Existing Data!B10", "label": "Water Cut Awal (wc0)", "unit": "fraksi", "min": 0.0, "max": 0.99},
    "d0": {"cell": "0.Existing Data!B8", "label": "Decline Rate Baseline (d0)", "unit": "fraksi/thn", "min": 0.01, "max": 0.50},
    "lc0": {"cell": "0.Existing Data!B11", "label": "Biaya Lifting Awal (lc0)", "unit": "USD/bbl", "min": 5.0, "max": 100.0},
    "n_total": {"cell": "0.Existing Data!B13", "label": "Jumlah Sumur Total", "unit": "sumur", "min": 1, "max": 500},
    "n_active": {"cell": "0.Existing Data!B14", "label": "Jumlah Sumur Aktif", "unit": "sumur", "min": 1, "max": 500},
    "n_idle": {"cell": "0.Existing Data!B15", "label": "Jumlah Sumur Idle", "unit": "sumur", "min": 0, "max": 500},
    "fac_life": {"cell": "0.Existing Data!B12", "label": "Sisa Umur Desain Fasilitas", "unit": "tahun", "min": 1, "max": 20},
    "reserve_2p_mmbbl": {"cell": "0.Existing Data!B7", "label": "Cadangan 2P", "unit": "MMbbl", "min": 1.0, "max": 500.0},
    "react_cost": {"cell": "0.Existing Data!B71", "label": "Biaya Reaktivasi per Sumur Idle", "unit": "USD", "min": 0.0, "max": 1000000.0},
    "overlap_same_func": {"cell": "0.Contingency!AN20", "label": "Bobot Overlap: Fungsi Sama", "unit": "fraksi", "min": 0.0, "max": 1.0},
    "overlap_same_class": {"cell": "0.Contingency!AN21", "label": "Bobot Overlap: Kelas Sama (Beda Fungsi)", "unit": "fraksi", "min": 0.0, "max": 1.0},
    "overlap_diff_class": {"cell": "0.Contingency!AN22", "label": "Bobot Overlap: Kelas Berbeda", "unit": "fraksi", "min": 0.0, "max": 1.0},
    "capex_annual_field": {"cell": "0.Existing Data!B21", "label": "Anggaran CAPEX Rutin BAU", "unit": "USD Juta/thn", "min": 0.5, "max": 20.0},
    
    # Subtab 1: Finansial
    "price_low": {"cell": "0.Existing Data!B39", "label": "Harga Minyak Acuan Low", "unit": "USD/bbl", "min": 20.0, "max": 200.0},
    "price_base": {"cell": "0.Existing Data!B40", "label": "Harga Minyak Acuan Base", "unit": "USD/bbl", "min": 20.0, "max": 200.0},
    "price_high": {"cell": "0.Existing Data!B41", "label": "Harga Minyak Acuan High", "unit": "USD/bbl", "min": 20.0, "max": 200.0},
    "dr_main": {"cell": "0.Existing Data!B45", "label": "Discount Rate Utama", "unit": "fraksi", "min": 0.01, "max": 0.30},
    "split_c": {"cell": "0.Existing Data!B42", "label": "Gross Split Kontraktor", "unit": "fraksi", "min": 0.05, "max": 0.95},
    "tax": {"cell": "0.Existing Data!B44", "label": "Tarif Pajak Penghasilan", "unit": "fraksi", "min": 0.0, "max": 0.60},
    "eval_period": {"cell": "0.Existing Data!B38", "label": "Periode Evaluasi PSC", "unit": "tahun", "min": 5, "max": 30},
    "lc_esc": {"cell": "0.Existing Data!B49", "label": "Eskalasi Biaya Lifting Tahunan", "unit": "fraksi/thn", "min": -0.05, "max": 0.20},
    "alpha": {"cell": "1.Contoh Perhitungan!B23", "label": "Alpha Sensitivitas Decline (α)", "unit": "fraksi", "min": 0.0, "max": 1.0},
    "wi_xyz": {"cell": "1.Contoh Perhitungan!B24", "label": "Working Interest Partner XYZ", "unit": "fraksi", "min": 0.0, "max": 0.90},
    "carry": {"cell": "1.Contoh Perhitungan!B26", "label": "Porsi CAPEX Carry XYZ (t=0)", "unit": "fraksi", "min": 0.0, "max": 1.0},
    
    # Subtab 2: Lingkungan, FMEA, Teknis
    "gwp_set": {"cell": "0.Existing Data!B100", "label": "Set Protokol GWP 100-Thn", "unit": "pilihan", "min": 1, "max": 2},
    "gwp_ch4": {"cell": "0.Existing Data!B113", "label": "GWP Metana (CH4)", "unit": "faktor", "min": 1.0, "max": 50.0},
    "scale_factor": {"cell": "0.Existing Data!B104", "label": "Faktor Skala Emisi Metana & Flare", "unit": "faktor", "min": 0.1, "max": 5.0},
    "s1_fugitive_ch4": {"cell": "0.Existing Data!B120", "label": "Faktor Emisi Fugitive CH4", "unit": "t/m3", "min": 0.0, "max": 0.1},
    "s1_venting_ch4": {"cell": "0.Existing Data!B121", "label": "Faktor Emisi Venting CH4", "unit": "t/m3", "min": 0.0, "max": 0.1},
    "grid_factor_sumatera": {"cell": "0.Existing Data!B127", "label": "Faktor Emisi Grid Sumatera", "unit": "tCO2e/MWh", "min": 0.1, "max": 2.0},
    "lift_kwh_per_bbl": {"cell": "0.Existing Data!B128", "label": "Konsumsi Listrik Artificial Lift", "unit": "kWh/bbl", "min": 0.05, "max": 5.0},
    "carbon_price_rp": {"cell": "0.Existing Data!B144", "label": "Pajak Karbon", "unit": "Rp/tCO2e", "min": 0.0, "max": 200000.0},
    "usd_rate": {"cell": "0.Existing Data!B96", "label": "Kurs Nilai Tukar Rupiah/USD", "unit": "Rp/USD", "min": 10000.0, "max": 30000.0},
    "rig_days_idle": {"cell": "0.Existing Data!B159", "label": "Durasi Rig per Sumur Idle", "unit": "hari", "min": 1.0, "max": 60.0},
    "rig_days_active": {"cell": "0.Existing Data!B160", "label": "Durasi Rig per Sumur Aktif [PLACEHOLDER]", "unit": "hari", "min": 1.0, "max": 30.0},
    "fmea_critical": {"cell": "1.Risk!B64", "label": "Ambang Batas Critical", "unit": "RPN", "min": 100, "max": 1000},
    "fmea_high": {"cell": "1.Risk!B65", "label": "Ambang Batas High", "unit": "RPN", "min": 50, "max": 500},
    "fmea_medium": {"cell": "1.Risk!B66", "label": "Ambang Batas Medium", "unit": "RPN", "min": 10, "max": 200},
    "fmea_low": {"cell": "1.Risk!B67", "label": "Ambang Batas Low", "unit": "RPN", "min": 0, "max": 100},
    "fmea_esc_severity": {"cell": "1.Risk!B68", "label": "Ambang Eskalasi Khusus Severity", "unit": "skala S", "min": 7, "max": 10},
    "tech_score_min": {"cell": "1.AHP!B35", "label": "Skor Skala Minimum Teknis", "unit": "skor", "min": 0.0, "max": 5.0},
    "tech_score_max": {"cell": "1.AHP!B36", "label": "Skor Skala Maksimum Teknis", "unit": "skor", "min": 1.0, "max": 10.0},
    "tech_trl_max": {"cell": "1.AHP!B37", "label": "Skala TRL Maksimum", "unit": "skala", "min": 1, "max": 9},
    "tech_local_cases_full": {"cell": "1.AHP!B38", "label": "Kasus Lokal untuk Skor Penuh", "unit": "kasus", "min": 1, "max": 10},

    # Subtab 3: AHP
    "ahp_l1_weights": {"cell": "1.AHP!C96:F96", "label": "Bobot AHP Level 1", "unit": "vektor", "min": 0.0, "max": 1.0},
}


class ConfigManager:
    """Manajer status konfigurasi runtime aplikasi Athena."""

    @staticmethod
    def get_diffs(active_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mendeteksi seluruh parameter yang menyimpang dari nilai default Excel V6."""
        diffs = []
        for key, val in active_config.items():
            if key in EXCEL_V6_DEFAULTS:
                default_val = EXCEL_V6_DEFAULTS[key]
                if key == "ahp_l1_weights" and isinstance(val, dict) and isinstance(default_val, dict):
                    has_diff = any(abs(float(val.get(k, 0)) - float(default_val.get(k, 0))) > 1e-3 for k in default_val)
                    if has_diff:
                        meta = PARAM_METADATA.get(key, {})
                        diffs.append({
                            "key": key,
                            "label": meta.get("label", key),
                            "cell": meta.get("cell", "-"),
                            "excel_val": "E:10.9%, T:18.9%, R:35.1%, F:35.1%",
                            "current_val": f"E:{float(val.get('Environmental',0))*100:.1f}%, T:{float(val.get('Technical',0))*100:.1f}%, R:{float(val.get('Risk',0))*100:.1f}%, F:{float(val.get('Financial',0))*100:.1f}%",
                            "unit": meta.get("unit", ""),
                            "diff": "Disesuaikan",
                        })
                elif isinstance(val, (int, float)) and isinstance(default_val, (int, float)):
                    if abs(val - default_val) > 1e-6:
                        meta = PARAM_METADATA.get(key, {})
                        diffs.append({
                            "key": key,
                            "label": meta.get("label", key),
                            "cell": meta.get("cell", "-"),
                            "excel_val": default_val,
                            "current_val": val,
                            "unit": meta.get("unit", ""),
                            "diff": val - default_val,
                        })
                elif val != default_val:
                    meta = PARAM_METADATA.get(key, {})
                    diffs.append({
                        "key": key,
                        "label": meta.get("label", key),
                        "cell": meta.get("cell", "-"),
                        "excel_val": default_val,
                        "current_val": val,
                        "unit": meta.get("unit", ""),
                        "diff": "-",
                    })
        return diffs

    @staticmethod
    def export_json(active_config: Dict[str, Any]) -> str:
        """Mengekspor konfigurasi aktif menjadi string JSON terformat."""
        diffs = ConfigManager.get_diffs(active_config)
        payload = {
            "version": "Athena_V6_CustomConfig",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "modified_count": len(diffs),
            "diffs": diffs,
            "full_overrides": active_config,
        }
        return json.dumps(payload, indent=2)

    @staticmethod
    def import_json(json_str: str) -> Dict[str, Any]:
        """Memuat konfigurasi dari string JSON."""
        data = json.loads(json_str)
        if "full_overrides" in data:
            return data["full_overrides"]
        return data


LOCKED_CELLS: Dict[str, str] = {
    "B39": "Periode evaluasi dikunci 15 tahun sesuai PRD §10.6.",
    "eval_period": "Periode evaluasi dikunci 15 tahun sesuai PRD §10.6.",
    "B21": "Sumur aktif di-treat dikunci 10 sumur (Contoh Perhitungan!B21).",
}


def validate_existing_data(ed_dict: Dict[str, Any]) -> List[str]:
    """
    Validates Existing Data inputs against business rules (PRD §10.6 & §13 T18).
    """
    errors = []
    if "n_total" in ed_dict and "n_active" in ed_dict and "n_idle" in ed_dict:
        if ed_dict["n_active"] + ed_dict["n_idle"] != ed_dict["n_total"]:
            errors.append(f"Jumlah sumur aktif ({ed_dict['n_active']}) + idle ({ed_dict['n_idle']}) harus sama dengan total sumur ({ed_dict['n_total']}).")
    if "price_low" in ed_dict and "price_base" in ed_dict and "price_high" in ed_dict:
        if not (ed_dict["price_low"] <= ed_dict["price_base"] <= ed_dict["price_high"]):
            errors.append("Harga minyak harus berurutan: Low <= Base <= High.")
    if "dr_low" in ed_dict and "dr_base" in ed_dict and "dr_high" in ed_dict:
        if not (ed_dict["dr_low"] <= ed_dict["dr_base"] <= ed_dict["dr_high"]):
            errors.append("Discount rate harus berurutan: Low <= Base <= High.")
    return errors

