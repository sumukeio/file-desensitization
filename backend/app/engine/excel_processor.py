import re
from pathlib import Path
from typing import Dict, Any, Callable, Optional, List, Set
from datetime import date, datetime

import openpyxl

from backend.app.engine.base import IFileProcessor
from backend.app.engine.rules.maskers import mask_text_middle, detect_and_mask_pii
from backend.app.engine.rules.pseudonym import PseudonymPool
from backend.app.engine.rules.profiles import (
    PSEUDO_COLUMN_MAPPING,
    CATEGORICAL_WHITELIST,
)
from backend.app.engine.rules.header_detector import resolve_header_row
from backend.app.engine.rules.diff_sampler import DiffSampleCollector

# Excel 工作表名非法字符
_SHEET_INVALID_CHARS = re.compile(r'[\\/?*\[\]]')


class ExcelProcessor(IFileProcessor):
    """Excel / CSV 文件脱敏处理器"""

    def validate(self, input_path: Path) -> bool:
        ext = input_path.suffix.lower()
        return ext in {".xlsx", ".xls", ".csv"} and input_path.exists()

    def process(
        self,
        input_path: Path,
        output_path: Path,
        profile: str = "ai_friendly",
        progress_callback: Optional[Callable[[int], None]] = None,
        custom_options: Optional[Dict[str, Any]] = None,
        shared_pseudo_pool: Optional[PseudonymPool] = None,
    ) -> Dict[str, Any]:
        """执行 Excel 脱敏核心管道"""
        pseudo_pool = shared_pseudo_pool or PseudonymPool()
        custom_options = custom_options or {}
        mask_headers = bool(custom_options.get("mask_headers", False))
        mask_sheet_names = bool(custom_options.get("mask_sheet_names", False))
        header_row_mode = str(custom_options.get("header_row_mode", "auto")).lower()
        manual_header_row = custom_options.get("header_row")
        if manual_header_row is not None:
            try:
                manual_header_row = int(manual_header_row)
            except (TypeError, ValueError):
                manual_header_row = None
        raw_overrides = custom_options.get("header_row_overrides") or {}
        header_row_overrides: Dict[str, int] = {}
        if isinstance(raw_overrides, dict):
            for k, v in raw_overrides.items():
                try:
                    header_row_overrides[str(k)] = int(v)
                except (TypeError, ValueError):
                    continue

        # 加载工作簿 (保留原格式)
        wb = openpyxl.load_workbook(str(input_path))
        total_sheets = len(wb.sheetnames)

        masked_count = 0
        diff_collector = DiffSampleCollector()
        header_rows: Dict[str, int] = {}
        sheet_renames: Dict[str, str] = {}

        # 记录原始 Sheet 名，供后续可选重命名与 Diff 使用
        original_sheet_names = list(wb.sheetnames)

        for sheet_idx, sheet_name in enumerate(original_sheet_names):
            ws = wb[sheet_name]
            max_row = ws.max_row
            max_col = ws.max_column

            if max_row < 1 or max_col < 1:
                continue

            header_row = resolve_header_row(
                ws,
                header_row_mode=header_row_mode,
                manual_header_row=manual_header_row,
                sheet_override=header_row_overrides.get(sheet_name),
            )
            header_rows[sheet_name] = header_row

            # 读取识别出的表头行（保留语义，建立列索引映射）
            headers = self._read_headers(ws, header_row, max_col)

            # 遍历数据行 —— 始终使用原始列名做实体匹配；表头上方标题区不处理
            data_start = header_row + 1
            if data_start > max_row:
                continue

            for row in range(data_start, max_row + 1):
                for col in range(1, max_col + 1):
                    cell = ws.cell(row, col)
                    raw_val = cell.value

                    if raw_val is None:
                        continue

                    # 公式与日期时间严格保留
                    if isinstance(raw_val, str) and raw_val.startswith("="):
                        continue
                    if isinstance(raw_val, (datetime, date)):
                        continue

                    col_name = headers[col - 1]
                    col_name_lower = col_name.lower()
                    new_val = raw_val
                    mask_type = "NONE"

                    # 1. 检查是否为高危 PII (手机、身份证、银行卡、邮箱、IP)
                    val_str = str(raw_val).strip()
                    is_pii, masked_pii, pii_type = detect_and_mask_pii(val_str)
                    if is_pii:
                        new_val = masked_pii
                        mask_type = f"PII_{pii_type}"
                    else:
                        # 2. 如果是纯数值且不是高危 PII，遵循“数字不处理/保留统计度量”
                        if isinstance(raw_val, (int, float)):
                            new_val = raw_val
                            mask_type = "NUMBER_KEEP"
                        # 3. 文本类型处理逻辑
                        elif isinstance(raw_val, str):
                            # AI 友好模式
                            if profile == "ai_friendly":
                                # 检查是否为已知实体列（执行跨表一致性假名化）
                                matched_entity = None
                                for k, prefix in PSEUDO_COLUMN_MAPPING.items():
                                    if k in col_name_lower:
                                        matched_entity = prefix
                                        break

                                if matched_entity:
                                    new_val = pseudo_pool.get_or_create(val_str, entity_type=matched_entity)
                                    mask_type = f"PSEUDO_{matched_entity}"
                                elif val_str in CATEGORICAL_WHITELIST:
                                    # 分类枚举白名单保留
                                    new_val = val_str
                                    mask_type = "CATEGORY_KEEP"
                                else:
                                    # 常规文本执行中间打星
                                    masked_str = mask_text_middle(val_str)
                                    if masked_str != val_str:
                                        new_val = masked_str
                                        mask_type = "TEXT_MIDDLE_MASK"
                            # 标准掩码模式
                            elif profile == "standard_mask":
                                masked_str = mask_text_middle(val_str)
                                if masked_str != val_str:
                                    new_val = masked_str
                                    mask_type = "TEXT_MIDDLE_MASK"
                            # 深度匿名化模式
                            elif profile == "strict_anon":
                                new_val = f"ANON_{hash(val_str) % 10000:04d}"
                                mask_type = "STRICT_ANON"

                    # 若发生变更，写回单元格并收集统计与样本
                    if new_val != raw_val:
                        cell.value = new_val
                        masked_count += 1
                        diff_collector.add({
                            "sheet": sheet_name,
                            "row": row,
                            "col": col,
                            "col_name": col_name,
                            "original": str(raw_val),
                            "desensitized": str(new_val),
                            "mask_type": mask_type,
                        })

                # 更新进度回调
                if progress_callback and max_row > data_start:
                    row_progress = (row - data_start + 1) / (max_row - data_start + 1)
                    overall_progress = int(((sheet_idx + row_progress) / total_sheets) * 100)
                    progress_callback(min(99, overall_progress))

            # —— 数据行处理完毕后，按开关改写识别出的表头行 ——
            if mask_headers:
                for col in range(1, max_col + 1):
                    cell = ws.cell(header_row, col)
                    if cell.value is None:
                        continue
                    raw_header = str(cell.value).strip()
                    if not raw_header:
                        continue
                    new_header = self._transform_structure_name(
                        raw_header, profile, pseudo_pool, entity_type="列"
                    )
                    if new_header != raw_header:
                        cell.value = new_header
                        masked_count += 1
                        diff_collector.add({
                            "sheet": sheet_name,
                            "row": header_row,
                            "col": col,
                            "col_name": raw_header,
                            "original": raw_header,
                            "desensitized": str(new_header),
                            "mask_type": "HEADER",
                        })

        # —— 全部 Sheet 数据与列名处理完毕后，按开关重命名 Sheet ——
        if mask_sheet_names:
            used_titles: Set[str] = set()
            renames = []
            for original_name in original_sheet_names:
                ws = wb[original_name]
                candidate = self._transform_structure_name(
                    original_name, profile, pseudo_pool, entity_type="Sheet"
                )
                safe_name = self._unique_sheet_title(str(candidate), used_titles)
                renames.append((ws, original_name, safe_name))

            for ws, original_name, safe_name in renames:
                if safe_name != original_name:
                    ws.title = safe_name
                    masked_count += 1
                    sheet_renames[original_name] = safe_name
                    diff_collector.add({
                        "sheet": original_name,
                        "row": 0,
                        "col": 0,
                        "col_name": "(工作表名称)",
                        "original": original_name,
                        "desensitized": safe_name,
                        "mask_type": "SHEET",
                    })

        # 保存脱敏后的新文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(output_path))
        wb.close()

        if progress_callback:
            progress_callback(100)

        return {
            "masked_count": masked_count,
            "diff_samples": diff_collector.samples,
            "header_rows": header_rows,
            "sheet_renames": sheet_renames,
        }

    @staticmethod
    def _read_headers(ws, header_row: int, max_col: int) -> List[str]:
        headers = []
        for col in range(1, max_col + 1):
            val = ws.cell(header_row, col).value
            headers.append(str(val).strip() if val is not None else f"Column_{col}")
        return headers

    def _transform_structure_name(
        self,
        raw: str,
        profile: str,
        pseudo_pool: PseudonymPool,
        entity_type: str,
    ) -> str:
        """按当前 Profile 转换列名或 Sheet 名。"""
        if profile == "ai_friendly":
            return pseudo_pool.get_or_create(raw, entity_type=entity_type)
        if profile == "standard_mask":
            return mask_text_middle(raw)
        if profile == "strict_anon":
            return f"ANON_{hash(raw) % 10000:04d}"
        return raw

    @staticmethod
    def _unique_sheet_title(candidate: str, used: Set[str]) -> str:
        """清洗非法字符、截断至 31 字符，并保证同簿唯一。"""
        cleaned = _SHEET_INVALID_CHARS.sub("_", candidate).strip()
        if not cleaned:
            cleaned = "Sheet"
        cleaned = cleaned[:31]

        if cleaned not in used:
            used.add(cleaned)
            return cleaned

        i = 1
        while True:
            suffix = f"_{i}"
            base_len = 31 - len(suffix)
            name = cleaned[:base_len] + suffix
            if name not in used:
                used.add(name)
                return name
            i += 1
