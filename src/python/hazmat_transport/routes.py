#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
危废/化学品输送管控子模块 - API路由

前缀 /hazmat，tag「危废/化学品输送管控」。
覆盖：总览、介质监测、路径合规、溯源管理、腐蚀评估、合规台账、应急封堵。
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from . import simulator
from .models import (
    ComplianceReportRequest,
    CorrosionEvalRequest,
    EmergencyActionRequest,
    RouteCheckRequest,
    TraceQueryRequest,
    to_dict,
)

router = APIRouter(prefix="/hazmat", tags=["危废/化学品输送管控"])


# ==============================================================================
# 总览
# ==============================================================================

@router.get("/overview", summary="危废输送管控总览KPI")
def hazmat_overview():
    return simulator.get_overview()


# ==============================================================================
# 介质状态监测
# ==============================================================================

@router.get("/media", summary="危废介质列表")
def list_media(hw_code: Optional[str] = None, status: Optional[str] = None):
    media = simulator.list_media(hw_code=hw_code, status=status)
    return {"media": media, "total": len(media)}


@router.get("/media/{media_id}", summary="介质监测详情")
def get_media(media_id: str):
    media = simulator.get_media(media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="介质不存在：%s" % media_id)
    return media


@router.get("/media/alerts", summary="介质监测告警")
def media_alerts():
    return {"alerts": simulator.get_media_alerts()}


@router.get("/media/stats", summary="介质分类统计")
def media_stats():
    return simulator.get_media_stats()


# ==============================================================================
# 输送路径合规校验
# ==============================================================================

@router.get("/routes", summary="输送路径列表")
def list_routes(status: Optional[str] = None):
    routes = simulator.list_routes(status=status)
    return {"routes": routes, "total": len(routes)}


@router.get("/routes/{route_id}", summary="路径详情")
def get_route(route_id: str):
    route = simulator.get_route(route_id)
    if route is None:
        raise HTTPException(status_code=404, detail="路径不存在：%s" % route_id)
    return route


@router.post("/routes/check", summary="路径合规校验")
def check_route(req: RouteCheckRequest):
    data = to_dict(req)
    return simulator.check_route_compliance(
        route_id=data["route_id"],
        waypoint=data.get("waypoint"),
    )


@router.get("/routes/stats", summary="路径合规统计")
def route_stats():
    return simulator.get_route_stats()


# ==============================================================================
# 全流程溯源管理
# ==============================================================================

@router.get("/trace", summary="溯源记录列表")
def list_trace(hw_code: Optional[str] = None, source: Optional[str] = None,
               status: Optional[str] = None):
    records = simulator.list_traceability(hw_code=hw_code, source=source, status=status)
    return {"traces": records, "total": len(records)}


@router.get("/trace/{trace_id}", summary="溯源记录详情")
def get_trace(trace_id: str):
    trace = simulator.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="溯源记录不存在：%s" % trace_id)
    return trace


@router.get("/trace/{trace_id}/chain", summary="溯源全链条")
def get_trace_chain(trace_id: str):
    return simulator.get_trace_chain(trace_id)


@router.get("/trace/stats", summary="溯源统计")
def trace_stats():
    return simulator.get_trace_stats()


# ==============================================================================
# 管段腐蚀余量评估
# ==============================================================================

@router.get("/segments", summary="管段列表")
def list_segments(route_id: Optional[str] = None, risk_level: Optional[str] = None):
    segments = simulator.list_pipe_segments(route_id=route_id, risk_level=risk_level)
    return {"segments": segments, "total": len(segments)}


@router.get("/segments/{segment_id}", summary="管段详情")
def get_segment(segment_id: str):
    segment = simulator.get_segment(segment_id)
    if segment is None:
        raise HTTPException(status_code=404, detail="管段不存在：%s" % segment_id)
    return segment


@router.post("/segments/evaluate", summary="腐蚀评估")
def evaluate_corrosion(req: CorrosionEvalRequest = CorrosionEvalRequest()):
    data = to_dict(req)
    return simulator.evaluate_corrosion(
        segment_id=data.get("segment_id"),
        route_id=data.get("route_id"),
    )


@router.get("/segments/stats", summary="腐蚀统计")
def corrosion_stats():
    return simulator.get_corrosion_stats()


# ==============================================================================
# 环保合规台账
# ==============================================================================

@router.get("/ledger", summary="合规台账列表")
def list_ledger(category: Optional[str] = None, factory: Optional[str] = None):
    ledger = simulator.list_ledger(category=category, factory=factory)
    return {"ledger": ledger, "total": len(ledger)}


@router.get("/ledger/stats", summary="合规台账统计")
def ledger_stats():
    return simulator.get_ledger_stats()


@router.post("/ledger/report", summary="生成合规报表")
def generate_report(req: ComplianceReportRequest = ComplianceReportRequest()):
    data = to_dict(req)
    return simulator.generate_compliance_report(
        category=data.get("category"),
        factory=data.get("factory"),
    )


# ==============================================================================
# 泄漏应急封堵
# ==============================================================================

@router.get("/valves", summary="应急阀门列表")
def list_valves(route_id: Optional[str] = None, status: Optional[str] = None):
    valves = simulator.list_valves(route_id=route_id, status=status)
    return {"valves": valves, "total": len(valves)}


@router.get("/valves/{valve_id}", summary="阀门详情")
def get_valve(valve_id: str):
    valve = simulator.get_valve(valve_id)
    if valve is None:
        raise HTTPException(status_code=404, detail="阀门不存在：%s" % valve_id)
    return valve


@router.post("/emergency/shutdown", summary="执行泄漏应急封堵")
def emergency_shutdown(req: EmergencyActionRequest):
    data = to_dict(req)
    return simulator.execute_emergency_shutdown(
        route_id=data["route_id"],
        leak_location=data.get("leak_location"),
        severity=data.get("severity", "medium"),
    )


@router.get("/emergency/stats", summary="应急阀门统计")
def emergency_stats():
    return simulator.get_emergency_stats()
