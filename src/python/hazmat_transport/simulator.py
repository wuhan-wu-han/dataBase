#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
危废/化学品输送管控子模块 - 模拟引擎

功能：
1. 介质状态监测：实时压力/温度/流量/浓度监测与告警
2. 输送路径合规校验：备案路径比对、改道/违规接驳检测
3. 全流程溯源管理：产生→输送→处置全链条追溯
4. 管段腐蚀余量评估：壁厚监测、剩余寿命预测
5. 环保合规台账：输送/处置/排放报表生成
6. 泄漏应急封堵：多级阀门级联关闭方案
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import (
    HAZMAT_MEDIA,
    now_str,
    seed_compliance_ledger,
    seed_emergency_valves,
    seed_media,
    seed_pipe_segments,
    seed_routes,
    seed_traceability,
)

# ==============================================================================
# 内存数据状态
# ==============================================================================

_state = {
    "media": seed_media(),
    "routes": seed_routes(),
    "traceability": seed_traceability(),
    "pipe_segments": seed_pipe_segments(),
    "compliance_ledger": seed_compliance_ledger(),
    "emergency_valves": seed_emergency_valves(),
    "alerts": [],
    "emergency_logs": [],
}


def _reset_alerts():
    """生成介质监测告警"""
    alerts = []
    for m in _state["media"]:
        if m["status"] == "warning":
            alerts.append({
                "alert_id": "ALT-%s" % m["media_id"],
                "media_id": m["media_id"],
                "media_name": m["name"],
                "hw_code": m["hw_code"],
                "type": "concentration_exceed",
                "severity": "high",
                "message": "%s浓度 %.0f mg/L 超过阈值 %.0f mg/L" % (
                    m["name"], m["concentration_mgL"], m["threshold_concentration"]
                ),
                "source": m["source"],
                "created_at": m["last_sample"],
            })
    if not alerts:
        alerts.append({
            "alert_id": "ALT-OK",
            "media_id": "ALL",
            "media_name": "全部介质",
            "hw_code": "ALL",
            "type": "normal",
            "severity": "info",
            "message": "所有介质监测指标正常",
            "source": "系统",
            "created_at": now_str(),
        })
    _state["alerts"] = alerts


_reset_alerts()


# ==============================================================================
# 总览 KPI
# ==============================================================================

def get_overview() -> Dict[str, Any]:
    media_count = len(_state["media"])
    route_count = len(_state["routes"])
    approved_routes = len([r for r in _state["routes"] if r["status"] == "approved"])
    deviated_routes = len([r for r in _state["routes"] if r["status"] == "deviated"])
    trace_count = len(_state["traceability"])
    completed_traces = len([t for t in _state["traceability"] if t["status"] == "completed"])
    in_transit = len([t for t in _state["traceability"] if t["status"] == "in_transit"])
    segment_count = len(_state["pipe_segments"])
    high_risk_segments = len([s for s in _state["pipe_segments"] if s["risk_level"] == "high"])
    ledger_count = len(_state["compliance_ledger"])
    compliant_count = len([l for l in _state["compliance_ledger"] if l["compliant"]])
    valve_count = len(_state["emergency_valves"])
    alert_valves = len([v for v in _state["emergency_valves"] if v["status"] == "alert"])

    return {
        "media_count": media_count,
        "media_warning_count": len([m for m in _state["media"] if m["status"] == "warning"]),
        "route_count": route_count,
        "approved_routes": approved_routes,
        "deviated_routes": deviated_routes,
        "trace_count": trace_count,
        "completed_traces": completed_traces,
        "in_transit_traces": in_transit,
        "segment_count": segment_count,
        "high_risk_segments": high_risk_segments,
        "ledger_count": ledger_count,
        "compliance_rate": round(compliant_count / ledger_count, 4) if ledger_count > 0 else 0,
        "valve_count": valve_count,
        "alert_valves": alert_valves,
        "alert_count": len([a for a in _state["alerts"] if a["severity"] != "info"]),
        "updated_at": now_str(),
    }


# ==============================================================================
# 介质状态监测
# ==============================================================================

def list_media(hw_code: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
    media = _state["media"]
    if hw_code:
        media = [m for m in media if m["hw_code"] == hw_code]
    if status:
        media = [m for m in media if m["status"] == status]
    return media


def get_media(media_id: str) -> Optional[Dict]:
    for m in _state["media"]:
        if m["media_id"] == media_id:
            return m
    return None


def get_media_alerts() -> List[Dict]:
    return _state["alerts"]


def get_media_stats() -> Dict[str, Any]:
    type_stats = {}
    for m in _state["media"]:
        t = m["media_type"]
        if t not in type_stats:
            type_stats[t] = {"type": t, "name": HAZMAT_MEDIA[t], "count": 0, "warning": 0}
        type_stats[t]["count"] += 1
        if m["status"] == "warning":
            type_stats[t]["warning"] += 1
    return {
        "total": len(_state["media"]),
        "by_type": list(type_stats.values()),
        "updated_at": now_str(),
    }


# ==============================================================================
# 输送路径合规校验
# ==============================================================================

def list_routes(status: Optional[str] = None) -> List[Dict]:
    routes = _state["routes"]
    if status:
        routes = [r for r in routes if r["status"] == status]
    return routes


def get_route(route_id: str) -> Optional[Dict]:
    for r in _state["routes"]:
        if r["route_id"] == route_id:
            return r
    return None


def check_route_compliance(route_id: str, waypoint: Optional[str] = None) -> Dict[str, Any]:
    route = get_route(route_id)
    if route is None:
        return {"error": "路径不存在：%s" % route_id}

    approved_route = None
    for r in _state["routes"]:
        if r["route_id"] != route_id and r["source"] == route["source"] and r["destination"] == route["destination"] and r["status"] == "approved":
            approved_route = r
            break

    if route["status"] == "approved":
        return {
            "route_id": route_id,
            "status": "approved",
            "compliant": True,
            "message": "路径合规，与备案路径一致",
            "waypoints": route["waypoints"],
            "checked_at": now_str(),
        }

    deviations = []
    if approved_route:
        approved_wp_names = set(wp[0] for wp in approved_route["waypoints"])
        current_wp_names = set(wp[0] for wp in route["waypoints"])
        extra_wps = current_wp_names - approved_wp_names
        for wp_name in extra_wps:
            deviations.append({
                "waypoint": wp_name,
                "type": "unauthorized_connection" if "未备案" in wp_name else "route_deviation",
                "severity": "high",
            })

    return {
        "route_id": route_id,
        "status": route["status"],
        "compliant": len(deviations) == 0,
        "message": "路径合规" if len(deviations) == 0 else "发现 %d 处违规" % len(deviations),
        "deviations": deviations,
        "current_waypoints": route["waypoints"],
        "approved_waypoints": approved_route["waypoints"] if approved_route else [],
        "checked_at": now_str(),
    }


def get_route_stats() -> Dict[str, Any]:
    total = len(_state["routes"])
    approved = len([r for r in _state["routes"] if r["status"] == "approved"])
    deviated = len([r for r in _state["routes"] if r["status"] == "deviated"])
    return {
        "total_routes": total,
        "approved": approved,
        "deviated": deviated,
        "compliance_rate": round(approved / total, 4) if total > 0 else 0,
        "updated_at": now_str(),
    }


# ==============================================================================
# 全流程溯源管理
# ==============================================================================

def list_traceability(hw_code: Optional[str] = None, source: Optional[str] = None,
                      status: Optional[str] = None) -> List[Dict]:
    records = _state["traceability"]
    if hw_code:
        records = [r for r in records if r["hw_code"] == hw_code]
    if source:
        records = [r for r in records if source in r["source"]]
    if status:
        records = [r for r in records if r["status"] == status]
    return records


def get_trace(trace_id: str) -> Optional[Dict]:
    for t in _state["traceability"]:
        if t["trace_id"] == trace_id:
            return t
    return None


def get_trace_chain(trace_id: str) -> Dict[str, Any]:
    trace = get_trace(trace_id)
    if trace is None:
        return {"error": "溯源记录不存在：%s" % trace_id}

    chain = [
        {"step": 1, "stage": "产生", "location": trace["source"], "time": trace["generate_time"], "status": "completed"},
    ]
    if trace["dispatch_time"]:
        chain.append({"step": 2, "stage": "启运", "location": trace["source"], "time": trace["dispatch_time"], "status": "completed"})
    if trace["status"] == "in_transit":
        chain.append({"step": 3, "stage": "运输中", "location": "途中", "time": "", "status": "in_progress"})
    if trace["arrive_time"]:
        chain.append({"step": 3 if trace["status"] != "in_transit" else 4, "stage": "到达", "location": trace["destination"], "time": trace["arrive_time"], "status": "completed"})
    if trace["status"] == "completed":
        chain.append({"step": 4 if trace["status"] != "in_transit" else 5, "stage": "处置", "location": trace["destination"], "time": trace["arrive_time"], "status": "completed", "result": trace["disposal_result"]})

    return {
        "trace_id": trace_id,
        "manifest_no": trace["manifest_no"],
        "chain": chain,
        "total_steps": len(chain),
        "current_status": trace["status"],
    }


def get_trace_stats() -> Dict[str, Any]:
    total = len(_state["traceability"])
    by_status = {}
    for t in _state["traceability"]:
        s = t["status"]
        by_status[s] = by_status.get(s, 0) + 1
    total_volume = sum(t["volume_m3"] for t in _state["traceability"])
    return {
        "total_traces": total,
        "by_status": by_status,
        "total_volume_m3": round(total_volume, 2),
        "updated_at": now_str(),
    }


# ==============================================================================
# 管段腐蚀余量评估
# ==============================================================================

def list_pipe_segments(route_id: Optional[str] = None, risk_level: Optional[str] = None) -> List[Dict]:
    segments = _state["pipe_segments"]
    if route_id:
        segments = [s for s in segments if s["route_id"] == route_id]
    if risk_level:
        segments = [s for s in segments if s["risk_level"] == risk_level]
    return segments


def get_segment(segment_id: str) -> Optional[Dict]:
    for s in _state["pipe_segments"]:
        if s["segment_id"] == segment_id:
            return s
    return None


def evaluate_corrosion(segment_id: Optional[str] = None, route_id: Optional[str] = None) -> Dict[str, Any]:
    segments = _state["pipe_segments"]
    if segment_id:
        segments = [s for s in segments if s["segment_id"] == segment_id]
    if route_id:
        segments = [s for s in segments if s["route_id"] == route_id]

    if not segments:
        return {"error": "未找到管段数据"}

    high_risk = [s for s in segments if s["risk_level"] == "high"]
    medium_risk = [s for s in segments if s["risk_level"] == "medium"]
    low_risk = [s for s in segments if s["risk_level"] == "low"]

    avg_remaining_life = round(sum(s["remaining_life_years"] for s in segments) / len(segments), 1)
    min_thickness = min(s["current_thickness_mm"] for s in segments)
    min_segment = [s for s in segments if s["current_thickness_mm"] == min_thickness][0]

    return {
        "total_segments": len(segments),
        "high_risk_count": len(high_risk),
        "medium_risk_count": len(medium_risk),
        "low_risk_count": len(low_risk),
        "avg_remaining_life_years": avg_remaining_life,
        "min_thickness_mm": min_thickness,
        "min_thickness_segment": min_segment["segment_id"],
        "min_thickness_location": min_segment["location"],
        "recommendations": _corrosion_recommendations(high_risk, medium_risk),
        "evaluated_at": now_str(),
    }


def _corrosion_recommendations(high_risk: List, medium_risk: List) -> List[str]:
    recs = []
    if high_risk:
        recs.append("【紧急】%d 段管段剩余寿命不足8年，建议立即安排更换" % len(high_risk))
        for s in high_risk[:3]:
            recs.append("  - %s (%s)：剩余 %.1f 年，当前壁厚 %.2f mm" % (
                s["segment_id"], s["location"], s["remaining_life_years"], s["current_thickness_mm"]
            ))
    if medium_risk:
        recs.append("【关注】%d 段管段剩余寿命8-15年，建议纳入年度更换计划" % len(medium_risk))
    if not high_risk and not medium_risk:
        recs.append("所有管段状态良好，按计划巡检即可")
    return recs


def get_corrosion_stats() -> Dict[str, Any]:
    segments = _state["pipe_segments"]
    by_route = {}
    for s in segments:
        r = s["route_id"]
        if r not in by_route:
            by_route[r] = {"route_id": r, "segment_count": 0, "high_risk": 0, "avg_life": 0}
        by_route[r]["segment_count"] += 1
        if s["risk_level"] == "high":
            by_route[r]["high_risk"] += 1
        by_route[r]["avg_life"] += s["remaining_life_years"]
    for r in by_route:
        by_route[r]["avg_life"] = round(by_route[r]["avg_life"] / by_route[r]["segment_count"], 1)

    return {
        "total_segments": len(segments),
        "by_route": list(by_route.values()),
        "updated_at": now_str(),
    }


# ==============================================================================
# 环保合规台账
# ==============================================================================

def list_ledger(category: Optional[str] = None, factory: Optional[str] = None) -> List[Dict]:
    ledger = _state["compliance_ledger"]
    if category:
        ledger = [l for l in ledger if l["category"] == category]
    if factory:
        ledger = [l for l in ledger if l["factory"] == factory]
    return ledger


def get_ledger_stats() -> Dict[str, Any]:
    ledger = _state["compliance_ledger"]
    total = len(ledger)
    compliant = len([l for l in ledger if l["compliant"]])
    by_category = {}
    for l in ledger:
        c = l["category"]
        if c not in by_category:
            by_category[c] = {"category": c, "name": l["category_name"], "total": 0, "compliant": 0}
        by_category[c]["total"] += 1
        if l["compliant"]:
            by_category[c]["compliant"] += 1
    for c in by_category:
        by_category[c]["rate"] = round(by_category[c]["compliant"] / by_category[c]["total"], 4)

    return {
        "total_records": total,
        "compliant_count": compliant,
        "compliance_rate": round(compliant / total, 4) if total > 0 else 0,
        "by_category": list(by_category.values()),
        "updated_at": now_str(),
    }


def generate_compliance_report(category: Optional[str] = None, factory: Optional[str] = None) -> Dict[str, Any]:
    ledger = list_ledger(category=category, factory=factory)
    total_volume = sum(l["volume_m3"] for l in ledger)
    compliant = len([l for l in ledger if l["compliant"]])
    issues = sum(l["issue_count"] for l in ledger)

    return {
        "report_type": "compliance",
        "category": category or "全部",
        "factory": factory or "全部",
        "record_count": len(ledger),
        "total_volume_m3": round(total_volume, 2),
        "compliant_count": compliant,
        "compliance_rate": round(compliant / len(ledger), 4) if ledger else 0,
        "issue_count": issues,
        "records": ledger,
        "generated_at": now_str(),
    }


# ==============================================================================
# 泄漏应急封堵
# ==============================================================================

def list_valves(route_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
    valves = _state["emergency_valves"]
    if route_id:
        valves = [v for v in valves if v["route_id"] == route_id]
    if status:
        valves = [v for v in valves if v["status"] == status]
    return valves


def get_valve(valve_id: str) -> Optional[Dict]:
    for v in _state["emergency_valves"]:
        if v["valve_id"] == valve_id:
            return v
    return None


def execute_emergency_shutdown(route_id: str, leak_location: Optional[str] = None,
                                severity: str = "medium") -> Dict[str, Any]:
    route_valves = [v for v in _state["emergency_valves"] if v["route_id"] == route_id]
    if not route_valves:
        return {"error": "路径 %s 无应急阀门" % route_id}

    route_valves.sort(key=lambda x: x["cascade_level"])

    if severity == "high":
        close_valves = route_valves
    elif severity == "medium":
        close_valves = [v for v in route_valves if v["cascade_level"] <= 2]
    else:
        close_valves = [v for v in route_valves if v["cascade_level"] == 1]

    actions = []
    total_response_time = 0
    for v in close_valves:
        actions.append({
            "valve_id": v["valve_id"],
            "location": v["location"],
            "cascade_level": v["cascade_level"],
            "action": "close",
            "response_time_sec": v["response_time_sec"],
            "status": "executed",
        })
        total_response_time += v["response_time_sec"]

    log = {
        "log_id": "EMG-%04d" % (len(_state["emergency_logs"]) + 1),
        "route_id": route_id,
        "leak_location": leak_location or "未知",
        "severity": severity,
        "valves_closed": len(actions),
        "total_response_time_sec": round(total_response_time, 1),
        "actions": actions,
        "notified_departments": _notify_departments(severity),
        "executed_at": now_str(),
    }
    _state["emergency_logs"].append(log)

    return log


def _notify_departments(severity: str) -> List[str]:
    depts = ["监控中心", "应急指挥办公室"]
    if severity in ("medium", "high"):
        depts.extend(["环保部门", "抢修队"])
    if severity == "high":
        depts.extend(["公安部门", "消防救援"])
    return depts


def get_emergency_stats() -> Dict[str, Any]:
    valves = _state["emergency_valves"]
    total = len(valves)
    normal = len([v for v in valves if v["status"] == "normal"])
    alert = len([v for v in valves if v["status"] == "alert"])
    auto_close = len([v for v in valves if v["auto_close"]])

    return {
        "total_valves": total,
        "normal_count": normal,
        "alert_count": alert,
        "auto_close_count": auto_close,
        "emergency_logs_count": len(_state["emergency_logs"]),
        "updated_at": now_str(),
    }
