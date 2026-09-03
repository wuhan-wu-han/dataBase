# -*- coding: utf-8 -*-
"""供水管网精细化管控子模块 — FastAPI 应用入口（端口 8004）"""
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, get_conn
from routers import monitor, dma, quality, pressure, secondary, hydrant, burst

app = FastAPI(title="供水管网精细化管控子模块", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(monitor.router)
app.include_router(dma.router)
app.include_router(quality.router)
app.include_router(pressure.router)
app.include_router(secondary.router)
app.include_router(hydrant.router)
app.include_router(burst.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/summary")
def summary():
    conn = get_conn()

    def q(sql, args=()):
        return conn.execute(sql, args).fetchone()[0]

    today0 = time.mktime(time.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d")) * 1000
    data = {
        "pipe_total": q("SELECT COUNT(*) FROM pipe"),
        "pipe_abnormal": q("SELECT COUNT(*) FROM pipe WHERE status!='正常'"),
        "active_alarms": q("SELECT COUNT(*) FROM alarm WHERE status='待处理'"),
        "monitor_today": q("SELECT COUNT(*) FROM monitor_record WHERE ts>=?", (today0,)),
        "avg_leakage_pct": q("SELECT ROUND(AVG(leakage_rate_pct),1) FROM dma_zone") or 0,
        "dma_abnormal": q("SELECT COUNT(*) FROM dma_zone WHERE status!='正常'"),
        "quality_abnormal": q("SELECT COUNT(*) FROM quality_node WHERE status='异常'"),
        "secondary_abnormal": q("SELECT COUNT(*) FROM secondary_unit WHERE status!='正常'"),
        "hydrant_total": q("SELECT COUNT(*) FROM hydrant"),
        "hydrant_abnormal": q("SELECT COUNT(*) FROM hydrant WHERE status!='正常'"),
        "burst_high": q("SELECT COUNT(*) FROM burst_case WHERE risk_level='高'"),
        "burst_pending": q("SELECT COUNT(*) FROM burst_case WHERE status IN ('风险预警','处置中','已关阀')"),
    }
    conn.close()
    return data


@app.get("/")
def root():
    return {"module": "water_supply_control", "status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=False)
