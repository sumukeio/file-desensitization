import os
import openpyxl
from pathlib import Path
from typing import Dict, Any, Callable, Optional, List
from datetime import date, datetime

from backend.app.engine.base import IFileProcessor
from backend.app.engine.rules.maskers import mask_text_middle, detect_and_mask_pii
from backend.app.engine.rules.pseudonym import PseudonymPool
from backend.app.engine.rules.profiles import (
    KNOWN_HEADERS_KEYWORDS,
    PSEUDO_COLUMN_MAPPING,
    CATEGORICAL_WHITELIST,
)


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

        # 加载工作簿 (保留原格式)
        wb = openpyxl.load_workbook(str(input_path))
        total_sheets = len(wb.sheetnames)
        
        masked_count = 0
        diff_samples: List[Dict[str, Any]] = []
        max_diff_samples = 30  # 最多收集 30 条样本供前端 Diff 预览

        for sheet_idx, sheet_name in enumerate(wb.sheetnames):
            ws = wb[sheet_name]
            max_row = ws.max_row
            max_col = ws.max_column

            if max_row < 1 or max_col < 1:
                continue

            # 读取第一行作为表头（保留语义，建立列索引映射）
            headers = []
            for col in range(1, max_col + 1):
                val = ws.cell(1, col).value
                headers.append(str(val).strip() if val is not None else f"Column_{col}")

            # 遍历数据行 (从第 2 行开始)
            for row in range(2, max_row + 1):
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
                        if len(diff_samples) < max_diff_samples:
                            diff_samples.append({
                                "sheet": sheet_name,
                                "row": row,
                                "col": col,
                                "col_name": col_name,
                                "original": str(raw_val),
                                "desensitized": str(new_val),
                                "mask_type": mask_type,
                            })

                # 更新进度回调
                if progress_callback and max_row > 1:
                    sheet_progress = int((row / max_row) * 100)
                    overall_progress = int(((sheet_idx + (row / max_row)) / total_sheets) * 100)
                    progress_callback(min(99, overall_progress))

        # 保存脱敏后的新文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(output_path))
        wb.close()

        if progress_callback:
            progress_callback(100)

        return {
            "masked_count": masked_count,
            "diff_samples": diff_samples,
        }
