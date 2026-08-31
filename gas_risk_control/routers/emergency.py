# -*- coding: utf-8 -*-
"""
功能 8：应急联动关阀
====================
泄漏预警触发后，根据事故点桩号自动计算隔离方案：
    1) 定位事故点两侧最近的截断阀（上游/下游）；
    2) 生成级联关阀时序：先关上游截断气源，再关下游防倒流，
       严重事件时级联扩大隔离至相邻第二道阀门；
    3) 评估隔离段长度、存气量、影响范围；
    4) 执行关阀并记录指令，修复完成后可一键恢复供气。
"""
import json
import math
import time

from fastapi import APIRouter, HTTPException

import database as db
from models import EmergencyTriggerReq

router = APIRouter(prefix="/api/emergency", tags=["8.应急联动关阀"])

PIPE_DIAMETER_M = 0.8      # 主线管径 DN800
PIPE_PRESSURE_MPA = 1.6    # 运行压力
USERS_PER_KM = 400         # 每公里影响用户数（估算）


def _build_plan(leak_km: float, level: str, valves: list) -> dict:
    """
    生成级联关阀方案。
    阀门按桩号排序后，取事故点两侧最近阀门为首道隔离，
    severe 级别再向外扩一道阀门做级联加强隔离。
    """
    ups = [v for v in valves if v["position_km"] < leak_km]
    downs = [v for v in valves if v["position_km"] > leak_km]

    steps = []
    seq = 1
    primary = []
    if ups:
        v = ups[-1]
        steps.append({"seq": seq, "valve_id": v["id"], "position_km": v["position_km"],
                      "action": "close", "delay_s": 0,
                      "reason": f"首道隔离：关闭上游阀 {v['id']}，截断气源"})
        primary.append(v); seq += 1
    if downs:
        v = downs[0]
        steps.append({"seq": seq, "valve_id": v["id"], "position_km": v["position_km"],
                      "action": "close", "delay_s": 5,
                      "reason": f"首道隔离：关闭下游阀 {v['id']}，防止下游倒流供气"})
        primary.append(v); seq += 1

    # 严重事件：级联扩大隔离范围（相邻第二道阀门）
    if level == "severe":
        if len(ups) >= 2:
            v = ups[-2]
            steps.append({"seq": seq, "valve_id": v["id"], "position_km": v["position_km"],
                          "action": "close", "delay_s": 30,
                          "reason": f"级联加强：关闭 {v['id']}，扩大上游隔离，防止泄漏点残留气源"})
            primary.insert(0, v); seq += 1
        if len(downs) >= 2:
            v = downs[1]
            steps.append({"seq": seq, "valve_id": v["id"], "position_km": v["position_km"],
                          "action": "close", "delay_s": 30,
                          "reason": f"级联加强：关闭 {v['id']}，扩大下游隔离"})
            primary.append(v); seq += 1

    if not steps:
        raise HTTPException(400, "事故点两侧均无可用阀门，无法生成隔离方案")

    seg_lo = min(v["position_km"] for v in primary)
    seg_hi = max(v["position_km"] for v in primary)
    seg_len = seg_hi - seg_lo
    # 隔离段存气量（标准状态估算）：几何容积 × 绝对压力倍数
    geom_m3 = math.pi * (PIPE_DIAMETER_M / 2) ** 2 * seg_len * 1000
    stored_m3 = geom_m3 * (PIPE_PRESSURE_MPA * 10 + 1)
    return {
        "leak_position_km": leak_km,
        "level": level,
        "steps": steps,
        "isolation_segment": {
            "from_km": seg_lo, "to_km": seg_hi, "length_km": round(seg_len, 2),
            "stored_gas_m3_std": round(stored_m3, 0),
            "affected_users_estimate": int(seg_len * USERS_PER_KM),
            "valves_closed": [v["id"] for v in primary],
        },
        "note": "隔离后应对段内余气放空，检测合格并经修复验收后方可恢复供气",
    }


@router.get("/valves", summary="阀门列表与状态")
def list_valves():
    """全部截断阀的桩号与开/关状态，用于绘制管线阀门拓扑。"""
    conn = db.get_conn()
    try:
        return db.rows_to_list(conn.execute("SELECT * FROM valves ORDER BY position_km"))
    finally:
        conn.close()


@router.post("/trigger", summary="触发应急联动（生成关阀方案）")
def trigger(req: EmergencyTriggerReq):
    """
    人工或泄漏报警联动触发。根据事故点桩号自动生成级联关阀方案，
    此时阀门尚未动作，需调用 /execute 执行。
    """
    if req.level not in ("warning", "severe"):
        raise HTTPException(400, "事件级别应为 warning/severe")
    conn = db.get_conn()
    try:
        valves = db.rows_to_list(conn.execute("SELECT * FROM valves ORDER BY position_km"))
        if not (valves[0]["position_km"] <= req.position_km <= valves[-1]["position_km"]):
            raise HTTPException(400, f"事故点应在管线范围 {valves[0]['position_km']}~{valves[-1]['position_km']}km 内")
        plan = _build_plan(req.position_km, req.level, valves)
        ts = int(time.time() * 1000)
        cur = conn.execute(
            "INSERT INTO emergency_events(ts_ms,position_km,source,level,status,plan) VALUES(?,?,?,?,?,?)",
            (ts, req.position_km, req.source, req.level, "planned", json.dumps(plan, ensure_ascii=False)))
        event_id = cur.lastrowid
        for s in plan["steps"]:
            conn.execute(
                "INSERT INTO valve_commands(ts_ms,event_id,valve_id,seq,action,delay_s) VALUES(?,?,?,?,?,?)",
                (ts, event_id, s["valve_id"], s["seq"], s["action"], s["delay_s"]))
        conn.commit()
        return {"event_id": event_id, "ts_ms": ts, "status": "planned", "plan": plan}
    finally:
        conn.close()


@router.post("/events/{event_id}/execute", summary="执行级联关阀")
def execute(event_id: int):
    """
    按方案时序执行关阀：更新阀门状态为关闭、记录执行时间，
    并返回隔离效果评估（隔离段、存气量、影响用户）。
    """
    conn = db.get_conn()
    try:
        ev = conn.execute("SELECT * FROM emergency_events WHERE id=?", (event_id,)).fetchone()
        if not ev:
            raise HTTPException(404, f"应急事件 {event_id} 不存在")
        if ev["status"] == "restored":
            raise HTTPException(400, "该事件已恢复供气，无需重复执行")
        plan = json.loads(ev["plan"])
        ts = int(time.time() * 1000)
        closed = []
        for s in plan["steps"]:
            conn.execute("UPDATE valves SET status='closed' WHERE id=?", (s["valve_id"],))
            conn.execute("UPDATE valve_commands SET executed=1 WHERE event_id=? AND valve_id=?",
                         (event_id, s["valve_id"]))
            closed.append(s["valve_id"])
        seg = plan["isolation_segment"]
        isolation = {
            **seg,
            "executed_at_ms": ts,
            "result": f"已关闭 {'、'.join(closed)}，隔离 {seg['from_km']}~{seg['to_km']}km 段，"
                      f"泄漏影响范围得到控制",
        }
        conn.execute("UPDATE emergency_events SET status='executed', isolation=? WHERE id=?",
                     (json.dumps(isolation, ensure_ascii=False), event_id))
        conn.commit()
        return {"ok": True, "event_id": event_id, "status": "executed", "isolation": isolation}
    finally:
        conn.close()


@router.post("/events/{event_id}/restore", summary="修复后恢复供气")
def restore(event_id: int):
    """抢修完成并检测合格后，重新开启该事件关闭的全部阀门。"""
    conn = db.get_conn()
    try:
        ev = conn.execute("SELECT * FROM emergency_events WHERE id=?", (event_id,)).fetchone()
        if not ev:
            raise HTTPException(404, f"应急事件 {event_id} 不存在")
        if ev["status"] != "executed":
            raise HTTPException(400, "仅已执行关阀的事件可恢复供气")
        plan = json.loads(ev["plan"])
        ts = int(time.time() * 1000)
        opened = []
        for s in plan["steps"]:
            conn.execute("UPDATE valves SET status='open' WHERE id=?", (s["valve_id"],))
            conn.execute("INSERT INTO valve_commands(ts_ms,event_id,valve_id,seq,action,delay_s,executed)"
                         " VALUES(?,?,?,?,?,?,1)", (ts, event_id, s["valve_id"], s["seq"], "open", 0))
            opened.append(s["valve_id"])
        conn.execute("UPDATE emergency_events SET status='restored' WHERE id=?", (event_id,))
        conn.commit()
        return {"ok": True, "event_id": event_id, "status": "restored",
                "valves_reopened": opened, "msg": "阀门已开启，恢复供气（请按规程缓慢升压并检漏）"}
    finally:
        conn.close()


@router.get("/events", summary="应急事件记录")
def events(limit: int = 20):
    """最近应急事件（含方案与执行状态）。"""
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT id,ts_ms,position_km,source,level,status FROM emergency_events "
            "ORDER BY id DESC LIMIT ?", (limit,)))
        return {"events": rows}
    finally:
        conn.close()


@router.get("/events/{event_id}", summary="应急事件详情")
def event_detail(event_id: int):
    conn = db.get_conn()
    try:
        ev = conn.execute("SELECT * FROM emergency_events WHERE id=?", (event_id,)).fetchone()
        if not ev:
            raise HTTPException(404, f"应急事件 {event_id} 不存在")
        cmds = db.rows_to_list(conn.execute(
            "SELECT * FROM valve_commands WHERE event_id=? ORDER BY seq", (event_id,)))
        return {**dict(ev),
                "plan": json.loads(ev["plan"]),
                "isolation": json.loads(ev["isolation"]) if ev["isolation"] else None,
                "commands": cmds}
    finally:
        conn.close()
