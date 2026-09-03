#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
危废/化学品输送管控子模块 - API路由

前缀 /hazmat，tag「危废/化学品输送管控」。
覆盖：总览、介质监测CRUD、路径合规CRUD、溯源管理CRUD、腐蚀评估CRUD、合规台账CRUD、应急封堵。
"""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import Optional

from . import simulator
from . import store as hstore
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
# 介质状态监测 CRUD
# ==============================================================================

@router.get("/media", summary="危废介质列表")
def list_media(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hw_code: str = "",
    status: str = "",
):
    res = hstore.list_media(page=page, page_size=page_size,
                                      hw_code=hw_code, status=status)
    return res


@router.post("/media", summary="新增介质监测记录")
def create_media(body: dict):
    return simulator.create_media(body)


@router.put("/media/{media_id}", summary="更新介质监测记录")
def update_media(media_id: str, body: dict):
    result = simulator.update_media(media_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="介质不存在：%s" % media_id)
    return result


@router.delete("/media/{media_id}", summary="删除介质监测记录")
def delete_media(media_id: str):
    if not simulator.delete_media(media_id):
        raise HTTPException(status_code=404, detail="介质不存在：%s" % media_id)
    return {"success": True}


@router.get("/media/alerts", summary="介质监测告警")
def media_alerts():
    return {"alerts": simulator.get_media_alerts()}


@router.get("/media/stats", summary="介质分类统计")
def media_stats():
    return simulator.get_media_stats()


# ==============================================================================
# 输送路径合规校验 CRUD
# ==============================================================================

@router.get("/routes", summary="输送路径列表")
def list_routes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = "",
):
    res = hstore.list_routes(page=page, page_size=page_size, status=status)
    return res


@router.post("/routes", summary="新增输送路径")
def create_route(body: dict):
    return simulator.create_route(body)


@router.put("/routes/{route_id}", summary="更新输送路径")
def update_route(route_id: str, body: dict):
    result = simulator.update_route(route_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="路径不存在：%s" % route_id)
    return result


@router.delete("/routes/{route_id}", summary="删除输送路径")
def delete_route(route_id: str):
    if not simulator.delete_route(route_id):
        raise HTTPException(status_code=404, detail="路径不存在：%s" % route_id)
    return {"success": True}


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
# 全流程溯源管理 CRUD
# ==============================================================================

@router.get("/trace", summary="溯源记录列表")
def list_trace(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hw_code: str = "",
    status: str = "",
):
    res = hstore.list_traces(page=page, page_size=page_size,
                                       hw_code=hw_code, status=status)
    return res


@router.post("/trace", summary="新增溯源记录")
def create_trace(body: dict):
    return simulator.create_trace(body)


@router.delete("/trace/{trace_id}", summary="删除溯源记录")
def delete_trace(trace_id: str):
    if not simulator.delete_trace(trace_id):
        raise HTTPException(status_code=404, detail="溯源记录不存在：%s" % trace_id)
    return {"success": True}


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
# 管段腐蚀余量评估 CRUD
# ==============================================================================

@router.get("/segments", summary="管段列表")
def list_segments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    route_id: str = "",
    risk_level: str = "",
):
    res = hstore.list_segments(page=page, page_size=page_size,
                                         route_id=route_id, risk_level=risk_level)
    return res


@router.post("/segments", summary="新增管段")
def create_segment(body: dict):
    return simulator.create_segment(body)


@router.put("/segments/{segment_id}", summary="更新管段信息")
def update_segment(segment_id: str, body: dict):
    result = simulator.update_segment(segment_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="管段不存在：%s" % segment_id)
    return result


@router.delete("/segments/{segment_id}", summary="删除管段")
def delete_segment(segment_id: str):
    if not simulator.delete_segment(segment_id):
        raise HTTPException(status_code=404, detail="管段不存在：%s" % segment_id)
    return {"success": True}


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
# 环保合规台账 CRUD
# ==============================================================================

@router.get("/ledger", summary="合规台账列表")
def list_ledger(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str = "",
    factory: str = "",
):
    res = hstore.list_ledger(page=page, page_size=page_size,
                                       category=category, factory=factory)
    return res


@router.post("/ledger", summary="新增合规台账记录")
def create_ledger(body: dict):
    return simulator.create_ledger(body)


@router.delete("/ledger/{record_id}", summary="删除合规台账记录")
def delete_ledger(record_id: str):
    if not simulator.delete_ledger(record_id):
        raise HTTPException(status_code=404, detail="台账记录不存在：%s" % record_id)
    return {"success": True}


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
# 泄漏应急封堵 CRUD + 操作
# ==============================================================================

@router.get("/valves", summary="应急阀门列表")
def list_valves(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    route_id: str = "",
    status: str = "",
):
    res = hstore.list_valves(page=page, page_size=page_size,
                                       route_id=route_id, status=status)
    return res


@router.post("/valves", summary="新增应急阀门")
def create_valve(body: dict):
    return simulator.create_valve(body)


@router.put("/valves/{valve_id}", summary="更新应急阀门")
def update_valve(valve_id: str, body: dict):
    result = simulator.update_valve(valve_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="阀门不存在：%s" % valve_id)
    return result


@router.delete("/valves/{valve_id}", summary="删除应急阀门")
def delete_valve(valve_id: str):
    if not simulator.delete_valve(valve_id):
        raise HTTPException(status_code=404, detail="阀门不存在：%s" % valve_id)
    return {"success": True}


@router.get("/valves/{valve_id}", summary="阀门详情")
def get_valve(valve_id: str):
    valve = simulator.get_valve(valve_id)
    if valve is None:
        raise HTTPException(status_code=404, detail="阀门不存在：%s" % valve_id)
    return valve


@router.post("/emergency/shutdown", summary="执行泄漏应急封堵")
def emergency_shutdown(req: EmergencyActionRequest):
    data = to_dict(req)
    return simulator.emergency_shutdown_and_log(
        route_id=data["route_id"],
        leak_location=data.get("leak_location"),
        severity=data.get("severity", "medium"),
    )


@router.get("/emergency/stats", summary="应急阀门统计")
def emergency_stats():
    return simulator.get_emergency_stats()


# ==============================================================================
# Excel 导入/导出（所有数据集合）
# ==============================================================================

def _import_hazmat(rows, create_fn):
    created = []
    for row in rows:
        try:
            create_fn(row)
            created.append(row)
        except Exception:
            pass
    return {"status": "success", "imported": len(created), "total_rows": len(rows)}

@router.get("/media/export", summary="导出介质监测 Excel")
def export_media():
    from common.excel_utils import download_xlsx
    data = hstore.list_media(page=1, page_size=99999)["data"]
    return download_xlsx(data, "hazmat_media.xlsx", "介质监测")

@router.post("/media/import", summary="从 Excel 导入介质监测")
def import_media(file: UploadFile = File(...)):
    content = file.file.read()
    from common.excel_utils import import_from_excel
    parsed = import_from_excel(content)
    return _import_hazmat(parsed["rows"], simulator.create_media)

@router.get("/routes/export", summary="导出输送路径 Excel")
def export_routes():
    from common.excel_utils import download_xlsx
    data = hstore.list_routes(page=1, page_size=99999)["data"]
    return download_xlsx(data, "hazmat_routes.xlsx", "输送路径")

@router.post("/routes/import", summary="从 Excel 导入输送路径")
def import_routes(file: UploadFile = File(...)):
    content = file.file.read()
    from common.excel_utils import import_from_excel
    parsed = import_from_excel(content)
    return _import_hazmat(parsed["rows"], simulator.create_route)

@router.get("/trace/export", summary="导出溯源记录 Excel")
def export_trace():
    from common.excel_utils import download_xlsx
    data = hstore.list_traces(page=1, page_size=99999)["data"]
    return download_xlsx(data, "hazmat_trace.xlsx", "溯源记录")

@router.post("/trace/import", summary="从 Excel 导入溯源记录")
def import_trace(file: UploadFile = File(...)):
    content = file.file.read()
    from common.excel_utils import import_from_excel
    parsed = import_from_excel(content)
    return _import_hazmat(parsed["rows"], simulator.create_trace)

@router.get("/segments/export", summary="导出管段腐蚀 Excel")
def export_segments():
    from common.excel_utils import download_xlsx
    data = hstore.list_segments(page=1, page_size=99999)["data"]
    return download_xlsx(data, "hazmat_segments.xlsx", "管段腐蚀")

@router.post("/segments/import", summary="从 Excel 导入管段腐蚀")
def import_segments(file: UploadFile = File(...)):
    content = file.file.read()
    from common.excel_utils import import_from_excel
    parsed = import_from_excel(content)
    return _import_hazmat(parsed["rows"], simulator.create_segment)

@router.get("/ledger/export", summary="导出合规台账 Excel")
def export_ledger():
    from common.excel_utils import download_xlsx
    data = hstore.list_ledger(page=1, page_size=99999)["data"]
    return download_xlsx(data, "hazmat_ledger.xlsx", "合规台账")

@router.post("/ledger/import", summary="从 Excel 导入合规台账")
def import_ledger(file: UploadFile = File(...)):
    content = file.file.read()
    from common.excel_utils import import_from_excel
    parsed = import_from_excel(content)
    return _import_hazmat(parsed["rows"], simulator.create_ledger)

@router.get("/valves/export", summary="导出应急阀门 Excel")
def export_valves():
    from common.excel_utils import download_xlsx
    data = hstore.list_valves(page=1, page_size=99999)["data"]
    return download_xlsx(data, "hazmat_valves.xlsx", "应急阀门")

@router.post("/valves/import", summary="从 Excel 导入应急阀门")
def import_valves(file: UploadFile = File(...)):
    content = file.file.read()
    from common.excel_utils import import_from_excel
    parsed = import_from_excel(content)
    return _import_hazmat(parsed["rows"], simulator.create_valve)
