#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""应急预案智能匹配与激活子模块 —— SQLite 表结构

列与 plan_api.simulator 中使用的 dict 键一一对应：
    PlanRecord         ← _plans 主体
    PlanFlowNode       ← _plans[*]["flow_nodes"]
    PlanActivation     ← _activations 主体
    PlanActivationNode ← _activations[*]["nodes"]
    PlanLiveMatch      ← _live_matches
    PlanEvent          ← _events
    PlanCounter        ← _match_seq / _activation_seq / _event_seq
    PlanDailyStat      ← _today / _today_match_count / _today_drill_count
    PlanMatchedAlarm   ← _matched_alarm_ids（重启后不重复匹配同一告警）
"""

from sqlalchemy import (Boolean, Column, ForeignKey, Integer, String, Text)

from .database import Base


class PlanRecord(Base):
    __tablename__ = "ep_plans"

    plan_id = Column(String(32), primary_key=True)
    plan_name = Column(String(200), nullable=False)
    category = Column(String(16), index=True)
    level_min = Column(Integer, default=1)
    level_max = Column(Integer, default=2)
    priority = Column(Integer, default=5)
    status = Column(String(16), index=True)
    objective = Column(Text)
    commander = Column(String(64))
    version_note = Column(String(200))
    scope_cabins = Column(Text)                 # JSON 数组
    scope_zones = Column(Text)                  # JSON 数组
    tags = Column(Text)                         # JSON 数组
    created_at = Column(String(32))
    updated_at = Column(String(32))


class PlanFlowNode(Base):
    __tablename__ = "ep_flow_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(String(32), ForeignKey("ep_plans.plan_id", ondelete="CASCADE"),
                     index=True)
    node_id = Column(String(16))
    seq = Column(Integer, default=1)
    node_type = Column(String(16))
    title = Column(String(200))
    desc = Column(Text)
    deadline_min = Column(Integer, default=30)
    responsible = Column(Text)                  # JSON 对象
    resources = Column(Text)                    # JSON 数组
    actions = Column(Text)                      # JSON 数组
    exit_condition = Column(Text)


class PlanActivation(Base):
    __tablename__ = "ep_activations"

    activation_id = Column(String(32), primary_key=True)
    plan_id = Column(String(32), index=True)
    plan_name = Column(String(200))
    category = Column(String(16))
    category_name = Column(String(64))
    trigger = Column(String(200))
    alarm_id = Column(String(64), nullable=True)
    status = Column(String(16), index=True)
    activated_at = Column(String(32))
    finished_at = Column(String(32), nullable=True)


class PlanActivationNode(Base):
    __tablename__ = "ep_activation_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activation_id = Column(String(32), ForeignKey("ep_activations.activation_id",
                                                  ondelete="CASCADE"), index=True)
    node_id = Column(String(16))
    title = Column(String(200))
    node_type = Column(String(16))
    status = Column(String(16))
    finished_at = Column(String(32), nullable=True)


class PlanLiveMatch(Base):
    __tablename__ = "ep_live_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String(32), index=True)
    time = Column(String(32), index=True)
    alarm_id = Column(String(64))
    alarm = Column(Text)                        # JSON 对象
    category = Column(String(16))
    category_name = Column(String(64))
    best = Column(Text, nullable=True)          # JSON 对象或 NULL
    candidates = Column(Text)                   # JSON 数组
    fallback = Column(Boolean, default=False)
    fallback_message = Column(String(300), nullable=True)
    auto_acked = Column(Boolean, default=False)


class PlanEvent(Base):
    __tablename__ = "ep_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(32), unique=True, index=True)
    time = Column(String(32), index=True)
    event_type = Column(String(24))             # dict 键：type
    level = Column(Integer, default=0)
    ref_id = Column(String(64))
    description = Column(String(500))
    payload = Column(Text)                      # JSON 对象


class PlanCounter(Base):
    __tablename__ = "ep_counters"

    name = Column(String(32), primary_key=True)
    value = Column(Integer, default=0)


class PlanDailyStat(Base):
    __tablename__ = "ep_daily_stats"

    day = Column(String(16), primary_key=True)
    match_count = Column(Integer, default=0)
    drill_count = Column(Integer, default=0)


class PlanMatchedAlarm(Base):
    __tablename__ = "ep_matched_alarms"

    alarm_id = Column(String(64), primary_key=True)
    matched_at = Column(String(32))
