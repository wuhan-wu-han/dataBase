#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""危化品监管 —— SQLite 表结构

对应 hazmat_transport simulator 中的多个内存集合。
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from .database import Base


# ------------------------------------------------------------------------------
# 介质监测
# ------------------------------------------------------------------------------

class HazmatMedia(Base):
    """化学品介质监测记录"""
    __tablename__ = "hazmat_media"

    media_id = Column(String(32), primary_key=True)
    name = Column(String(200), nullable=False)
    hw_code = Column(String(50))
    media_type = Column(String(50))
    concentration_mgL = Column(Numeric(10, 2), default=0)
    threshold_concentration = Column(Numeric(10, 2), default=0)
    source = Column(String(100))
    last_sample = Column(String(30))
    status = Column(String(20), default="normal", index=True)  # normal/warning/alert
    pipeline_id = Column(String(50))
    temperature = Column(Numeric(8, 2), default=0)
    pressure = Column(Numeric(8, 2), default=0)
    flow_rate = Column(Numeric(10, 2), default=0)
    created_at = Column(String(30))
    updated_at = Column(String(30))


# ------------------------------------------------------------------------------
# 输送路径
# ------------------------------------------------------------------------------

class HazmatRoute(Base):
    """危险化学品输送路线"""
    __tablename__ = "hazmat_routes"

    route_id = Column(String(32), primary_key=True)
    source = Column(String(200))
    destination = Column(String(200))
    waypoints = Column(Text)              # JSON 数组 [[waypoint_name, lat, lng], ...]
    length_km = Column(Numeric(8, 2))
    approved_date = Column(String(30))
    company = Column(String(200))
    status = Column(String(20), default="pending", index=True)  # pending/approved/deviated
    hazard_level = Column(String(30))
    created_at = Column(String(30))


# ------------------------------------------------------------------------------
# 全流程溯源
# ------------------------------------------------------------------------------

class HazmatTrace(Base):
    """危险废物全流程溯源记录"""
    __tablename__ = "hazmat_traces"

    trace_id = Column(String(32), primary_key=True)
    manifest_no = Column(String(100))
    hw_code = Column(String(50))
    substance_name = Column(String(200))
    volume_m3 = Column(Numeric(10, 2))
    source = Column(String(200))
    destination = Column(String(200))
    carrier = Column(String(200))
    driver = Column(String(50))
    license_plate = Column(String(30))
    generate_time = Column(String(30))
    dispatch_time = Column(String(30), nullable=True)
    arrive_time = Column(String(30), nullable=True)
    disposal_result = Column(String(500))
    status = Column(String(20), default="in_transit", index=True)  # completed/in_transit


# ------------------------------------------------------------------------------
# 管段腐蚀评估
# ------------------------------------------------------------------------------

class HazmatPipeSegment(Base):
    """管段腐蚀余量监测"""
    __tablename__ = "hazmat_pipe_segments"

    segment_id = Column(String(32), primary_key=True)
    route_id = Column(String(32), ForeignKey("hazmat_routes.route_id"), index=True)
    location = Column(String(300))
    material = Column(String(50))
    diameter_mm = Column(Integer)
    wall_thickness_mm = Column(Numeric(8, 2))
    current_thickness_mm = Column(Numeric(8, 2))
    corrosion_rate = Column(Numeric(6, 4))
    remaining_life_years = Column(Numeric(6, 1))
    risk_level = Column(String(20), index=True)  # high/medium/low
    last_inspection = Column(String(30))
    next_inspection = Column(String(30))
    created_at = Column(String(30))


# ------------------------------------------------------------------------------
# 环保合规台账
# ------------------------------------------------------------------------------

class HazmatLedger(Base):
    """环保合规台账"""
    __tablename__ = "hazmat_ledger"

    record_id = Column(String(32), primary_key=True)
    category = Column(String(50), index=True)
    category_name = Column(String(100))
    factory = Column(String(200))
    substance = Column(String(200))
    volume_m3 = Column(Numeric(10, 2))
    compliant = Column(Boolean, default=True)
    issue_count = Column(Integer, default=0)
    record_date = Column(String(30))
    created_at = Column(String(30))


# ------------------------------------------------------------------------------
# 应急阀门
# ------------------------------------------------------------------------------

class HazmatValve(Base):
    """泄漏应急封堵阀门"""
    __tablename__ = "hazmat_valves"

    valve_id = Column(String(32), primary_key=True)
    route_id = Column(String(32), ForeignKey("hazmat_routes.route_id"), index=True)
    location = Column(String(300))
    cascade_level = Column(Integer, default=1)  # 1/2/3
    response_time_sec = Column(Numeric(6, 1))
    valve_type = Column(String(50))
    status = Column(String(20), default="normal", index=True)  # normal/alert
    auto_close = Column(Boolean, default=False)
    last_test = Column(String(30))
    created_at = Column(String(30))


# ------------------------------------------------------------------------------
# 应急日志
# ------------------------------------------------------------------------------

class HazmatEmergencyLog(Base):
    """泄漏应急封堵操作日志"""
    __tablename__ = "hazmat_emergency_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(32), unique=True, index=True)
    route_id = Column(String(32))
    leak_location = Column(String(300))
    severity = Column(String(20), index=True)  # low/medium/high
    valves_closed = Column(Integer, default=0)
    total_response_time_sec = Column(Numeric(8, 1))
    executed_at = Column(String(30))
