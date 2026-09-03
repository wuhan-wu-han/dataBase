#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工单全流程管理 —— SQLite 表结构

列与 workorder.simulator 中使用的 dict 键一一对应：
    WoOrder        ← _state["orders"] 主体
    WoTimeline     ← orders[*]["process"]
    WoStaff        ← _state["staff"]
    WoSlaRule      ← _state["sla_rules"]
    WoDispatchLog  ← _state["dispatch_logs"]
    WoCounter      ← _state["order_seq"]
"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text

from .database import Base


class WoOrder(Base):
    __tablename__ = "wo_orders"

    order_id = Column(String(32), primary_key=True)
    title = Column(String(200), nullable=False)
    channel = Column(String(32))
    category = Column(String(32))
    required_skill = Column(String(64))
    priority = Column(String(16))
    status = Column(String(16), index=True)
    location = Column(String(128))
    description = Column(Text)
    reporter = Column(String(64))
    created_at = Column(String(32), index=True)
    sla_deadline = Column(String(32))
    sla_hours = Column(Integer, default=24)
    assignee = Column(String(64), nullable=True)
    assignee_id = Column(String(32), nullable=True)
    resolved_at = Column(String(32), nullable=True)
    rating = Column(Integer, nullable=True)
    escalated = Column(Boolean, default=False)


class WoTimeline(Base):
    __tablename__ = "wo_timeline"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(32), ForeignKey("wo_orders.order_id", ondelete="CASCADE"),
                      index=True)
    seq = Column(Integer, default=0)
    step = Column(String(32))
    step_name = Column(String(64))
    at = Column(String(32))
    operator = Column(String(64))
    note = Column(Text)


class WoStaff(Base):
    __tablename__ = "wo_staff"

    staff_id = Column(String(32), primary_key=True)
    name = Column(String(64), nullable=False)
    skills = Column(Text)                    # JSON 数组
    status = Column(String(16), index=True)
    location = Column(String(128))
    phone = Column(String(32))
    completed_orders = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)


class WoSlaRule(Base):
    __tablename__ = "wo_sla_rules"

    priority = Column(String(16), primary_key=True)
    priority_name = Column(String(32))
    response_hours = Column(Integer)
    warning_threshold = Column(Float)
    escalate_multiplier = Column(Float)
    escalate_target = Column(String(64))
    desc = Column(String(300))


class WoDispatchLog(Base):
    __tablename__ = "wo_dispatch_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(32), index=True)
    staff_id = Column(String(32))
    staff_name = Column(String(64))
    dispatched_at = Column(String(32))
    method = Column(String(32))


class WoCounter(Base):
    __tablename__ = "wo_counters"

    name = Column(String(32), primary_key=True)
    value = Column(Integer, default=0)
