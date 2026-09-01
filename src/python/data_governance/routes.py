#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据治理与中台服务子模块 - API路由

前缀 /governance，tag「数据治理与中台服务」。
覆盖：总览、主数据CRUD、数据标准、质量管控、时空分析、统一API服务。
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from . import simulator
from .models import (
    MasterDataQueryRequest,
    QualityCheckRequest,
    SpatialAnalyzeRequest,
    to_dict,
)

router = APIRouter(prefix="/governance", tags=["数据治理与中台服务"])


# ==============================================================================
# 总览
# ==============================================================================

@router.get("/overview", summary="数据治理总览KPI")
def governance_overview():
    return simulator.get_overview()


# ==============================================================================
# 主数据管理
# ==============================================================================

@router.get("/master/stats", summary="五大主数据统计概览")
def master_stats():
    return {"master_data": simulator.get_master_stats()}


@router.get("/master/{data_type}", summary="主数据列表查询")
def list_master(data_type: str,
                status: Optional[str] = None,
                zone: Optional[str] = None,
                department: Optional[str] = None):
    filters = {}
    if status:
        filters["status"] = status
    if zone:
        filters["zone"] = zone
    if department:
        filters["department"] = department
    try:
        items = simulator.list_master_data(data_type, filters if filters else None)
        return {"data": items, "total": len(items), "type": data_type}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/master/{data_type}/{item_id}", summary="主数据详情")
def get_master_item(data_type: str, item_id: str):
    item = simulator.get_master_item(data_type, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="主数据不存在：%s/%s" % (data_type, item_id))
    return item


# ==============================================================================
# 数据标准体系
# ==============================================================================

@router.get("/standards", summary="数据标准列表")
def list_standards():
    standards = simulator.list_standards()
    return {"standards": standards, "total": len(standards)}


@router.get("/standards/{code}", summary="数据标准详情")
def get_standard(code: str):
    std = simulator.get_standard(code)
    if std is None:
        raise HTTPException(status_code=404, detail="数据标准不存在：%s" % code)
    return std


@router.get("/compliance", summary="数据标准合规检查")
def check_compliance():
    return simulator.check_compliance()


# ==============================================================================
# 数据质量管控
# ==============================================================================

@router.get("/quality/report", summary="数据质量报告")
def quality_report():
    return simulator.get_quality_report()


@router.post("/quality/check", summary="执行数据质量校验")
def run_quality_check(req: QualityCheckRequest = QualityCheckRequest()):
    data = to_dict(req)
    return simulator.run_quality_check(
        data_type=data.get("data_type") or "sensor",
        sample_size=data.get("sample_size") or 1000,
    )


@router.get("/quality/alerts", summary="数据质量告警")
def quality_alerts():
    return {"alerts": simulator.get_quality_alerts()}


# ==============================================================================
# 时空数据引擎
# ==============================================================================

@router.post("/spatial/analyze", summary="时空分析（缓冲区/拓扑/路径/叠加/地理编码）")
def spatial_analyze(req: SpatialAnalyzeRequest):
    data = to_dict(req)
    analyze_type = data.get("analyze_type") or "buffer"
    try:
        return simulator.spatial_analyze(
            analyze_type=analyze_type,
            zone=data.get("zone"),
            radius_m=float(data.get("radius_m") or 100.0),
            layer=data.get("layer"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/spatial/topology", summary="管网拓扑分析")
def topology(zone: Optional[str] = None):
    return simulator.spatial_analyze("topology", zone=zone)


@router.get("/spatial/path", summary="路径分析")
def path_analysis(zone: Optional[str] = None):
    return simulator.spatial_analyze("path", zone=zone)


@router.get("/spatial/buffer", summary="缓冲区分析")
def buffer_analysis(zone: Optional[str] = None, radius_m: float = Query(100.0, ge=10, le=5000)):
    return simulator.spatial_analyze("buffer", zone=zone, radius_m=radius_m)


# ==============================================================================
# 统一数据服务API
# ==============================================================================

@router.get("/api/services", summary="统一数据服务API列表")
def list_api_services(domain: Optional[str] = None):
    services = simulator.list_api_services(domain=domain)
    return {"services": services, "total": len(services)}


@router.get("/api/services/{api_id}", summary="API服务详情")
def get_api_service(api_id: str):
    service = simulator.get_api_service(api_id)
    if service is None:
        raise HTTPException(status_code=404, detail="API服务不存在：%s" % api_id)
    return service


@router.get("/api/stats", summary="API调用统计")
def api_stats():
    return simulator.get_api_stats()


@router.get("/api/audit", summary="API调用审计日志")
def api_audit(limit: int = Query(20, ge=1, le=100)):
    return {"logs": simulator.get_api_audit_logs(limit=limit)}
