# -*- coding: utf-8 -*-
"""
市政井盖全生命周期管控子模块 —— API 主入口
============================================
FastAPI + SQLite，五大功能：
  1. 状态实时监测    /api/monitor      多维采集 + 自动风险告警
  2. 一井一档档案    /api/archive      电子台账 + 运维履历
  3. 隐患闭环处置    /api/orders       告警→派发→上报→核验→销号
  4. 被盗追踪管理    /api/theft        轨迹回放 + 定位追踪 + 公安联动
  5. 防坠网台账      /api/safety-net   安装登记 + 破损/维修/更换
启动时自动建表并注入确定性演示数据（90+ 条）。
"""
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database as db
import seed
from routers import archive, monitor, orders, safety_net, theft


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    seed.seed()
    yield


app = FastAPI(title="市政井盖全生命周期管控子系统",
              description="实时监测 / 一井一档 / 闭环处置 / 被盗追踪 / 防坠网台账",
              version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(monitor.router)
app.include_router(archive.router)
app.include_router(orders.router)
app.include_router(theft.router)
app.include_router(safety_net.router)


@app.get("/", summary="服务信息")
def index():
    return {"name": "市政井盖全生命周期管控子系统", "version": "1.0.0",
            "docs": "/docs", "summary": "/api/summary"}


@app.get("/api/summary", summary="大屏顶部统计")
def summary():
    conn = db.get_conn()
    try:
        def _count(sql, args=()):
            return conn.execute(sql, args).fetchone()["c"]
        total_orders = _count("SELECT COUNT(*) c FROM work_orders")
        closed_orders = _count("SELECT COUNT(*) c FROM work_orders WHERE status='已闭环'")
        return {
            "manhole_total": _count("SELECT COUNT(*) c FROM manholes"),
            "manhole_abnormal": _count(
                "SELECT COUNT(*) c FROM manholes WHERE status<>'正常'"),
            "active_alarms": _count(
                "SELECT COUNT(*) c FROM alarms WHERE status<>'已闭环'"),
            "orders_pending": _count(
                "SELECT COUNT(*) c FROM work_orders WHERE status IN ('待派发','处置中','待核验')"),
            "close_rate_pct": round(closed_orders / total_orders * 100, 1) if total_orders else 0,
            "theft_cases": _count("SELECT COUNT(*) c FROM alarms WHERE type='被盗异动'"),
            "police_records": _count("SELECT COUNT(*) c FROM police_records"),
            "net_total": _count("SELECT COUNT(*) c FROM safety_nets"),
            "net_broken": _count(
                "SELECT COUNT(*) c FROM safety_nets WHERE net_status='破损'"),
        }
    finally:
        conn.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0",
                port=int(os.environ.get("PORT", "8003")), reload=False)
