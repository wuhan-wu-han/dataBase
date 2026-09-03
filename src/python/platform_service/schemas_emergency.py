"""应急预案模块 - Pydantic Schema

字段与 alarm-warning-frontend/src/views/emergencyPlan/Index.vue 的表单/表格逐一对应。
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class PlanBody(BaseModel):
    """新增 / 编辑预案"""
    model_config = ConfigDict(extra="allow")

    plan_name: str = Field(..., min_length=1, max_length=200)
    category: str
    level_min: int = 1
    level_max: int = 2
    priority: int = 5
    status: str = "draft"
    commander: Optional[str] = ""
    scope_cabins: Optional[List[str]] = []
    scope_zones: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    objective: Optional[str] = ""


class PlanPatch(BaseModel):
    """部分更新（状态切换只传 status）"""
    model_config = ConfigDict(extra="allow")

    plan_name: Optional[str] = None
    category: Optional[str] = None
    level_min: Optional[int] = None
    level_max: Optional[int] = None
    priority: Optional[int] = None
    status: Optional[str] = None
    commander: Optional[str] = None
    scope_cabins: Optional[List[str]] = None
    scope_zones: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    objective: Optional[str] = None


class NodeBody(BaseModel):
    """新增 / 编辑流程节点"""
    model_config = ConfigDict(extra="allow")

    node_type: Optional[str] = "action"
    title: str = Field(..., min_length=1, max_length=200)
    desc: Optional[str] = ""
    deadline_min: Optional[int] = 30
    exit_condition: Optional[str] = ""


class NodePatch(BaseModel):
    model_config = ConfigDict(extra="allow")

    node_type: Optional[str] = None
    title: Optional[str] = None
    desc: Optional[str] = None
    deadline_min: Optional[int] = None
    exit_condition: Optional[str] = None


class MatchBody(BaseModel):
    model_config = ConfigDict(extra="allow")

    level: int = 1
    top_n: int = 5
    category: Optional[str] = None
    cabin: Optional[str] = None
    zone: Optional[str] = None


class DrillBody(MatchBody):
    description: Optional[str] = ""
    activate_best: bool = True
    plan_id: Optional[str] = None


class FlowNodeOut(BaseModel):
    node_id: str
    seq: int
    node_type: str
    title: str
    desc: str
    deadline_min: int
    exit_condition: str


class PlanOut(BaseModel):
    plan_id: str
    plan_name: str
    category: str
    level_min: int
    level_max: int
    priority: int
    status: str
    commander: str
    scope_cabins: List[str] = []
    scope_zones: List[str] = []
    tags: List[str] = []
    objective: str
    created_at: str
    updated_at: str
    flow_nodes: List[FlowNodeOut] = []


class CategoryOut(BaseModel):
    code: str
    name: str
    description: str
    sensor_metrics: List[str] = []
    drill_alarm_code: str
    plan_count: int = 0
    active_count: int = 0


class CandidateOut(BaseModel):
    rank: int
    plan_id: str
    plan_name: str
    score: float
    reasons: List[str] = []


class MatchOut(BaseModel):
    candidates: List[CandidateOut]
    fallback: bool = False
    fallback_message: str = ""


class ActivationNodeOut(BaseModel):
    node_id: str
    node_type: str
    title: str
    status: str
    finished_at: Optional[str] = None


class ActivationOut(BaseModel):
    activation_id: str
    plan_id: str
    plan_name: str
    category_name: str
    trigger: str
    status: str
    activated_at: str
    finished_at: Optional[str] = None
    nodes: List[ActivationNodeOut] = []


class LiveMatchOut(BaseModel):
    time: str
    alarm_id: str
    alarm: Dict[str, Any]
    category_name: str
    best: Dict[str, Any]
    auto_acked: bool
    fallback: bool


class OverviewOut(BaseModel):
    total_plans: int
    active_plans: int
    today_match_count: int
    today_drill_count: int
