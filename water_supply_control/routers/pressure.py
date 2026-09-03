# -*- coding: utf-8 -*-
"""功能4 智能压力调度 — 峰谷时段+地形高差自动计算泵站调节方案"""
import time

from fastapi import APIRouter

from database import get_conn
from models import PressurePlanForm

router = APIRouter(prefix="/api/pressure", tags=["智能压力调度"])

# 峰谷时段基准调节系数：夜间低谷降压节能，高峰保压
PERIOD_FACTOR = {"早高峰": 1.05, "晚高峰": 1.08, "日间平峰": 1.0, "夜间低谷": 0.85}


@router.get("/stations")
def stations():
    conn = get_conn()
    rows = [dict(r) for r in conn.execute("SELECT * FROM pump_station ORDER BY id")]
    conn.close()
    return {"total": len(rows), "items": rows}


@router.post("/plan")
def make_plan(form: PressurePlanForm):
    """根据峰谷时段与地形高差自动计算目标压力、节能率与爆管风险降幅"""
    conn = get_conn()
    st = conn.execute("SELECT * FROM pump_station WHERE id=?", (form.station_id,)).fetchone()
    if not st:
        conn.close()
        return {"ok": False, "detail": "泵站不存在"}
    factor = PERIOD_FACTOR.get(form.period, 1.0)
    terrain = form.terrain_delta_m if form.terrain_delta_m is not None else (st["supply_elev_m"] or 0) * 0.2
    # 目标压力 = 当前压力 × 时段系数 + 地形补偿(每10m高差约0.1MPa)
    target = round(st["current_pressure_mpa"] * factor + terrain / 100.0, 3)
    target = max(0.18, min(0.6, target))
    cur = st["current_pressure_mpa"] or 0.3
    energy = round(abs(cur - target) / cur * 38, 1) if cur else 0
    risk = "高" if cur > 0.5 else ("中" if cur > 0.42 else "低")
    ts = int(time.time() * 1000)
    cur2 = conn.execute(
        "INSERT INTO pressure_plan(station_id, period, terrain_delta_m, current_pressure_mpa,"
        " target_pressure_mpa, energy_save_pct, burst_risk_reduce, status, created_ts)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (form.station_id, form.period, terrain, cur, target, energy,
         "由%s降至%s" % (risk, "低" if target <= 0.42 else "中"), "已生成", ts))
    conn.execute("UPDATE pump_station SET current_pressure_mpa=? WHERE id=?",
                 (target, form.station_id))
    conn.commit()
    conn.close()
    return {"ok": True, "id": cur2.lastrowid, "target_pressure_mpa": target,
            "energy_save_pct": energy, "burst_risk": risk}


@router.get("/plans")
def plans(station_id: int = 0):
    conn = get_conn()
    sql = """SELECT pp.*, ps.code AS station_code, ps.name AS station_name
             FROM pressure_plan pp JOIN pump_station ps ON ps.id=pp.station_id"""
    args = []
    if station_id:
        sql += " WHERE pp.station_id=?"
        args.append(station_id)
    sql += " ORDER BY pp.created_ts DESC LIMIT 50"
    rows = [dict(r) for r in conn.execute(sql, args).fetchall()]
    conn.close()
    return {"total": len(rows), "items": rows}


@router.post("/plans/{plan_id}/apply")
def apply_plan(plan_id: int):
    conn = get_conn()
    p = conn.execute("SELECT * FROM pressure_plan WHERE id=?", (plan_id,)).fetchone()
    if p:
        conn.execute("UPDATE pressure_plan SET status='已执行' WHERE id=?", (plan_id,))
        conn.execute("UPDATE pump_station SET current_pressure_mpa=? WHERE id=?",
                     (p["target_pressure_mpa"], p["station_id"]))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/stats")
def stats():
    conn = get_conn()
    by_period = [dict(r) for r in conn.execute(
        "SELECT period AS name, COUNT(*) AS value FROM pressure_plan GROUP BY period")]
    avg_save = conn.execute(
        "SELECT ROUND(AVG(energy_save_pct),1) FROM pressure_plan").fetchone()[0] or 0
    conn.close()
    return {"by_period": by_period, "avg_energy_save_pct": avg_save}
