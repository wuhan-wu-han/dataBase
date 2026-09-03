# -*- coding: utf-8 -*-
"""功能1 实时运行监测 — 压力/流量/液位/水质/形变/漏损全时段在线监测"""
import time

from fastapi import APIRouter

from database import get_conn
from models import MonitorForm

router = APIRouter(prefix="/api/monitor", tags=["实时运行监测"])


def _judge(f: MonitorForm):
    """阈值自动研判，返回告警列表 [(type, level, detail)]"""
    out = []
    if f.pressure_mpa is not None:
        if f.pressure_mpa < 0.15:
            out.append(("低压告警", "中", f"管道压力 {f.pressure_mpa}MPa，低于服务下限 0.15MPa"))
        elif f.pressure_mpa > 0.6:
            out.append(("高压告警", "高", f"管道压力 {f.pressure_mpa}MPa，超安全上限 0.6MPa，存在爆管隐患"))
    if f.deformation_mm is not None and f.deformation_mm > 5:
        out.append(("管道形变", "高", f"管道形变 {f.deformation_mm}mm，超阈值 5mm"))
    if f.turbidity_ntu is not None and f.turbidity_ntu > 1:
        out.append(("浊度超标", "中", f"浊度 {f.turbidity_ntu}NTU，超国标 1NTU"))
    if f.residual_cl is not None and f.residual_cl < 0.05:
        out.append(("余氯不足", "中", f"余氯 {f.residual_cl}mg/L，低于国标 0.05mg/L"))
    if f.level_cm is not None and f.level_cm < 20:
        out.append(("液位偏低", "低", f"液位 {f.level_cm}cm，低于下限 20cm"))
    return out


@router.post("/data")
def collect(form: MonitorForm):
    ts = int(time.time() * 1000)
    alarms = _judge(form)
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO monitor_record(pipe_id, ts, pressure_mpa, flow_m3h, level_cm,
           turbidity_ntu, residual_cl, deformation_mm, is_abnormal)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (form.pipe_id, ts, form.pressure_mpa, form.flow_m3h, form.level_cm,
         form.turbidity_ntu, form.residual_cl, form.deformation_mm, 1 if alarms else 0))
    rid = cur.lastrowid
    created = []
    for i, (atype, level, detail) in enumerate(alarms):
        code = "AL%s%d" % (ts % 10 ** 9, i)
        conn.execute(
            "INSERT INTO alarm(alarm_code, pipe_id, source, type, level, detail, alarm_ts, status)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (code, form.pipe_id, "管网", atype, level, detail, ts, "待处理"))
        created.append({"type": atype, "level": level, "detail": detail})
    if alarms:
        conn.execute("UPDATE pipe SET status='告警' WHERE id=? AND status='正常'", (form.pipe_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "id": rid, "is_abnormal": bool(alarms), "alarms_created": created}


@router.get("/latest")
def latest(keyword: str = "", only_abnormal: bool = False):
    conn = get_conn()
    sql = """
    SELECT p.id, p.code, p.name, p.district, p.road_name, p.status, m.ts,
           m.pressure_mpa, m.flow_m3h, m.level_cm, m.turbidity_ntu, m.residual_cl,
           m.deformation_mm, m.is_abnormal
    FROM pipe p LEFT JOIN (
        SELECT mr.* FROM monitor_record mr
        JOIN (SELECT pipe_id, MAX(id) AS mid FROM monitor_record GROUP BY pipe_id) t
          ON mr.id = t.mid
    ) m ON m.pipe_id = p.id
    """
    where, args = [], []
    if keyword:
        where.append("(p.code LIKE ? OR p.name LIKE ? OR p.road_name LIKE ? OR p.district LIKE ?)")
        args += ["%%%s%%" % keyword] * 4
    if only_abnormal:
        where.append("(m.is_abnormal = 1 OR p.status != '正常')")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY p.id"
    rows = [dict(r) for r in conn.execute(sql, args).fetchall()]
    conn.close()
    return {"total": len(rows), "items": rows}


@router.get("/history")
def history(pipe_id: int):
    conn = get_conn()
    pipe = conn.execute("SELECT * FROM pipe WHERE id=?", (pipe_id,)).fetchone()
    recs = [dict(r) for r in conn.execute(
        "SELECT * FROM monitor_record WHERE pipe_id=? ORDER BY ts DESC LIMIT 60", (pipe_id,)).fetchall()]
    conn.close()
    return {"pipe": dict(pipe) if pipe else None, "records": recs}


@router.get("/alarms")
def alarms(status: str = "", level: str = "", type: str = "", source: str = "",
           page: int = 1, page_size: int = 8):
    conn = get_conn()
    sql = """SELECT a.*, p.code, p.name, p.road_name, p.district FROM alarm a
             LEFT JOIN pipe p ON p.id = a.pipe_id"""
    where, args = [], []
    if status:
        where.append("a.status=?"); args.append(status)
    if level:
        where.append("a.level=?"); args.append(level)
    if type:
        where.append("a.type=?"); args.append(type)
    if source:
        where.append("a.source=?"); args.append(source)
    if where:
        sql += " WHERE " + " AND ".join(where)
    total = conn.execute("SELECT COUNT(*) FROM (%s)" % sql, args).fetchone()[0]
    sql += " ORDER BY a.alarm_ts DESC LIMIT ? OFFSET ?"
    args += [page_size, (page - 1) * page_size]
    rows = [dict(r) for r in conn.execute(sql, args).fetchall()]
    conn.close()
    return {"total": total, "items": rows}


@router.post("/alarms/{alarm_id}/handle")
def handle_alarm(alarm_id: int, status: str = "已处理"):
    conn = get_conn()
    conn.execute("UPDATE alarm SET status=? WHERE id=?", (status, alarm_id))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/alarm-trend")
def alarm_trend():
    conn = get_conn()
    rows = conn.execute("SELECT alarm_ts, level FROM alarm").fetchall()
    conn.close()
    days, idx = [], {}
    for i in range(6, -1, -1):
        d = time.localtime(time.time() - i * 86400)
        key = "%d-%02d-%02d" % (d.tm_year, d.tm_mon, d.tm_mday)
        days.append(key)
        idx[key] = len(days) - 1
    series = {lv: [0] * 7 for lv in ("高", "中", "低")}
    for r in rows:
        d = time.localtime(r["alarm_ts"] / 1000)
        key = "%d-%02d-%02d" % (d.tm_year, d.tm_mon, d.tm_mday)
        if key in idx and r["level"] in series:
            series[r["level"]][idx[key]] += 1
    return {"days": [d[5:] for d in days],
            "series": [{"name": k, "data": v} for k, v in series.items()]}


@router.get("/stats")
def stats():
    conn = get_conn()
    by_type = [dict(r) for r in conn.execute(
        "SELECT type AS name, COUNT(*) AS value FROM alarm GROUP BY type ORDER BY value DESC LIMIT 6")]
    by_level = [dict(r) for r in conn.execute(
        "SELECT level AS name, COUNT(*) AS value FROM alarm GROUP BY level")]
    today0 = time.mktime(time.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d")) * 1000
    monitor_today = conn.execute(
        "SELECT COUNT(*) FROM monitor_record WHERE ts>=?", (today0,)).fetchone()[0]
    conn.close()
    return {"by_type": by_type, "by_level": by_level, "monitor_today": monitor_today}
