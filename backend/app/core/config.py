import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_DIR = BASE_DIR.parent
UPLOAD_DIR = BASE_DIR / "temp" / "uploads"
PROCESSED_DIR = BASE_DIR / "temp" / "processed"

# 确保临时沙箱目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# 限制单文件最大 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024

# 支持的文件后缀
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}

# 文件保留最长时间（秒），默认 1800 秒（30分钟自动销毁）
FILE_EXPIRY_SECONDS = 1800
