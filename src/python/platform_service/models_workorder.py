"""工单管理模块 - SQLAlchemy 模型定义

字段命名与 alarm-warning-frontend/src/mock/workorder.js 逐字段对齐，
确保前端去除 Mock fallback 后无需改动渲染逻辑。
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, Index
from database import Base


class WorkOrder(Base):
    """工单主表 —— 对应 mock.orders[*]"""
    __tablename__ = "work_orders"

    order_id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False)
    channel = Column(String(30))            # hotline / app / patrol / iot
    category = Column(String(30))           # repair / inspect / install / complaint
    priority = Column(String(20))           # urgent / high / medium / low
    status = Column(String(20))             # pending / assigned / onsite / resolved / closed
    location = Column(String(200))
    assignee = Column(String(100), nullable=True)
    reporter = Column(String(100))
    created_at = Column(String(40))
    sla_hours = Column(Integer, default=24)
    sla_deadline = Column(String(40))
    resolved_at = Column(String(40), nullable=True)
    rating = Column(Integer, nullable=True)
    escalated = Column(Boolean, default=False)
    description = Column(Text)
    required_skill = Column(String(100))
    # 用于派单评分的固定距离（米）
    distance_base = Column(Integer, default=1000)

    __table_args__ = (
        Index('idx_wo_status', 'status'),
        Index('idx_wo_priority', 'priority'),
        Index('idx_wo_created', 'created_at'),
    )


class OrderTimeline(Base):
    """工单流程时间线 —— 对应 mock.process.timeline[*]"""
    __tablename__ = "order_timeline"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), nullable=False, index=True)
    step = Column(String(30))               # created / dispatched / processing / completed / closed
    step_name = Column(String(100))
    at = Column(String(40))                 # '2026-08-30 09:15:00' 空格分隔，与 Mock 一致
    operator = Column(String(100))
    note = Column(Text)

    __table_args__ = (
        Index('idx_tl_order', 'order_id'),
    )


class Staff(Base):
    """运维人员 —— 对应 mock.staff.staff[*]"""
    __tablename__ = "staff"

    staff_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    skills = Column(String(300))            # 逗号分隔，输出时转数组
    status = Column(String(20))             # idle / busy / off
    location = Column(String(200))
    phone = Column(String(20))
    completed_orders = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)
    active_orders = Column(Integer, default=0)
    distance_m = Column(Integer, default=1000)   # 距典型工单位置距离，用于派单评分

    __table_args__ = (
        Index('idx_staff_status', 'status'),
    )


class SlaRule(Base):
    """SLA 规则 —— 对应 mock.slaRules.rules[*]"""
    __tablename__ = "sla_rules"

    priority = Column(String(20), primary_key=True)
    priority_name = Column(String(50))
    response_hours = Column(Integer)
    warning_threshold = Column(Float)
    escalate_multiplier = Column(Float)
    escalate_target = Column(String(100))
    desc = Column(String(300))
