#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""风险研判与综合治理 —— SQLite 表结构

单表设计：risk_analysis，对应 data_governance simulator 中的主数据管理。
"""

from sqlalchemy import Column, Integer, String, Text

from .database import Base


class RiskAnalysis(Base):
    """风险研判主表"""
    __tablename__ = "risk_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_name = Column(String(200), nullable=False)
    risk_level = Column(String(20), index=True)       # 高/中/低
    risk_type = Column(String(50), index=True)        # 燃气/电力/交通/等
    location = Column(String(300))
    description = Column(Text)
    status = Column(String(20), default="active", index=True)  # active/archived
    create_time = Column(String(30), nullable=False)
