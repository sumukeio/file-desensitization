"""RFC003：表头行自动识别与手动指定。"""
import openpyxl
from pathlib import Path

from backend.app.engine.excel_processor import ExcelProcessor
from backend.app.engine.rules.header_detector import detect_header_row, resolve_header_row
from backend.app.core.config import WORKSPACE_DIR


class TestHeaderDetection:
    def setup_method(self):
        self.processor = ExcelProcessor()
        self.output_dir = WORKSPACE_DIR / "temp" / "test_output" / "header_fixtures"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _make_title_header_workbook(self, path: Path) -> None:
        """模拟：标题行 + 空行 + 表头 + 数据。"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "2601-2608店铺汇总"
        ws["A1"] = "店铺汇总（1-8月）按累计销售额降序"
        ws["A3"] = "店铺"
        ws["B3"] = "负责人"
        ws["C3"] = "2601-2608销售额"
        ws["D3"] = "2601-2608毛利率"
        ws["A4"] = "测试店铺A"
        ws["B4"] = "张三"
        ws["C4"] = 100000.5
        ws["D4"] = 0.12
        ws["A5"] = "测试店铺B"
        ws["B5"] = "李四"
        ws["C5"] = 80000.0
        ws["D5"] = 0.09
        wb.save(str(path))
        wb.close()

    def test_detect_header_row_on_title_layout(self):
        src = self.output_dir / "title_layout.xlsx"
        self._make_title_header_workbook(src)
        wb = openpyxl.load_workbook(str(src))
        ws = wb.active
        assert detect_header_row(ws) == 3
        wb.close()

    def test_auto_mode_skips_title_and_masks_data_by_real_header(self):
        src = self.output_dir / "title_src.xlsx"
        out = self.output_dir / "title_out.xlsx"
        self._make_title_header_workbook(src)

        result = self.processor.process(src, out, profile="ai_friendly")
        wb = openpyxl.load_workbook(str(out))
        ws = wb.active

        assert result["header_rows"]["2601-2608店铺汇总"] == 3
        # 标题行保留
        assert "店铺汇总" in str(ws.cell(1, 1).value)
        # 表头保留
        assert ws.cell(3, 1).value == "店铺"
        # 数据按真实列名假名化
        assert str(ws.cell(4, 1).value).startswith("店铺_")
        assert str(ws.cell(5, 1).value).startswith("店铺_")
        wb.close()

    def test_manual_header_row_override(self):
        src = self.output_dir / "manual_src.xlsx"
        out = self.output_dir / "manual_out.xlsx"
        self._make_title_header_workbook(src)

        self.processor.process(
            src,
            out,
            profile="ai_friendly",
            custom_options={"header_row_mode": "manual", "header_row": 1},
        )
        wb = openpyxl.load_workbook(str(out))
        ws = wb.active
        # 手动指定第 1 行为表头时，标题会被当成列名上下文；第 4 行起才当数据
        assert ws.cell(1, 1).value == "店铺汇总（1-8月）按累计销售额降序"
        wb.close()

    def test_mask_headers_applies_to_detected_row(self):
        src = self.output_dir / "mask_header_src.xlsx"
        out = self.output_dir / "mask_header_out.xlsx"
        self._make_title_header_workbook(src)

        self.processor.process(
            src,
            out,
            profile="ai_friendly",
            custom_options={"mask_headers": True, "header_row_mode": "auto"},
        )
        wb = openpyxl.load_workbook(str(out))
        ws = wb.active

        assert ws.cell(1, 1).value == "店铺汇总（1-8月）按累计销售额降序"
        assert ws.cell(3, 1).value == "列_01"
        assert str(ws.cell(4, 1).value).startswith("店铺_")
        wb.close()

    def test_simple_first_row_header_still_works(self):
        src = self.output_dir / "simple_src.xlsx"
        out = self.output_dir / "simple_out.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws["A1"] = "ASIN"
        ws["B1"] = "店铺"
        ws["A2"] = "B082TEST001"
        ws["B2"] = "测试店铺A"
        wb.save(str(src))
        wb.close()

        result = self.processor.process(src, out, profile="ai_friendly")
        wb = openpyxl.load_workbook(str(out))
        ws = wb.active
        assert result["header_rows"][ws.title] == 1
        assert ws.cell(1, 1).value == "ASIN"
        assert str(ws.cell(2, 2).value).startswith("店铺_")
        wb.close()

    def test_resolve_header_row_manual_priority(self):
        src = self.output_dir / "resolve_src.xlsx"
        self._make_title_header_workbook(src)
        wb = openpyxl.load_workbook(str(src))
        ws = wb.active
        assert resolve_header_row(ws, header_row_mode="manual", manual_header_row=3) == 3
        assert resolve_header_row(ws, header_row_mode="auto") == 3
        wb.close()

    def test_sheet_override_beats_auto_and_manual(self):
        """RFC005：按 Sheet 纠错覆盖优先于全局 manual / 自动识别。"""
        src = self.output_dir / "override_src.xlsx"
        self._make_title_header_workbook(src)
        wb = openpyxl.load_workbook(str(src))
        ws = wb.active
        # 自动会识别到第 3 行；覆盖强制第 1 行
        assert resolve_header_row(ws, header_row_mode="auto", sheet_override=1) == 1
        assert resolve_header_row(
            ws, header_row_mode="manual", manual_header_row=3, sheet_override=1
        ) == 1
        wb.close()

    def test_process_applies_override_per_sheet_only(self):
        """仅覆盖一个 Sheet 时，其它 Sheet 仍自动识别。"""
        src = self.output_dir / "mixed_override_src.xlsx"
        out = self.output_dir / "mixed_override_out.xlsx"

        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = "普通表"
        ws1["A1"] = "ASIN"
        ws1["B1"] = "店铺"
        ws1["A2"] = "B082TEST001"
        ws1["B2"] = "测试店"

        ws2 = wb.create_sheet("标题表")
        ws2["A1"] = "店铺和团队销售额汇总（示例）"
        ws2["A2"] = None
        ws2["A3"] = "ASIN"
        ws2["B3"] = "店铺"
        ws2["A4"] = "B082TEST001"
        ws2["B4"] = "测试店"
        wb.save(str(src))
        wb.close()

        result = self.processor.process(
            src,
            out,
            profile="ai_friendly",
            custom_options={
                "header_row_mode": "auto",
                # 故意把「标题表」纠成第 1 行（错误但用于验证覆盖生效）
                "header_row_overrides": {"标题表": 1},
            },
        )
        assert result["header_rows"]["普通表"] == 1
        assert result["header_rows"]["标题表"] == 1

