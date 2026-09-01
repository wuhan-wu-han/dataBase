# -*- coding: utf-8 -*-
"""
main.py — 资产数字化台账子模块 服务入口
=======================================
天信城市生命线管网 AI 智慧平台 · 燃气资产数字化台账
启动方式：
    pip install -r requirements.txt
    python main.py          # 默认端口 8002（可用环境变量 PORT 覆盖）
接口文档：http://localhost:8002/docs
"""
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
import seed
from routers import assets, lifecycle, inventory, ownership


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时建表并注入模拟数据（幂等）。"""
    database.init_db()
    seed.seed()
    yield


app = FastAPI(
    title="资产数字化台账子模块",
    description="天信城市生命线管网 AI 智慧平台：资产全景台账 / 全生命周期档案 / 资产盘点 / 资产权属管理",
    version="1.0.0",
    lifespan=lifespan,
)

# 前端大屏跨域调用（本地演示开放全部来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assets.router)       # 1. 资产全景台账
app.include_router(lifecycle.router)    # 2. 全生命周期档案
app.include_router(inventory.router)    # 3. 资产盘点
app.include_router(ownership.router)    # 4. 资产权属管理


@app.get("/", tags=["系统"], summary="服务信息")
def root():
    return {
        "name": "资产数字化台账子模块",
        "platform": "天信城市生命线管网 AI 智慧平台",
        "docs": "/docs",
        "frontend": "打开 ../gas_asset_frontend 构建产物（dist/）",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8001")))
