"""
Module loader.py: membaca seluruh input konstan dari Angker_BCC_Excel_Calculations_V5.xlsx
sesuai PRD §3 dan memvalidasinya terhadap nilai yang tertulis di PRD.
"""

import os
import openpyxl
import warnings
from typing import Dict, Any, List, Tuple
from athena_app.config.v5_cell_map import (
    EXISTING_DATA_MAP,
    V5_EXISTING_DATA_MAP,
    V6_EXISTING_DATA_MAP,
    CONTOH_PERHITUNGAN_MAP,
    V5_CONTOH_PERHITUNGAN_MAP,
    V6_CONTOH_PERHITUNGAN_MAP,
    ICP_CELLS,
    V5_ICP_CELLS,
    V6_ICP_CELLS,
    PRICE_CELLS,
    V5_PRICE_CELLS,
    V6_PRICE_CELLS,
    OPEX_BAU_ITEMS,
    V5_OPEX_BAU_ITEMS,
    V6_OPEX_BAU_ITEMS,
    COMB_DRIVE_RANGE,
    COMB_HETERO_RANGE,
    COMB_REASON_AQUIFER_RANGE,
    COMB_REASON_HETERO_RANGE,
    COMB_COMPAT_MATRIX_RANGE,
    COMB_RAW_4047_RANGE,
    COMB_PASSED_453_RANGE,
    CRC_ID_BARU_RANGE,
    CRC_METHOD_NAME_RANGE,
    CRC_P_RANGE,
    CRC_R_RANGE,
    CRC_DASAR_RANGE,
    CRC_CLASS_RANGE,
    CRC_F1_RANGE,
    CRC_F2_RANGE,
    CRC_U_RANGE,
    OVERLAP_WEIGHT_CELLS,
    CRC_PASSED_IDS_RANGE,
    BREAKDOWN_ROW_START,
    BREAKDOWN_ROW_END,
    REACTIVATION_ROW,
    V6_BREAKDOWN_ROW_END,
    V6_REACTIVATION_ROW,
    METHOD_MAPPINGS,
    NAME_TO_OLD_ID,
    OLD_ID_TO_NAME,
    NAME_TO_NEW_ID,
    NEW_ID_TO_NAME,
)


from athena_app.config.sheet_names import get_sheet_names_for_wb

class V5DataLoader:
    def __init__(self, excel_path: str):
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excel file not found at: {excel_path}")
        self.excel_path = excel_path
        self.wb = openpyxl.load_workbook(excel_path, data_only=False)
        self.sheets = get_sheet_names_for_wb(self.wb)
        self.is_v6 = ("0.Existing Data" in self.sheets.values() or "0.Introduction" in self.sheets.values())
        self.warnings: List[str] = []

    def _warn_if_diff(self, name: str, actual: Any, expected: Any, tol: float = 1e-6):
        if expected is None:
            return
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            if abs(actual - expected) > tol:
                msg = f"WARNING: {name} value mismatch! Actual: {actual}, Expected: {expected}"
                self.warnings.append(msg)
                warnings.warn(msg)
        elif actual != expected:
            msg = f"WARNING: {name} value mismatch! Actual: {actual}, Expected: {expected}"
            self.warnings.append(msg)
            warnings.warn(msg)

    def load_existing_data(self) -> Dict[str, Any]:
        ws = self.wb[self.sheets["existing_data"]]
        data: Dict[str, Any] = {}

        cell_map = V6_EXISTING_DATA_MAP if self.is_v6 else V5_EXISTING_DATA_MAP
        for key, info in cell_map.items():
            cell_val = ws[info["cell"]].value
            val = float(cell_val) if isinstance(cell_val, (int, float)) else cell_val
            data[key] = val
            self._warn_if_diff(key, val, info["expected"])

        # Reserve 2P in barrels
        data["reserve_2p"] = data["reserve_2p_mmbbl"] * 1_000_000

        # ICP price points
        icp_cells = V6_ICP_CELLS if self.is_v6 else V5_ICP_CELLS
        data["icp_prices"] = {}
        for year, cell in icp_cells.items():
            data["icp_prices"][year] = float(ws[cell].value)

        # Price low, base, high
        data["price_low"] = float(ws[icp_cells["2016"]].value)   # 64
        data["price_base"] = float(ws[icp_cells["2024"]].value)  # 80
        data["price_high"] = float(ws[icp_cells["2019"]].value)  # 117
        data["split_g"] = 1.0 - data["split_c"]                  # 0.45

        # OPEX BAU
        opex_items = V6_OPEX_BAU_ITEMS if self.is_v6 else V5_OPEX_BAU_ITEMS
        opex_bau_sum = sum(float(ws[c].value) for c in opex_items)
        data["opex_bau"] = opex_bau_sum
        self._warn_if_diff("opex_bau", opex_bau_sum, 4_000_000.0)

        # CAPEX BAU Carry-forward
        data["capex_bau_cf"] = opex_bau_sum * data["fac_life"]
        self._warn_if_diff("capex_bau_cf", data["capex_bau_cf"], 20_000_000.0)

        # Idle parameters
        data["wc_idle0"] = data["wc0"]
        data["q_idle"] = data["q0"] / data["n_active"]

        # Reactivation cost from CAPEX OPEX Breakdown
        ws_brk = self.wb[self.sheets["capex_opex_breakdown"]]
        react_row = V6_REACTIVATION_ROW if self.is_v6 else REACTIVATION_ROW
        data["react_cost"] = float(ws_brk[f"C{react_row}"].value)
        self._warn_if_diff("react_cost", data["react_cost"], 159_279.0)

        return data

    def load_contoh_perhitungan(self) -> Dict[str, Any]:
        ws = self.wb[self.sheets["contoh_perhitungan"]]
        data: Dict[str, Any] = {}
        cp_map = V6_CONTOH_PERHITUNGAN_MAP if self.is_v6 else V5_CONTOH_PERHITUNGAN_MAP
        for key, info in cp_map.items():
            val = float(ws[info["cell"]].value)
            data[key] = val
            self._warn_if_diff(key, val, info["expected"])

        data["wi_pne"] = 1.0 - data["wi_xyz"]
        return data

    def load_methods_and_compatibility(self) -> Dict[str, Any]:
        ws_intro = self.wb[self.sheets["introduction"]]
        ws_comb = self.wb[self.sheets["combination"]]

        methods_18: List[Dict[str, Any]] = []
        for r in range(10, 28):
            old_id = r - 9
            cls = ws_intro[f"A{r}"].value
            name = ws_intro[f"B{r}"].value
            methods_18.append({
                "id_old": old_id,
                "class": cls,
                "name": name,
            })

        # Combination flags and reasons (+1 shift for V6_1)
        comb_start = 7 if self.is_v6 else 6
        for i, m in enumerate(methods_18):
            r = i + comb_start
            drive = int(ws_comb[f"G{r}"].value)
            hetero = int(ws_comb[f"H{r}"].value)
            alasan_aq = ws_comb[f"M{r}"].value
            alasan_het = ws_comb[f"N{r}"].value
            m["drive_aquifer"] = drive
            m["hetero_high"] = hetero
            m["lolos"] = drive * hetero
            m["status"] = "Lolos" if (drive * hetero == 1) else "Eliminasi"
            m["alasan_aquifer"] = alasan_aq
            m["alasan_hetero"] = alasan_het
            m["id_new"] = NAME_TO_NEW_ID.get(m["name"])

        # Compatibility matrix 18x18
        # Cols V to AM -> 22 to 39
        compat_matrix: List[List[Any]] = []
        for r in range(comb_start, comb_start + 18):
            row_vals = []
            for c in range(22, 40):
                val = ws_comb.cell(r, c).value
                if val == "-":
                    row_vals.append(val)
                else:
                    row_vals.append(int(val))
            compat_matrix.append(row_vals)

        return {
            "methods_18": methods_18,
            "compat_matrix": compat_matrix,
        }

    def load_crc_parameters(self) -> Dict[str, Any]:
        ws = self.wb[self.sheets["contingency_rate_combination"]]

        methods_13: List[Dict[str, Any]] = []
        for r in range(4, 17):
            id_new = int(ws[f"BB{r}"].value)
            name = str(ws[f"AM{r}"].value).strip()
            p = float(ws[f"BC{r}"].value)
            r_val = float(ws[f"BD{r}"].value)
            dasar = str(ws[f"BE{r}"].value).strip() if ws[f"BE{r}"].value else ""
            cls = str(ws[f"BF{r}"].value).strip()
            f1 = str(ws[f"BG{r}"].value).strip()
            f2 = str(ws[f"BH{r}"].value).strip() if ws[f"BH{r}"].value else None
            u = float(ws[f"BJ{r}"].value)

            methods_13.append({
                "id_new": id_new,
                "id_old": NAME_TO_OLD_ID.get(name),
                "name": name,
                "p": p,
                "r": r_val,
                "u": u,
                "class": cls,
                "f1": f1,
                "f2": f2,
                "dasar": dasar,
            })

        overlap_weights = {
            "same_function": float(ws[OVERLAP_WEIGHT_CELLS["same_function"]["cell"]].value),
            "same_class": float(ws[OVERLAP_WEIGHT_CELLS["same_class"]["cell"]].value),
            "diff_class": float(ws[OVERLAP_WEIGHT_CELLS["diff_class"]["cell"]].value),
        }
        for k, v in overlap_weights.items():
            self._warn_if_diff(f"overlap_{k}", v, OVERLAP_WEIGHT_CELLS[k]["expected"])

        return {
            "methods_13": methods_13,
            "overlap_weights": overlap_weights,
        }

    def load_capex_opex_breakdown(self) -> Dict[str, Any]:
        ws = self.wb[self.sheets["capex_opex_breakdown"]]
        items: List[Dict[str, Any]] = []

        end_row = V6_BREAKDOWN_ROW_END if self.is_v6 else BREAKDOWN_ROW_END
        for r in range(BREAKDOWN_ROW_START, end_row + 1):
            cost_type = ws.cell(r, 12).value  # L
            if cost_type in ["CAPEX", "OPEX"]:
                raw_id = ws.cell(r, 11).value  # K
                item_name = str(ws.cell(r, 2).value).strip()
                pool = str(ws.cell(r, 13).value).strip()
                rule = str(ws.cell(r, 14).value).strip()

                if raw_id == "R":
                    # Reactivation cost item
                    val = float(ws.cell(r, 3).value)
                    items.append({
                        "row": r,
                        "method_id": "R",
                        "cost_type": cost_type,
                        "name": item_name,
                        "pool": pool,
                        "rule": rule,
                        "value": val,
                        "vol": None,
                        "unit_price": None,
                        "freq": None,
                    })
                else:
                    method_id = int(raw_id)
                    if cost_type == "CAPEX":
                        val = float(ws.cell(r, 3).value)
                        vol, unit_p, freq = None, None, None
                    else:
                        vol = float(ws.cell(r, 6).value)
                        unit_p = float(ws.cell(r, 8).value)
                        freq = float(ws.cell(r, 10).value)
                        val = vol * unit_p * freq

                    items.append({
                        "row": r,
                        "method_id": method_id,
                        "cost_type": cost_type,
                        "name": item_name,
                        "pool": pool,
                        "rule": rule,
                        "value": val,
                        "vol": vol,
                        "unit_price": unit_p,
                        "freq": freq,
                    })

        return {"items": items}

    def load_all(self) -> Dict[str, Any]:
        existing_data = self.load_existing_data()
        contoh_perhitungan = self.load_contoh_perhitungan()
        comb_data = self.load_methods_and_compatibility()
        crc_data = self.load_crc_parameters()
        breakdown_data = self.load_capex_opex_breakdown()

        return {
            "existing_data": existing_data,
            "contoh_perhitungan": contoh_perhitungan,
            "methods_18": comb_data["methods_18"],
            "compat_matrix": comb_data["compat_matrix"],
            "methods_13": crc_data["methods_13"],
            "overlap_weights": crc_data["overlap_weights"],
            "breakdown_items": breakdown_data["items"],
            "warnings": self.warnings,
        }
