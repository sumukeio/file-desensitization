import asyncio
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from backend.app.core.config import UPLOAD_DIR, PROCESSED_DIR
from backend.app.schemas.task import TaskItem, TaskStatus, DesensitizeProfile
from backend.app.engine.excel_processor import ExcelProcessor
from backend.app.engine.rules.pseudonym import PseudonymPool


class TaskQueueManager:
    """异步排队任务管理器，支持多文件按顺序/并发队列处理与批次假名共享"""

    def __init__(self):
        self.tasks: Dict[str, TaskItem] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self.processor = ExcelProcessor()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.batch_pseudo_pool = PseudonymPool()  # 批次共享假名池，支持跨文件 JOIN 关联
        self._worker_task: Optional[asyncio.Task] = None
        self._is_running = False

    def start_worker(self):
        if not self._is_running:
            self._is_running = True
            self._worker_task = asyncio.create_task(self._queue_worker())

    async def stop_worker(self):
        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()

    async def add_task(
        self,
        file_name: str,
        file_bytes: bytes,
        profile: DesensitizeProfile = DesensitizeProfile.AI_FRIENDLY,
        mask_headers: bool = False,
        mask_sheet_names: bool = False,
        header_row_mode: str = "auto",
        header_row: Optional[int] = None,
        header_row_overrides: Optional[Dict[str, int]] = None,
    ) -> TaskItem:
        task_id = str(uuid.uuid4())
        input_filename = f"{task_id}_{file_name}"
        input_path = UPLOAD_DIR / input_filename
        
        # 写入上传临时文件
        with open(input_path, "wb") as f:
            f.write(file_bytes)

        task_item = TaskItem(
            task_id=task_id,
            file_name=file_name,
            file_size=len(file_bytes),
            profile=profile,
            mask_headers=mask_headers,
            mask_sheet_names=mask_sheet_names,
            header_row_mode=header_row_mode,
            header_row=header_row,
            header_row_overrides=header_row_overrides or {},
            status=TaskStatus.PENDING,
            progress=0,
            masked_count=0,
            created_at=time.time(),
        )

        self.tasks[task_id] = task_item
        await self.queue.put(task_id)
        return task_item

    async def reprocess_with_header_override(
        self,
        task_id: str,
        sheet_name: Optional[str] = None,
        header_row: Optional[int] = None,
        clear_override: bool = False,
    ) -> TaskItem:
        """对已完成/失败任务按 Sheet 纠错表头行后重新入队（原上传文件复用）。"""
        task_item = self.tasks.get(task_id)
        if not task_item:
            raise ValueError("任务不存在")
        if task_item.status not in {TaskStatus.COMPLETED, TaskStatus.FAILED}:
            raise ValueError("仅已完成或失败的任务可纠错重跑")

        input_path = UPLOAD_DIR / f"{task_id}_{task_item.file_name}"
        if not input_path.exists():
            raise ValueError("原始上传文件已不存在，请重新上传")

        overrides = dict(task_item.header_row_overrides or {})
        if clear_override:
            if not sheet_name:
                raise ValueError("恢复自动识别时必须指定工作表名称")
            overrides.pop(sheet_name, None)
        else:
            if not sheet_name or header_row is None:
                raise ValueError("纠错重跑需要工作表名称与表头行号")
            overrides[sheet_name] = max(1, int(header_row))

        task_item.header_row_overrides = overrides
        task_item.status = TaskStatus.PENDING
        task_item.progress = 0
        task_item.masked_count = 0
        task_item.error_message = None
        task_item.completed_at = None
        task_item.diff_samples = []
        task_item.header_rows = {}
        task_item.sheet_renames = {}
        task_item.output_filename = None

        await self.queue.put(task_id)
        return task_item

    def get_task(self, task_id: str) -> Optional[TaskItem]:
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[TaskItem]:
        # 按创建时间顺序排列
        return sorted(self.tasks.values(), key=lambda t: t.created_at)

    def clear_completed(self):
        # 清空已完成任务并重置假名池
        completed_ids = [tid for tid, t in self.tasks.items() if t.status in {TaskStatus.COMPLETED, TaskStatus.FAILED}]
        for tid in completed_ids:
            del self.tasks[tid]
        if not self.tasks:
            self.batch_pseudo_pool.clear()

    async def _queue_worker(self):
        """后台队列消费循环，按顺序提取任务执行脱敏"""
        while self._is_running:
            try:
                task_id = await self.queue.get()
                task_item = self.tasks.get(task_id)
                if not task_item:
                    self.queue.task_done()
                    continue

                task_item.status = TaskStatus.PROCESSING
                task_item.progress = 5

                input_path = UPLOAD_DIR / f"{task_id}_{task_item.file_name}"
                out_name = f"desensitized_{task_item.file_name}"
                output_path = PROCESSED_DIR / f"{task_id}_{out_name}"

                def update_progress(p: int):
                    task_item.progress = p

                loop = asyncio.get_running_loop()
                custom_options = {
                    "mask_headers": task_item.mask_headers,
                    "mask_sheet_names": task_item.mask_sheet_names,
                    "header_row_mode": task_item.header_row_mode,
                    "header_row": task_item.header_row,
                    "header_row_overrides": task_item.header_row_overrides or {},
                }
                try:
                    # 在线程池中执行计算密集型 Excel 脱敏，避免阻塞事件循环
                    result = await loop.run_in_executor(
                        self.executor,
                        lambda: self.processor.process(
                            input_path,
                            output_path,
                            task_item.profile.value,
                            update_progress,
                            custom_options,
                            self.batch_pseudo_pool,
                        ),
                    )

                    task_item.status = TaskStatus.COMPLETED
                    task_item.progress = 100
                    task_item.masked_count = result["masked_count"]
                    task_item.diff_samples = result["diff_samples"]
                    task_item.header_rows = result.get("header_rows") or {}
                    task_item.sheet_renames = result.get("sheet_renames") or {}
                    task_item.completed_at = time.time()
                    task_item.output_filename = out_name

                except Exception as e:
                    task_item.status = TaskStatus.FAILED
                    task_item.error_message = str(e)
                finally:
                    self.queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(1)


# 全局单例
task_queue_manager = TaskQueueManager()
