#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""危化品监管 —— SQLite 读写适配层

对应 hazmat_transport simulator 中的6个内存集合：
media / routes / traceability / pipe_segments / compliance_ledger / emergency_valves
"""

import json
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from persistence import SessionLocal, from_json, init_db, to_json
    from persistence.hazmat_tables import (
        HazmatMedia, HazmatRoute, HazmatTrace, HazmatPipeSegment,
        HazmatLedger, HazmatValve, HazmatEmergencyLog,
    )
except ImportError:
    from src.python.persistence import SessionLocal, from_json, init_db, to_json
    from src.python.persistence.hazmat_tables import (
        HazmatMedia, HazmatRoute, HazmatTrace, HazmatPipeSegment,
        HazmatLedger, HazmatValve, HazmatEmergencyLog,
    )

_NOW = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==============================================================================
# 介质监测 CRUD
# ==============================================================================

def list_media(page: int = 1, page_size: int = 20, hw_code: str = "", status: str = ""):
    db = SessionLocal()
    try:
        q = db.query(HazmatMedia)
        if hw_code:
            q = q.filter(HazmatMedia.hw_code == hw_code)
        if status:
            q = q.filter(HazmatMedia.status == status)
        total = q.count()
        items = q.order_by(HazmatMedia.media_id).offset((page - 1) * page_size) \
                 .limit(page_size).all()
        return {"data": [_media_row(r) for r in items], "total": total}
    finally:
        db.close()


def get_media(media_id: str):
    db = SessionLocal()
    try:
        row = db.query(HazmatMedia).filter(HazmatMedia.media_id == media_id).first()
        return _media_row(row) if row else None
    finally:
        db.close()


def create_media(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        row = HazmatMedia(**{k: data.get(k) for k in (
            "media_id", "name", "hw_code", "media_type", "concentration_mgL",
            "threshold_concentration", "source", "last_sample", "status",
            "pipeline_id", "temperature", "pressure", "flow_rate",
        )}, created_at=now, updated_at=now)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _media_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_media(media_id: str, data: Dict) -> Optional[Dict]:
    db = SessionLocal()
    try:
        row = db.query(HazmatMedia).filter(HazmatMedia.media_id == media_id).first()
        if row is None:
            return None
        for k in ("name", "hw_code", "media_type", "concentration_mgL",
                   "threshold_concentration", "source", "last_sample", "status",
                   "pipeline_id", "temperature", "pressure", "flow_rate"):
            if k in data and data[k] is not None:
                setattr(row, k, data[k])
        row.updated_at = _NOW()
        db.commit()
        db.refresh(row)
        return _media_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_media(media_id: str) -> bool:
    db = SessionLocal()
    try:
        c = db.query(HazmatMedia).filter(HazmatMedia.media_id == media_id).delete()
        db.commit()
        return c > 0
    finally:
        db.close()


# ==============================================================================
# 输送路径 CRUD
# ==============================================================================

def list_routes(page: int = 1, page_size: int = 20, status: str = ""):
    db = SessionLocal()
    try:
        q = db.query(HazmatRoute)
        if status:
            q = q.filter(HazmatRoute.status == status)
        total = q.count()
        items = q.order_by(HazmatRoute.route_id).offset((page - 1) * page_size) \
                 .limit(page_size).all()
        return {"data": [_route_row(r) for r in items], "total": total}
    finally:
        db.close()


def get_route(route_id: str):
    db = SessionLocal()
    try:
        row = db.query(HazmatRoute).filter(HazmatRoute.route_id == route_id).first()
        return _route_row(row) if row else None
    finally:
        db.close()


def create_route(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        wp = data.get("waypoints")
        row = HazmatRoute(**{k: data.get(k) for k in (
            "route_id", "source", "destination", "length_km", "approved_date",
            "company", "status", "hazard_level",
        )}, waypoints=to_json(wp), created_at=now)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _route_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_route(route_id: str, data: Dict) -> Optional[Dict]:
    db = SessionLocal()
    try:
        row = db.query(HazmatRoute).filter(HazmatRoute.route_id == route_id).first()
        if row is None:
            return None
        for k in ("source", "destination", "length_km", "approved_date",
                   "company", "status", "hazard_level"):
            if k in data and data[k] is not None:
                setattr(row, k, data[k])
        if "waypoints" in data:
            row.waypoints = to_json(data["waypoints"])
        db.commit()
        db.refresh(row)
        return _route_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_route(route_id: str) -> bool:
    db = SessionLocal()
    try:
        c = db.query(HazmatRoute).filter(HazmatRoute.route_id == route_id).delete()
        db.commit()
        return c > 0
    finally:
        db.close()


# ==============================================================================
# 全流程溯源 CRUD
# ==============================================================================

def list_traces(page: int = 1, page_size: int = 20, hw_code: str = "", status: str = ""):
    db = SessionLocal()
    try:
        q = db.query(HazmatTrace)
        if hw_code:
            q = q.filter(HazmatTrace.hw_code == hw_code)
        if status:
            q = q.filter(HazmatTrace.status == status)
        total = q.count()
        items = q.order_by(HazmatTrace.trace_id).offset((page - 1) * page_size) \
                 .limit(page_size).all()
        return {"data": [_trace_row(r) for r in items], "total": total}
    finally:
        db.close()


def get_trace(trace_id: str):
    db = SessionLocal()
    try:
        row = db.query(HazmatTrace).filter(HazmatTrace.trace_id == trace_id).first()
        return _trace_row(row) if row else None
    finally:
        db.close()


def create_trace(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        row = HazmatTrace(**{k: data.get(k) for k in (
            "trace_id", "manifest_no", "hw_code", "substance_name",
            "volume_m3", "source", "destination", "carrier", "driver",
            "license_plate", "generate_time",
        )}, dispatch_time=data.get("dispatch_time"), arrive_time=data.get("arrive_time"),
                          disposal_result=data.get("disposal_result", ""), status=data.get("status", "in_transit"),
                          created_at=now)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _trace_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_trace(trace_id: str) -> bool:
    db = SessionLocal()
    try:
        c = db.query(HazmatTrace).filter(HazmatTrace.trace_id == trace_id).delete()
        db.commit()
        return c > 0
    finally:
        db.close()


# ==============================================================================
# 管段腐蚀评估 CRUD
# ==============================================================================

def list_segments(page: int = 1, page_size: int = 20, route_id: str = "", risk_level: str = ""):
    db = SessionLocal()
    try:
        q = db.query(HazmatPipeSegment)
        if route_id:
            q = q.filter(HazmatPipeSegment.route_id == route_id)
        if risk_level:
            q = q.filter(HazmatPipeSegment.risk_level == risk_level)
        total = q.count()
        items = q.order_by(HazmatPipeSegment.segment_id).offset((page - 1) * page_size) \
                 .limit(page_size).all()
        return {"data": [_segment_row(r) for r in items], "total": total}
    finally:
        db.close()


def get_segment(segment_id: str):
    db = SessionLocal()
    try:
        row = db.query(HazmatPipeSegment).filter(HazmatPipeSegment.segment_id == segment_id).first()
        return _segment_row(row) if row else None
    finally:
        db.close()


def create_segment(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        row = HazmatPipeSegment(**{k: data.get(k) for k in (
            "segment_id", "route_id", "location", "material", "diameter_mm",
            "wall_thickness_mm", "current_thickness_mm", "corrosion_rate",
            "remaining_life_years", "risk_level", "last_inspection", "next_inspection",
        )}, created_at=now)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _segment_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_segment(segment_id: str, data: Dict) -> Optional[Dict]:
    db = SessionLocal()
    try:
        row = db.query(HazmatPipeSegment).filter(HazmatPipeSegment.segment_id == segment_id).first()
        if row is None:
            return None
        for k in ("route_id", "location", "material", "diameter_mm",
                   "wall_thickness_mm", "current_thickness_mm", "corrosion_rate",
                   "remaining_life_years", "risk_level", "last_inspection", "next_inspection"):
            if k in data and data[k] is not None:
                setattr(row, k, data[k])
        db.commit()
        db.refresh(row)
        return _segment_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_segment(segment_id: str) -> bool:
    db = SessionLocal()
    try:
        c = db.query(HazmatPipeSegment).filter(HazmatPipeSegment.segment_id == segment_id).delete()
        db.commit()
        return c > 0
    finally:
        db.close()


# ==============================================================================
# 环保合规台账 CRUD
# ==============================================================================

def list_ledger(page: int = 1, page_size: int = 20, category: str = "", factory: str = ""):
    db = SessionLocal()
    try:
        q = db.query(HazmatLedger)
        if category:
            q = q.filter(HazmatLedger.category == category)
        if factory:
            q = q.filter(HazmatLedger.factory == factory)
        total = q.count()
        items = q.order_by(HazmatLedger.record_id).offset((page - 1) * page_size) \
                 .limit(page_size).all()
        return {"data": [_ledger_row(r) for r in items], "total": total}
    finally:
        db.close()


def get_ledger(record_id: str):
    db = SessionLocal()
    try:
        row = db.query(HazmatLedger).filter(HazmatLedger.record_id == record_id).first()
        return _ledger_row(row) if row else None
    finally:
        db.close()


def create_ledger(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        row = HazmatLedger(**{k: data.get(k) for k in (
            "record_id", "category", "category_name", "factory", "substance",
            "volume_m3", "compliant", "issue_count", "record_date",
        )}, created_at=now)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _ledger_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_ledger(record_id: str) -> bool:
    db = SessionLocal()
    try:
        c = db.query(HazmatLedger).filter(HazmatLedger.record_id == record_id).delete()
        db.commit()
        return c > 0
    finally:
        db.close()


# ==============================================================================
# 应急阀门 CRUD
# ==============================================================================

def list_valves(page: int = 1, page_size: int = 20, route_id: str = "", status: str = ""):
    db = SessionLocal()
    try:
        q = db.query(HazmatValve)
        if route_id:
            q = q.filter(HazmatValve.route_id == route_id)
        if status:
            q = q.filter(HazmatValve.status == status)
        total = q.count()
        items = q.order_by(HazmatValve.valve_id).offset((page - 1) * page_size) \
                 .limit(page_size).all()
        return {"data": [_valve_row(r) for r in items], "total": total}
    finally:
        db.close()


def get_valve(valve_id: str):
    db = SessionLocal()
    try:
        row = db.query(HazmatValve).filter(HazmatValve.valve_id == valve_id).first()
        return _valve_row(row) if row else None
    finally:
        db.close()


def create_valve(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        auto_close = data.get("auto_close", False)
        if isinstance(auto_close, str):
            auto_close = auto_close.lower() in ("true", "1", "yes")
        row = HazmatValve(**{k: data.get(k) for k in (
            "valve_id", "route_id", "location", "cascade_level",
            "response_time_sec", "valve_type", "status",
        )}, auto_close=auto_close, last_test=data.get("last_test"), created_at=now)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _valve_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_valve(valve_id: str, data: Dict) -> Optional[Dict]:
    db = SessionLocal()
    try:
        row = db.query(HazmatValve).filter(HazmatValve.valve_id == valve_id).first()
        if row is None:
            return None
        for k in ("route_id", "location", "cascade_level", "response_time_sec",
                   "valve_type", "status", "last_test"):
            if k in data and data[k] is not None:
                setattr(row, k, data[k])
        if "auto_close" in data:
            v = data["auto_close"]
            row.auto_close = v if isinstance(v, bool) else str(v).lower() in ("true", "1", "yes")
        db.commit()
        db.refresh(row)
        return _valve_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_valve(valve_id: str) -> bool:
    db = SessionLocal()
    try:
        c = db.query(HazmatValve).filter(HazmatValve.valve_id == valve_id).delete()
        db.commit()
        return c > 0
    finally:
        db.close()


# ==============================================================================
# 应急日志（append-only）
# ==============================================================================

def append_emergency_log(data: Dict) -> Dict:
    db = SessionLocal()
    try:
        now = _NOW()
        row = HazmatEmergencyLog(**{k: data.get(k) for k in (
            "log_id", "route_id", "leak_location", "severity",
            "valves_closed", "total_response_time_sec",
        )}, executed_at=now)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _emergency_log_row(row)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ==============================================================================
# 辅助映射
# ==============================================================================

def _media_row(r):
    if r is None:
        return None
    return {k: getattr(r, k) for k in (
        "media_id", "name", "hw_code", "media_type", "concentration_mgL",
        "threshold_concentration", "source", "last_sample", "status",
        "pipeline_id", "temperature", "pressure", "flow_rate",
        "created_at", "updated_at",
    )}


def _route_row(r):
    if r is None:
        return None
    return {k: (from_json(getattr(r, k)) if k == "waypoints" else getattr(r, k)) for k in (
        "route_id", "source", "destination", "waypoints",
        "length_km", "approved_date", "company", "status", "hazard_level",
        "created_at",
    )}


def _trace_row(r):
    if r is None:
        return None
    return {k: getattr(r, k) for k in (
        "trace_id", "manifest_no", "hw_code", "substance_name",
        "volume_m3", "source", "destination", "carrier", "driver",
        "license_plate", "generate_time", "dispatch_time", "arrive_time",
        "disposal_result", "status", "created_at",
    )}


def _segment_row(r):
    if r is None:
        return None
    return {k: getattr(r, k) for k in (
        "segment_id", "route_id", "location", "material", "diameter_mm",
        "wall_thickness_mm", "current_thickness_mm", "corrosion_rate",
        "remaining_life_years", "risk_level", "last_inspection",
        "next_inspection", "created_at",
    )}


def _ledger_row(r):
    if r is None:
        return None
    return {k: getattr(r, k) for k in (
        "record_id", "category", "category_name", "factory", "substance",
        "volume_m3", "compliant", "issue_count", "record_date", "created_at",
    )}


def _valve_row(r):
    if r is None:
        return None
    return {k: getattr(r, k) for k in (
        "valve_id", "route_id", "location", "cascade_level",
        "response_time_sec", "valve_type", "status", "auto_close",
        "last_test", "created_at",
    )}


def _emergency_log_row(r):
    if r is None:
        return None
    return {k: getattr(r, k) for k in (
        "id", "log_id", "route_id", "leak_location", "severity",
        "valves_closed", "total_response_time_sec", "executed_at",
    )}
