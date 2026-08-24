from typing import Dict, Optional


class PseudonymPool:
    """
    实体一致性假名化映射池 (Consistent Pseudonymization Pool)
    保证同一个实体在全表（甚至跨文件同一批次）中无论出现多少次，均映射为一致的代号。
    例如：'B082123C4P' -> 'ASIN_001', '店铺名-US' -> '店铺_01'
    """
    def __init__(self):
        # 结构: { entity_type: { raw_value: pseudo_value } }
        self._mappings: Dict[str, Dict[str, str]] = {}
        # 结构: { entity_type: counter }
        self._counters: Dict[str, int] = {}

    def get_or_create(self, raw_value: str, entity_type: str = "实体", prefix: Optional[str] = None) -> str:
        if not raw_value:
            return raw_value
            
        tag = prefix or entity_type
        if tag not in self._mappings:
            self._mappings[tag] = {}
            self._counters[tag] = 1
            
        if raw_value not in self._mappings[tag]:
            idx = self._counters[tag]
            self._counters[tag] += 1
            self._mappings[tag][raw_value] = f"{tag}_{idx:02d}"
            
        return self._mappings[tag][raw_value]

    def clear(self):
        self._mappings.clear()
        self._counters.clear()
