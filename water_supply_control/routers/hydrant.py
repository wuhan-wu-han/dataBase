# -*- coding: utf-8 -*-
"""功能6 消防栓专项管理 — 水压/出水监测、盗用异常告警、设备台账增改查"""
import time

from fastapi import APIRouter, HTTPException

from database import get_conn
from models import HydrantForm, HydrantTestForm

router = APIRouter(prefix="/api/hydrant", tags=["消防栓专项管理"])


@router.get("/list")
def list_hydrants(keyword: str = "", status: str = "", district: str = "",
                  page: int = 1, page_size: int = 10):
    conn = get_conn()
    sql = """SELECT h.*, p.code AS pipe_code FROM hydrant h
             LEFT JOIN pipe p ON p.id=h.pipe_id"""
    where, args = [], []
    if keyword:
        where.append("(h.code LIKE ? OR h.location LIKE ? OR h.road_name LIKE ?)")
        args += ["%%%s%%" % keyword] * 3
    if status:
        where.append("h.status=?"); args.append(status)
    if district:
        where.append("h.district=?"); args.append(district)
    if where:
        sql += " WHERE " + " AND ".join(where)
    total = conn.execute("SELECT COUNT(*) FROM (%s)" % sql, args).fetchone()[0]
    sql += " ORDER BY h.id LIMIT ? OFFSET ?"
    args += [page_size, (page - 1) * page_size]
    rows = [dict(r) for r in conn.execute(sql, args).fetchall()]
    conn.close()
    return {"total": total, "items": rows}


@router.get("/options")
def options():
    conn = get_conn()
    districts = [r[0] for r in conn.execute(
        "SELECT DISTINCT district FROM hydrant WHERE district IS NOT NULL ORDER BY district")]
    pipes = [dict(r) for r in conn.execute("SELECT id, code, name FROM pipe ORDER BY id")]
    conn.close()
    return {"districts": districts, "pipes": pipes}


@router.post("")
def create(form: HydrantForm):
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM hydrant").fetchone()[0]
    code = "XH%04d" % (n + 1)
    cur = conn.execute(
        "INSERT INTO hydrant(code, location, road_name, district, pipe_id, pressure_mpa,"
        " install_date, remark) VALUES (?,?,?,?,?,?,?,?)",
        (code, form.location, form.road_name, form.district, form.pipe_id,
         form.pressure_mpa, form.install_date, form.remark))
    conn.commit()
    conn.close()
    return {"ok": True, "id": cur.lastrowid, "code": code}


@router.put("/{hydrant_id}")
def update(hydrant_id: int, form: HydrantForm):
    conn = get_conn()
    conn.execute(
        "UPDATE hydrant SET location=?, road_name=?, district=?, pipe_id=?,"
        " pressure_mpa=?, install_date=?, remark=? WHERE id=?",
        (form.location, form.road_name, form.district, form.pipe_id,
         form.pressure_mpa, form.install_date, form.remark, hydrant_id))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/{hydrant_id}/test")
def test(hydrant_id: int, form: HydrantTestForm):
    """出水测试：水压/出水监测，盗用与压力异常自动告警"""
    ts = int(time.time() * 1000)
    conn = get_conn()
    h = conn.execute("SELECT * FROM hydrant WHERE id=?", (hydrant_id,)).fetchone()
    if not h:
        conn.close()
        raise HTTPException(404, "消防栓不存在")
    alerts = []
    if form.pressure_mpa is not None and form.pressure_mpa < 0.1:
        alerts.append(("消防栓水压 %sMPa 不足，影响消防取水" % form.pressure_mpa, "高"))
    if form.test_flow_ls is not None and form.test_flow_ls > 30:
        alerts.append(("出水流量 %sL/s 异常偏大，疑似盗用消防用水" % form.test_flow_ls, "中"))
    conn.execute(
        "UPDATE hydrant SET pressure_mpa=COALESCE(?,pressure_mpa),"
        " test_flow_ls=COALESCE(?,test_flow_ls), last_test_ts=?, status=? WHERE id=?",
        (form.pressure_mpa, form.test_flow_ls, ts,
         "告警" if alerts else "正常", hydrant_id))
    conn.execute(
        "INSERT INTO hydrant_event(hydrant_id, type, ts, detail, status)"
        " VALUES (?,?,?,?,?)",
        (hydrant_id, "出水测试", ts, form.note or "例行出水测试", "已处理"))
    for i, (detail, level) in enumerate(alerts):
        conn.execute(
            "INSERT INTO alarm(alarm_code, pipe_id, source, type, level, detail, alarm_ts,"
            " status) VALUES (?,?,?,?,?,?,?,?)",
            ("XH%d%d" % (ts % 10 ** 9, i), h["pipe_id"], "消防栓", "消防栓告警", level,
             detail, ts, "待处理"))
    conn.commit()
    conn.close()
    return {"ok": True, "is_abnormal": bool(alerts),
            "alarms": [{"level": a[1], "detail": a[0]} for a in alerts]}


@router.get("/{hydrant_id}/events")
def events(hydrant_id: int):
    conn = get_conn()
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM hydrant_event WHERE hydrant_id=? ORDER BY ts DESC LIMIT 50",
        (hydrant_id,)).fetchall()]
    conn.close()
    return {"total": len(rows), "items": rows}


@router.get("/stats/summary")
def summary():
    conn = get_conn()
    by_status = [dict(r) for r in conn.execute(
        "SELECT status AS name, COUNT(*) AS value FROM hydrant GROUP BY status")]
    by_district = [dict(r) for r in conn.execute(
        "SELECT district AS name, COUNT(*) AS value FROM hydrant WHERE district IS NOT NULL"
        " GROUP BY district ORDER BY value DESC")]
    conn.close()
    return {"by_status": by_status, "by_district": by_district}
