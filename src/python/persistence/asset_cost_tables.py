#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""资产全生命周期成本 —— SQLite 表结构

对应 asset_cost simulator 中的资产台账、费用记录、LCC分析。
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from .database import Base


# ------------------------------------------------------------------------------
# 资产台账
# ------------------------------------------------------------------------------

class AssetCostAsset(Base):
    """资产价值与成本管理主表"""
    __tablename__ = "asset_costs"

    asset_id = Column(String(32), primary_key=True)
    name = Column(String(200), nullable=False)
    category = Column(String(50), index=True)
    category_name = Column(String(100))
    region = Column(String(100), index=True)
    material = Column(String(50))
    material_name = Column(String(100))
    specs = Column(String(200))
    original_value = Column(Numeric(15, 2), default=0)
    install_date = Column(String(30))
    depr_method = Column(String(30))          # STRAIGHT_LINE/DOUBLE_DECLINING/SUM_OF_YEARS
    depr_years = Column(Integer, default=20)
    residual_rate = Column(Numeric(5, 4), default=0.05)
    status = Column(String(20), default="待审核", index=True)  # 待审核/在用/已审核/已驳回/报废
    created_at = Column(String(30))
    review_comment = Column(String(500))
    review_time = Column(String(30))


# ------------------------------------------------------------------------------
# 费用记录
# ------------------------------------------------------------------------------

class AssetCostRecord(Base):
    """运维成本归集记录"""
    __tablename__ = "asset_cost_records"

    record_id = Column(String(32), primary_key=True)
    asset_id = Column(String(32), ForeignKey("asset_costs.asset_id", ondelete="CASCADE"), index=True)
    cost_type = Column(String(50), index=True)  # procurement/maintenance/depreciation/scrap
    amount = Column(Numeric(15, 2), default=0)
    description = Column(String(500))
    region = Column(String(100))
    record_date = Column(String(30))
    approved = Column(Boolean, default=False)
    review_time = Column(String(30))
    created_at = Column(String(30))


# ------------------------------------------------------------------------------
# LCC分析
# ------------------------------------------------------------------------------

class AssetCostLccAnalysis(Base):
    """LCC 全生命周期成本分析"""
    __tablename__ = "asset_cost_lcc"

    analysis_id = Column(String(32), primary_key=True)
    project_name = Column(String(200))
    design_life = Column(Integer, default=30)
    discount_rate = Column(Numeric(6, 4), default=0.05)
    options = Column(Text)           # JSON 数组 [material_options]
    recommended = Column(String(50))
    created_at = Column(String(30))
