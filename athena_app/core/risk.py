"""
Module core/risk.py: FMEA (Failure Mode and Effects Analysis) per skenario Top-10.
Sesuai PRD Addendum v3.1 §4.3 dan aturan audit Excel V6 ('1.Risk').
"""

from typing import Dict, Any, List, Tuple
import numpy as np


# Probabilitas batas bawah untuk Occurrence (O: 1..10) dari '1.Risk'!C40:C49 -> B40:B49
OCCURRENCE_TABLE: List[Tuple[float, int]] = [
    (0.50, 10),
    (0.35, 9),
    (0.25, 8),
    (0.15, 7),
    (0.10, 6),
    (0.05, 5),
    (0.025, 4),
    (0.01, 3),
    (0.005, 2),
    (0.00, 1),
]

def lookup_occurrence(p: float) -> int:
    """LOOKUP(P, $C$40:$C$49, $B$40:$B$49)"""
    for threshold, o_score in OCCURRENCE_TABLE:
        if p >= threshold - 1e-9:
            return o_score
    return 1


# 7 Metode yang dinilai di Excel V6 (Addendum §4.0b)
# CRC ID -> Nama & Agregat FMEA Metode (dari '1.Risk'!I83:O87)
RATED_METHODS_RISK: Dict[int, Dict[str, Any]] = {
    1: {"name": "Polymer Gel", "sum_rpn": 972, "max_rpn": 336, "count_fm": 5, "high": 5, "crit": 2},
    2: {"name": "PPG", "sum_rpn": 740, "max_rpn": 245, "count_fm": 4, "high": 3, "crit": 3},
    4: {"name": "Straddle Pkr", "sum_rpn": 702, "max_rpn": 216, "count_fm": 5, "high": 3, "crit": 1},
    6: {"name": "Bridge Plug", "sum_rpn": 551, "max_rpn": 216, "count_fm": 4, "high": 3, "crit": 2},
    8: {"name": "AS-1 + CIBP", "sum_rpn": 657, "max_rpn": 216, "count_fm": 5, "high": 3, "crit": 2},
    11: {"name": "Re-perf", "sum_rpn": 811, "max_rpn": 294, "count_fm": 5, "high": 3, "crit": 2},
    12: {"name": "PLT Recompl.", "sum_rpn": 678, "max_rpn": 343, "count_fm": 4, "high": 2, "crit": 2},
}

# Register Lengkap Failure Mode Metode ('1.Risk'!A91:Q129)
METHOD_FAILURE_MODES_REGISTER: List[Dict[str, Any]] = [
    # Polymer Gel (ID 1)
    {"fm": "1.1 Gelasi dini di tubing / lubang sumur", "method_id": 1, "method": "Polymer Gel", "p": 0.05, "s": 8, "o": 5, "d": 3, "rpn": 120, "class": "High", "active": 1, "effect": "Tubing/perforasi tersumbat, CT cleanout", "cause": "Crosslinker/biosida tak kompatibel, suhu"},
    {"fm": "1.2 Gel masuk zona minyak (non-selektif)", "method_id": 1, "method": "Polymer Gel", "p": 0.15, "s": 8, "o": 7, "d": 6, "rpn": 336, "class": "Critical", "active": 1, "effect": "Permeabilitas minyak turun permanen", "cause": "Tanpa isolasi zona, heterogenitas tinggi"},
    {"fm": "1.3 Gel hilang ke rekahan / thief zone di luar desain", "method_id": 1, "method": "Polymer Gel", "p": 0.12, "s": 6, "o": 6, "d": 5, "rpn": 180, "class": "High", "active": 1, "effect": "Volume efektif kurang, WC tidak turun", "cause": "Heterogenitas High, tekanan rekah rendah"},
    {"fm": "1.4 Gel terbilas / mengalir balik sebelum gelasi", "method_id": 1, "method": "Polymer Gel", "p": 0.10, "s": 6, "o": 6, "d": 6, "rpn": 216, "class": "Critical", "active": 1, "effect": "Blok tidak terbentuk, rig day terbuang", "cause": "Fluks akuifer besar, waktu gelasi panjang"},
    {"fm": "1.5 Kesalahan mixing (konsentrasi / rasio crosslinker)", "method_id": 1, "method": "Polymer Gel", "p": 0.05, "s": 6, "o": 5, "d": 4, "rpn": 120, "class": "High", "active": 1, "effect": "Gel lemah atau gelasi tak terkontrol", "cause": "Kontrol kualitas lapangan terbatas"},
    {"fm": "1.E Efikasi: WC tidak turun sesuai target (1 - p metode)", "method_id": 1, "method": "Polymer Gel", "p": 0.40, "s": 6, "o": 9, "d": 6, "rpn": 324, "class": "Critical", "active": 0, "effect": "Biaya treatment terbuang, WC tetap", "cause": "p metode, 0.Contingency Rate Combination"},
    # PPG (ID 2)
    {"fm": "2.1 Ukuran partikel PPG tidak cocok dengan kanal", "method_id": 2, "method": "PPG", "p": 0.15, "s": 6, "o": 7, "d": 5, "rpn": 210, "class": "Critical", "active": 1, "effect": "Partikel menyumbat dekat sumur", "cause": "Tanpa data kanal; PPG untuk injektor"},
    {"fm": "2.2 PPG menyumbat perforasi zona minyak", "method_id": 2, "method": "PPG", "p": 0.10, "s": 7, "o": 6, "d": 5, "rpn": 210, "class": "Critical", "active": 1, "effect": "Produksi minyak turun", "cause": "Injeksi lewat perforasi non-selektif"},
    {"fm": "2.3 Pompa / CT tersumbat partikel (settling, carrier)", "method_id": 2, "method": "PPG", "p": 0.06, "s": 5, "o": 5, "d": 3, "rpn": 75, "class": "Medium", "active": 1, "effect": "NPT, job dihentikan", "cause": "Slurry mengendap, rate pompa rendah"},
    {"fm": "2.4 Degradasi PPG (suhu/salinitas), efek hilang", "method_id": 2, "method": "PPG", "p": 0.15, "s": 5, "o": 7, "d": 7, "rpn": 245, "class": "Critical", "active": 1, "effect": "WC naik kembali dalam < 12 bulan", "cause": "Stabilitas termal/salinitas, bukti produser lemah"},
    {"fm": "2.E Efikasi: WC tidak turun sesuai target (1 - p metode)", "method_id": 2, "method": "PPG", "p": 0.30, "s": 6, "o": 8, "d": 6, "rpn": 288, "class": "Critical", "active": 0, "effect": "Biaya treatment terbuang, WC tetap", "cause": "p metode, 0.Contingency Rate Combination"},
    # Straddle Pkr (ID 4)
    {"fm": "4.1 Packer gagal set / elemen rusak", "method_id": 4, "method": "Straddle Pkr", "p": 0.03, "s": 5, "o": 4, "d": 2, "rpn": 40, "class": "Low", "active": 1, "effect": "Rerun dan NPT", "cause": "Burr perforasi memotong elastomer"},
    {"fm": "4.2 Seal packer bocor setelah set", "method_id": 4, "method": "Straddle Pkr", "p": 0.08, "s": 7, "o": 5, "d": 5, "rpn": 175, "class": "High", "active": 1, "effect": "Air masuk interval, isolasi gagal", "cause": "Degradasi elemen, diferensial tekanan akuifer"},
    {"fm": "4.3 Packer macet / tidak bisa dilepas", "method_id": 4, "method": "Straddle Pkr", "p": 0.03, "s": 8, "o": 4, "d": 3, "rpn": 96, "class": "Medium", "active": 1, "effect": "Fishing/milling, sumur berisiko", "cause": "Pasir/scale, setting berlebih"},
    {"fm": "4.4 Interval isolasi salah posisi", "method_id": 4, "method": "Straddle Pkr", "p": 0.05, "s": 7, "o": 5, "d": 5, "rpn": 175, "class": "High", "active": 1, "effect": "Zona air terbuka / zona minyak tertutup", "cause": "Korelasi kedalaman keliru"},
    {"fm": "4.5 Air memintas lewat channel semen di belakang casing", "method_id": 4, "method": "Straddle Pkr", "p": 0.10, "s": 6, "o": 6, "d": 6, "rpn": 216, "class": "Critical", "active": 1, "effect": "WC tetap walau packer sehat", "cause": "Channel semen, akuifer aktif"},
    {"fm": "4.E Efikasi: WC tidak turun sesuai target (1 - p metode)", "method_id": 4, "method": "Straddle Pkr", "p": 0.25, "s": 6, "o": 8, "d": 6, "rpn": 288, "class": "Critical", "active": 0, "effect": "Biaya treatment terbuang, WC tetap", "cause": "p metode, 0.Contingency Rate Combination"},
    # Bridge Plug (ID 6)
    {"fm": "6.1 Plug gagal set / preset sebelum kedalaman", "method_id": 6, "method": "Bridge Plug", "p": 0.02, "s": 5, "o": 3, "d": 2, "rpn": 30, "class": "Low", "active": 1, "effect": "Fish/rerun, milling", "cause": "O-ring setting tool, over-tightening"},
    {"fm": "6.2 Plug bocor (seal/slip) pada casing sumur idle", "method_id": 6, "method": "Bridge Plug", "p": 0.08, "s": 7, "o": 5, "d": 3, "rpn": 105, "class": "High", "active": 1, "effect": "Air tidak terisolasi, perlu rerun", "cause": "Casing kotor/korosi, debris di slip"},
    {"fm": "6.3 Plug diset di kedalaman salah", "method_id": 6, "method": "Bridge Plug", "p": 0.05, "s": 8, "o": 5, "d": 5, "rpn": 200, "class": "Critical", "active": 1, "effect": "Zona minyak terisolasi permanen", "cause": "Korelasi log, diagnosis sumber air"},
    {"fm": "6.4 Air memintas lewat channel semen di belakang casing", "method_id": 6, "method": "Bridge Plug", "p": 0.12, "s": 6, "o": 6, "d": 6, "rpn": 216, "class": "Critical", "active": 1, "effect": "WC tetap walau plug sehat", "cause": "Channel semen, akuifer aktif"},
    {"fm": "6.E Efikasi: WC tidak turun sesuai target (1 - p metode)", "method_id": 6, "method": "Bridge Plug", "p": 0.15, "s": 6, "o": 7, "d": 6, "rpn": 252, "class": "Critical", "active": 0, "effect": "Biaya treatment terbuang, WC tetap", "cause": "p metode, 0.Contingency Rate Combination"},
    # AS-1 + CIBP (ID 8)
    {"fm": "8.1 CIBP gagal set / preset", "method_id": 8, "method": "AS-1 + CIBP", "p": 0.03, "s": 5, "o": 4, "d": 2, "rpn": 40, "class": "Low", "active": 1, "effect": "Fish/rerun, milling", "cause": "O-ring setting tool, over-tightening"},
    {"fm": "8.2 Seal CIBP / packer bocor", "method_id": 8, "method": "AS-1 + CIBP", "p": 0.08, "s": 7, "o": 5, "d": 3, "rpn": 105, "class": "High", "active": 1, "effect": "Air tidak terisolasi, perlu rerun", "cause": "Casing kotor/korosi, elemen degradasi"},
    {"fm": "8.3 AS-1 packer macet / tidak bisa dilepas", "method_id": 8, "method": "AS-1 + CIBP", "p": 0.04, "s": 8, "o": 4, "d": 3, "rpn": 96, "class": "Medium", "active": 1, "effect": "Fishing/milling, sumur berisiko", "cause": "Pasir/scale, setting berlebih"},
    {"fm": "8.4 CIBP diset di kedalaman salah", "method_id": 8, "method": "AS-1 + CIBP", "p": 0.05, "s": 8, "o": 5, "d": 5, "rpn": 200, "class": "Critical", "active": 1, "effect": "Zona minyak terisolasi permanen", "cause": "Korelasi log, diagnosis sumber air"},
    {"fm": "8.5 Air memintas lewat channel semen di belakang casing", "method_id": 8, "method": "AS-1 + CIBP", "p": 0.12, "s": 6, "o": 6, "d": 6, "rpn": 216, "class": "Critical", "active": 1, "effect": "WC tetap walau plug sehat", "cause": "Channel semen, akuifer aktif"},
    {"fm": "8.E Efikasi: WC tidak turun sesuai target (1 - p metode)", "method_id": 8, "method": "AS-1 + CIBP", "p": 0.15, "s": 6, "o": 7, "d": 6, "rpn": 252, "class": "Critical", "active": 0, "effect": "Biaya treatment terbuang; bukti AS-1+CIBP NOT FOUND", "cause": "p dianalogikan bridge plug"},
    # Re-perf (ID 11)
    {"fm": "11.1 Gun misfire / discharge parsial", "method_id": 11, "method": "Re-perf", "p": 0.04, "s": 4, "o": 4, "d": 2, "rpn": 32, "class": "Low", "active": 1, "effect": "Perforasi kurang, trip tambahan", "cause": "Ignition terganggu fluida sumur"},
    {"fm": "11.2 Gun macet / debris tertinggal di lubang", "method_id": 11, "method": "Re-perf", "p": 0.02, "s": 7, "o": 3, "d": 3, "rpn": 63, "class": "Medium", "active": 1, "effect": "Fishing, rig day tambahan", "cause": "Debris, deformasi casing"},
    {"fm": "11.3 Perforasi baru dekat zona air, WC naik", "method_id": 11, "method": "Re-perf", "p": 0.15, "s": 7, "o": 7, "d": 6, "rpn": 294, "class": "Critical", "active": 1, "effect": "WC lebih tinggi dari sebelum job", "cause": "Penentuan interval tidak akurat"},
    {"fm": "11.4 Zona bypassed tidak berisi minyak movable", "method_id": 11, "method": "Re-perf", "p": 0.20, "s": 6, "o": 7, "d": 7, "rpn": 294, "class": "Critical", "active": 1, "effect": "Tidak ada tambahan minyak", "cause": "Saturasi tak terverifikasi tanpa log"},
    {"fm": "11.5 Kerusakan casing / semen akibat tembakan", "method_id": 11, "method": "Re-perf", "p": 0.03, "s": 8, "o": 4, "d": 4, "rpn": 128, "class": "High", "active": 1, "effect": "Kebocoran casing, channel baru", "cause": "Casing tua, efek shaped charge"},
    {"fm": "11.E Efikasi: WC tidak turun sesuai target (1 - p metode)", "method_id": 11, "method": "Re-perf", "p": 0.40, "s": 6, "o": 9, "d": 6, "rpn": 324, "class": "Critical", "active": 0, "effect": "Biaya treatment terbuang, WC tetap", "cause": "p metode, 0.Contingency Rate Combination"},
    # PLT Recompl. (ID 12)
    {"fm": "12.1 PLT tidak bisa dijalankan (sumur idle tak mengalir)", "method_id": 12, "method": "PLT Recompl.", "p": 0.15, "s": 4, "o": 7, "d": 2, "rpn": 56, "class": "Medium", "active": 1, "effect": "Diagnosis tertunda, rig day tambahan", "cause": "Sumur idle perlu aktivasi/artificial lift"},
    {"fm": "12.2 Salah interpretasi PLT (rate rendah, WC tinggi)", "method_id": 12, "method": "PLT Recompl.", "p": 0.20, "s": 7, "o": 7, "d": 7, "rpn": 343, "class": "Critical", "active": 1, "effect": "Zona air salah, workover salah sasaran", "cause": "Spinner dynamic range kecil, minyak sedikit"},
    {"fm": "12.3 Interval rekompleksi salah / air ikut ter-commingle", "method_id": 12, "method": "PLT Recompl.", "p": 0.10, "s": 6, "o": 6, "d": 6, "rpn": 216, "class": "Critical", "active": 1, "effect": "WC naik setelah rekompleksi", "cause": "Alokasi rate zona tidak pasti"},
    {"fm": "12.4 String PLT macet / hilang di lubang", "method_id": 12, "method": "PLT Recompl.", "p": 0.02, "s": 7, "o": 3, "d": 3, "rpn": 63, "class": "Medium", "active": 1, "effect": "Fishing, rig day tambahan", "cause": "Debris, scale, deviasi"},
    {"fm": "12.E Efikasi: WC tidak turun sesuai target (1 - p metode)", "method_id": 12, "method": "PLT Recompl.", "p": 0.30, "s": 6, "o": 8, "d": 6, "rpn": 288, "class": "Critical", "active": 0, "effect": "Biaya treatment terbuang; bukti level vendor", "cause": "p metode, 0.Contingency Rate Combination"},
]

# Konstanta Probabilitas yang diekspor ke Technical Implementation (Addendum §4.0a)
P_CASING_IDLE_BURUK = 0.15  # '1.Risk'!C146 (G3)
P_PLT_FAIL = 0.15           # '1.Risk'!D125 (12.1)

# Failure Mode Generik G1-G7 ('1.Risk'!A144:F150)
GENERIC_FAILURE_MODES = [
    {"code": "G1", "name": "Alat macet / fish di lubang", "scope": "run", "p": 0.03, "s": 7, "d_base": 3, "d_plt": 3},
    {"code": "G2", "name": "Well control event saat re-entry", "scope": "run", "p": 0.01, "s": 10, "d_base": 3, "d_plt": 3},
    {"code": "G3", "name": "Integritas casing/tubing sumur idle buruk", "scope": "well", "p": 0.15, "s": 8, "d_base": 4, "d_plt": 4},
    {"code": "G4", "name": "Mobilisasi rig/alat terlambat, NPT", "scope": "well", "p": 0.30, "s": 4, "d_base": 2, "d_plt": 2},
    {"code": "G5", "name": "Tumpahan kimia / cairan sumur / semen", "scope": "run", "p": 0.02, "s": 8, "d_base": 2, "d_plt": 2},
    {"code": "G6", "name": "Salah diagnosis sumber air", "scope": "well", "p": 0.20, "s": 7, "d_base": 7, "d_plt": 4},
    {"code": "G7", "name": "Reaktivasi sumur idle gagal", "scope": "well", "p": 0.10, "s": 6, "d_base": 3, "d_plt": 3},
]

# Failure Mode Interface I1-I7 ('1.Risk'!A151:E157)
INTERFACE_FAILURE_MODES = [
    {"code": "I1", "name": "Gel/PPG + Plug", "p": 0.05, "s": 6, "d": 5, "check": lambda ids: (1 in ids or 2 in ids) and (6 in ids or 8 in ids)},
    {"code": "I2", "name": "Straddle + Plug", "p": 0.04, "s": 6, "d": 4, "check": lambda ids: 4 in ids and 6 in ids},
    {"code": "I3", "name": "Polymer Gel + PPG", "p": 0.10, "s": 8, "d": 6, "check": lambda ids: 1 in ids and 2 in ids},
    {"code": "I4", "name": "Plug + Re-perf", "p": 0.10, "s": 7, "d": 6, "check": lambda ids: 11 in ids and (6 in ids or 8 in ids)},
    {"code": "I5", "name": "Gel/PPG + Re-perf", "p": 0.08, "s": 7, "d": 6, "check": lambda ids: (1 in ids or 2 in ids) and 11 in ids},
    {"code": "I6", "name": "PLT + Plug", "p": 0.12, "s": 8, "d": 5, "check": lambda ids: 12 in ids and (6 in ids or 8 in ids)},
    {"code": "I7", "name": "Gel/PPG + AS-1/CIBP", "p": 0.05, "s": 6, "d": 5, "check": lambda ids: (1 in ids or 2 in ids) and 8 in ids},
]


def calculate_scenario_risk(
    scenario_info: Dict[str, Any],
    rank_sa: int,
    config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Menghitung profil risiko FMEA lengkap untuk 1 skenario Top-10.
    """
    combo = scenario_info["combo"]
    method_ids = [m for m in [combo.get("id_1"), combo.get("id_2"), combo.get("id_3"), combo.get("id_4")] if m is not None]
    n_methods = len(method_ids)
    p_gabungan = scenario_info["cont"]["contingency_rate"]
    
    # Validasi robustness §4.0b: Periksa apakah ada metode di luar 7 metode Excel
    unrated = [m for m in method_ids if m not in RATED_METHODS_RISK]
    if unrated:
        raise ValueError(
            f"Skenario #{scenario_info['no']} memiliki metode CRC ID {unrated} yang belum memiliki data penilaian FMEA di Excel V6. "
            f"Excel hanya menilai 7 metode: 1, 2, 4, 6, 8, 11, 12."
        )

    # 1. Agregasi RPN Metode (Blok A kol F, E, L, M, N)
    sum_rpn_metode = sum(RATED_METHODS_RISK[m]["sum_rpn"] for m in method_ids)
    count_fm_metode = sum(RATED_METHODS_RISK[m]["count_fm"] for m in method_ids)
    max_rpn_metode = max(RATED_METHODS_RISK[m]["max_rpn"] for m in method_ids)
    crit_metode = sum(RATED_METHODS_RISK[m]["crit"] for m in method_ids)
    high_metode = sum(RATED_METHODS_RISK[m]["high"] for m in method_ids)

    # 2. Blok D — Failure Mode Tingkat Strategi
    has_plt = (12 in method_ids)

    # Efikasi gabungan (baris 143)
    p_fail_efficacy = 1.0 - p_gabungan
    o_efficacy = lookup_occurrence(p_fail_efficacy)
    d_efficacy = 6  # F143 = 6, E143 = 6
    s_efficacy = 7  # D143 = 7
    rpn_efficacy = s_efficacy * o_efficacy * d_efficacy

    # Generik G1-G7 (baris 144-150)
    generic_rpns = []
    for g in GENERIC_FAILURE_MODES:
        p_eff = 1.0 - (1.0 - g["p"]) ** n_methods if g["scope"] == "run" else g["p"]
        o_val = lookup_occurrence(p_eff)
        d_val = g["d_plt"] if has_plt else g["d_base"]
        rpn_g = g["s"] * o_val * d_val
        generic_rpns.append(rpn_g)
    sum_rpn_generic = sum(generic_rpns)

    # Interface I1-I7 (baris 151-157)
    interface_rpns = []
    for item in INTERFACE_FAILURE_MODES:
        if item["check"](method_ids):
            o_val = lookup_occurrence(item["p"])
            rpn_i = item["s"] * o_val * item["d"]
        else:
            rpn_i = 0
        interface_rpns.append(rpn_i)
    sum_rpn_interface = sum(interface_rpns)

    # Ambang FMEA dinamis dari config
    th_crit = int(config.get("fmea_critical", 200)) if config else 200
    th_high = int(config.get("fmea_high", 100)) if config else 100
    th_med = int(config.get("fmea_medium", 50)) if config else 50

    # Rekapitulasi Blok D
    strat_all_rpns = [rpn_efficacy] + generic_rpns + interface_rpns
    max_rpn_strat = max(strat_all_rpns)
    count_fm_active_strat = sum(1 for r in strat_all_rpns if r > 0)
    crit_strat = sum(1 for r in strat_all_rpns if r >= th_crit)
    high_strat = sum(1 for r in strat_all_rpns if r >= th_high)

    # Agregasi Total Baris Strategi ('1.Risk'!F:N)
    rpn_total = sum_rpn_metode + rpn_efficacy + sum_rpn_generic + sum_rpn_interface
    total_fm_active = count_fm_metode + count_fm_active_strat
    rpn_avg = rpn_total / total_fm_active if total_fm_active > 0 else 0.0
    rpn_max = max(max_rpn_metode, max_rpn_strat)
    fm_critical = crit_metode + crit_strat
    # Sesuai Addendum §4.3 catatan: N dikurangi M karena hitungan >= High sudah mencakup yang >= Critical
    fm_high = (high_metode + high_strat) - fm_critical

    # Kelas risiko
    if rpn_max >= th_crit:
        risk_class = "Critical"
    elif rpn_max >= th_high:
        risk_class = "High"
    elif rpn_max >= th_med:
        risk_class = "Medium"
    else:
        risk_class = "Low"

    return {
        "no": scenario_info["no"],
        "name": scenario_info["kombinasi"],
        "rank_sa": rank_sa,
        "p_gabungan": p_gabungan,
        "n_methods": n_methods,
        "total_fm_active": total_fm_active,
        "sum_rpn_metode": sum_rpn_metode,
        "rpn_efficacy": rpn_efficacy,
        "sum_rpn_generic": sum_rpn_generic,
        "sum_rpn_interface": sum_rpn_interface,
        "rpn_total": rpn_total,
        "rpn_avg": rpn_avg,
        "rpn_max": rpn_max,
        "fm_critical": fm_critical,
        "fm_high": fm_high,
        "risk_class": risk_class,
        "npv10_80": scenario_info["metrics"]["prices"][80]["npv10"] / 1e6,
    }


def calculate_all_top10_risks(
    top10_sa: List[Dict[str, Any]],
    config: Dict[str, Any] = None,
) -> List[Dict[str, Any]]:
    """
    Menghitung FMEA untuk seluruh 10 skenario teratas SA dan mengurutkan rank risiko (RPN naik).
    """
    results = []
    for rank_idx, s in enumerate(top10_sa):
        res = calculate_scenario_risk(s, rank_sa=rank_idx + 1, config=config)
        results.append(res)

    # Rank risiko: urut RPN Total ascending (makin rendah RPN makin baik)
    sorted_by_rpn = sorted(results, key=lambda x: x["rpn_total"])
    for risk_rank, item in enumerate(sorted_by_rpn, start=1):
        item["risk_rank"] = risk_rank

    return results



def get_fmea_register_summary() -> Dict[str, Any]:
    """
    Mengambil data ringkasan failure mode register per metode ('1.Risk'!B20:E22)
    dan daftar register lengkap untuk tabel UI.
    """
    # Mencari FM dengan RPN tertinggi (aktif)
    active_fms = [f for f in METHOD_FAILURE_MODES_REGISTER if f["active"] == 1]
    highest_fm = max(active_fms, key=lambda x: x["rpn"])
    
    n_critical_total = sum(1 for f in active_fms if f["class"] == "Critical")
    n_high_total = sum(1 for f in active_fms if f["class"] == "High")
    
    # Rata-rata kontribusi kategori RPN dari '1.Risk'!B22:E22
    # [Metode: 55.2%, Efikasi: 4.7%, Generik: 25.8%, Interface: 14.4%]
    return {
        "highest_fm": highest_fm,
        "n_critical_total": n_critical_total,
        "n_high_total": n_high_total,
        "total_fms": len(METHOD_FAILURE_MODES_REGISTER),
        "pct_metode": 55.2,
        "pct_efikasi": 4.7,
        "pct_generik": 25.8,
        "pct_interface": 14.4,
        "register": METHOD_FAILURE_MODES_REGISTER,
    }

