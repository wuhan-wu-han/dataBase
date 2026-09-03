"""应急预案模块 - SQLAlchemy 模型定义

字段命名与 alarm-warning-frontend/src/mock/emergencyPlan.js 逐字段对齐。
数组字段（scope_cabins / scope_zones / tags / sensor_metrics）以 JSON 文本存储。
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, Index
from database import Base


class PlanCategory(Base):
    """事件类别 —— 对应 mock.categories.categories[*]"""
    __tablename__ = "plan_categories"

    code = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    sensor_metrics = Column(Text)          # JSON 数组
    drill_alarm_code = Column(String(50))

    # plan_count / active_count 由查询实时计算，不存字段


class EmergencyPlan(Base):
    """应急预案 —— 对应 mock.plans.plans[*]"""
    __tablename__ = "emergency_plans"

    plan_id = Column(String(50), primary_key=True)
    plan_name = Column(String(200), nullable=False)
    category = Column(String(50), index=True)
    level_min = Column(Integer, default=1)
    level_max = Column(Integer, default=3)
    priority = Column(Integer, default=5)
    status = Column(String(20), default="active")   # active / draft / archived
    commander = Column(String(100))
    scope_cabins = Column(Text)     # JSON 数组
    scope_zones = Column(Text)      # JSON 数组
    tags = Column(Text)             # JSON 数组
    objective = Column(Text)
    created_at = Column(String(40))
    updated_at = Column(String(40))

    __table_args__ = (
        Index('idx_plan_category', 'category'),
        Index('idx_plan_status', 'status'),
    )


class FlowNode(Base):
    """预案流程节点 —— 对应 plans[*].flow_nodes[*]"""
    __tablename__ = "flow_nodes"

    node_id = Column(String(50), primary_key=True)
    plan_id = Column(String(50), index=True)
    seq = Column(Integer)
    node_type = Column(String(30))       # notification / action / decision
    title = Column(String(200))
    desc = Column(Text)
    deadline_min = Column(Integer, default=30)
    exit_condition = Column(Text)

    __table_args__ = (
        Index('idx_node_plan', 'plan_id'),
    )


class LiveMatch(Base):
    """实时匹配记录 —— 对应 mock.liveMatches.matches[*]"""
    __tablename__ = "live_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(String(40))
    alarm_id = Column(String(50), index=True)
    alarm_desc = Column(String(300))
    metric = Column(String(50))
    category_name = Column(String(100))
    best_plan_name = Column(String(200))
    best_score = Column(Float)
    auto_acked = Column(Boolean, default=False)
    fallback = Column(Boolean, default=False)


class Activation(Base):
    """预案激活实例 —— 对应 mock.activations.activations[*]"""
    __tablename__ = "activations"

    activation_id = Column(String(50), primary_key=True)
    plan_id = Column(String(50), index=True)
    plan_name = Column(String(200))
    category_name = Column(String(100))
    trigger = Column(String(200))
    status = Column(String(20), default="running")   # running / finished
    activated_at = Column(String(40))
    finished_at = Column(String(40), nullable=True)

    __table_args__ = (
        Index('idx_act_status', 'status'),
    )


class ActivationNode(Base):
    """激活实例节点 —— 对应 activations[*].nodes[*]"""
    __tablename__ = "activation_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activation_id = Column(String(50), index=True)
    node_id = Column(String(50))
    seq = Column(Integer)                  # 仅用于排序，不输出给前端
    node_type = Column(String(30))
    title = Column(String(200))
    status = Column(String(20), default="pending")  # pending / running / done
    finished_at = Column(String(40), nullable=True)

    __table_args__ = (
        Index('idx_actnode_activation', 'activation_id'),
    )
