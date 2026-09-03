# -*- coding: utf-8 -*-
"""功能7 爆管影响分析 — 风险预判、停水影响评估、最优关阀方案推荐"""
import time

from fastapi import APIRouter

from database import get_conn
from models import BurstHandleForm

router = APIRouter(prefix="/api/burst", tags=["爆管影响分析"])


@router.get("/cases")
def cases(status: str = ""):
    conn = get_conn()
    sql = """SELECT bc.*, p.code, p.name, p.district, p.road_name, p.diameter_mm,
             p.material, p.lay_date FROM burst_case bc
             JOIN pipe p ON p.id=bc.pipe_id"""
    args = []
    if status:
        sql += " WHERE bc.status=?"
        args.append(status)
    sql += " ORDER BY bc.risk_score DESC"
    rows = [dict(r) for r in conn.execute(sql, args).fetchall()]
    conn.close()
    return {"total": len(rows), "items": rows}


@router.post("/predict")
def predict(pipe_id: int):
    """爆管风险预判：管龄+材质+压力综合评分，自动评估停水影响并生成关阀方案"""
    conn = get_conn()
    p = conn.execute("SELECT * FROM pipe WHERE id=?", (pipe_id,)).fetchone()
    if not p:
        conn.close()
        return {"ok": False, "detail": "管道不存在"}
    # 评分：管龄权重40% + 材质权重30% + 当前压力权重30%
    age = 2026 - int((p["lay_date"] or "2010-01-01")[:4])
    age_score = min(age / 40.0, 1) * 40
    mat_score = {"灰铸铁": 30, "预应力砼": 26, "钢管": 18, "球墨铸铁": 12, "PE": 8}.get(
        p["material"], 15)
    mr = conn.execute(
        "SELECT pressure_mpa FROM monitor_record WHERE pipe_id=? ORDER BY ts DESC LIMIT 1",
        (pipe_id,)).fetchone()
    pr = (mr["pressure_mpa"] if mr and mr["pressure_mpa"] else 0.3)
    pr_score = min(pr / 0.6, 1) * 30
    score = round(age_score + mat_score + pr_score, 1)
    level = "高" if score >= 60 else ("中" if score >= 40 else "低")
    affected = int((p["diameter_mm"] or 300) * 3.2)
    area = "%s%s沿线" % (p["district"] or "", p["road_name"] or "")
    ts = int(time.time() * 1000)
    cur = conn.execute(
        "INSERT INTO burst_case(pipe_id, risk_score, risk_level, predict_detail,"
        " affected_users, affected_area, status, created_ts) VALUES (?,?,?,?,?,?,?,?)",
        (pipe_id, score, level,
         "管龄%d年(%s材质)评分%.0f + 运行压力%.2fMPa评分%.0f，综合风险%.1f"
         % (age, p["material"] or "未知", age_score, pr, pr_score, score),
         affected, area, "风险预警", ts))
    case_id = cur.lastrowid
    # 最优关阀方案：本管段两端阀 + 上游连通阀，按操作顺序推荐
    valves = [
        ("FV%s-A" % p["code"], "%s上游端阀门" % (p["name"]), 1),
        ("FV%s-B" % p["code"], "%s下游端阀门" % (p["name"]), 2),
        ("FV%s-C" % p["code"], "%s连通支管阀门" % (p["road_name"] or "主干"), 3),
    ]
    for vc, pos, no in valves:
        conn.execute(
            "INSERT INTO burst_valve(case_id, valve_code, position, order_no, is_selected)"
            " VALUES (?,?,?,?,1)", (case_id, vc, pos, no))
    conn.commit()
    conn.close()
    return {"ok": True, "case_id": case_id, "risk_score": score, "risk_level": level,
            "affected_users": affected, "valves": [
                {"valve_code": v[0], "position": v[1], "order_no": v[2]} for v in valves]}


@router.get("/{case_id}/valves")
def valves(case_id: int):
    conn = get_conn()
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM burst_valve WHERE case_id=? ORDER BY order_no", (case_id,)).fetchall()]
    conn.close()
    return {"total": len(rows), "items": rows}


@router.post("/{case_id}/handle")
def handle(case_id: int, form: BurstHandleForm):
    """关阀处置状态流转：风险预警→处置中→已关阀→已修复"""
    conn = get_conn()
    conn.execute("UPDATE burst_case SET status=? WHERE id=?", (form.status, case_id))
    if form.status == "已修复":
        c = conn.execute("SELECT pipe_id FROM burst_case WHERE id=?", (case_id,)).fetchone()
        if c:
            conn.execute("UPDATE pipe SET status='正常' WHERE id=?", (c["pipe_id"],))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/stats/summary")
def summary():
    conn = get_conn()
    by_level = [dict(r) for r in conn.execute(
        "SELECT risk_level AS name, COUNT(*) AS value FROM burst_case GROUP BY risk_level")]
    by_status = [dict(r) for r in conn.execute(
        "SELECT status AS name, COUNT(*) AS value FROM burst_case GROUP BY status")]
    conn.close()
    return {"by_level": by_level, "by_status": by_status}
