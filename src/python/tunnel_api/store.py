#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""地下综合管廊管控 —— SQLite 读写适配层

可持久化内容：管线台账(TunnelPipeline)、环境告警(TunnelAlarm)、安防门禁记录(TunnelAccessRecord)。
注意：传感器实时读数(_sensor_state/_history)不持久化，由后台线程启动时自动重建。
"""

import json
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from persistence import SessionLocal, from_json, init_db, to_json
    from persistence.tunnel_tables import TunnelPipeline, TunnelAlarm, TunnelAccessRecord
except ImportError:
    from src.python.persistence import SessionLocal, from_json, init_db, to_json
    from src.python.persistence.tunnel_tables import TunnelPipeline, TunnelAlarm, TunnelAccessRecord

_NOW = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==============================================================================
# 管线台账 CRUD
# ==============================================================================

def list_pipelines(page: int = 1, page_size: int = 20, cabin: str = "",
                   pipeline_type: str = "", status: str = ""):
    db = SessionLocal()
    try:
        q = db.query(TunnelPipeline)
        if cabin:
            q = q.filter(TunnelPipeline.cabin == cabin)
        if pipeline_type:
            q = q.filter(TunnelPipeline.pipeline_type == pipeline_type)
        if status:
            q = q.filter(TunnelPipeline.status == status)
        total = q.count()
        items = q.order_by(TunnelPipeline.pipeline_id).offset((page - 1) * page_size) \
                 .limit(page_size).all()
        return {"data": [_pipe_row(r) for r in items], "total": total}
    finally:
        db.close()


def get_pipeline(pipeline_id: str):
    db = SessionLocal()
    try:
        row = db.query(TunnelPipeline).filter(TunnelPipeline.pipeline_id == pipeline_id).first()
        return _pipe_row(row) if row else None
    finally:
        db.close()


def create_pipeline(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        row = TunnelPipeline(**{k: data.get(k) for k in (
            "pipeline_id", "cabin", "cabin_name", "zone_code", "zone",
            "pipeline_type", "medium", "diameter_mm", "material",
            "install_date", "commission_date", "manufacturer", "pressure_rating",
            "design_life", "status", "inspection_interval_days",
            "last_inspection", "next_inspection",
        )}, created_at=now)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _pipe_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_pipeline(pipeline_id: str, data: Dict) -> Optional[Dict]:
    db = SessionLocal()
    try:
        row = db.query(TunnelPipeline).filter(TunnelPipeline.pipeline_id == pipeline_id).first()
        if row is None:
            return None
        for k in ("cabin", "cabin_name", "zone_code", "zone", "pipeline_type",
                   "medium", "diameter_mm", "material", "install_date",
                   "commission_date", "manufacturer", "pressure_rating", "design_life",
                   "status", "inspection_interval_days", "last_inspection", "next_inspection"):
            if k in data and data[k] is not None:
                setattr(row, k, data[k])
        db.commit()
        db.refresh(row)
        return _pipe_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_pipeline(pipeline_id: str) -> bool:
    db = SessionLocal()
    try:
        c = db.query(TunnelPipeline).filter(TunnelPipeline.pipeline_id == pipeline_id).delete()
        db.commit()
        return c > 0
    finally:
        db.close()


# ==============================================================================
# 环境告警 CRUD
# ==============================================================================

def list_alarms(page: int = 1, page_size: int = 20, cabin: str = "",
                status: str = "", metric: str = ""):
    db = SessionLocal()
    try:
        q = db.query(TunnelAlarm)
        if cabin:
            q = q.filter(TunnelAlarm.cabin == cabin)
        if status:
            q = q.filter(TunnelAlarm.status == status)
        if metric:
            q = q.filter(TunnelAlarm.metric == metric)
        total = q.count()
        items = q.order_by(TunnelAlarm.time.desc()).offset((page - 1) * page_size) \
                 .limit(page_size).all()
        return {"data": [_alarm_row(r) for r in items], "total": total}
    finally:
        db.close()


def get_alarm(alarm_id: str):
    db = SessionLocal()
    try:
        row = db.query(TunnelAlarm).filter(TunnelAlarm.alarm_id == alarm_id).first()
        return _alarm_row(row) if row else None
    finally:
        db.close()


def create_alarm(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        ack_time = data.get("ack_time") or (now if data.get("status") == "已处理" else None)
        row = TunnelAlarm(**{k: data.get(k) for k in (
            "alarm_id", "source_id", "source_type", "cabin", "zone_code",
            "metric", "metric_name", "value", "unit", "level", "severity",
            "alarm_code", "desc", "status",
        )}, ack_time=ack_time, time=now)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _alarm_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_alarm(alarm_id: str, data: Dict) -> Optional[Dict]:
    db = SessionLocal()
    try:
        row = db.query(TunnelAlarm).filter(TunnelAlarm.alarm_id == alarm_id).first()
        if row is None:
            return None
        for k in ("status", "ack_time"):
            if k in data and data[k] is not None:
                setattr(row, k, data[k])
        db.commit()
        db.refresh(row)
        return _alarm_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_alarm(alarm_id: str) -> bool:
    db = SessionLocal()
    try:
        c = db.query(TunnelAlarm).filter(TunnelAlarm.alarm_id == alarm_id).delete()
        db.commit()
        return c > 0
    finally:
        db.close()


# ==============================================================================
# 门禁记录 CRUD
# ==============================================================================

def list_access_records(page: int = 1, page_size: int = 20, gate_id: str = "",
                        person_id: str = ""):
    db = SessionLocal()
    try:
        q = db.query(TunnelAccessRecord)
        if gate_id:
            q = q.filter(TunnelAccessRecord.gate_id == gate_id)
        if person_id:
            q = q.filter(TunnelAccessRecord.person_id == person_id)
        total = q.count()
        items = q.order_by(TunnelAccessRecord.record_id.desc()).offset((page - 1) * page_size) \
                 .limit(page_size).all()
        return {"data": [_access_row(r) for r in items], "total": total}
    finally:
        db.close()


def get_access_record(record_id: str):
    db = SessionLocal()
    try:
        row = db.query(TunnelAccessRecord).filter(TunnelAccessRecord.record_id == record_id).first()
        return _access_row(row) if row else None
    finally:
        db.close()


def create_access_record(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        authorized = data.get("authorized", True)
        if isinstance(authorized, str):
            authorized = authorized.lower() in ("true", "1", "yes")
        row = TunnelAccessRecord(**{k: data.get(k) for k in (
            "record_id", "gate_id", "gate_name", "location", "direction",
            "person_id", "person_name",
        )}, authorized=authorized, time=now)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _access_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_access_record(record_id: str) -> bool:
    db = SessionLocal()
    try:
        c = db.query(TunnelAccessRecord).filter(TunnelAccessRecord.record_id == record_id).delete()
        db.commit()
        return c > 0
    finally:
        db.close()


# ==============================================================================
# 辅助映射
# ==============================================================================

def _pipe_row(r):
    if r is None:
        return None
    return {k: getattr(r, k) for k in (
        "pipeline_id", "cabin", "cabin_name", "zone_code", "zone",
        "pipeline_type", "medium", "diameter_mm", "material",
        "install_date", "commission_date", "manufacturer", "pressure_rating",
        "design_life", "status", "inspection_interval_days",
        "last_inspection", "next_inspection", "created_at",
    )}


def _alarm_row(r):
    if r is None:
        return None
    return {k: getattr(r, k) for k in (
        "alarm_id", "source_id", "source_type", "cabin", "zone_code",
        "metric", "metric_name", "value", "unit", "level", "severity",
        "alarm_code", "desc", "status", "ack_time", "time",
    )}


def _access_row(r):
    if r is None:
        return None
    return {k: getattr(r, k) for k in (
        "record_id", "gate_id", "gate_name", "location", "direction",
        "person_id", "person_name", "authorized", "time",
    )}
