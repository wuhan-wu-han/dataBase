# -*- coding: utf-8 -*-
"""
道路地下隐患防控子模块 —— API 主入口
======================================
FastAPI + SQLite，三大功能：
  1. 地下空洞风险评估  /api/cavity
  2. 道路沉降监测      /api/subsidence
  3. 施工影响评估      /api/construction
启动时自动建表并注入确定性演示数据（≥30 条）。
"""
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database as db
import seed
from routers import cavity, construction, subsidence
from routers.subsidence import compute_point_summaries


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    seed.seed()
    yield


app = FastAPI(title="道路地下隐患防控子系统",
              description="地下空洞风险评估 / 道路沉降监测 / 施工影响评估",
              version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(cavity.router)
app.include_router(subsidence.router)
app.include_router(construction.router)


@app.get("/", summary="服务信息")
def index():
    return {"name": "道路地下隐患防控子系统", "version": "1.0.0",
            "docs": "/docs", "summary": "/api/summary"}


@app.get("/api/summary", summary="大屏顶部统计")
def summary():
    conn = db.get_conn()
    try:
        def _count(sql):
            return conn.execute(sql).fetchone()["c"]
        points = compute_point_summaries(conn)
        sub_high = sum(1 for p in points if p["risk_level"] == "高风险")
        cavity_status = db.rows_to_list(conn.execute(
            "SELECT status name, COUNT(*) value FROM cavities GROUP BY status"))
        return {
            "cavity_total": _count("SELECT COUNT(*) c FROM cavities"),
            "cavity_high": _count("SELECT COUNT(*) c FROM cavities WHERE risk_level='高风险'"),
            "cavity_unhandled": _count("SELECT COUNT(*) c FROM cavities WHERE status<>'已处置'"),
            "cavity_by_status": cavity_status,
            "subsidence_points": len(points),
            "subsidence_high": sub_high,
            "subsidence_records": _count("SELECT COUNT(*) c FROM subsidence_records"),
            "construction_total": _count("SELECT COUNT(*) c FROM construction_assess"),
            "construction_high": _count(
                "SELECT COUNT(*) c FROM construction_assess WHERE risk_level='高风险'"),
        }
    finally:
        conn.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0",
                port=int(os.environ.get("PORT", "8002")), reload=False)
