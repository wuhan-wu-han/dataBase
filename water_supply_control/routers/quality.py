# -*- coding: utf-8 -*-
"""功能3 水质全流程溯源 — 水厂到终端全链路追踪，污染异常定位问题管段"""
import time

from fastapi import APIRouter

from database import get_conn
from models import QualityForm

router = APIRouter(prefix="/api/quality", tags=["水质全流程溯源"])


@router.get("/chain")
def chain():
    """返回水厂→泵站→管网→二次供水→终端用户全链路节点及最新水质"""
    conn = get_conn()
    nodes = [dict(r) for r in conn.execute(
        "SELECT * FROM quality_node ORDER BY seq").fetchall()]
    conn.close()
    return {"nodes": nodes}


@router.get("/records")
def records(node_id: int, limit: int = 30):
    conn = get_conn()
    node = conn.execute("SELECT * FROM quality_node WHERE id=?", (node_id,)).fetchone()
    recs = [dict(r) for r in conn.execute(
        "SELECT * FROM quality_record WHERE node_id=? ORDER BY ts DESC LIMIT ?",
        (node_id, limit)).fetchall()]
    conn.close()
    return {"node": dict(node) if node else None, "records": recs}


@router.post("/data")
def collect(form: QualityForm):
    """录入节点水质，异常自动告警并沿链路溯源定位问题管段"""
    ts = int(time.time() * 1000)
    conn = get_conn()
    node = conn.execute("SELECT * FROM quality_node WHERE id=?", (form.node_id,)).fetchone()
    if not node:
        conn.close()
        return {"ok": False, "detail": "节点不存在"}
    abnormal = []
    if form.turbidity_ntu is not None and form.turbidity_ntu > 1:
        abnormal.append(("浊度超标", "中", "浊度 %sNTU 超国标 1NTU" % form.turbidity_ntu))
    if form.residual_cl is not None and form.residual_cl < 0.05:
        abnormal.append(("余氯不足", "中", "余氯 %smg/L 低于国标 0.05mg/L" % form.residual_cl))
    if form.ph is not None and (form.ph < 6.5 or form.ph > 8.5):
        abnormal.append(("pH异常", "高", "pH %s 超出 6.5-8.5 安全区间" % form.ph))
    conn.execute(
        "INSERT INTO quality_record(node_id, ts, turbidity_ntu, residual_cl, ph, is_abnormal)"
        " VALUES (?,?,?,?,?,?)",
        (form.node_id, ts, form.turbidity_ntu, form.residual_cl, form.ph, 1 if abnormal else 0))
    # 溯源：异常节点关联管段或上游最近管段即为疑似问题管段
    suspect = None
    if abnormal:
        row = conn.execute(
            "SELECT p.code, p.name FROM quality_node q JOIN pipe p ON p.id=q.pipe_id"
            " WHERE q.id=?", (form.node_id,)).fetchone()
        if row:
            suspect = row
        else:
            up = conn.execute(
                "SELECT * FROM quality_node WHERE seq<? ORDER BY seq DESC LIMIT 1",
                (node["seq"],)).fetchone()
            if up and up["pipe_id"]:
                suspect = conn.execute(
                    "SELECT code, name FROM pipe WHERE id=?", (up["pipe_id"],)).fetchone()
    for i, (atype, level, detail) in enumerate(abnormal):
        extra = "；疑似问题管段：%s(%s)" % (suspect["name"], suspect["code"]) if suspect else ""
        conn.execute(
            "INSERT INTO alarm(alarm_code, pipe_id, source, type, level, detail, alarm_ts,"
            " status) VALUES (?,?,?,?,?,?,?,?)",
            ("Q%d%d" % (ts % 10 ** 9, i), None, "水质溯源",
             atype, level, detail + extra, ts, "待处理"))
    if abnormal:
        conn.execute("UPDATE quality_node SET status='异常' WHERE id=?", (form.node_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "is_abnormal": bool(abnormal),
            "suspect_pipe": dict(suspect) if suspect else None,
            "alarms": [{"type": a[0], "level": a[1], "detail": a[2]} for a in abnormal]}


@router.get("/stats")
def stats():
    conn = get_conn()
    by_kind = [dict(r) for r in conn.execute(
        "SELECT kind AS name, COUNT(*) AS value FROM quality_node GROUP BY kind ORDER BY MIN(seq)")]
    abnormal = conn.execute(
        "SELECT COUNT(*) FROM quality_node WHERE status='异常'").fetchone()[0]
    conn.close()
    return {"by_kind": by_kind, "abnormal_nodes": abnormal}
