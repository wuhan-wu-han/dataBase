#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""资产全生命周期成本 —— SQLite 读写适配层

对应 asset_cost simulator 中的三个核心集合：
_assets / _cost_records / _lcc_analyses
"""

import json
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from persistence import SessionLocal, from_json, init_db, to_json
    from persistence.asset_cost_tables import AssetCostAsset, AssetCostRecord, AssetCostLccAnalysis
except ImportError:
    from src.python.persistence import SessionLocal, from_json, init_db, to_json
    from src.python.persistence.asset_cost_tables import AssetCostAsset, AssetCostRecord, AssetCostLccAnalysis

_NOW = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==============================================================================
# 资产台账 CRUD
# ==============================================================================

def list_assets(page: int = 1, page_size: int = 20, category: str = "",
                region: str = "", status: str = ""):
    db = SessionLocal()
    try:
        q = db.query(AssetCostAsset)
        if category:
            q = q.filter(AssetCostAsset.category == category | AssetCostAsset.category_name == category)
        if region:
            q = q.filter(AssetCostAsset.region == region)
        if status:
            q = q.filter(AssetCostAsset.status == status)
        total = q.count()
        items = q.order_by(AssetCostAsset.asset_id).offset((page - 1) * page_size) \
                 .limit(page_size).all()
        return {"data": [_asset_row(r) for r in items], "total": total,
                "page": page, "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size}
    finally:
        db.close()


def get_asset(asset_id: str):
    db = SessionLocal()
    try:
        row = db.query(AssetCostAsset).filter(AssetCostAsset.asset_id == asset_id).first()
        return _asset_row(row) if row else None
    finally:
        db.close()


def create_asset(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        original_value = float(data.get("original_value") or 0)
        residual_rate = float(data.get("residual_rate") or 0.05)
        depr_years = int(data.get("depr_years") or 20)
        row = AssetCostAsset(**{k: data.get(k) for k in (
            "asset_id", "name", "category", "category_name", "region",
            "material", "material_name", "specs",
            "install_date", "depr_method", "status",
        )}, original_value=original_value, residual_rate=residual_rate,
                             depr_years=depr_years, created_at=now)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _asset_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_asset(asset_id: str, data: Dict) -> Optional[Dict]:
    db = SessionLocal()
    try:
        row = db.query(AssetCostAsset).filter(AssetCostAsset.asset_id == asset_id).first()
        if row is None:
            return None
        for k in ("name", "category", "category_name", "region", "material",
                   "material_name", "specs", "status", "review_comment"):
            if k in data and data[k] is not None:
                setattr(row, k, data[k])
        if "original_value" in data:
            row.original_value = float(data["original_value"])
        if "depr_years" in data:
            row.depr_years = int(data["depr_years"])
        if "residual_rate" in data:
            row.residual_rate = float(data["residual_rate"])
        if "review_time" in data:
            row.review_time = data["review_time"]
        db.commit()
        db.refresh(row)
        return _asset_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def review_asset(asset_id: str, approved: bool, comment: str = ""):
    """审核通过/驳回"""
    db = SessionLocal()
    try:
        row = db.query(AssetCostAsset).filter(AssetCostAsset.asset_id == asset_id).first()
        if row is None:
            return None
        row.status = "已审核" if approved else "已驳回"
        row.review_comment = comment
        row.review_time = _NOW()
        db.commit()
        db.refresh(row)
        return _asset_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_asset(asset_id: str) -> bool:
    db = SessionLocal()
    try:
        c = db.query(AssetCostAsset).filter(AssetCostAsset.asset_id == asset_id).delete()
        db.commit()
        return c > 0
    finally:
        db.close()


# ==============================================================================
# 费用记录 CRUD
# ==============================================================================

def list_cost_records(page: int = 1, page_size: int = 20, cost_type: str = "",
                      region: str = "", asset_id: str = ""):
    db = SessionLocal()
    try:
        q = db.query(AssetCostRecord)
        if cost_type:
            q = q.filter(AssetCostRecord.cost_type == cost_type)
        if region:
            q = q.filter(AssetCostRecord.region == region)
        if asset_id:
            q = q.filter(AssetCostRecord.asset_id == asset_id)
        total = q.count()
        items = q.order_by(AssetCostRecord.record_id).offset((page - 1) * page_size) \
                 .limit(page_size).all()
        return {"data": [_record_row(r) for r in items], "total": total,
                "page": page, "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size}
    finally:
        db.close()


def get_cost_record(record_id: str):
    db = SessionLocal()
    try:
        row = db.query(AssetCostRecord).filter(AssetCostRecord.record_id == record_id).first()
        return _record_row(row) if row else None
    finally:
        db.close()


def create_cost_record(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        amount = float(data.get("amount") or 0)
        row = AssetCostRecord(**{k: data.get(k) for k in (
            "record_id", "asset_id", "cost_type", "description", "region",
            "record_date",
        )}, amount=amount, approved=False, created_at=now)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _record_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def review_cost_record(record_id: str, approved: bool):
    """审批费用记录"""
    db = SessionLocal()
    try:
        row = db.query(AssetCostRecord).filter(AssetCostRecord.record_id == record_id).first()
        if row is None:
            return None
        row.approved = approved
        row.review_time = _NOW()
        db.commit()
        db.refresh(row)
        return _record_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_cost_record(record_id: str) -> bool:
    db = SessionLocal()
    try:
        c = db.query(AssetCostRecord).filter(AssetCostRecord.record_id == record_id).delete()
        db.commit()
        return c > 0
    finally:
        db.close()


# ==============================================================================
# LCC 分析 CRUD
# ==============================================================================

def list_lcc():
    db = SessionLocal()
    try:
        rows = db.query(AssetCostLccAnalysis).order_by(AssetCostLccAnalysis.analysis_id).all()
        return [_lcc_row(r) for r in rows]
    finally:
        db.close()


def get_lcc(analysis_id: str):
    db = SessionLocal()
    try:
        row = db.query(AssetCostLccAnalysis).filter(AssetCostLccAnalysis.analysis_id == analysis_id).first()
        return _lcc_row(row) if row else None
    finally:
        db.close()


def create_lcc(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        options = data.get("options")
        row = AssetCostLccAnalysis(
            analysis_id=data.get("analysis_id", ""),
            project_name=data.get("project_name", ""),
            design_life=int(data.get("design_life") or 30),
            discount_rate=float(data.get("discount_rate") or 0.05),
            options=to_json(options),
            recommended=data.get("recommended", ""),
            created_at=now,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _lcc_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ==============================================================================
# 辅助映射
# ==============================================================================

def _asset_row(r):
    if r is None:
        return None
    return {k: (float(getattr(r, k)) if k in ("original_value", "residual_rate") else getattr(r, k)) for k in (
        "asset_id", "name", "category", "category_name", "region", "material",
        "material_name", "specs", "original_value", "install_date",
        "depr_method", "depr_years", "residual_rate", "status",
        "created_at", "review_comment", "review_time",
    )}


def _record_row(r):
    if r is None:
        return None
    return {k: (float(getattr(r, k)) if k == "amount" else getattr(r, k)) for k in (
        "record_id", "asset_id", "cost_type", "amount", "description",
        "region", "record_date", "approved", "review_time", "created_at",
    )}


def _lcc_row(r):
    if r is None:
        return None
    return {k: (from_json(getattr(r, k)) if k == "options" else getattr(r, k)) for k in (
        "analysis_id", "project_name", "design_life", "discount_rate",
        "options", "recommended", "created_at",
    )}
