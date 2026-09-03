"""Platform Service —— FastAPI + SQLite + SQLAlchemy + Pydantic

监听 8000 端口，承接 Spring Cloud Gateway 的 /api/platform/** 转发（StripPrefix=2）。
本阶段实现：工单管理（/workorder）、应急预案（/plan）。
"""
import os
import sys

# 允许从任意工作目录启动：把本目录加入模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import Base, engine
import models_workorder  # noqa: F401  —— 建表需要
import models_emergency  # noqa: F401
from routers import workorder, emergency_plan
from seed_data import seed_all

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="安塞城市生命线 · Platform Service",
    description="工单管理 / 应急预案 数据持久化服务（SQLite）",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 网关 StripPrefix=2 → 直接命中 /workorder、/plan
app.include_router(workorder.router)
app.include_router(emergency_plan.router)
# 同时支持绕过网关直连 8000 访问完整路径，便于联调与冒烟测试
app.include_router(workorder.router, prefix="/api/platform")
app.include_router(emergency_plan.router, prefix="/api/platform")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500,
                        content={"success": False, "code": 500,
                                 "detail": f"服务内部错误：{exc}"})


@app.get("/", summary="服务信息")
def index():
    return {"service": "platform-service", "version": "1.0.0",
            "modules": ["/workorder", "/plan"], "docs": "/docs"}


@app.get("/health", summary="健康检查")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    seed_all()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
