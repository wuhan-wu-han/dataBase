#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字化预案管理子模块 - API路由

前缀 /plan，tag「应急预案管理」。
入参校验失败返回 422；资源不存在返回 404；业务规则冲突返回 400。
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from . import simulator
from .models import (
    ActivateRequest,
    DrillRequest,
    FlowNodeRequest,
    MatchRequest,
    PLAN_CATEGORIES,
    PlanCreateRequest,
    PlanUpdateRequest,
    to_dict,
)

router = APIRouter(prefix="/plan", tags=["应急预案管理"])


def _handle_value_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    if "不存在" in message:
        return HTTPException(status_code=404, detail=message)
    return HTTPException(status_code=400, detail=message)


# ==============================================================================
# 总览与目录
# ==============================================================================

@router.get("/overview", summary="预案管理总览KPI")
def plan_overview():
    return simulator.get_overview()


@router.get("/categories", summary="8大类预案目录与统计")
def plan_categories():
    return {"categories": simulator.get_category_stats(), "total": len(PLAN_CATEGORIES)}


# ==============================================================================
# 预案 CRUD
# ==============================================================================

@router.get("/plans", summary="预案列表（可按类别/状态/关键词过滤 + 分页）")
def list_plans(category: Optional[str] = None,
               status: Optional[str] = None,
               keyword: Optional[str] = None,
               page: int = Query(1, ge=1),
               page_size: int = Query(0, ge=0, le=500)):
    if category and category.upper() not in PLAN_CATEGORIES:
        raise HTTPException(status_code=422, detail="未知预案类别：%s" % category)
    if status and status not in ("active", "draft", "deprecated"):
        raise HTTPException(status_code=422, detail="非法状态过滤：%s" % status)
    return simulator.query_plans(category=category, status=status, keyword=keyword,
                                 page=page, page_size=page_size)


@router.post("/plans", summary="新建预案")
def create_plan(req: PlanCreateRequest):
    data = to_dict(req)
    if not (data.get("plan_name") or "").strip():
        raise HTTPException(status_code=422, detail="plan_name 不能为空")
    try:
        return simulator.create_plan(data)
    except ValueError as exc:
        raise _handle_value_error(exc)


@router.get("/plans/{plan_id}", summary="预案详情（含流程节点）")
def get_plan(plan_id: str):
    plan = simulator.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="预案不存在：%s" % plan_id)
    return plan


@router.put("/plans/{plan_id}", summary="修订预案（自动刷新 updated_at）")
def update_plan(plan_id: str, req: PlanUpdateRequest):
    data = {k: v for k, v in to_dict(req).items() if v is not None}
    if not data:
        raise HTTPException(status_code=422, detail="未提供任何待修改字段")
    if "plan_name" in data and not str(data["plan_name"]).strip():
        raise HTTPException(status_code=422, detail="plan_name 不能为空")
    try:
        return simulator.update_plan(plan_id, data)
    except ValueError as exc:
        raise _handle_value_error(exc)


@router.delete("/plans/{plan_id}", summary="删除预案")
def delete_plan(plan_id: str):
    try:
        simulator.delete_plan(plan_id)
    except ValueError as exc:
        raise _handle_value_error(exc)
    return {"message": "预案已删除", "plan_id": plan_id}


# ==============================================================================
# 流程节点
# ==============================================================================

@router.post("/plans/{plan_id}/nodes", summary="新增流程节点")
def add_node(plan_id: str, req: FlowNodeRequest):
    data = to_dict(req)
    if not (data.get("title") or "").strip():
        raise HTTPException(status_code=422, detail="节点 title 不能为空")
    try:
        return simulator.add_flow_node(plan_id, data)
    except ValueError as exc:
        raise _handle_value_error(exc)


@router.put("/plans/{plan_id}/nodes/{node_id}", summary="修订流程节点")
def update_node(plan_id: str, node_id: str, req: FlowNodeRequest):
    data = {k: v for k, v in to_dict(req).items() if v is not None}
    if not data:
        raise HTTPException(status_code=422, detail="未提供任何待修改字段")
    try:
        return simulator.update_flow_node(plan_id, node_id, data)
    except ValueError as exc:
        raise _handle_value_error(exc)


@router.delete("/plans/{plan_id}/nodes/{node_id}", summary="删除流程节点")
def delete_node(plan_id: str, node_id: str):
    try:
        return simulator.delete_flow_node(plan_id, node_id)
    except ValueError as exc:
        raise _handle_value_error(exc)


# ==============================================================================
# 智能匹配
# ==============================================================================

@router.post("/match", summary="手动预案匹配（按类别/指标/告警码+级别+位置）")
def match_plans(req: MatchRequest):
    data = to_dict(req)
    if not (data.get("category") or data.get("metric") or data.get("alarm_code")):
        raise HTTPException(status_code=422, detail="category / metric / alarm_code 至少提供一项")
    top_n = int(data.get("top_n") or 3)
    if not (1 <= top_n <= 10):
        raise HTTPException(status_code=422, detail="top_n 需在 1-10 之间")
    return simulator.run_match(data, top_n=top_n)


@router.get("/match/live", summary="管廊告警实时匹配流")
def match_live(limit: int = Query(20, ge=1, le=50)):
    return {
        "matches": simulator.get_live_matches(limit=limit),
        "tunnel_linked": simulator.get_overview()["tunnel_linked"],
    }


# ==============================================================================
# 演练与激活
# ==============================================================================

@router.post("/drill", summary="发起演练（生成52xxx演练事件并可选激活最优预案）")
def drill(req: DrillRequest):
    data = to_dict(req)
    try:
        return simulator.run_drill(
            category=data.get("category") or "",
            level=int(data.get("level") or 1),
            cabin=data.get("cabin"),
            zone=data.get("zone"),
            description=data.get("description") or "",
            activate_best=bool(data.get("activate_best", True)),
        )
    except ValueError as exc:
        raise _handle_value_error(exc)


@router.post("/activate", summary="激活预案（生成处置实例）")
def activate(req: ActivateRequest):
    data = to_dict(req)
    if not (data.get("plan_id") or "").strip():
        raise HTTPException(status_code=422, detail="plan_id 不能为空")
    try:
        return simulator.activate_plan(
            plan_id=data["plan_id"].strip(),
            alarm_id=data.get("alarm_id"),
            trigger_label=data.get("trigger_label") or "",
        )
    except ValueError as exc:
        raise _handle_value_error(exc)


@router.get("/activations", summary="处置实例列表")
def list_activations(status: Optional[str] = None):
    if status and status not in ("running", "finished"):
        raise HTTPException(status_code=422, detail="非法状态过滤：%s" % status)
    activations = simulator.list_activations(status=status)
    return {"activations": activations, "total": len(activations)}


@router.post("/activations/{activation_id}/nodes/{node_id}/done", summary="推进处置节点")
def node_done(activation_id: str, node_id: str):
    try:
        return simulator.mark_node_done(activation_id, node_id)
    except ValueError as exc:
        raise _handle_value_error(exc)


@router.post("/activations/{activation_id}/finish", summary="完结处置实例")
def finish(activation_id: str):
    try:
        return simulator.finish_activation(activation_id)
    except ValueError as exc:
        raise _handle_value_error(exc)
