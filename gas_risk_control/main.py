# -*- coding: utf-8 -*-
"""
main.py — 燃气管网安全风控系统 服务入口
=======================================
启动方式：
    pip install -r requirements.txt
    python main.py
随后：
    后端接口文档:  http://localhost:8003/docs
    前端页面:      用浏览器打开 ../gas_risk_frontend/index.html
"""
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
import simulator
from routers import (monitoring, leak, diffusion, third_party,
                     user_safety, occupation, cathodic, emergency)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表、补录历史数据并开启毫秒级数据模拟线程；退出时停止。"""
    database.init_db()
    simulator.seed_history()
    simulator.start()
    yield
    simulator.stop()


app = FastAPI(
    title="燃气管网安全风控系统",
    description="实时监测 / 微泄漏定位 / 扩散仿真 / 第三方破坏预警 / 用户用气安全 / "
                "占压隐患管理 / 阴极保护监测 / 应急联动关阀",
    version="1.0.0",
    lifespan=lifespan,
)

# 允许前端页面跨域调用（前端为本地静态页面，开放全部来源便于演示）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 8 大功能模块路由
app.include_router(monitoring.router)   # 1. 实时安全监测
app.include_router(leak.router)         # 2. 微泄漏精准定位
app.include_router(diffusion.router)    # 3. 泄漏扩散仿真
app.include_router(third_party.router)  # 4. 第三方破坏预警
app.include_router(user_safety.router)  # 5. 用户端用气安全
app.include_router(occupation.router)   # 6. 占压隐患管理
app.include_router(cathodic.router)     # 7. 阴极保护监测
app.include_router(emergency.router)    # 8. 应急联动关阀


@app.get("/", tags=["系统"], summary="服务信息")
def root():
    return {
        "name": "燃气管网安全风控系统",
        "version": "1.0.0",
        "docs": "/docs",
        "frontend": "打开 ../gas_risk_frontend/index.html",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003)
