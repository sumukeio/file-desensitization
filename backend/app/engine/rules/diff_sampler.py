"""效果对比样本收集器：每 Sheet 结构/数据各自限额，避免先处理的 Sheet 挤爆后续页。"""
from typing import Any, Dict, List


STRUCTURE_SAMPLES_PER_SHEET = 5
DATA_SAMPLES_PER_SHEET = 5
# 软全局上限：正常应靠每 Sheet 限额约束；此值仅防极端膨胀
MAX_DIFF_SAMPLES_TOTAL = 2000
STRUCTURE_MASK_TYPES = {"HEADER", "SHEET"}


class DiffSampleCollector:
    """按 Sheet 分别限制结构样本与数据样本数量。"""

    def __init__(
        self,
        structure_per_sheet: int = STRUCTURE_SAMPLES_PER_SHEET,
        data_per_sheet: int = DATA_SAMPLES_PER_SHEET,
        max_total: int = MAX_DIFF_SAMPLES_TOTAL,
    ):
        self.structure_per_sheet = structure_per_sheet
        self.data_per_sheet = data_per_sheet
        self.max_total = max_total
        self._samples: List[Dict[str, Any]] = []
        self._sheet_structure_counts: Dict[str, int] = {}
        self._sheet_data_counts: Dict[str, int] = {}

    def add(self, sample: Dict[str, Any]) -> bool:
        if len(self._samples) >= self.max_total:
            return False

        mask_type = sample.get("mask_type", "")
        sheet = str(sample.get("sheet") or "")

        if mask_type in STRUCTURE_MASK_TYPES:
            count = self._sheet_structure_counts.get(sheet, 0)
            if count >= self.structure_per_sheet:
                return False
            self._sheet_structure_counts[sheet] = count + 1
            self._samples.append(sample)
            return True

        count = self._sheet_data_counts.get(sheet, 0)
        if count >= self.data_per_sheet:
            return False

        self._sheet_data_counts[sheet] = count + 1
        self._samples.append(sample)
        return True

    @property
    def samples(self) -> List[Dict[str, Any]]:
        return self._samples
