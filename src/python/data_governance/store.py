#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""风险研判（数据治理） —— SQLite 读写适配层

复用 persistence.risk_analysis_tables 单表设计，存储用户手动 CRUD 的
risk_analysis 记录。原始主数据（pipelines/equipment/personnel/orgs/geo_spaces）
仍走 models.seed_*() 种子注入，不入库。
"""

import json
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from persistence import DB_PATH, SessionLocal, from_json, init_db, to_json
    from persistence.risk_analysis_tables import RiskAnalysis as RiskModel
except ImportError:
    from src.python.persistence import DB_PATH, SessionLocal, from_json, init_db, to_json
    from src.python.persistence.risk_analysis_tables import RiskAnalysis as RiskModel

_now = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==============================================================================
# 读取
# ==============================================================================

def load_risks(page: int = 1, page_size: int = 20,
               keyword: str = "", risk_level: str = "",
               risk_type: str = "", status: str = "") -> Dict[str, Any]:
    db = SessionLocal()
    try:
        q = db.query(RiskModel)
        if keyword:
            q = q.filter(RiskModel.risk_name.like(f"%{keyword}%") |
                         RiskModel.location.like(f"%{keyword}%"))
        if risk_level:
            q = q.filter(RiskModel.risk_level == risk_level)
        if risk_type:
            q = q.filter(RiskModel.risk_type == risk_type)
        if status:
            q = q.filter(RiskModel.status == status)

        total = q.count()
        rows = q.order_by(RiskModel.id.desc()) \
                .offset((page - 1) * page_size) \
                .limit(page_size).all()

        return {
            "data": [_row_to_dict(r) for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    finally:
        db.close()


def get_risk(item_id: int) -> Optional[Dict]:
    db = SessionLocal()
    try:
        row = db.query(RiskModel).filter(RiskModel.id == item_id).first()
        return _row_to_dict(row) if row else None
    finally:
        db.close()


# ==============================================================================
# 写入
# ==============================================================================

def create_risk(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        row = RiskModel(
            risk_name=data.get("risk_name", ""),
            risk_level=data.get("risk_level", "中"),
            risk_type=data.get("risk_type", "综合"),
            location=data.get("location", ""),
            description=data.get("description", ""),
            status=data.get("status", "active"),
            create_time=_now(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _row_to_dict(row)
    except Exception as exc:
        db.rollback()
        traceback.print_exc()
        raise
    finally:
        db.close()


def update_risk(item_id: int, data: Dict) -> Optional[Dict]:
    db = SessionLocal()
    try:
        row = db.query(RiskModel).filter(RiskModel.id == item_id).first()
        if row is None:
            return None
        for key in ("risk_name", "risk_level", "risk_type", "location",
                     "description", "status"):
            if key in data and data[key] is not None:
                setattr(row, key, data[key])
        db.commit()
        db.refresh(row)
        return _row_to_dict(row)
    except Exception as exc:
        db.rollback()
        traceback.print_exc()
        raise
    finally:
        db.close()


def delete_risk(item_id: int) -> bool:
    db = SessionLocal()
    try:
        count = db.query(RiskModel).filter(RiskModel.id == item_id).delete()
        db.commit()
        return count > 0
    except Exception as exc:
        db.rollback()
        traceback.print_exc()
        raise
    finally:
        db.close()


def change_risk_status(item_id: int, status: str) -> Optional[Dict]:
    db = SessionLocal()
    try:
        row = db.query(RiskModel).filter(RiskModel.id == item_id).first()
        if row is None:
            return None
        row.status = status
        db.commit()
        db.refresh(row)
        return _row_to_dict(row)
    finally:
        db.close()


# ==============================================================================
# 辅助函数
# ==============================================================================

def _row_to_dict(row) -> Dict[str, Any]:
    if row is None:
        return {}
    return {
        "id": row.id,
        "risk_name": row.risk_name,
        "risk_level": row.risk_level,
        "risk_type": row.risk_type,
        "location": row.location,
        "description": row.description,
        "status": row.status,
        "create_time": row.create_time,
    }
