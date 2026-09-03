# -*- coding: utf-8 -*-
"""功能2 DMA 分区漏损管理 — 分区计量/夜间最小流量/漏损率核算/暗漏定位"""
import time

from fastapi import APIRouter, HTTPException

from database import get_conn
from models import DmaRecordForm

router = APIRouter(prefix="/api/dma", tags=["DMA分区漏损管理"])


@router.get("/zones")
def zones(keyword: str = "", status: str = ""):
    conn = get_conn()
    sql = "SELECT * FROM dma_zone"
    where, args = [], []
    if keyword:
        where.append("(code LIKE ? OR name LIKE ? OR district LIKE ?)")
        args += ["%%%s%%" % keyword] * 3
    if status:
        where.append("status=?"); args.append(status)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id"
    rows = [dict(r) for r in conn.execute(sql, args).fetchall()]
    conn.close()
    return {"total": len(rows), "items": rows}


@router.get("/records")
def records(dma_id: int, days: int = 7):
    conn = get_conn()
    zone = conn.execute("SELECT * FROM dma_zone WHERE id=?", (dma_id,)).fetchone()
    recs = [dict(r) for r in conn.execute(
        "SELECT * FROM dma_record WHERE dma_id=? ORDER BY date DESC LIMIT ?",
        (dma_id, days)).fetchall()]
    conn.close()
    return {"zone": dict(zone) if zone else None, "records": recs}


@router.post("/records")
def add_record(form: DmaRecordForm):
    """录入分区计量数据，自动核算漏损率并做夜间最小流量研判"""
    if form.billed_m3 > form.inflow_m3:
        raise HTTPException(400, "售水量不能大于供水量")
    ts = int(time.time() * 1000)
    rate = round((form.inflow_m3 - form.billed_m3) / form.inflow_m3 * 100, 2)
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO dma_record(dma_id, date, inflow_m3, billed_m3, night_min_flow_m3h,"
        " leakage_rate_pct) VALUES (?,?,?,?,?,?)",
        (form.dma_id, form.date, form.inflow_m3, form.billed_m3,
         form.night_min_flow_m3h, rate))
    rid = cur.lastrowid
    alerts = []
    if rate > 12:
        alerts.append(("漏损率 %s%% 超管控线 12%%，疑似暗漏" % rate, "高"))
    if form.night_min_flow_m3h is not None and form.night_min_flow_m3h > 8:
        alerts.append(("夜间最小流量 %s m3/h 偏高，存在持续暗漏" % form.night_min_flow_m3h, "中"))
    for i, (detail, level) in enumerate(alerts):
        conn.execute(
            "INSERT INTO alarm(alarm_code, pipe_id, source, type, level, detail, alarm_ts,"
            " status) VALUES (?,?,?,?,?,?,?,?)",
            ("DMA%d%d" % (ts % 10 ** 9, i), None, "DMA分区", "漏损告警", level, detail,
             ts, "待处理"))
    conn.execute(
        "UPDATE dma_zone SET leakage_rate_pct=?, night_min_flow_m3h=?, status=?"
        " WHERE id=?",
        (rate, form.night_min_flow_m3h, "漏损偏高" if rate > 12 else "正常", form.dma_id))
    conn.commit()
    conn.close()
    return {"ok": True, "id": rid, "leakage_rate_pct": rate, "alerts": alerts}


@router.get("/stats")
def stats():
    conn = get_conn()
    zones = conn.execute("SELECT * FROM dma_zone").fetchall()
    by_rate = [dict(r) for r in conn.execute(
        "SELECT name, leakage_rate_pct AS value FROM dma_zone ORDER BY leakage_rate_pct DESC")]
    night = [dict(r) for r in conn.execute(
        "SELECT name, night_min_flow_m3h AS value FROM dma_zone ORDER BY night_min_flow_m3h DESC")]
    total_users = sum(z["user_count"] or 0 for z in zones)
    avg_rate = round(sum(z["leakage_rate_pct"] or 0 for z in zones) / max(len(zones), 1), 2)
    dark = [dict(r) for r in conn.execute(
        "SELECT code, name, dark_leak_location FROM dma_zone WHERE dark_leak_location IS NOT NULL"
        " AND dark_leak_location != ''")]
    conn.close()
    return {"by_rate": by_rate, "night": night, "total_users": total_users,
            "avg_rate": avg_rate, "dark_leaks": dark}


@router.post("/zones/{zone_id}/locate")
def locate(zone_id: int, location: str):
    """暗漏点位精准定位登记"""
    conn = get_conn()
    conn.execute("UPDATE dma_zone SET dark_leak_location=?, status='暗漏定位' WHERE id=?",
                 (location, zone_id))
    conn.execute(
        "INSERT INTO alarm(alarm_code, pipe_id, source, type, level, detail, alarm_ts, status)"
        " VALUES (?,?,?,?,?,?,?,?)",
        ("DMA%dLOC%d" % (zone_id, int(time.time() * 1000) % 10 ** 6),
         None, "DMA分区", "暗漏定位", "高",
         "暗漏点位定位：%s" % location, time.time() * 1000, "待处理"))
    conn.commit()
    conn.close()
    return {"ok": True}
