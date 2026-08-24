from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Callable, Optional


class IFileProcessor(ABC):
    """通用文件脱敏处理器抽象基类，支持 Excel/CSV 及未来 Word/PDF 扩展"""

    @abstractmethod
    def validate(self, input_path: Path) -> bool:
        """格式与有效性校验"""
        pass

    @abstractmethod
    def process(
        self,
        input_path: Path,
        output_path: Path,
        profile: str,
        progress_callback: Optional[Callable[[int], None]] = None,
        custom_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行脱敏处理
        :param input_path: 输入文件路径
        :param output_path: 输出文件路径
        :param profile: 预设脱敏模式 (ai_friendly / standard_mask / strict_anon)
        :param progress_callback: 进度回调 (0-100)
        :param custom_options: 自定义规则配置
        :return: 包含处理统计指标 (masked_count, diff_samples) 的字典
        """
        pass
