# -*- coding: utf-8 -*-
"""功能5 二次供水管控 — 水箱液位/水质/消毒设备状态实时监控告警"""
import time

from fastapi import APIRouter

from database import get_conn
from models import SecondaryForm

router = APIRouter(prefix="/api/secondary", tags=["二次供水管控"])


@router.get("/units")
def units(keyword: str = "", status: str = ""):
    conn = get_conn()
    sql = "SELECT * FROM secondary_unit"
    where, args = [], []
    if keyword:
        where.append("(code LIKE ? OR community LIKE ? OR district LIKE ?)")
        args += ["%%%s%%" % keyword] * 3
    if status:
        where.append("status=?"); args.append(status)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id"
    rows = [dict(r) for r in conn.execute(sql, args).fetchall()]
    conn.close()
    return {"total": len(rows), "items": rows}


@router.post("/data")
def collect(form: SecondaryForm):
    """上报二次供水实时数据，异常自动告警"""
    ts = int(time.time() * 1000)
    conn = get_conn()
    u = conn.execute("SELECT * FROM secondary_unit WHERE id=?", (form.unit_id,)).fetchone()
    if not u:
        conn.close()
        return {"ok": False, "detail": "二次供水单元不存在"}
    alerts = []
    if form.level_pct is not None:
        if form.level_pct < 20:
            alerts.append(("水箱液位 %s%% 过低，存在断水风险" % form.level_pct, "高"))
        elif form.level_pct > 95:
            alerts.append(("水箱液位 %s%% 过高，溢流风险" % form.level_pct, "低"))
    if form.turbidity_ntu is not None and form.turbidity_ntu > 1:
        alerts.append(("水箱浊度 %sNTU 超标" % form.turbidity_ntu, "中"))
    if form.residual_cl is not None and form.residual_cl < 0.05:
        alerts.append(("水箱余氯 %smg/L 不足，消毒不达标" % form.residual_cl, "中"))
    if form.disinfect_status and form.disinfect_status != "正常":
        alerts.append(("消毒设备%s，需立即检修" % form.disinfect_status, "高"))
    conn.execute(
        "UPDATE secondary_unit SET level_pct=COALESCE(?,level_pct),"
        " turbidity_ntu=COALESCE(?,turbidity_ntu), residual_cl=COALESCE(?,residual_cl),"
        " disinfect_status=COALESCE(?,disinfect_status), status=?, last_check=?"
        " WHERE id=?",
        (form.level_pct, form.turbidity_ntu, form.residual_cl, form.disinfect_status,
         "告警" if alerts else "正常",
         time.strftime("%Y-%m-%d %H:%M", time.localtime(ts / 1000)), form.unit_id))
    for i, (detail, level) in enumerate(alerts):
        conn.execute(
            "INSERT INTO alarm(alarm_code, pipe_id, source, type, level, detail, alarm_ts,"
            " status) VALUES (?,?,?,?,?,?,?,?)",
            ("SW%d%d" % (ts % 10 ** 9, i), None, "二次供水", "二供告警", level, detail,
             ts, "待处理"))
    conn.commit()
    conn.close()
    return {"ok": True, "is_abnormal": bool(alerts),
            "alarms": [{"level": a[1], "detail": a[0]} for a in alerts]}


@router.get("/stats")
def stats():
    conn = get_conn()
    by_status = [dict(r) for r in conn.execute(
        "SELECT status AS name, COUNT(*) AS value FROM secondary_unit GROUP BY status")]
    abnormal = conn.execute(
        "SELECT COUNT(*) FROM secondary_unit WHERE status!='正常'").fetchone()[0]
    conn.close()
    return {"by_status": by_status, "abnormal": abnormal}
