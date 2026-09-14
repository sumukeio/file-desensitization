from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DesensitizeProfile(str, Enum):
    AI_FRIENDLY = "ai_friendly"     # 推荐：AI 分析友好模式（保护表头/枚举，假名化实体，保留数值）
    STANDARD_MASK = "standard_mask" # 标准掩码模式（文本中间打星，手机身份证掩码）
    STRICT_ANON = "strict_anon"     # 深度完全匿名化模式


class TaskStatus(str, Enum):
    PENDING = "pending"         # 排队中
    PARSING = "parsing"         # 解析中
    PROCESSING = "processing"   # 脱敏中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败


class CellDiff(BaseModel):
    row: int
    col: int
    col_name: str
    original: Any
    desensitized: Any
    mask_type: str


class TaskItem(BaseModel):
    task_id: str
    file_name: str
    file_size: int
    profile: DesensitizeProfile = DesensitizeProfile.AI_FRIENDLY
    mask_headers: bool = False
    mask_sheet_names: bool = False
    header_row_mode: str = "auto"
    header_row: Optional[int] = None
    header_row_overrides: Dict[str, int] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    masked_count: int = 0
    error_message: Optional[str] = None
    created_at: float
    completed_at: Optional[float] = None
    output_filename: Optional[str] = None
    diff_samples: List[Dict[str, Any]] = Field(default_factory=list)
    header_rows: Dict[str, int] = Field(default_factory=dict)
    sheet_renames: Dict[str, str] = Field(default_factory=dict)


class TaskListResponse(BaseModel):
    total: int
    tasks: List[TaskItem]
