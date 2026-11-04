"""
Module config_registry.py: Registry ruang konfigurasi dan graf dependensi "Dipakai di".
Sesuai PRD + UI/UX Guidelines v5.1 §7.1, §7.3, §7.7, §10 (T12, T13), Lampiran A & B.

Ruang Konfigurasi:
(a) Setiap sel konstanta yang dibaca rumus mana pun (5.556 sel di New_Calc).
(b) Rumus konstan tanpa referensi sel: 47 rumus (17 menjadi field: 15 1.AHP + C106:D106 Technical;
    30 nol definisi BAU di 1.Environmental Impact B82:P82, B97:P97 = struktur).
(c) Sel LINK (1.Contoh Perhitungan B6:B31, 0.Existing Data B40:B42, dll) dan sel OVERRIDE (0.Existing Data B71).
(d) Aturan di defined names: sa_poolc/fi_poolc, sa_poolo/fi_poolo.
"""

from typing import Dict, Any, List, Set, Tuple

# Konstanta Verifikasi Acceptance Test T12
TOTAL_CONSTANT_CELLS_READ_BY_FORMULAS = 5556
TOTAL_CONSTANT_NUMERICAL_FORMULAS = 47
TOTAL_CONSTANT_FORMULA_FIELDS = 17
TOTAL_BAU_ZERO_STRUCTURAL_FORMULAS = 30

# 10 Halaman downstream di bawah simulasi (SEMUA HILIR)
ALL_DOWNSTREAM_PAGES = [
    "Proyeksi Stand-Alone",
    "Skenario Farm-In",
    "Ringkasan SA vs Farm-In",
    "Dampak Lingkungan",
    "Risiko (FMEA)",
    "Implementasi Teknis",
    "Secondary Recovery",
    "Simulasi Kontrak",
    "AHP & TOPSIS",
    "Skenario Terpilih",
]

# 6 Tab Pengaturan (§7.2)
SETTINGS_TABS = [
    "0 · Data & Kombinasi",
    "1 · Model Finansial",
    "2 · Multi-Kriteria",
    "3 · AHP & TOPSIS",
    "4 · Simulasi Lanjutan",
    "5 · Skenario Terpilih",
]

# Pemetaan "Dipakai di" per grup persis tabel katalog PRD §7.3 (Test T13)
GROUP_WHERE_USED: Dict[str, List[str]] = {
    # Tab 0: Data & Kombinasi
    "0.1 Data teknis lapangan": ALL_DOWNSTREAM_PAGES,
    "0.2 Sumur idle": ALL_DOWNSTREAM_PAGES,
    "0.3 Master metode": ALL_DOWNSTREAM_PAGES,
    "0.4 Aturan overlap": ALL_DOWNSTREAM_PAGES,
    "0.5 Hard constraint dan kompatibilitas": ALL_DOWNSTREAM_PAGES,
    "0.6 Daftar kombinasi": ALL_DOWNSTREAM_PAGES,
    "0.7 CAPEX & OPEX per metode": ALL_DOWNSTREAM_PAGES,
    "0.8 Biaya BAU": ALL_DOWNSTREAM_PAGES,
    "0.9 Aturan pool": ALL_DOWNSTREAM_PAGES,

    # Tab 1: Model Finansial
    "1.1 Harga minyak skenario": ALL_DOWNSTREAM_PAGES,
    "1.2 Fiskal PSC dan pajak": ALL_DOWNSTREAM_PAGES,
    "1.3 Discount rate": ALL_DOWNSTREAM_PAGES,
    "1.4 Lifting cost baseline": ALL_DOWNSTREAM_PAGES,
    "1.5 Lifting cost basis liquid": ALL_DOWNSTREAM_PAGES,
    "1.6 Model produksi": ALL_DOWNSTREAM_PAGES,
    "1.7 Hub parameter": ALL_DOWNSTREAM_PAGES,
    "1.8 Farm-In": [
        "Proyeksi Stand-Alone",
        "Skenario Farm-In",
        "Ringkasan SA vs Farm-In",
        "Simulasi Kontrak",
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "1.9 Anggaran, umur fasilitas, periode": ALL_DOWNSTREAM_PAGES,
    "1.10 Referensi makro": [],

    # Tab 2: Multi-Kriteria
    "2.1 Lingkungan: data dan saklar": [
        "Dampak Lingkungan",
        "AHP & TOPSIS",
        "Skenario Terpilih",
        "Secondary Recovery",
        "Simulasi Kontrak",
    ],
    "2.2 Lingkungan: faktor emisi": [
        "Dampak Lingkungan",
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "2.3 Lingkungan: pembanding, karbon, rig": [
        "Dampak Lingkungan",
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "2.4 Risiko: skala Occurrence": [
        "Risiko (FMEA)",
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "2.5 Risiko: ambang kelas": [
        "Risiko (FMEA)",
        "Skenario Terpilih",
    ],
    "2.6 Risiko: register per metode": [
        "Risiko (FMEA)",
        "Implementasi Teknis",
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "2.7 Risiko: generik dan interface": [
        "Risiko (FMEA)",
        "Implementasi Teknis",
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "2.8 Teknis: skala": [
        "Implementasi Teknis",
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "2.9 Teknis: skor per metode": [
        "Implementasi Teknis",
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "2.10 Pemetaan metode yang dinilai": [
        "Risiko (FMEA)",
        "Implementasi Teknis",
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],

    # Tab 3: AHP & TOPSIS
    "3.1 Level 1: kriteria": [
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "3.2 Level 2: Environmental": [
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "3.3 Level 2: Technical": [
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "3.4 Level 2: Risk": [
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "3.5 Level 2: Financial": [
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "3.6 Batas CR dan RI": [
        "AHP & TOPSIS",
    ],
    "3.7 Metadata sub-kriteria": [
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],
    "3.8 Kriteria TOPSIS": [
        "AHP & TOPSIS",
    ],
    "3.9 Pembanding bobot sama rata": [
        "AHP & TOPSIS",
    ],

    # Tab 4: Simulasi Lanjutan
    "4.1 Secondary recovery: saklar": [
        "Secondary Recovery",
        "Skenario Terpilih",
    ],
    "4.2 Secondary recovery: asumsi skema": [
        "Secondary Recovery",
        "Skenario Terpilih",
    ],
    "4.3 Secondary recovery: fasing CAPEX": [
        "Secondary Recovery",
        "Skenario Terpilih",
    ],
    "4.4 Kontrak": [
        "Simulasi Kontrak",
        "AHP & TOPSIS",
        "Skenario Terpilih",
    ],

    # Tab 5: Skenario Terpilih
    "5.1 Pemilihan dan horizon": [
        "Skenario Terpilih",
    ],
    "5.2 Keputusan farm-in": [
        "Skenario Terpilih",
    ],
    "5.3 Parameter negosiasi": [
        "Skenario Terpilih",
    ],
}

# 1 Kalimat Fungsi per Grup (§7.3)
GROUP_FUNCTION_TEXT: Dict[str, str] = {
    # Tab 0
    "0.1 Data teknis lapangan": "Data reservoir, produksi, fasilitas, dan jumlah sumur Athena.",
    "0.2 Sumur idle": "Asumsi water cut, laju acuan, dan biaya reaktivasi sumur idle.",
    "0.3 Master metode": "Peluang sukses (p), penurunan water cut (r), uplift minyak (u), kelas, dan fungsi tiap metode.",
    "0.4 Aturan overlap": "Faktor overlap saat dua metode berfungsi sama, berkelas sama, atau berbeda kelas.",
    "0.5 Hard constraint dan kompatibilitas": "Flag lolos aquifer drive dan heterogenitas tinggi per metode, dan nilai kompatibilitas antar-pasangan metode (2 sinergis, 1 layak, 0 tidak digabung).",
    "0.6 Daftar kombinasi": "Kombinasi 1-4 metode yang dievaluasi (default 453).",
    "0.7 CAPEX & OPEX per metode": "Item biaya per metode: harga, satuan, pool, aturan.",
    "0.8 Biaya BAU": "Rincian CAPEX/OPEX BAU tahunan.",
    "0.9 Aturan pool": "Pool yang digabung dengan nilai maksimum antarmetode (Sekali).",

    # Tab 1
    "1.1 Harga minyak skenario": "Tiga harga yang dipakai seluruh perhitungan dan label radio harga.",
    "1.2 Fiskal PSC dan pajak": "Bagian kontraktor, bagian pemerintah, pajak penghasilan.",
    "1.3 Discount rate": "Diskonto utama dan sensitivitas.",
    "1.4 Lifting cost baseline": "Biaya lifting 2026 dan eskalasi tahunan.",
    "1.5 Lifting cost basis liquid": "Porsi biaya fixed per kasus, kasus yang dipakai, dan lintasan setelah tahun 1.",
    "1.6 Model produksi": "Sensitivitas decline terhadap penurunan water cut (alpha).",
    "1.7 Hub parameter": "Link parameter model finansial; bisa ditimpa per sel.",
    "1.8 Farm-In": "Working interest dan porsi carry CAPEX program oleh XYZ.",
    "1.9 Anggaran, umur fasilitas, periode": "Kolam capex korporat, siklus renewal fasilitas, periode evaluasi, tahun dasar.",
    "1.10 Referensi makro": "Investasi hulu nasional.",

    # Tab 2
    "2.1 Lingkungan: data dan saklar": "Kurs, set GWP, cakupan Scope 3, faktor skala metana, equity share.",
    "2.2 Lingkungan: faktor emisi": "GWP, konversi, Scope 1, Scope 2, Scope 3.",
    "2.3 Lingkungan: pembanding, karbon, rig": "Pembanding OGCI, pajak karbon, emisi rig workover.",
    "2.4 Risiko: skala Occurrence": "Batas bawah probabilitas untuk skor O 1-10.",
    "2.5 Risiko: ambang kelas": "Ambang Critical/High/Medium/Low dan eskalasi Severity.",
    "2.6 Risiko: register per metode": "P(gagal), S, dan D tiap failure mode 7 metode.",
    "2.7 Risiko: generik dan interface": "Cakupan, P dasar, S, D, D jika ada PLT (G1-G7, I1-I7).",
    "2.8 Teknis: skala": "Skor minimum/maksimum, TRL maksimum, kasus lokal penuh.",
    "2.9 Teknis: skor per metode": "Atribut T1-T5 untuk 7 metode yang dinilai.",
    "2.10 Pemetaan metode yang dinilai": "ID master metode untuk 7 kolom penilaian Risiko dan Teknis.",

    # Tab 3
    "3.1 Level 1: kriteria": "Perbandingan berpasangan 4 kriteria (E, T, R, F).",
    "3.2 Level 2: Environmental": "Pairwise E1-E5.",
    "3.3 Level 2: Technical": "Pairwise T1-T5.",
    "3.4 Level 2: Risk": "Pairwise R1-R5.",
    "3.5 Level 2: Financial": "Pairwise F1-F5.",
    "3.6 Batas CR dan RI": "Ambang CR per ukuran matriks dan tabel Random Index.",
    "3.7 Metadata sub-kriteria": "Nama, arah (Benefit/Cost), status data, sumber nilai 20 sub-kriteria.",
    "3.8 Kriteria TOPSIS": "10 ID yang diimplementasikan, dan status sumber nilainya.",
    "3.9 Pembanding bobot sama rata": "Bobot pembanding 4 kriteria.",

    # Tab 4
    "4.1 Secondary recovery: saklar": "Jangka waktu EOR, kasus RF, kasus harga, ambang gate, faktor lifting.",
    "4.2 Secondary recovery: asumsi skema": "RF Low/Mid/High, respons, decline, sumur, CAPEX, OPEX, biaya variabel per skema.",
    "4.3 Secondary recovery: fasing CAPEX": "Porsi CAPEX per tahun proyek per skema.",
    "4.4 Kontrak": "Multiple Exit, FTP, ETBS, diskon risiko Exit, basis biaya, porsi CAPEX t=0.",

    # Tab 5
    "5.1 Pemilihan dan horizon": "Rank TOPSIS yang ditampilkan, kasus harga, batas produksi sampai 2P habis, toleransi rekonsiliasi.",
    "5.2 Keputusan farm-in": "Metric negosiasi: ACCEPT atau NEGOSIASI.",
    "5.3 Parameter negosiasi": "NPV minimum XYZ, langkah grid, floor WI XYZ, plafon promote, batas atas WI XYZ.",
}

# Pembagian grup per tab
TAB_GROUPS: Dict[str, List[str]] = {
    "0 · Data & Kombinasi": [
        "0.1 Data teknis lapangan",
        "0.2 Sumur idle",
        "0.3 Master metode",
        "0.4 Aturan overlap",
        "0.5 Hard constraint dan kompatibilitas",
        "0.6 Daftar kombinasi",
        "0.7 CAPEX & OPEX per metode",
        "0.8 Biaya BAU",
        "0.9 Aturan pool",
    ],
    "1 · Model Finansial": [
        "1.1 Harga minyak skenario",
        "1.2 Fiskal PSC dan pajak",
        "1.3 Discount rate",
        "1.4 Lifting cost baseline",
        "1.5 Lifting cost basis liquid",
        "1.6 Model produksi",
        "1.7 Hub parameter",
        "1.8 Farm-In",
        "1.9 Anggaran, umur fasilitas, periode",
        "1.10 Referensi makro",
    ],
    "2 · Multi-Kriteria": [
        "2.1 Lingkungan: data dan saklar",
        "2.2 Lingkungan: faktor emisi",
        "2.3 Lingkungan: pembanding, karbon, rig",
        "2.4 Risiko: skala Occurrence",
        "2.5 Risiko: ambang kelas",
        "2.6 Risiko: register per metode",
        "2.7 Risiko: generik dan interface",
        "2.8 Teknis: skala",
        "2.9 Teknis: skor per metode",
        "2.10 Pemetaan metode yang dinilai",
    ],
    "3 · AHP & TOPSIS": [
        "3.1 Level 1: kriteria",
        "3.2 Level 2: Environmental",
        "3.3 Level 2: Technical",
        "3.4 Level 2: Risk",
        "3.5 Level 2: Financial",
        "3.6 Batas CR dan RI",
        "3.7 Metadata sub-kriteria",
        "3.8 Kriteria TOPSIS",
        "3.9 Pembanding bobot sama rata",
    ],
    "4 · Simulasi Lanjutan": [
        "4.1 Secondary recovery: saklar",
        "4.2 Secondary recovery: asumsi skema",
        "4.3 Secondary recovery: fasing CAPEX",
        "4.4 Kontrak",
    ],
    "5 · Skenario Terpilih": [
        "5.1 Pemilihan dan horizon",
        "5.2 Keputusan farm-in",
        "5.3 Parameter negosiasi",
    ],
}


def get_where_used(group_id: str) -> List[str]:
    """Mengembalikan daftar halaman yang terdampak oleh grup konfigurasi tertentu."""
    return GROUP_WHERE_USED.get(group_id, ALL_DOWNSTREAM_PAGES)


def get_group_function(group_id: str) -> str:
    """Mengembalikan teks 1 kalimat fungsi per grup (§7.3)."""
    return GROUP_FUNCTION_TEXT.get(group_id, "")

