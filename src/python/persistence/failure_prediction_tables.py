#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""故障预报与寿命预测 —— SQLite 表结构

对应 Java 侧 alarm-warning-service 的 FailurePrediction 实体。该 Java 服务在本项目
中从不启动（老师底座），故由 Python :8000 提供 /api/failure-predictions 接口，
数据落在共享库 platform.db。列与前端 FailurePrediction.vue 使用的字段一一对应
（下划线库列 ↔ 驼峰接口字段，转换在 store.py 完成）。
"""

from sqlalchemy import Column, Float, Integer, String

from .database import Base


class FailurePrediction(Base):
    __tablename__ = "failure_prediction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(64), index=True)
    device_type = Column(String(64))
    area_id = Column(String(64))
    health_score = Column(Integer, default=0)        # 健康度 0-100
    risk_score = Column(Integer, default=0)          # 风险分 0-100
    failure_probability = Column(Float, default=0.0)  # 故障概率 %
    remaining_life_month = Column(Integer, default=0)  # 剩余寿命（月）
    prediction_level = Column(String(16), index=True)  # LOW/MEDIUM/HIGH/CRITICAL
    prediction_time = Column(String(32))              # ISO8601 文本
