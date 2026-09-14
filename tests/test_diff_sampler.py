"""RFC004 / issue002：效果对比按 Sheet 采样（结构≤5、数据≤5）。"""
from backend.app.engine.rules.diff_sampler import DiffSampleCollector


def _data_sample(sheet: str, idx: int) -> dict:
    return {
        "sheet": sheet,
        "row": idx,
        "col": 1,
        "col_name": "ASIN",
        "mask_type": "PSEUDO_ASIN",
        "original": f"orig-{idx}",
        "desensitized": f"mask-{idx}",
    }


def _header_sample(sheet: str, idx: int = 1) -> dict:
    return {
        "sheet": sheet,
        "row": 1,
        "col": idx,
        "col_name": f"COL{idx}",
        "mask_type": "HEADER",
        "original": f"COL{idx}",
        "desensitized": f"列_{idx:02d}",
    }


class TestDiffSampleCollector:
    def test_structure_and_data_have_separate_per_sheet_caps(self):
        collector = DiffSampleCollector(structure_per_sheet=5, data_per_sheet=5, max_total=200)
        for i in range(10):
            collector.add(_header_sample("SheetA", i))
        for i in range(10):
            collector.add(_data_sample("SheetA", i))

        structure = [s for s in collector.samples if s["mask_type"] in {"HEADER", "SHEET"}]
        data = [s for s in collector.samples if s["mask_type"] not in {"HEADER", "SHEET"}]
        assert len(structure) == 5
        assert len(data) == 5

    def test_later_sheets_still_get_samples(self):
        """回归 issue002：前面 Sheet 不得挤掉后面 Sheet。"""
        collector = DiffSampleCollector(structure_per_sheet=5, data_per_sheet=5, max_total=200)
        for sheet_idx in range(18):
            sheet = f"S{sheet_idx:02d}"
            for i in range(12):
                collector.add(_header_sample(sheet, i))
            for i in range(12):
                collector.add(_data_sample(sheet, i))

        per_sheet_data = {}
        per_sheet_structure = {}
        for s in collector.samples:
            sheet = s["sheet"]
            if s["mask_type"] in {"HEADER", "SHEET"}:
                per_sheet_structure[sheet] = per_sheet_structure.get(sheet, 0) + 1
            else:
                per_sheet_data[sheet] = per_sheet_data.get(sheet, 0) + 1

        assert len(per_sheet_data) == 18
        assert all(v == 5 for v in per_sheet_data.values())
        assert all(v == 5 for v in per_sheet_structure.values())
        assert len(collector.samples) == 18 * 10

    def test_sheet_rename_counts_toward_structure_cap(self):
        collector = DiffSampleCollector(structure_per_sheet=5, data_per_sheet=5, max_total=50)
        for i in range(4):
            collector.add(_header_sample("原表", i))
        collector.add({
            "sheet": "原表",
            "mask_type": "SHEET",
            "original": "原表",
            "desensitized": "Sheet_01",
        })
        collector.add(_header_sample("原表", 99))  # 第 6 条结构，应被拒

        structure = [s for s in collector.samples if s["mask_type"] in {"HEADER", "SHEET"}]
        assert len(structure) == 5
        assert any(s["mask_type"] == "SHEET" for s in structure)

    def test_soft_global_cap_still_applies(self):
        collector = DiffSampleCollector(structure_per_sheet=5, data_per_sheet=5, max_total=10)
        for i in range(20):
            collector.add(_data_sample("S1", i))
            collector.add(_data_sample("S2", i))
        assert len(collector.samples) == 10
