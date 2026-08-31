# -*- coding: utf-8 -*-
"""
功能 4：第三方破坏预警
======================
识别管道周边的施工机械振动、违规开挖、重型车辆、钻探/爆破等扰动，
依据《石油天然气管道保护法》式的分区距离规则进行分级告警：

    距管中心线 < 5m   —— 管道保护范围内禁止机械开挖/钻探/爆破 → 严重
    5m ~ 20m          —— 控制作业区，需审批与旁站监护           → 预警
    20m ~ 50m         —— 安全控制区，纳入观察                    → 关注
事件类型权重（违规开挖、爆破等升级）与扰动强度参与评分。
"""
import random
import time

from fastapi import APIRouter, Query

import database as db
from models import ThirdPartyEventReq

router = APIRouter(prefix="/api/third-party", tags=["4.第三方破坏预警"])

# 事件类型权重：越高表示对管道威胁越大
TYPE_WEIGHT = {
    "机械施工振动": 1.0,
    "违规开挖": 1.3,
    "重型车辆通行": 0.6,
    "钻探作业": 1.1,
    "爆破作业": 1.6,
}

PROTECT_M = 5.0    # 管道保护范围
CONTROL_M = 20.0   # 控制作业区
SAFE_M = 50.0      # 安全控制区


def _grade(req_like: dict) -> dict:
    """
    分级评估：先按距离分区定基础级别，再结合类型权重与扰动强度评分微调。
    返回 {level, score, distance_rule, suggestion}
    """
    dist = req_like["lateral_m"]
    w = TYPE_WEIGHT.get(req_like["event_type"], 1.0)
    intensity = req_like.get("intensity", 5.0)
    # 评分：强度 × 类型权重 × 距离衰减（越近分越高）
    decay = PROTECT_M / max(dist, 0.5) if dist < SAFE_M else 0.05
    score = round(min(100.0, intensity * 8 * w * decay), 1)

    if dist < PROTECT_M:
        level = "severe"
        rule = f"侵入管道保护范围（<{PROTECT_M:.0f}m），属禁止作业行为"
        suggestion = "立即责令停工，派员现场监护，必要时启动应急关阀预案"
        # 违规开挖/爆破在保护范围内直接顶格
        if req_like["event_type"] in ("违规开挖", "爆破作业"):
            score = 100.0
    elif dist < CONTROL_M:
        level = "severe" if (w >= 1.3 and intensity >= 7) else "warning"
        rule = f"位于控制作业区（{PROTECT_M:.0f}~{CONTROL_M:.0f}m），需审批与旁站监护"
        suggestion = "核查施工许可，安排巡线员旁站监护，向施工方交底管道位置"
    elif dist < SAFE_M:
        level = "warning" if intensity >= 8 else "notice"
        rule = f"位于安全控制区（{CONTROL_M:.0f}~{SAFE_M:.0f}m）"
        suggestion = "纳入日常巡线重点，登记施工单位信息"
    else:
        level = "notice"
        rule = f"超出安全控制区（>{SAFE_M:.0f}m）"
        suggestion = "常规观察"
    return {"level": level, "score": score, "distance_rule": rule, "suggestion": suggestion}


@router.post("/event", summary="上报周边施工/扰动事件")
def report_event(req: ThirdPartyEventReq):
    """
    上报一起第三方事件（可由光纤振动预警系统、无人机巡检或人工上报触发），
    服务端立即做安全距离越界判定并生成告警级别。
    """
    g = _grade(req.model_dump())
    ts = int(time.time() * 1000)
    conn = db.get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO third_party_events(ts_ms,event_type,location_km,lateral_m,intensity,"
            "description,level,score) VALUES(?,?,?,?,?,?,?,?)",
            (ts, req.event_type, req.location_km, req.lateral_m, req.intensity,
             req.description, g["level"], g["score"]))
        conn.commit()
        eid = cur.lastrowid
    finally:
        conn.close()
    return {"event_id": eid, "ts_ms": ts, **g, "event": req.model_dump()}


@router.post("/simulate", summary="随机生成一起施工事件（演示）")
def simulate_event():
    """随机桩号、随机距离与类型，模拟一次第三方施工扰动上报。"""
    req = ThirdPartyEventReq(
        event_type=random.choice(list(TYPE_WEIGHT.keys())),
        location_km=round(random.uniform(0, 50), 1),
        lateral_m=round(random.choice([2, 4, 8, 15, 30, 60]) + random.uniform(-1, 1), 1),
        intensity=round(random.uniform(3, 10), 1),
        description="模拟事件：光纤振动监测系统自动上报",
    )
    return report_event(req)


@router.get("/warnings", summary="当前告警列表（按风险排序）")
def warnings(limit: int = Query(50, ge=1, le=200)):
    """最近事件及其告警级别，按评分降序排列，用于预警大屏。"""
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT * FROM third_party_events ORDER BY score DESC, ts_ms DESC LIMIT ?", (limit,)))
        for r in rows:
            r["distance_rule"] = _grade(r)["distance_rule"]
        summary = {
            "severe": sum(1 for r in rows if r["level"] == "severe"),
            "warning": sum(1 for r in rows if r["level"] == "warning"),
            "notice": sum(1 for r in rows if r["level"] == "notice"),
        }
        return {"summary": summary, "events": rows}
    finally:
        conn.close()


@router.get("/realtime", summary="沿线扰动态势（分段统计）")
def realtime_status():
    """
    将管线按 5km 分段统计最近 24 小时内的扰动事件，
    返回各段风险值，供态势图着色。
    """
    conn = db.get_conn()
    try:
        since = int(time.time() * 1000) - 86400000
        rows = conn.execute(
            "SELECT location_km, MAX(score) max_score, COUNT(*) n FROM third_party_events "
            "WHERE ts_ms>=? GROUP BY CAST(location_km/5 AS INT)", (since,)).fetchall()
        segs = [{"segment_km": f"{int(r['location_km']//5)*5}-{int(r['location_km']//5)*5+5}",
                 "max_score": r["max_score"], "event_count": r["n"]} for r in rows]
        return {"segments": sorted(segs, key=lambda s: s["segment_km"])}
    finally:
        conn.close()
