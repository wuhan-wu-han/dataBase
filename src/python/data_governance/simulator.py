#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据治理与中台服务子模块 - 模拟引擎

功能：
1. 主数据管理：五大主数据统一查询与管理
2. 数据质量管控：完整性/准确性/时效性/一致性校验，质量评分
3. 时空数据引擎：拓扑计算、路径分析、缓冲区分析
4. 统一数据服务API：调用统计、流量控制、审计日志
"""

import random
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np

from .models import (
    DATA_STANDARDS,
    PIPELINE_TYPES,
    QUALITY_RULES,
    now_str,
    seed_api_services,
    seed_equipment,
    seed_geo_spaces,
    seed_organizations,
    seed_personnel,
    seed_pipelines,
)

# ==============================================================================
# 内存数据状态
# ==============================================================================

_state = {
    "pipelines": seed_pipelines(),
    "equipment": seed_equipment(),
    "personnel": seed_personnel(),
    "organizations": seed_organizations(),
    "geo_spaces": seed_geo_spaces(),
    "api_services": seed_api_services(),
    "quality_reports": [],
    "audit_logs": [],
    "spatial_cache": {},
    # 风险研判持久化集合（SQLite 读写后合并）
    "risks": [],
}


def _init_db():
    """初始化数据库并加载风险研判数据"""
    try:
        from . import store as _store
        _store.init_db()
        if not _has_risks():
            # 空库则注入少量种子
            _store.create_risk({
                "risk_name": "燃气管线老旧腐蚀", "risk_level": "高",
                "risk_type": "燃气", "location": "Z01区段主干管",
                "description": "DN300 PE管线敷设超5年，存在腐蚀风险",
                "status": "active",
            })
            _store.create_risk({
                "risk_name": "电力电缆过载预警", "risk_level": "中",
                "risk_type": "电力", "location": "Z02区段",
                "description": "10kV电缆负荷率接近85%，需关注",
                "status": "active",
            })
            _store.create_risk({
                "risk_name": "排水系统汛期承压", "risk_level": "低",
                "risk_type": "排水", "location": "Z03区段",
                "description": "雨水排水管DN500，历史积水点",
                "status": "active",
            })
        _load_risks(_store)
    except Exception as exc:
        print("[data_governance] DB 初始化失败：%s" % exc)


def _load_risks(_store):
    res = _store.load_risks(page=1, page_size=9999)
    _state["risks"] = res.get("data", [])


def _has_risks():
    db = None
    try:
        from persistence import SessionLocal
        from persistence.risk_analysis_tables import RiskAnalysis
        db = SessionLocal()
        count = db.query(RiskAnalysis).count()
        return count > 0
    except Exception:
        return False
    finally:
        if db:
            db.close()


_init_db()


def _reset_quality_reports():
    """生成数据质量报告"""
    reports = []
    for code, rule in QUALITY_RULES.items():
        score = round(random.uniform(0.88, 0.99), 4)
        reports.append({
            "rule_code": code,
            "rule_name": rule["name"],
            "score": score,
            "threshold": rule["threshold"],
            "passed": score >= rule["threshold"],
            "checked_at": now_str(),
            "sample_size": random.randint(5000, 50000),
            "error_count": random.randint(0, 50) if score < 0.95 else random.randint(0, 5),
        })
    _state["quality_reports"] = reports


_reset_quality_reports()


# ==============================================================================
# 总览 KPI
# ==============================================================================

def get_overview() -> Dict[str, Any]:
    total_master = (
        len(_state["pipelines"])
        + len(_state["equipment"])
        + len(_state["personnel"])
        + len(_state["organizations"])
        + len(_state["geo_spaces"])
    )
    api_total_calls = sum(s["call_count_24h"] for s in _state["api_services"])
    quality_scores = [r["score"] for r in _state["quality_reports"]]
    avg_quality = round(sum(quality_scores) / len(quality_scores), 4) if quality_scores else 0

    return {
        "total_master_data": total_master,
        "pipeline_count": len(_state["pipelines"]),
        "equipment_count": len(_state["equipment"]),
        "personnel_count": len(_state["personnel"]),
        "organization_count": len(_state["organizations"]),
        "geo_space_count": len(_state["geo_spaces"]),
        "data_standards_count": len(DATA_STANDARDS),
        "quality_rules_count": len(QUALITY_RULES),
        "avg_quality_score": avg_quality,
        "quality_passed": all(r["passed"] for r in _state["quality_reports"]),
        "api_services_count": len(_state["api_services"]),
        "api_total_calls_24h": api_total_calls,
        "api_avg_response_ms": round(
            sum(s["avg_response_ms"] for s in _state["api_services"]) / len(_state["api_services"]), 1
        ),
        "updated_at": now_str(),
    }


# ==============================================================================
# 主数据管理
# ==============================================================================

MASTER_DATA_TYPES = {
    "pipeline": ("pipelines", "pipeline_id"),
    "equipment": ("equipment", "equipment_id"),
    "personnel": ("personnel", "person_id"),
    "organization": ("organizations", "org_id"),
    "geo_space": ("geo_spaces", "geo_id"),
}


def list_master_data(data_type: str, filters: Optional[Dict] = None) -> List[Dict]:
    if data_type not in MASTER_DATA_TYPES:
        raise ValueError("未知主数据类型：%s" % data_type)
    collection, _ = MASTER_DATA_TYPES[data_type]
    data = _state[collection]
    if filters:
        for key, val in filters.items():
            data = [d for d in data if str(d.get(key, "")).lower() == str(val).lower()]
    return data


def get_master_item(data_type: str, item_id: str) -> Optional[Dict]:
    if data_type not in MASTER_DATA_TYPES:
        raise ValueError("未知主数据类型：%s" % data_type)
    collection, id_field = MASTER_DATA_TYPES[data_type]
    for item in _state[collection]:
        if item[id_field] == item_id:
            return item
    return None


def get_master_stats() -> List[Dict]:
    return [
        {"type": "pipeline", "name": "管网", "count": len(_state["pipelines"]),
         "subtypes": len(PIPELINE_TYPES), "icon": "pipeline"},
        {"type": "equipment", "name": "设备", "count": len(_state["equipment"]),
         "subtypes": len(set(e["name"] for e in _state["equipment"])), "icon": "equipment"},
        {"type": "personnel", "name": "人员", "count": len(_state["personnel"]),
         "subtypes": len(set(p["department"] for p in _state["personnel"])), "icon": "personnel"},
        {"type": "organization", "name": "组织机构", "count": len(_state["organizations"]),
         "subtypes": 2, "icon": "organization"},
        {"type": "geo_space", "name": "地理空间", "count": len(_state["geo_spaces"]),
         "subtypes": len(set(g["type"] for g in _state["geo_spaces"])), "icon": "geo"},
    ]


# ==============================================================================
# 数据标准体系
# ==============================================================================

def list_standards() -> List[Dict]:
    return list(DATA_STANDARDS.values())


def get_standard(code: str) -> Optional[Dict]:
    return DATA_STANDARDS.get(code.upper())


# ==============================================================================
# 数据质量管控
# ==============================================================================

def get_quality_report() -> Dict[str, Any]:
    scores = [r["score"] for r in _state["quality_reports"]]
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0
    return {
        "overall_score": avg_score,
        "overall_level": _score_level(avg_score),
        "rules": _state["quality_reports"],
        "checked_at": now_str(),
        "trend_7d": _quality_trend(),
    }


def run_quality_check(data_type: str = "sensor", sample_size: int = 1000) -> Dict[str, Any]:
    _reset_quality_reports()
    for report in _state["quality_reports"]:
        report["checked_at"] = now_str()
        report["sample_size"] = sample_size
    scores = [r["score"] for r in _state["quality_reports"]]
    avg_score = round(sum(scores) / len(scores), 4)
    return {
        "status": "completed",
        "data_type": data_type,
        "sample_size": sample_size,
        "overall_score": avg_score,
        "overall_level": _score_level(avg_score),
        "rules": _state["quality_reports"],
        "checked_at": now_str(),
    }


def _score_level(score: float) -> str:
    if score >= 0.95:
        return "优秀"
    if score >= 0.90:
        return "良好"
    if score >= 0.80:
        return "一般"
    return "需改进"


def _quality_trend() -> List[Dict]:
    trend = []
    for i in range(7):
        day = datetime.now() - timedelta(days=6 - i)
        trend.append({
            "date": day.strftime("%m-%d"),
            "score": round(0.90 + random.uniform(-0.03, 0.06), 4),
        })
    return trend


def get_quality_alerts() -> List[Dict]:
    alerts = []
    for report in _state["quality_reports"]:
        if not report["passed"]:
            alerts.append({
                "alert_id": "QA-%s" % report["rule_code"],
                "rule_code": report["rule_code"],
                "rule_name": report["rule_name"],
                "severity": "high" if report["score"] < 0.85 else "medium",
                "message": "%s得分 %.2f 低于阈值 %.2f" % (
                    report["rule_name"], report["score"], report["threshold"]
                ),
                "created_at": report["checked_at"],
            })
    if not alerts:
        alerts.append({
            "alert_id": "QA-OK",
            "rule_code": "ALL",
            "rule_name": "全部规则",
            "severity": "info",
            "message": "数据质量全部达标，无异常告警",
            "created_at": now_str(),
        })
    return alerts


# ==============================================================================
# 时空数据引擎
# ==============================================================================

def spatial_analyze(analyze_type: str, zone: Optional[str] = None,
                    radius_m: float = 100.0, layer: Optional[str] = None) -> Dict[str, Any]:
    if analyze_type == "buffer":
        return _buffer_analysis(zone, radius_m)
    if analyze_type == "topology":
        return _topology_analysis(zone)
    if analyze_type == "path":
        return _path_analysis(zone)
    if analyze_type == "overlay":
        return _overlay_analysis(zone, layer)
    if analyze_type == "geocode":
        return _geocode_analysis(zone)
    raise ValueError("未知分析类型：%s" % analyze_type)


def _buffer_analysis(zone: Optional[str], radius_m: float) -> Dict[str, Any]:
    target_zones = [z for z in _state["geo_spaces"] if z["type"] == "zone"]
    if zone:
        target_zones = [z for z in target_zones if zone in z.get("name", "")]
    affected_pipelines = []
    for pl in _state["pipelines"]:
        if zone is None or pl["zone"] in [z.get("name", "") for z in target_zones]:
            affected_pipelines.append(pl["pipeline_id"])
    affected_equipment = []
    for eq in _state["equipment"]:
        loc_zone = eq["location"].split("-")[0] if "-" in eq["location"] else eq["location"]
        if zone is None or loc_zone in [z.get("name", "") for z in target_zones]:
            affected_equipment.append(eq["equipment_id"])
    return {
        "analyze_type": "buffer",
        "center_zone": zone or "全部",
        "radius_m": radius_m,
        "affected_pipelines": affected_pipelines,
        "affected_equipment": affected_equipment,
        "affected_count": len(affected_pipelines) + len(affected_equipment),
        "calculated_at": now_str(),
    }


def _topology_analysis(zone: Optional[str]) -> Dict[str, Any]:
    pipelines = _state["pipelines"]
    if zone:
        pipelines = [p for p in pipelines if p["zone"] == zone]
    nodes = set()
    edges = []
    for pl in pipelines:
        start = "%s-START" % pl["pipeline_id"]
        end = "%s-END" % pl["pipeline_id"]
        nodes.add(start)
        nodes.add(end)
        edges.append({"from": start, "to": end, "pipeline_id": pl["pipeline_id"], "length_m": pl["length_m"]})
    return {
        "analyze_type": "topology",
        "zone": zone or "全部",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "total_length_m": sum(e["length_m"] for e in edges),
        "connectivity": "connected" if len(edges) > 0 else "disconnected",
        "edges": edges[:10],
        "calculated_at": now_str(),
    }


def _path_analysis(zone: Optional[str]) -> Dict[str, Any]:
    zones = [z for z in _state["geo_spaces"] if z["type"] == "zone"]
    if len(zones) < 2:
        return {"analyze_type": "path", "path": [], "total_distance_m": 0}
    path = []
    total_dist = 0
    for i, z in enumerate(zones[:3]):
        dist = random.randint(200, 500) if i > 0 else 0
        total_dist += dist
        path.append({
            "seq": i + 1,
            "zone": z["name"],
            "center": z["center"],
            "distance_from_prev_m": dist,
        })
    return {
        "analyze_type": "path",
        "zone": zone or "全部",
        "path": path,
        "total_distance_m": total_dist,
        "calculated_at": now_str(),
    }


def _overlay_analysis(zone: Optional[str], layer: Optional[str]) -> Dict[str, Any]:
    target_layer = layer or "pipeline"
    overlays = []
    for geo in _state["geo_spaces"]:
        if geo["type"] != "zone":
            continue
        if zone and zone not in geo.get("name", ""):
            continue
        count = 0
        if target_layer == "pipeline":
            count = len([p for p in _state["pipelines"] if p["zone"] in geo.get("name", "")])
        elif target_layer == "equipment":
            count = len([e for e in _state["equipment"] if geo["name"][:3] in e.get("location", "")])
        overlays.append({
            "geo_id": geo["geo_id"],
            "geo_name": geo["name"],
            "layer": target_layer,
            "overlap_count": count,
        })
    return {
        "analyze_type": "overlay",
        "zone": zone or "全部",
        "layer": target_layer,
        "overlays": overlays,
        "calculated_at": now_str(),
    }


def _geocode_analysis(zone: Optional[str]) -> Dict[str, Any]:
    results = []
    for geo in _state["geo_spaces"]:
        if zone and zone not in geo.get("name", ""):
            continue
        results.append({
            "geo_id": geo["geo_id"],
            "name": geo["name"],
            "type": geo["type"],
            "center": geo["center"],
            "bbox": geo["bbox"],
            "confidence": round(random.uniform(0.92, 0.99), 3),
        })
    return {
        "analyze_type": "geocode",
        "results": results,
        "total": len(results),
        "calculated_at": now_str(),
    }


# ==============================================================================
# 统一数据服务API管理
# ==============================================================================

def list_api_services(domain: Optional[str] = None) -> List[Dict]:
    services = _state["api_services"]
    if domain:
        services = [s for s in services if s["domain"] == domain]
    return services


def get_api_service(api_id: str) -> Optional[Dict]:
    for s in _state["api_services"]:
        if s["api_id"] == api_id:
            return s
    return None


def get_api_stats() -> Dict[str, Any]:
    services = _state["api_services"]
    total_calls = sum(s["call_count_24h"] for s in services)
    total_qps = sum(s["qps_limit"] for s in services)
    avg_response = round(sum(s["avg_response_ms"] for s in services) / len(services), 1)
    domain_stats = {}
    for s in services:
        d = s["domain"]
        if d not in domain_stats:
            domain_stats[d] = {"domain": d, "api_count": 0, "calls_24h": 0}
        domain_stats[d]["api_count"] += 1
        domain_stats[d]["calls_24h"] += s["call_count_24h"]
    return {
        "total_apis": len(services),
        "total_calls_24h": total_calls,
        "total_qps_limit": total_qps,
        "avg_response_ms": avg_response,
        "domain_stats": list(domain_stats.values()),
        "top_apis": sorted(services, key=lambda x: x["call_count_24h"], reverse=True)[:5],
        "updated_at": now_str(),
    }


def get_api_audit_logs(limit: int = 20) -> List[Dict]:
    if not _state["audit_logs"]:
        _generate_audit_logs(50)
    return _state["audit_logs"][:limit]


def _generate_audit_logs(count: int):
    methods = ["GET", "POST", "PUT", "DELETE"]
    statuses = [200, 200, 200, 200, 201, 400, 401, 403, 404, 500]
    callers = ["dashboard", "mobile_app", "third_party", "admin_console", "batch_job"]
    logs = []
    for i in range(count):
        api = random.choice(_state["api_services"])
        logs.append({
            "log_id": "LOG-%05d" % (i + 1),
            "api_id": api["api_id"],
            "api_name": api["name"],
            "method": random.choice(methods),
            "endpoint": api["endpoint"],
            "caller": random.choice(callers),
            "status_code": random.choice(statuses),
            "response_ms": random.randint(10, 500),
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 1440))).strftime("%Y-%m-%d %H:%M:%S"),
        })
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    _state["audit_logs"] = logs


# ==============================================================================
# 数据标准合规检查
# ==============================================================================

def check_compliance() -> Dict[str, Any]:
    checks = []
    for code, std in DATA_STANDARDS.items():
        compliance = round(random.uniform(0.92, 0.99), 4)
        checks.append({
            "standard_code": code,
            "standard_name": std["name"],
            "compliance_rate": compliance,
            "passed": compliance >= 0.95,
            "sample_count": std["sample_count"],
            "violations": random.randint(0, 20) if compliance < 0.95 else random.randint(0, 3),
        })
    avg_compliance = round(sum(c["compliance_rate"] for c in checks) / len(checks), 4)
    return {
        "overall_compliance": avg_compliance,
        "overall_passed": all(c["passed"] for c in checks),
        "checks": checks,
        "checked_at": now_str(),
    }


# ==============================================================================
# 风险研判 CRUD（持久化）
# ==============================================================================

def list_risks(page: int = 1, page_size: int = 20, keyword: str = "",
               risk_level: str = "", risk_type: str = "", status: str = ""):
    from . import store as _store
    res = _store.load_risks(page=page, page_size=page_size, keyword=keyword,
                            risk_level=risk_level, risk_type=risk_type, status=status)
    # 同时合并到内存中的 risks 列表供 overview 使用
    _load_risks(_store)
    return res


def create_risk(data: Dict) -> Dict:
    from . import store as _store
    result = _store.create_risk(data)
    _load_risks(_store)
    return result


def update_risk(item_id: int, data: Dict) -> Optional[Dict]:
    from . import store as _store
    result = _store.update_risk(item_id, data)
    if result:
        _load_risks(_store)
    return result


def delete_risk(item_id: int) -> bool:
    from . import store as _store
    result = _store.delete_risk(item_id)
    if result:
        _load_risks(_store)
    return result


def change_risk_status(item_id: int, status: str) -> Optional[Dict]:
    from . import store as _store
    result = _store.change_risk_status(item_id, status)
    if result:
        _load_risks(_store)
    return result


def get_risk_item_count() -> int:
    """获取风险研判总数（供 overview 统计用）"""
    try:
        from persistence import SessionLocal
        from persistence.risk_analysis_tables import RiskAnalysis
        db = SessionLocal()
        count = db.query(RiskAnalysis).count()
        db.close()
        return count
    except Exception:
        return len(_state.get("risks", []))
