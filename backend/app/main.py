from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.app.core.config import WORKSPACE_DIR
from backend.app.core.queue import task_queue_manager
from backend.app.api.endpoints import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动后台任务消费 Worker
    task_queue_manager.start_worker()
    yield
    # 关闭后台 Worker
    await task_queue_manager.stop_worker()


app = FastAPI(
    title="自动文件脱敏工具站 API",
    description="面向大模型数据安全喂送的智能 Excel 脱敏中台",
    version="1.0.0",
    lifespan=lifespan,
)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router)

# 挂载前端静态页面 (如果前端目录存在)
frontend_dir = WORKSPACE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
