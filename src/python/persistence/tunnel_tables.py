#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""地下综合管廊管控 —— SQLite 表结构

对应 tunnel_api simulator 中的管线台账、告警、安防门禁等可持久化状态。
注意：传感器实时读数（_sensor_state / _history）不持久化，重启由后台线程自动重建。
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from .database import Base


# ------------------------------------------------------------------------------
# 管线台账
# ------------------------------------------------------------------------------

class TunnelPipeline(Base):
    """管廊管线登记"""
    __tablename__ = "tunnel_pipelines"

    pipeline_id = Column(String(32), primary_key=True)
    cabin = Column(String(20), index=True)
    cabin_name = Column(String(100))
    zone_code = Column(Integer, index=True)
    zone = Column(String(50))
    pipeline_type = Column(String(50), index=True)
    medium = Column(String(100))
    diameter_mm = Column(Integer)
    material = Column(String(50))
    install_date = Column(String(30))
    commission_date = Column(String(30))
    manufacturer = Column(String(200))
    pressure_rating = Column(Numeric(8, 2))
    design_life = Column(Integer)
    status = Column(String(20), default="normal", index=True)  # normal/maintenance/offline
    inspection_interval_days = Column(Integer, default=90)
    last_inspection = Column(String(30))
    next_inspection = Column(String(30))
    created_at = Column(String(30))


# ------------------------------------------------------------------------------
# 环境告警
# ------------------------------------------------------------------------------

class TunnelAlarm(Base):
    """管廊环境告警"""
    __tablename__ = "tunnel_alarms"

    alarm_id = Column(String(32), primary_key=True)
    source_id = Column(String(50))
    source_type = Column(String(20), default="sensor")  # sensor/gate/other
    cabin = Column(String(20), index=True)
    zone_code = Column(String(50))
    metric = Column(String(30), index=True)
    metric_name = Column(String(50))
    value = Column(Numeric(12, 4))
    unit = Column(String(20))
    level = Column(Integer)            # 0=normal, 1=warning, 2=critical
    severity = Column(String(20))      # 预警/严重
    alarm_code = Column(Integer)
    desc = Column(String(300))
    status = Column(String(20), default="未处理", index=True)  # 未处理/已处理
    ack_time = Column(String(30), nullable=True)
    time = Column(String(30), index=True)


# ------------------------------------------------------------------------------
# 安防门禁记录
# ------------------------------------------------------------------------------

class TunnelAccessRecord(Base):
    """管廊安防门禁出入记录"""
    __tablename__ = "tunnel_access_records"

    record_id = Column(String(32), primary_key=True)
    gate_id = Column(String(50))
    gate_name = Column(String(100))
    location = Column(String(200))
    direction = Column(String(10))     # 进/出
    person_id = Column(String(50))
    person_name = Column(String(100))
    authorized = Column(Boolean, default=True)
    time = Column(String(30), index=True)
