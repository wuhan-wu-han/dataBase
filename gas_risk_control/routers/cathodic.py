# -*- coding: utf-8 -*-
"""
功能 7：阴极保护监测
====================
管道阴极保护系统（恒电位仪 + 测试桩）的通电电位、断电电位、输出电流监测，
并依据 GB/T 21448 准则评估腐蚀防护效果：

    断电电位（瞬时断电去极化电位，CSE 参比）：
      E > -0.85V            → 保护不足（存在腐蚀风险）
      -1.2V ≤ E ≤ -0.85V    → 保护正常
      E < -1.2V             → 过保护（涂层阴极剥离/氢脆风险）
    输出电流相对额定值明显下降 → 恒电位仪/阳极地床异常
"""
import json
import time

from fastapi import APIRouter, HTTPException, Query

import database as db
from models import CathodicDataReq

router = APIRouter(prefix="/api/cathodic", tags=["7.阴极保护监测"])

E_MIN = -0.85   # 最小保护电位（V, CSE）
E_MAX = -1.20   # 最大（最负）保护电位


def _evaluate_potential(e_off: float, e_on: float, current_a: float, rated_a: float) -> dict:
    """按准则评价单桩保护效果。"""
    issues, score = [], 100.0
    if e_off is None:
        return {"status": "no_data", "status_text": "无数据", "score": 0, "issues": ["缺少断电电位数据"]}

    if e_off > E_MIN:
        status, status_text = "under", "保护不足"
        issues.append(f"断电电位 {e_off:.3f}V 正于 {E_MIN}V，未达到最小保护电位，管体存在腐蚀风险")
        score -= 40
    elif e_off < E_MAX:
        status, status_text = "over", "过保护"
        issues.append(f"断电电位 {e_off:.3f}V 负于 {E_MAX}V，过保护可能导致涂层阴极剥离")
        score -= 25
    else:
        status, status_text = "normal", "保护正常"

    # 通断电电位差过大说明存在较大 IR 降，应以断电电位为准（提示）
    if e_on is not None and abs(e_on - e_off) > 0.3:
        issues.append(f"通电/断电电位差 {abs(e_on - e_off):.2f}V，IR 降较大，评价以断电电位为准")

    # 输出电流异常判断
    if rated_a and rated_a > 0:
        ratio = current_a / rated_a if current_a is not None else 0
        if ratio < 0.3:
            issues.append(f"输出电流 {current_a:.1f}A 仅为额定值 {rated_a:.0f}A 的 {ratio*100:.0f}%，"
                          "疑似恒电位仪故障或阳极地床失效")
            score -= 30
            if status == "normal":
                status, status_text = "under", "保护不足(输出异常)"
        elif ratio > 1.15:
            issues.append(f"输出电流超额定值（{current_a:.1f}A/{rated_a:.0f}A），检查输出调节")
            score -= 10

    if not issues:
        issues.append(f"断电电位 {e_off:.3f}V 处于保护区间 [{E_MAX}V, {E_MIN}V]，防腐效果良好")
    return {"status": status, "status_text": status_text,
            "score": max(0, round(score, 1)), "issues": issues}


@router.get("/test-piles", summary="测试桩列表")
def test_piles():
    conn = db.get_conn()
    try:
        return db.rows_to_list(conn.execute("SELECT * FROM test_piles ORDER BY position_km"))
    finally:
        conn.close()


@router.post("/data", summary="上报阴极保护监测数据")
def report_data(req: CathodicDataReq):
    """
    上报一帧测试桩数据（可由采集器定时上报）。
    上报后立即按准则评价并返回评价结论。
    """
    ts = req.ts_ms or int(time.time() * 1000)
    conn = db.get_conn()
    try:
        pile = conn.execute("SELECT * FROM test_piles WHERE id=?", (req.pile_id,)).fetchone()
        if not pile:
            raise HTTPException(404, f"测试桩 {req.pile_id} 不存在")
        conn.execute(
            "INSERT INTO cathodic_data(ts_ms,pile_id,on_potential_v,off_potential_v,output_current_a)"
            " VALUES(?,?,?,?,?)",
            (ts, req.pile_id, req.on_potential_v, req.off_potential_v, req.output_current_a))
        conn.commit()
        ev = _evaluate_potential(req.off_potential_v, req.on_potential_v,
                                 req.output_current_a, pile["rated_current_a"])
        return {"ok": True, "ts_ms": ts, "evaluation": ev}
    finally:
        conn.close()


@router.get("/realtime", summary="各测试桩最新数据与评价")
def realtime():
    """每个测试桩最新一帧数据 + 保护效果评价结论。"""
    conn = db.get_conn()
    try:
        piles = db.rows_to_list(conn.execute("SELECT * FROM test_piles ORDER BY position_km"))
        result = []
        for p in piles:
            row = conn.execute(
                "SELECT * FROM cathodic_data WHERE pile_id=? ORDER BY id DESC LIMIT 1", (p["id"],)).fetchone()
            item = {**p, "latest": dict(row) if row else None}
            if row:
                item["evaluation"] = _evaluate_potential(
                    row["off_potential_v"], row["on_potential_v"],
                    row["output_current_a"], p["rated_current_a"])
            else:
                item["evaluation"] = _evaluate_potential(None, None, None, p["rated_current_a"])
            result.append(item)
        return {"piles": result, "criteria": {"e_min_v": E_MIN, "e_max_v": E_MAX}}
    finally:
        conn.close()


@router.get("/evaluate", summary="腐蚀防护效果综合评估")
def evaluate():
    """
    全网阴极保护综合评估：逐桩评价 + 保护率、平均得分与整改建议。
    """
    data = realtime()
    piles = data["piles"]
    n = len(piles)
    normal = sum(1 for p in piles if p["evaluation"]["status"] == "normal")
    avg_score = round(sum(p["evaluation"]["score"] for p in piles) / n, 1) if n else 0
    suggestions = []
    for p in piles:
        if p["evaluation"]["status"] == "under":
            suggestions.append(f"{p['name']}（{p['position_km']}km）保护不足：提高恒电位仪输出或检查阳极地床")
        elif p["evaluation"]["status"] == "over":
            suggestions.append(f"{p['name']}（{p['position_km']}km）过保护：下调输出电压")
    return {
        "piles": piles,
        "summary": {
            "total": n, "normal": normal,
            "protection_rate_pct": round(normal / n * 100, 1) if n else 0,
            "avg_score": avg_score,
        },
        "suggestions": suggestions or ["全线阴极保护运行正常"],
    }


@router.get("/history", summary="测试桩历史趋势")
def history(pile_id: int = Query(...), hours: int = Query(24, ge=1, le=24 * 30)):
    """指定测试桩最近 N 小时的电位/电流趋势。"""
    conn = db.get_conn()
    try:
        since = int(time.time() * 1000) - hours * 3600000
        rows = db.rows_to_list(conn.execute(
            "SELECT ts_ms,on_potential_v,off_potential_v,output_current_a FROM cathodic_data "
            "WHERE pile_id=? AND ts_ms>=? ORDER BY ts_ms", (pile_id, since)))
        return {"pile_id": pile_id, "hours": hours, "points": rows}
    finally:
        conn.close()


@router.post("/simulate-data", summary="生成一轮全网测试桩数据（演示）")
def simulate_data(under_pile: int = Query(None, description="强制某桩保护不足（演示）"),
                  over_pile: int = Query(None, description="强制某桩过保护（演示）")):
    """为全部测试桩生成一帧仿真数据（默认围绕 -0.95~-1.05V 正常区间波动）。"""
    import random
    conn = db.get_conn()
    try:
        piles = db.rows_to_list(conn.execute("SELECT * FROM test_piles"))
        ts = int(time.time() * 1000)
        out = []
        for p in piles:
            e_off = random.uniform(-1.08, -0.92)
            if p["id"] == under_pile:
                e_off = random.uniform(-0.78, -0.70)   # 保护不足
            elif p["id"] == over_pile:
                e_off = random.uniform(-1.35, -1.25)   # 过保护
            e_on = e_off - random.uniform(0.05, 0.20)  # 通电电位更负（含 IR 降）
            current = p["rated_current_a"] * random.uniform(0.75, 1.05)
            if p["id"] == under_pile:
                current = p["rated_current_a"] * random.uniform(0.1, 0.25)  # 输出异常
            conn.execute(
                "INSERT INTO cathodic_data(ts_ms,pile_id,on_potential_v,off_potential_v,output_current_a)"
                " VALUES(?,?,?,?,?)", (ts, p["id"], round(e_on, 3), round(e_off, 3), round(current, 2)))
            out.append({"pile_id": p["id"], "off_potential_v": round(e_off, 3)})
        conn.commit()
        return {"ok": True, "ts_ms": ts, "generated": out}
    finally:
        conn.close()
