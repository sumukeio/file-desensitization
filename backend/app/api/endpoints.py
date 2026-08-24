import io
import zipfile
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from backend.app.core.config import PROCESSED_DIR, ALLOWED_EXTENSIONS
from backend.app.core.queue import task_queue_manager
from backend.app.schemas.task import TaskItem, TaskListResponse, DesensitizeProfile, TaskStatus

router = APIRouter(prefix="/api")


@router.post("/upload", response_model=List[TaskItem])
async def upload_files(
    files: List[UploadFile] = File(...),
    profile: str = Form("ai_friendly"),
):
    """接收批量文件上传并压入脱敏队列"""
    try:
        prof_enum = DesensitizeProfile(profile)
    except ValueError:
        prof_enum = DesensitizeProfile.AI_FRIENDLY

    created_tasks = []
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue

        file_bytes = await file.read()
        task_item = await task_queue_manager.add_task(
            file_name=file.filename,
            file_bytes=file_bytes,
            profile=prof_enum,
        )
        created_tasks.append(task_item)

    if not created_tasks:
        raise HTTPException(status_code=400, detail="未上传有效的 Excel/CSV 文件 (.xlsx, .xls, .csv)")

    return created_tasks


@router.get("/tasks", response_model=TaskListResponse)
async def get_tasks():
    """获取当前所有任务的状态与进度"""
    tasks = task_queue_manager.get_all_tasks()
    return TaskListResponse(total=len(tasks), tasks=tasks)


@router.get("/tasks/{task_id}/diff")
async def get_task_diff(task_id: str):
    """获取指定任务的脱敏前后 Diff 样本"""
    task = task_queue_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {
        "task_id": task_id,
        "file_name": task.file_name,
        "status": task.status,
        "masked_count": task.masked_count,
        "diff_samples": task.diff_samples,
    }


@router.get("/tasks/{task_id}/download")
async def download_single_file(task_id: str):
    """下载单个脱敏后的 Excel 文件"""
    task = task_queue_manager.get_task(task_id)
    if not task or task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="文件尚未处理完成或不存在")

    file_path = PROCESSED_DIR / f"{task_id}_{task.output_filename}"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="物理文件未找到")

    return FileResponse(
        path=file_path,
        filename=task.output_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/download-all")
async def download_all_zip():
    """一键打包下载全部已完成的脱敏文件"""
    tasks = [t for t in task_queue_manager.get_all_tasks() if t.status == TaskStatus.COMPLETED]
    if not tasks:
        raise HTTPException(status_code=400, detail="暂无已完成的脱敏文件可供打包")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for t in tasks:
            file_path = PROCESSED_DIR / f"{t.task_id}_{t.output_filename}"
            if file_path.exists():
                zf.write(file_path, arcname=t.output_filename)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=desensitized_excel_bundle.zip"},
    )


@router.post("/tasks/clear")
async def clear_tasks():
    """清空已完成列表并重置映射池"""
    task_queue_manager.clear_completed()
    return {"status": "ok", "message": "已完成任务已清理"}
