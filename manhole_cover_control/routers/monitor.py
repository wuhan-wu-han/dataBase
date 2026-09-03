# -*- coding: utf-8 -*-
"""
功能 1：状态实时监测
=====================
采集井盖倾角、位移、破损、井下水位、有毒气体多维监测数据；
实时展示监测指标；异常数据按阈值规则自动产生风险告警记录，
并自动生成待派发运维工单（联动功能 3 闭环流程）。
"""
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

import database as db
from models import (DAMAGE_LEVELS, MonitorDataReq, check_monitor)

router = APIRouter(prefix="/api/monitor", tags=["1.状态实时监测"])


def _gen_alarm_code(conn) -> str:
    day = time.strftime("%Y%m%d")
    n = conn.execute("SELECT COUNT(*) c FROM alarms WHERE alarm_code LIKE ?",
                     (f"GJ-{day}-%",)).fetchone()["c"] + 1
    return f"GJ-{day}-{n:02d}"


def _gen_order_code(conn) -> str:
    day = time.strftime("%Y%m%d")
    n = conn.execute("SELECT COUNT(*) c FROM work_orders WHERE order_code LIKE ?",
                     (f"GD-{day}-%",)).fetchone()["c"] + 1
    return f"GD-{day}-{n:02d}"


def raise_alarms(conn, manhole_id: int, values: dict, ts: int) -> list:
    """异常判定 → 写告警 + 自动建待派发工单 + 井盖状态联动。"""
    hits = check_monitor(values.get("tilt_deg"), values.get("displacement_mm"),
                         values.get("damage"), values.get("water_level_cm"),
                         values.get("gas_ppm"))
    created = []
    for h in hits:
        # 同类告警未闭环时不重复产生
        dup = conn.execute(
            "SELECT 1 FROM alarms WHERE manhole_id=? AND type=? AND status<>'已闭环'",
            (manhole_id, h["type"])).fetchone()
        if dup:
            continue
        cur = conn.execute(
            "INSERT INTO alarms(alarm_code,manhole_id,type,level,detail,alarm_ts,status,created_ts)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (_gen_alarm_code(conn), manhole_id, h["type"], h["level"], h["detail"],
             ts, "待派发", ts))
        alarm_id = cur.lastrowid
        handle = {"被盗异动": "公安报案", "有毒气体告警": "现场核查",
                  "井盖破损": "更换"}.get(h["type"], "维修")
        conn.execute(
            "INSERT INTO work_orders(order_code,alarm_id,manhole_id,handle_type,status,created_ts)"
            " VALUES(?,?,?,?,?,?)",
            (_gen_order_code(conn), alarm_id, manhole_id, handle, "待派发", ts))
        new_status = "被盗" if h["type"] == "被盗异动" else "告警"
        conn.execute(
            "UPDATE manholes SET status=? WHERE id=? AND status IN ('正常','告警')",
            (new_status, manhole_id))
        created.append({"alarm_id": alarm_id, "type": h["type"], "level": h["level"],
                        "detail": h["detail"]})
    return created


@router.post("/data", summary="采集监测数据（异常自动告警）")
def collect(req: MonitorDataReq):
    if req.damage is not None and req.damage not in DAMAGE_LEVELS:
        raise HTTPException(400, f"破损情况应为：{'/'.join(DAMAGE_LEVELS)}")
    ts = req.ts or int(time.time() * 1000)
    conn = db.get_conn()
    try:
        manhole = conn.execute("SELECT * FROM manholes WHERE id=?", (req.manhole_id,)).fetchone()
        if not manhole:
            raise HTTPException(404, f"井盖 {req.manhole_id} 不存在")
        values = {"tilt_deg": req.tilt_deg, "displacement_mm": req.displacement_mm,
                  "damage": req.damage, "water_level_cm": req.water_level_cm,
                  "gas_ppm": req.gas_ppm}
        abnormal = 1 if check_monitor(**values) else 0
        cur = conn.execute(
            "INSERT INTO monitor_data(manhole_id,ts,tilt_deg,displacement_mm,damage,"
            "water_level_cm,gas_ppm,is_abnormal,created_ts) VALUES(?,?,?,?,?,?,?,?,?)",
            (req.manhole_id, ts, req.tilt_deg, req.displacement_mm,
             req.damage or "完好", req.water_level_cm, req.gas_ppm, abnormal, ts))
        alarms = raise_alarms(conn, req.manhole_id, values, ts)
        conn.commit()
        return {"ok": True, "id": cur.lastrowid, "is_abnormal": bool(abnormal),
                "alarms_created": alarms}
    finally:
        conn.close()


@router.get("/latest", summary="全部井盖实时监测指标")
def latest(keyword: Optional[str] = Query(None, description="编号/道路/位置"),
           only_abnormal: bool = Query(False, description="仅看异常井盖")):
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT m.id, m.code, m.location, m.road_name, m.district, m.type, m.status,"
            " d.ts, d.tilt_deg, d.displacement_mm, d.damage, d.water_level_cm, d.gas_ppm,"
            " d.is_abnormal FROM manholes m"
            " LEFT JOIN monitor_data d ON d.id = (SELECT id FROM monitor_data"
            "   WHERE manhole_id=m.id ORDER BY ts DESC LIMIT 1)"
            " ORDER BY d.is_abnormal DESC, m.id"))
    finally:
        conn.close()
    if keyword:
        rows = [r for r in rows if keyword in (r["code"] or "") + (r["road_name"] or "")
                + (r["location"] or "")]
    if only_abnormal:
        rows = [r for r in rows if r["is_abnormal"] or r["status"] != "正常"]
    return {"total": len(rows), "items": rows}


@router.get("/history", summary="单井盖监测历史曲线")
def history(manhole_id: int = Query(...), limit: int = Query(100, ge=1, le=500)):
    conn = db.get_conn()
    try:
        manhole = conn.execute("SELECT * FROM manholes WHERE id=?", (manhole_id,)).fetchone()
        if not manhole:
            raise HTTPException(404, f"井盖 {manhole_id} 不存在")
        rows = db.rows_to_list(conn.execute(
            "SELECT * FROM monitor_data WHERE manhole_id=? ORDER BY ts DESC LIMIT ?",
            (manhole_id, limit)))
        return {"manhole": dict(manhole), "records": rows[::-1]}
    finally:
        conn.close()


@router.get("/alarms", summary="风险告警记录列表")
def alarms(status: Optional[str] = None, level: Optional[str] = None,
           type: Optional[str] = None, manhole_id: Optional[int] = None,
           page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    where, args = [], []
    if status:
        where.append("a.status=?"); args.append(status)
    if level:
        where.append("a.level=?"); args.append(level)
    if type:
        where.append("a.type=?"); args.append(type)
    if manhole_id:
        where.append("a.manhole_id=?"); args.append(manhole_id)
    sql = ("SELECT a.*, m.code, m.location, m.road_name, m.district FROM alarms a"
           " JOIN manholes m ON m.id=a.manhole_id" +
           (" WHERE " + " AND ".join(where) if where else "") +
           " ORDER BY a.alarm_ts DESC")
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(sql, args))
        total = len(rows)
        return {"total": total, "page": page, "page_size": page_size,
                "items": rows[(page - 1) * page_size: page * page_size]}
    finally:
        conn.close()


@router.get("/alarm-trend", summary="告警趋势（近 7 日 × 等级）")
def alarm_trend():
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT date(alarm_ts/1000,'unixepoch','localtime') day, level,"
            " COUNT(*) n FROM alarms GROUP BY day, level ORDER BY day"))
    finally:
        conn.close()
    days = sorted({r["day"] for r in rows})[-7:]
    series = {lv: [0] * len(days) for lv in ("高", "中", "低")}
    for r in rows:
        if r["day"] in days and r["level"] in series:
            series[r["level"]][days.index(r["day"])] = r["n"]
    return {"days": days,
            "series": [{"name": k, "data": v} for k, v in series.items()]}


@router.get("/stats", summary="监测与告警统计")
def stats():
    conn = db.get_conn()
    try:
        by_type = db.rows_to_list(conn.execute(
            "SELECT type name, COUNT(*) value FROM alarms GROUP BY type ORDER BY value DESC"))
        by_level = db.rows_to_list(conn.execute(
            "SELECT level name, COUNT(*) value FROM alarms GROUP BY level"))
        by_status = db.rows_to_list(conn.execute(
            "SELECT status name, COUNT(*) value FROM alarms GROUP BY status"))
        today_ms = int(time.mktime(time.strptime(time.strftime("%Y-%m-%d"),
                                                  "%Y-%m-%d")) * 1000)
        return {"by_type": by_type, "by_level": by_level, "by_status": by_status,
                "monitor_today": conn.execute(
                    "SELECT COUNT(*) c FROM monitor_data WHERE ts>=?", (today_ms,)).fetchone()["c"]}
    finally:
        conn.close()
