#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工单全流程管理子模块 - API路由

前缀 /workorder，tag「工单全流程管理」。
覆盖：总览、多渠道接入、智能派单、过程跟踪、时效管控。
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from . import simulator
from .models import (
    CHANNELS,
    ORDER_CATEGORIES,
    DispatchAssignRequest,
    OrderCreateRequest,
    OrderQueryRequest,
    OrderUpdateRequest,
    ProcessAdvanceRequest,
    to_dict,
)

router = APIRouter(prefix="/workorder", tags=["工单全流程管理"])


# ==============================================================================
# 总览
# ==============================================================================

@router.get("/overview", summary="工单管理总览KPI")
def workorder_overview():
    return simulator.get_overview()


# ==============================================================================
# 工单管理（多渠道接入）
# ==============================================================================

@router.get("/orders", summary="工单列表查询（支持过滤 + 分页）")
def list_orders(channel: Optional[str] = None,
                status: Optional[str] = None,
                priority: Optional[str] = None,
                location: Optional[str] = None,
                page: int = Query(1, ge=1),
                page_size: int = Query(0, ge=0, le=1000)):
    filters = {}
    if channel:
        filters["channel"] = channel
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if location:
        filters["location"] = location
    return simulator.query_orders(filters if filters else None,
                                  page=page, page_size=page_size)


@router.get("/orders/stats", summary="工单统计（渠道/状态/优先级/趋势）")
def order_stats():
    return simulator.get_order_stats()


@router.get("/orders/channels", summary="接入渠道定义")
def list_channels():
    return {"channels": [{"key": k, **v} for k, v in CHANNELS.items()],
            "categories": [{"key": k, **v} for k, v in ORDER_CATEGORIES.items()]}


@router.post("/orders", summary="新建工单（携带 order_id 时视为编辑）")
def create_order(req: OrderCreateRequest):
    data = to_dict(req)
    try:
        if data.get("order_id"):
            return simulator.update_order(data["order_id"], data)
        return simulator.create_order(
            title=data.get("title") or "",
            channel=data.get("channel") or "user",
            category=data.get("category") or "electrical",
            priority=data.get("priority") or "medium",
            location=data.get("location"),
            description=data.get("description"),
            reporter=data.get("reporter"),
            sla_hours=data.get("sla_hours"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.put("/orders/{order_id}", summary="编辑工单")
def update_order(order_id: str, req: OrderUpdateRequest):
    try:
        return simulator.update_order(order_id, to_dict(req))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.delete("/orders/{order_id}", summary="删除工单")
def delete_order(order_id: str):
    try:
        simulator.delete_order(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"success": True, "code": 200, "message": "工单已删除", "order_id": order_id}


@router.get("/orders/{order_id}", summary="工单详情")
def get_order(order_id: str):
    order = simulator.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="工单不存在：%s" % order_id)
    return order


# ==============================================================================
# 智能派单
# ==============================================================================

@router.get("/dispatch/recommend", summary="智能派单推荐")
def dispatch_recommend(order_id: Optional[str] = None,
                       required_skill: Optional[str] = None,
                       location: Optional[str] = None):
    try:
        return simulator.recommend_dispatch(
            order_id=order_id, required_skill=required_skill, location=location)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/dispatch/assign", summary="派单确认")
def dispatch_assign(req: DispatchAssignRequest):
    data = to_dict(req)
    try:
        return simulator.assign_order(data["order_id"], data["staff_id"])
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/dispatch/logs", summary="派单记录")
def dispatch_logs(limit: int = Query(20, ge=1, le=100)):
    return {"logs": simulator.get_dispatch_logs(limit=limit)}


# ==============================================================================
# 运维人员
# ==============================================================================

@router.get("/staff", summary="运维人员列表")
def list_staff(status: Optional[str] = None):
    staff = simulator.list_staff(status=status)
    return {"staff": staff, "total": len(staff)}


@router.get("/staff/workload", summary="人员工作负载")
def staff_workload():
    return {"workload": simulator.get_staff_workload()}


@router.get("/staff/{staff_id}", summary="人员详情")
def get_staff(staff_id: str):
    staff = simulator.get_staff(staff_id)
    if staff is None:
        raise HTTPException(status_code=404, detail="运维人员不存在：%s" % staff_id)
    return staff


# ==============================================================================
# 过程跟踪
# ==============================================================================

@router.get("/process/{order_id}", summary="工单处置过程时间线")
def get_process(order_id: str):
    try:
        return simulator.get_process(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/process/advance", summary="推进流程节点")
def advance_process(req: ProcessAdvanceRequest):
    data = to_dict(req)
    try:
        return simulator.advance_process(
            order_id=data["order_id"],
            step=data["step"],
            note=data.get("note"),
            rating=data.get("rating"),
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ==============================================================================
# 时效管控（SLA）
# ==============================================================================

@router.get("/sla/rules", summary="时效管控规则")
def sla_rules():
    return {"rules": simulator.list_sla_rules()}


@router.get("/sla/monitor", summary="SLA实时监控")
def sla_monitor():
    return simulator.sla_monitor()


@router.post("/sla/escalate", summary="超期工单升级督办")
def sla_escalate(order_id: str):
    try:
        return simulator.escalate_order(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
