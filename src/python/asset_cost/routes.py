#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资产价值与成本管理子模块 - API路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from . import simulator
from .models import (
    AssetCreateRequest, CostRecordRequest, LCCAnalysisRequest,
    to_dict, ASSET_CATEGORIES, PIPE_MATERIALS, REGIONS, DEPR_METHODS,
)

router = APIRouter(prefix="/asset-cost", tags=["资产价值与成本管理"])


@router.get("/overview", summary="资产总览")
def overview():
    return simulator.get_overview()


@router.get("/assets", summary="资产列表（分页）")
def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    region: Optional[str] = None,
    status: Optional[str] = None,
):
    return simulator.list_assets(page, page_size, category, region, status)


@router.get("/assets/{asset_id}", summary="资产详情")
def get_asset(asset_id: str):
    result = simulator.get_asset(asset_id)
    if not result:
        raise HTTPException(404, f"资产 {asset_id} 不存在")
    return result


@router.post("/assets", summary="新增资产")
def add_asset(req: AssetCreateRequest):
    return simulator.add_asset(to_dict(req))


@router.delete("/assets/{asset_id}", summary="删除资产")
def delete_asset(asset_id: str):
    if not simulator.delete_asset(asset_id):
        raise HTTPException(404, f"资产 {asset_id} 不存在")
    return {"message": f"资产 {asset_id} 已删除"}


@router.post("/assets/{asset_id}/review", summary="审核资产")
def review_asset(asset_id: str, approved: bool = Query(...), comment: str = Query("")):
    result = simulator.review_asset(asset_id, approved, comment)
    if not result:
        raise HTTPException(404, f"资产 {asset_id} 不存在")
    return result


@router.get("/assets/{asset_id}/depreciation", summary="资产折旧明细表")
def depreciation_schedule(asset_id: str):
    result = simulator.depreciation_schedule(asset_id)
    if not result:
        raise HTTPException(404, f"资产 {asset_id} 不存在")
    return result


@router.get("/cost-records", summary="费用记录列表（分页）")
def list_cost_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    cost_type: Optional[str] = None,
    region: Optional[str] = None,
    asset_id: Optional[str] = None,
):
    return simulator.list_cost_records(page, page_size, cost_type, region, asset_id)


@router.post("/cost-records", summary="新增费用记录")
def add_cost_record(req: CostRecordRequest):
    return simulator.add_cost_record(to_dict(req))


@router.delete("/cost-records/{record_id}", summary="删除费用记录")
def delete_cost_record(record_id: str):
    if not simulator.delete_cost_record(record_id):
        raise HTTPException(404, f"费用记录 {record_id} 不存在")
    return {"message": f"费用记录 {record_id} 已删除"}


@router.post("/cost-records/{record_id}/review", summary="审核费用记录")
def review_cost_record(record_id: str, approved: bool = Query(...)):
    result = simulator.review_cost_record(record_id, approved)
    if not result:
        raise HTTPException(404, f"费用记录 {record_id} 不存在")
    return result


@router.get("/cost-analysis", summary="运维成本分析")
def cost_analysis():
    return simulator.cost_analysis()


@router.get("/lcc", summary="LCC分析列表")
def list_lcc():
    return simulator.list_lcc_analyses()


@router.get("/lcc/{analysis_id}", summary="LCC分析详情")
def get_lcc(analysis_id: str):
    result = simulator.get_lcc_analysis(analysis_id)
    if not result:
        raise HTTPException(404, f"LCC分析 {analysis_id} 不存在")
    return result


@router.post("/lcc", summary="执行LCC分析")
def run_lcc(req: LCCAnalysisRequest):
    return simulator.run_lcc_analysis(to_dict(req))


@router.get("/config/categories", summary="资产分类配置")
def get_categories():
    return ASSET_CATEGORIES


@router.get("/config/materials", summary="管材配置")
def get_materials():
    return PIPE_MATERIALS


@router.get("/config/regions", summary="区域列表")
def get_regions():
    return REGIONS


@router.get("/config/depr-methods", summary="折旧方法")
def get_depr_methods():
    return DEPR_METHODS
