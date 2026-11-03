"""
Module ui/page_settings.py: Halaman Pengaturan Lanjutan (Scenario & Assumption Generator).
Ditulis ulang total sesuai PRD Addendum v4.1 §10 dan UI/UX Guidelines §10.4:
- Password Gate: ANGKER123 (session-based)
- 11 Subtab fungsional dengan st.segmented_control (bukan st.tabs)
- Panel penjelasan per subtab (FUNGSI, KALAU DIUBAH, TIDAK BERUBAH, HALAMAN TERDAMPAK, WAKTU HITUNG)
- Model override untuk sel ber-link (§10.7) dengan tombol "Ikuti rumus Excel"
- Live AHP pairwise comparison (skala diskret Saaty) + Live Preview 10 Sub-kriteria TOPSIS
- Penandaan chip "Perluasan" (T2/T3/T5/F4/F5) dan peringatan blokir (E2/E3/E4/E5/R5)
- Bagian parameter terkunci (§10.6) dengan alasan eksplisit
- Ekspor / Impor JSON (§10.8)
"""

import json
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np

from athena_app.core.config_manager import (
    CONFIG_PASSWORD,
    EXCEL_V6_DEFAULTS,
    SAATY_SCALE_VALUES,
    get_saaty_text,
    calculate_ahp_matrix,
    DEFAULT_AHP_LEVEL1,
    DEFAULT_AHP_LEVEL2,
    ConfigManager,
)
from athena_app.config.topsis_sources import (
    TOPSIS_SOURCE_REGISTRY,
    BLOCKED_SUB_IDS,
    ALL_AHP_SUBCRITERIA,
)
from athena_app.core.topsis import compute_all_ahp_global_weights, validate_top10_subcriteria
from athena_app.ui.components import render_footnote


# 11 Subtab Label Persis PRD §10.2
SETTINGS_SUBTABS = [
    "Data Lapangan",
    "CAPEX & OPEX",
    "Ekonomi & Kontrak PSC",
    "Metode & Kombinasi",
    "Farm-In",
    "Lingkungan",
    "Risiko (FMEA)",
    "Teknis",
    "AHP & TOPSIS",
    "Secondary Recovery",
    "Simulasi Kontrak",
]

SUBTAB_PANELS = {
    "Data Lapangan": {
        "fungsi": "Data fisik Lapangan Athena dari casebook: cadangan, produksi, water cut, decline, biaya lifting, umur fasilitas, jumlah sumur, dan asumsi sumur idle. Ini fondasi seluruh perhitungan produksi.",
        "kalau_diubah": "Produksi 15 tahun untuk BAU dan ke-453 skenario dihitung ulang, sehingga NPV, IRR, Take, ranking, Top-10, dan semua halaman sesudahnya ikut berubah. Beberapa parameter hanya memengaruhi halaman tertentu — lihat kolom ⓘ.",
        "tidak_berubah": "Daftar 453 kombinasi dan kompatibilitas metode.",
        "halaman_terdampak": ["Semua halaman"],
        "waktu_hitung": "Penuh (453 skenario, beberapa detik)",
    },
    "CAPEX & OPEX": {
        "fungsi": "Semua biaya: (a) biaya treatment per metode per sumur — CAPEX sekali di tahun 0, OPEX tiap tahun mulai tahun 1; (b) biaya reaktivasi sumur idle; (c) biaya rutin lapangan BAU.",
        "kalau_diubah": "Biaya per kombinasi dihitung ulang dengan aturan pool, lalu proyeksi, ranking, dan semua halaman sesudahnya. Untuk item ber-aturan Sekali, kenaikan biaya satu metode belum tentu mengubah biaya kombinasi: dalam satu pool yang dipakai adalah biaya termahal di antara metode dalam kombinasi itu.",
        "tidak_berubah": "Produksi, water cut, contingency rate, dan angka emisi per skenario. Halaman Lingkungan, Risiko, dan Teknis hanya berubah bila perubahan biaya mengganti anggota Top-10.",
        "halaman_terdampak": ["Semua halaman (Lingkungan, Risiko, Teknis lewat pergantian Top-10)"],
        "waktu_hitung": "Penuh (453 skenario, beberapa detik)",
    },
    "Ekonomi & Kontrak PSC": {
        "fungsi": "Asumsi pasar dan fiskal yang mengubah barel menjadi uang: harga minyak tiga kasus, bagi hasil Gross Split, pajak, tingkat diskonto, dan eskalasi biaya. Juga data pasar ICP 2026 sebagai sumber harga.",
        "kalau_diubah": "Revenue dan cash flow 453 skenario dihitung ulang; ranking, Top-10, dan semua halaman sesudahnya ikut berubah. Produksi dan volume air tidak berubah.",
        "tidak_berubah": "Produksi, emisi, skor teknis, skor FMEA (kecuali bila Top-10 berganti).",
        "halaman_terdampak": ["Semua halaman kecuali Kombinasi, Hard Constraint, dan Variabel Inti"],
        "waktu_hitung": "Penuh (453 skenario, beberapa detik)",
    },
    "Metode & Kombinasi": {
        "fungsi": "Seberapa efektif tiap metode bila berhasil (p, r, u), seberapa tumpang-tindih dua metode dalam satu kombinasi, dan seberapa kuat penurunan water cut memperlambat decline.",
        "kalau_diubah": "Contingency rate, penurunan water cut, dan uplift gabungan semua kombinasi dihitung ulang → produksi → semua halaman. p juga masuk ke baris efikasi FMEA (1 − p) dan risiko efikasi gabungan (R1 di TOPSIS).",
        "tidak_berubah": "Biaya, daftar kombinasi.",
        "halaman_terdampak": ["Semua halaman"],
        "waktu_hitung": "Penuh (453 skenario, beberapa detik)",
    },
    "Farm-In": {
        "fungsi": "Pembagian skema farm-in dengan mitra XYZ: porsi working interest dan porsi CAPEX program yang ditanggung XYZ.",
        "kalau_diubah": "Hasil Farm-In Top-10 dan Ringkasan SA vs Farm-In dihitung ulang. Karena Simulasi Kontrak memakai biaya bagian PNE (saklar C107 = 1), NPV skema kontrak dan kolom 'Jenis Perpanjangan' di TOPSIS juga bisa berubah.",
        "tidak_berubah": "Proyeksi SA, ranking 453, Top-10, Lingkungan, Risiko, Teknis, Secondary Recovery, dan nilai Ci TOPSIS.",
        "halaman_terdampak": ["Farm-In", "Ringkasan SA vs Farm-In", "Simulasi Kontrak", "AHP & TOPSIS (kolom Jenis Perpanjangan)"],
        "waktu_hitung": "Cepat (< 1 detik)",
    },
    "Lingkungan": {
        "fungsi": "Faktor emisi dan asumsi untuk menghitung Scope 1, 2, 3 dan produced water Top-10.",
        "kalau_diubah": "Halaman Dampak Lingkungan dihitung ulang. Hanya faktor yang memengaruhi intensitas Scope 1+2 yang ikut mengubah TOPSIS (sub-kriteria E1); faktor Scope 3 hanya mengubah tampilan halaman Lingkungan.",
        "tidak_berubah": "Semua angka finansial, produksi, ranking SA.",
        "halaman_terdampak": ["Dampak Lingkungan", "AHP & TOPSIS (sub-kriteria E1)"],
        "waktu_hitung": "Cepat (< 1 detik)",
    },
    "Risiko (FMEA)": {
        "fungsi": "Skala dan penilaian FMEA: probabilitas, severity, detection untuk setiap failure mode, serta ambang kelas risiko.",
        "kalau_diubah": "Halaman Risiko dihitung ulang. Dua probabilitas (G3 integritas casing sumur idle dan 12.1 PLT tidak bisa dijalankan) juga dipakai skor T5 di halaman Teknis. RPN efikasi gabungan dan RPN eksekusi masuk TOPSIS sebagai R1 dan R2.",
        "tidak_berubah": "Angka finansial, Top-10, Lingkungan.",
        "halaman_terdampak": ["Risiko", "Implementasi Teknis", "AHP & TOPSIS"],
        "waktu_hitung": "Cepat (< 1 detik)",
    },
    "Teknis": {
        "fungsi": "Penilaian teknis per metode: kecocokan dengan masalah reservoir, kematangan teknologi, kompleksitas, umur efektif, dan cakupan sumur.",
        "kalau_diubah": "Skor T1-T5 Top-10 dihitung ulang. Dengan bobot AHP sekarang, hanya T1 dan T4 yang masuk TOPSIS; T2, T3, T5 hanya tampil di halaman Teknis.",
        "tidak_berubah": "Angka finansial, Top-10, Lingkungan, Risiko.",
        "halaman_terdampak": ["Implementasi Teknis", "AHP & TOPSIS"],
        "waktu_hitung": "Cepat (< 1 detik)",
    },
    "AHP & TOPSIS": {
        "fungsi": "Penilaian kepentingan relatif antar-kriteria (perbandingan berpasangan skala Saaty) yang menghasilkan bobot. Bobot ini menentukan 10 sub-kriteria TOPSIS dan pengaruhnya.",
        "kalau_diubah": "Bobot dan peringkat TOPSIS dihitung ulang. Mesin proyeksi tidak disentuh.",
        "tidak_berubah": "Semua angka finansial, Top-10, Lingkungan, Risiko, Teknis, Secondary Recovery, Simulasi Kontrak.",
        "halaman_terdampak": ["AHP & TOPSIS"],
        "waktu_hitung": "Cepat (< 1 detik)",
    },
    "Secondary Recovery": {
        "fungsi": "Asumsi skema setelah kontrak awal: kapan secondary recovery dianggap perlu, incremental recovery tiap skema, waktu respons, biaya, dan fasing CAPEX.",
        "kalau_diubah": "Hanya halaman Secondary Recovery yang dihitung ulang — tidak ada halaman lain yang memakai hasilnya.",
        "tidak_berubah": "Semua halaman lain, termasuk TOPSIS.",
        "halaman_terdampak": ["Secondary Recovery"],
        "waktu_hitung": "Cepat (< 1 detik)",
    },
    "Simulasi Kontrak": {
        "fungsi": "Asumsi untuk membandingkan opsi perpanjangan kontrak: termin Cost Recovery (FTP, ETBS), nilai Exit, basis biaya, dan jadwal CAPEX.",
        "kalau_diubah": "Halaman Simulasi Kontrak dihitung ulang, dan kolom 'Jenis Perpanjangan' di TOPSIS bisa berubah. Waktu habisnya cadangan tidak berubah (itu ditentukan produksi).",
        "tidak_berubah": "Semua halaman lain dan nilai Ci TOPSIS.",
        "halaman_terdampak": ["Simulasi Kontrak", "AHP & TOPSIS (kolom Jenis Perpanjangan)"],
        "waktu_hitung": "Cepat (< 1 detik)",
    },
}

SETTINGS_PANELS = SUBTAB_PANELS


def init_settings_state():
    """Menginisialisasi session state konfigurasi."""
    if "config_unlocked" not in st.session_state:
        st.session_state["config_unlocked"] = False
    if "active_config" not in st.session_state:
        st.session_state["active_config"] = dict(EXCEL_V6_DEFAULTS)
    if "staged_config" not in st.session_state:
        st.session_state["staged_config"] = dict(st.session_state["active_config"])
    if "ahp_matrix_l1" not in st.session_state:
        st.session_state["ahp_matrix_l1"] = np.copy(DEFAULT_AHP_LEVEL1)
    if "ahp_matrix_l2" not in st.session_state:
        st.session_state["ahp_matrix_l2"] = {k: np.copy(v) for k, v in DEFAULT_AHP_LEVEL2.items()}
    if "linked_overrides" not in st.session_state:
        st.session_state["linked_overrides"] = {
            "price_low": {"follow_formula": True, "custom_val": 64.0},
            "price_base": {"follow_formula": True, "custom_val": 80.0},
            "price_high": {"follow_formula": True, "custom_val": 117.0},
            "wc_idle0": {"follow_formula": True, "custom_val": 0.91},
            "q_idle_per_well": {"follow_formula": True, "custom_val": 34.482759},
            "react_cost": {"follow_formula": True, "custom_val": 159279.0},
            "idle_wells_treated": {"follow_formula": True, "custom_val": 87.0},
        }


def render_settings_page(engine_results: dict):
    init_settings_state()

    st.subheader("🔒 Pengaturan Lanjutan (Scenario & Assumption Generator)")
    st.markdown(
        "*Ubah asumsi teknis, finansial, lingkungan, risiko, dan bobot perbandingan AHP untuk menghasilkan "
        "skenario alternatif secara interaktif.*"
    )

    # 1. GATE PASSWORD (PRD §10.9)
    if not st.session_state["config_unlocked"]:
        col_gate, _ = st.columns([1.3, 1.7])
        with col_gate:
            st.info("🔒 Akses pengaturan generator skenario kustom dilindungi kata sandi.")
            with st.form("config_unlock_form"):
                st.markdown("**Masukkan Kata Sandi:**")
                pwd_input = st.text_input(
                    "Kata Sandi Pengaturan",
                    type="password",
                    key="pwd_field",
                    placeholder="Ketik kata sandi",
                    help="Masukkan kata sandi 'ANGKER123' untuk membuka akses penuh.",
                    label_visibility="collapsed",
                )
                submit_unlock = st.form_submit_button("🔓 Buka Kunci Pengaturan", use_container_width=True)
                if submit_unlock:
                    if pwd_input == CONFIG_PASSWORD:
                        st.session_state["config_unlocked"] = True
                        st.success("Kata sandi benar. Membuka akses pengaturan...")
                        st.rerun()
                    else:
                        st.error("Kata sandi salah. Silakan coba lagi.")
        return

    # 2. STATUS ASUMSI AKTIF & AUDIT BANNER (§10.8)
    diffs = ConfigManager.get_diffs(st.session_state["active_config"])
    if len(diffs) > 0:
        st.warning(
            f"⚠️ **ASUMSI AKTIF: KUSTOM ({len(diffs)} parameter diubah dari acuan Excel V6_1)** — "
            f"Seluruh model kalkulasi hilir mencerminkan penyesuaian ini."
        )
    else:
        st.info(
            "✅ **ASUMSI AKTIF: ASLI EXCEL V6_1** — Seluruh perhitungan 453 skenario dan modul multi-kriteria "
            "menggunakan nilai default resmi."
        )

    # 3. 11 SUBTABS MENGGUNAKAN st.segmented_control (§10.2)
    selected_subtab = st.segmented_control(
        "Pilih Subtab Pengaturan:",
        options=SETTINGS_SUBTABS,
        default=SETTINGS_SUBTABS[0],
        selection_mode="single",
        key="settings_subtab_selector",
    )
    if not selected_subtab:
        selected_subtab = SETTINGS_SUBTABS[0]

    # Panel Penjelasan Subtab (Fungsi / Dampak / Halaman Terdampak / Waktu Hitung) (§10.3)
    p_info = SUBTAB_PANELS.get(selected_subtab, {})
    with st.container():
        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 16px; margin: 10px 0 16px 0; font-size: 0.88rem; line-height: 1.5; color: #1B1F23;">
                <div style="margin-bottom: 4px;"><strong>FUNGSI:</strong> {p_info.get('fungsi', '-')}</div>
                <div style="margin-bottom: 4px;"><strong>KALAU DIUBAH:</strong> {p_info.get('kalau_diubah', '-')}</div>
                <div style="margin-bottom: 4px;"><strong>TIDAK BERUBAH:</strong> {p_info.get('tidak_berubah', '-')}</div>
                <div style="display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; margin-top: 6px;">
                    <div><strong>HALAMAN TERDAMPAK:</strong> <span style="background: #E0F2FE; color: #0369A1; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">{", ".join(p_info.get('halaman_terdampak', []))}</span></div>
                    <div><strong>WAKTU HITUNG:</strong> <span style="background: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">{p_info.get('waktu_hitung', '-')}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Form Editor berdasarkan Subtab
    staged = st.session_state["staged_config"]

    if selected_subtab == "Data Lapangan":
        group = st.selectbox(
            "Pilih Grup Data Lapangan:",
            ["Reservoir & Cadangan", "Produksi & Water Cut", "Fasilitas & Sumur", "Asumsi Sumur Idle"],
            key="g_field_data",
        )
        if group == "Reservoir & Cadangan":
            staged["stoiip"] = st.number_input("STOIIP (MMbbl) [B5]", value=float(staged.get("stoiip", 950.0)), help="Hanya dipakai Secondary Recovery: volume tambahan skema = incremental RF × STOIIP.")
            staged["reserve_2p_mmbbl"] = st.number_input("Cadangan 2P (MMbbl) [B8]", value=float(staged.get("reserve_2p_mmbbl", 38.0)), help="Tidak mengubah NPV proyeksi. Mengubah sisa oil, gate Secondary Recovery, kapan cadangan habis, dan nilai Exit.")
            st.caption("ℹ️ *B6 (Recovery factor 21%) dan B7 (Produksi kumulatif 200 MMbbl) adalah REFERENSI data casebook, tidak mengubah hasil.*")

        elif group == "Produksi & Water Cut":
            staged["d0"] = st.number_input("Decline Rate Baseline (/tahun) [B9]", value=float(staged.get("d0", 0.075)), format="%.4f", help="Laju turun produksi per tahun. Treatment memperlambatnya menjadi decline × (1 − alpha × p × r).")
            staged["q0"] = st.number_input("Produksi Saat Ini 2026 (bopd) [B10]", value=float(staged.get("q0", 2000.0)), help="Menskalakan seluruh produksi, revenue, dan biaya lifting. Dasar produksi acuan sumur idle.")
            staged["wc0"] = st.number_input("Water Cut Saat Ini 2026 (fraksi) [B11]", value=float(staged.get("wc0", 0.91)), format="%.4f", help="Memengaruhi volume air terproduksi, batas atas uplift dari penurunan water cut.")
            staged["lc0"] = st.number_input("Biaya Lifting Awal (USD/bbl) [B12]", value=float(staged.get("lc0", 31.0)), help="Naik → OPEX semua skenario naik → NPV, Take, dan IRR turun.")

        elif group == "Fasilitas & Sumur":
            staged["fac_life"] = st.number_input("Sisa Umur Fasilitas (tahun) [B13]", value=int(staged.get("fac_life", 5)), min_value=1, max_value=15, help="Menentukan siklus dan besar CAPEX carry-forward BAU, serta skala skor T4. Urutan ranking finansial tidak berubah.")
            c_w1, c_w2 = st.columns(2)
            with c_w1:
                staged["n_active"] = st.number_input("Jumlah Sumur Aktif [B15]", value=int(staged.get("n_active", 58)), min_value=1, help="Menskalakan biaya treatment sumur aktif.")
            with c_w2:
                staged["n_idle"] = st.number_input("Jumlah Sumur Idle [B16]", value=int(staged.get("n_idle", 87)), min_value=0, help="Menskalakan produksi sumur idle dan biaya reaktivasi.")
            staged["n_total"] = staged["n_active"] + staged["n_idle"]
            st.caption(f"Total Sumur Terhitung [B14]: **{staged['n_total']} sumur** (= B15 + B16).")

        elif group == "Asumsi Sumur Idle":
            st.markdown("###### Model Override Sel Ber-link (§10.7)")
            c_link1, c_link2 = st.columns([3, 1])
            with c_link1:
                staged["react_cost"] = st.number_input("Biaya Reaktivasi per Sumur Idle (USD) [B72]", value=float(staged.get("react_cost", 159279.0)), help="Bisa ditimpa dengan angka kustom. Dipakai juga di Secondary Recovery skema Workover.")
            with c_link2:
                st.write("")
                st.write("")
                if st.button("Ikuti rumus Excel", key="btn_reset_b72"):
                    staged["react_cost"] = 159279.0
                    st.success("Link B72 dikembalikan ke rumus Excel (= CAPEX OPEX!C190).")

    elif selected_subtab == "Ekonomi & Kontrak PSC":
        group = st.selectbox("Pilih Grup Ekonomi:", ["Harga Minyak Skenario", "Gross Split & Pajak", "Discount Rate", "Eskalasi & Konteks"], key="g_econ")
        if group == "Harga Minyak Skenario":
            st.markdown("###### Tiga Kasus Harga Minyak (B40, B41, B42)")
            st.caption("Dapat ditimpa; tombol 'Ikuti ICP' mengembalikan link ke harga pasar.")
            c_p1, c_p2, c_p3 = st.columns(3)
            with c_p1:
                staged["price_low"] = st.number_input("Harga Low (USD/bbl) [B40]", value=float(staged.get("price_low", 64.0)))
            with c_p2:
                staged["price_base"] = st.number_input("Harga Base (USD/bbl) [B41]", value=float(staged.get("price_base", 80.0)))
            with c_p3:
                staged["price_high"] = st.number_input("Harga High (USD/bbl) [B42]", value=float(staged.get("price_high", 117.0)))
            if st.button("Ikuti ICP 2026", key="btn_reset_prices"):
                staged["price_low"] = 64.0
                staged["price_base"] = 80.0
                staged["price_high"] = 117.0
                st.rerun()

        elif group == "Gross Split & Pajak":
            staged["split_c"] = st.number_input("Split Kontraktor (Gross Split) [B43]", value=float(staged.get("split_c", 0.55)), min_value=0.0, max_value=1.0, format="%.2f", help="Naik → bagian kontraktor dan NPV naik, Gov. Take turun.")
            st.caption(f"Split Pemerintah [B44]: **{(1.0 - staged['split_c']):.2f}** (read-only = 1 - B43).")
            staged["tax"] = st.number_input("Tarif Pajak Penghasilan [B45]", value=float(staged.get("tax", 0.40)), min_value=0.0, max_value=1.0, format="%.2f", help="Naik → Take dan NPV turun.")

        elif group == "Discount Rate":
            st.caption("Label kolom NPV di seluruh aplikasi akan mengikuti angka discount rate aktif ini (T17).")
            c_d1, c_d2, c_d3 = st.columns(3)
            with c_d1:
                staged["dr_low"] = st.number_input("DR Rendah (NPV,8) [B47]", value=float(staged.get("dr_low", 0.08)), format="%.2f")
            with c_d2:
                staged["dr_main"] = st.number_input("DR Utama (NPV,10) [B46]", value=float(staged.get("dr_main", 0.10)), format="%.2f")
            with c_d3:
                staged["dr_high"] = st.number_input("DR Tinggi (NPV,12) [B48]", value=float(staged.get("dr_high", 0.12)), format="%.2f")

        elif group == "Eskalasi & Konteks":
            staged["lc_esc"] = st.number_input("Eskalasi Biaya Lifting (/tahun) [B50]", value=float(staged.get("lc_esc", 0.03)), min_value=-0.1, max_value=0.2, format="%.3f")
            staged["capex_annual_field"] = st.number_input("Kolom Capex Korporat Revitalisasi (Juta USD) [B23]", value=float(staged.get("capex_annual_field", 60.0)), help="Hanya dipakai untuk pengecekan batas anggaran capex di Secondary Recovery.")

    elif selected_subtab == "Metode & Kombinasi":
        st.markdown("###### Aturan Overlap & Sensitivitas Decline")
        c_o1, c_o2, c_o3 = st.columns(3)
        with c_o1:
            staged["overlap_same_func"] = st.number_input("Overlap: Fungsi Sama [AN20]", value=float(staged.get("overlap_same_func", 0.80)), min_value=0.0, max_value=1.0, format="%.2f")
        with c_o2:
            staged["overlap_same_class"] = st.number_input("Overlap: Kelas Sama [AN21]", value=float(staged.get("overlap_same_class", 0.40)), min_value=0.0, max_value=1.0, format="%.2f")
        with c_o3:
            staged["overlap_diff_class"] = st.number_input("Overlap: Kelas Beda [AN22]", value=float(staged.get("overlap_diff_class", 0.15)), min_value=0.0, max_value=1.0, format="%.2f")

        staged["alpha"] = st.number_input("Sensitivitas Decline (Alpha) [Contoh Perhitungan!B24]", value=float(staged.get("alpha", 0.50)), min_value=0.0, max_value=1.0, format="%.2f", help="Decline baru = decline × (1 − alpha × p × r). Naik → penurunan produksi lebih lambat.")

    elif selected_subtab == "Farm-In":
        st.markdown("###### Parameter Skema Farm-In dengan Mitra XYZ")
        staged["wi_xyz"] = st.number_input("Working Interest Mitra XYZ [B25]", value=float(staged.get("wi_xyz", 0.40)), min_value=0.0, max_value=1.0, format="%.2f", help="Porsi kepemilikan dan pendapatan/biaya mitra XYZ.")
        st.caption(f"Working Interest PNE: **{(1.0 - staged['wi_xyz']):.2f}** (read-only = 1 - B25).")
        staged["carry"] = st.number_input("Porsi Carry CAPEX Program Th-0 oleh XYZ [B27]", value=float(staged.get("carry", 0.70)), min_value=0.0, max_value=1.0, format="%.2f", help="Porsi CAPEX awal yang ditanggung oleh XYZ.")

    elif selected_subtab == "AHP & TOPSIS":
        st.markdown("###### Perbandingan Berpasangan Skala Saaty & Pratinjau TOPSIS Live (§10.4)")
        ahp_group = st.selectbox(
            "Pilih Level / Kriteria Penilaian:",
            [
                "Level 1 — Kriteria Utama (4x4)",
                "Level 2 — Environmental (5x5)",
                "Level 2 — Technical (5x5)",
                "Level 2 — Risk (5x5)",
                "Level 2 — Financial (5x5)",
                "Pratinjau 10 Sub-kriteria TOPSIS Live",
            ],
            key="sb_ahp_group",
        )

        mat_l1 = st.session_state["ahp_matrix_l1"]
        mat_l2 = st.session_state["ahp_matrix_l2"]

        if ahp_group == "Level 1 — Kriteria Utama (4x4)":
            pairs = [
                (0, 1, "Environmental", "Technical"),
                (0, 2, "Environmental", "Risk"),
                (0, 3, "Environmental", "Financial"),
                (1, 2, "Technical", "Risk"),
                (1, 3, "Technical", "Financial"),
                (2, 3, "Risk", "Financial"),
            ]
            for i, j, name_a, name_b in pairs:
                cur_val = float(mat_l1[i, j])
                val_idx = min(range(len(SAATY_SCALE_VALUES)), key=lambda k: abs(SAATY_SCALE_VALUES[k] - cur_val))
                slider_val = st.select_slider(
                    f"{name_a} vs {name_b}:",
                    options=SAATY_SCALE_VALUES,
                    value=SAATY_SCALE_VALUES[val_idx],
                    format_func=lambda v: f"{v:.2f}" if v >= 1 else f"1/{round(1/v)}",
                    key=f"saaty_l1_{i}_{j}",
                )
                mat_l1[i, j] = slider_val
                mat_l1[j, i] = 1.0 / slider_val
                st.caption(f"*{get_saaty_text(slider_val, name_a, name_b)}*")

            w1, _, _, cr1, is_ok1 = calculate_ahp_matrix(mat_l1)
            cr_color = "green" if is_ok1 else "red"
            st.markdown(f"**Rasio Konsistensi CR Level 1:** <span style='color:{cr_color}; font-weight:700;'>{cr1:.4f}</span> (Batas: 0.08)", unsafe_allow_html=True)

        elif "Pratinjau" in ahp_group:
            all_gw = compute_all_ahp_global_weights(mat_l1, mat_l2)
            top10_live = all_gw[:10]
            is_valid, block_msg, exts = validate_top10_subcriteria(top10_live)

            if not is_valid:
                st.error(f"🚫 **Peringatan Pemblokiran TOPSIS:**\n\n{block_msg}")
            elif exts:
                st.info(f"ℹ️ **Chip Perluasan Aktif:** Sub-kriteria **{', '.join(exts)}** akan dinilai memakai kolom perluasan sheet model.")
            else:
                st.success("✅ **Valid:** 10 sub-kriteria teratas sesuai dengan 10 sumber asli sheet `3.TOPSIS` Excel V6_1.")

            df_p = pd.DataFrame([
                {
                    "Rank Global": s["rank"],
                    "ID": s["id"],
                    "Sub-kriteria": s["name"],
                    "Dimensi": s["criteria"],
                    "Bobot Global": f"{s['global_weight']*100:.2f}%",
                    "Arah": s["direction"],
                    "Status Sumber": "Perluasan" if s["id"] in exts else ("BLOCKED" if s["id"] in BLOCKED_SUB_IDS else "Excel Asli"),
                }
                for s in top10_live
            ])
            st.dataframe(df_p, use_container_width=True, hide_index=True)

    elif selected_subtab == "Secondary Recovery":
        st.markdown("###### Parameter Gate & Asumsi Secondary Recovery")
        staged["sr_gate_threshold"] = st.number_input("Ambang Sisa Oil untuk Gate (% dari 2P) [B6]", value=float(staged.get("sr_gate_threshold", 0.10)), min_value=0.01, max_value=0.50, format="%.2f", help="Sisa oil di atas ambang ini dianggap memerlukan secondary recovery.")
        staged["sr_rf_case"] = st.radio("Kasus Incremental RF [B4]:", [1, 2, 3], index=1, horizontal=True, format_func=lambda x: {1: "1 = Low", 2: "2 = Mid", 3: "3 = High"}[x])
        staged["sr_price_case"] = st.radio("Kasus Harga Minyak SR [B5]:", [1, 2, 3], index=1, horizontal=True, format_func=lambda x: {1: "1 = Low", 2: "2 = Base", 3: "3 = High"}[x])
        staged["sr_lifting_factor"] = st.number_input("Faktor Lifting Cost Barrel SR [B7]", value=float(staged.get("sr_lifting_factor", 1.0)), min_value=0.1, max_value=2.0, format="%.2f")

    elif selected_subtab == "Simulasi Kontrak":
        st.markdown("###### Parameter Evaluasi Kontrak (Gross Split, Cost Recovery, Exit)")
        c_e1, c_e2, c_e3 = st.columns(3)
        with c_e1:
            staged["exit_mult_low"] = st.number_input("Multiple Exit Low (USD/bbl 2P) [B97]", value=float(staged.get("exit_mult_low", 2.0)))
        with c_e2:
            staged["exit_mult_base"] = st.number_input("Multiple Exit Base (USD/bbl 2P) [C97]", value=float(staged.get("exit_mult_base", 4.0)))
        with c_e3:
            staged["exit_mult_high"] = st.number_input("Multiple Exit High (USD/bbl 2P) [D97]", value=float(staged.get("exit_mult_high", 8.0)))

        staged["cost_recovery_ftp"] = st.number_input("FTP Cost Recovery (fraksi) [C101]", value=float(staged.get("cost_recovery_ftp", 0.20)), min_value=0.0, max_value=0.5, format="%.2f")
        staged["cost_recovery_etbs_contractor"] = st.number_input("ETBS Bagian Kontraktor (fraksi) [C102]", value=float(staged.get("cost_recovery_etbs_contractor", 0.30)), min_value=0.0, max_value=1.0, format="%.2f")
        staged["exit_risk_discount"] = st.number_input("Diskon Risiko Mature Field (Exit) [C104]", value=float(staged.get("exit_risk_discount", 0.15)), min_value=0.0, max_value=0.5, format="%.2f")
        staged["contract_cost_basis"] = st.radio("Basis CAPEX & OPEX [C107]:", [1, 2], index=0, horizontal=True, format_func=lambda x: "1 = PNE (setelah farm-in)" if x == 1 else "2 = SA (stand-alone penuh)")
        staged["contract_capex_t0_portion"] = st.number_input("Porsi CAPEX di Tahun t=0 [C108]", value=float(staged.get("contract_capex_t0_portion", 1.0)), min_value=0.0, max_value=1.0, format="%.2f")

    # 4. BAGIAN BAWAH STICKY: TOMBOL TERAPKAN & KEMBALIKAN (§10.2)
    st.markdown("---")
    col_act1, col_act2, col_act3, col_act4 = st.columns([1.5, 1.2, 1.2, 1.2])

    with col_act1:
        if st.button("🚀 Terapkan & Hitung Ulang", type="primary", use_container_width=True):
            st.session_state["active_config"] = dict(staged)
            st.success("Konfigurasi berhasil diterapkan! Menghitung ulang seluruh pipeline...")
            st.rerun()

    with col_act2:
        if st.button("↺ Kembalikan Semua", use_container_width=True):
            st.session_state["staged_config"] = dict(EXCEL_V6_DEFAULTS)
            st.session_state["active_config"] = dict(EXCEL_V6_DEFAULTS)
            st.session_state["ahp_matrix_l1"] = np.copy(DEFAULT_AHP_LEVEL1)
            st.session_state["ahp_matrix_l2"] = {k: np.copy(v) for k, v in DEFAULT_AHP_LEVEL2.items()}
            st.info("Seluruh parameter dikembalikan ke nilai resmi Excel V6_1.")
            st.rerun()

    with col_act3:
        json_export = json.dumps({
            "version": "V6_1",
            "timestamp": datetime.now().isoformat(),
            "config": staged,
        }, indent=2)
        st.download_button(
            "⬇️ Unduh .json",
            data=json_export,
            file_name=f"Athena_Custom_Assumptions_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with col_act4:
        uploaded_file = st.file_uploader("Muat .json", type=["json"], label_visibility="collapsed")
        if uploaded_file is not None:
            try:
                loaded_data = json.load(uploaded_file)
                if loaded_data.get("version") != "V6_1":
                    st.error("Gagal: File JSON ini bukan berasal dari versi acuan Excel V6_1.")
                else:
                    st.session_state["staged_config"] = loaded_data["config"]
                    st.session_state["active_config"] = loaded_data["config"]
                    st.success("Konfigurasi JSON berhasil dimuat!")
                    st.rerun()
            except Exception as e:
                st.error(f"Format JSON tidak valid: {e}")

    # 5. BAGIAN "TIDAK DAPAT DIUBAH DI VERSI INI" (PRD §10.6)
    with st.expander("🔒 Bagian Parameter Terkunci di Versi Ini (§10.6)", expanded=False):
        st.markdown(
            """
            | Parameter Dikunci | Alasan Metodologis / Teknis |
            |---|---|
            | **`0.Existing Data!B39` Periode Evaluasi (15 tahun)** | Casebook menetapkan 2026–2040. Beberapa sheet Excel memakai horizon 15 tahun tetap: `1.Environmental Impact` memiliki 15 kolom tahun (B:P), dan `2.Contract Simulations` membagi sisa CAPEX dengan angka tetap 14. Mengubahnya membuat model tidak dapat dicocokkan dengan Excel. |
            | **`1.Contoh Perhitungan!B21` Sumur Aktif yang Di-treat** | Di rumus Excel, uplift produksi sumur aktif dihitung dari produksi seluruh lapangan (`B6 × 365`), tidak bergantung jumlah sumur yang di-treat; angka ini hanya mengalikan biaya. Menguranginya akan menurunkan biaya tanpa mengurangi manfaat — hasilnya tidak masuk akal secara fisik. |
            | **Matriks Kompatibilitas & Hard Constraint** | Mengubah jumlah 453 kombinasi dan penomoran skenario; sheet Risiko dan Teknis hanya memiliki data penilaian untuk 7 metode. |
            | **Struktur Pooling Biaya** | Struktur logika pooling (Sekali / Maksimum vs Jumlah), bukan angka nilai perlakuan. |
            | **Arah Cost/Benefit AHP & Tabel RI Saaty** | Definisi baku metodologi AHP dan literatur Saaty. |
            """
        )

    render_footnote()
