"""工单管理模块 - Pydantic Schema

字段与前端 form/表格逐一对应；写接口均允许缺省，由后端补默认值。
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class OrderBody(BaseModel):
    """新增 / 编辑（upsert）工单请求体"""
    model_config = ConfigDict(extra="allow")

    order_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    channel: Optional[str] = "hotline"
    category: Optional[str] = "repair"
    priority: Optional[str] = "medium"
    status: Optional[str] = None
    location: Optional[str] = ""
    assignee: Optional[str] = None
    reporter: Optional[str] = ""
    description: Optional[str] = ""
    sla_hours: Optional[int] = None
    required_skill: Optional[str] = None


class AdvanceBody(BaseModel):
    model_config = ConfigDict(extra="allow")

    order_id: str
    step: str
    note: Optional[str] = ""


class AssignBody(BaseModel):
    model_config = ConfigDict(extra="allow")

    order_id: str
    staff_id: str


class OrderOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    order_id: str
    title: str
    channel: str
    category: str
    priority: str
    status: str
    location: str
    assignee: Optional[str] = None
    reporter: str
    created_at: str
    sla_hours: int
    sla_deadline: Optional[str] = None
    resolved_at: Optional[str] = None
    rating: Optional[int] = None
    escalated: bool = False
    description: str
    required_skill: str


class OrderListOut(BaseModel):
    orders: List[OrderOut]
    total: int
    page: int = 1
    page_size: int = 20


class StaffOut(BaseModel):
    staff_id: str
    name: str
    skills: List[str]
    status: str
    location: str
    phone: str
    completed_orders: int
    avg_rating: float


class StaffListOut(BaseModel):
    staff: List[StaffOut]
    total: int = 0


class WorkloadOut(BaseModel):
    staff_id: str
    name: str
    status: str
    status_name: str
    active_orders: int
    completed_orders: int
    avg_rating: float


class WorkloadListOut(BaseModel):
    workload: List[WorkloadOut]


class SlaRuleOut(BaseModel):
    priority: str
    priority_name: str
    response_hours: int
    warning_threshold: float
    escalate_multiplier: float
    escalate_target: str
    desc: str


class SlaRulesOut(BaseModel):
    rules: List[SlaRuleOut]


class SlaItemOut(BaseModel):
    order_id: str
    title: str
    priority: str
    priority_name: str
    status: str
    status_name: str
    assignee: Optional[str] = None
    elapsed_hours: float
    sla_hours: int
    remaining_hours: float
    sla_status: str
    sla_status_name: str
    sla_deadline: Optional[str] = None


class SlaMonitorOut(BaseModel):
    monitored: int
    summary: Dict[str, int]
    items: List[SlaItemOut]


class ProcessStepOut(BaseModel):
    name: str
    code: str


class TimelineOut(BaseModel):
    step: str
    step_name: str
    at: str
    operator: str
    note: str


class ProcessOut(BaseModel):
    steps: List[ProcessStepOut]
    current_step_index: int
    timeline: List[TimelineOut]


class CandidateOut(BaseModel):
    staff_id: str
    name: str
    skills: List[str]
    status: str
    status_name: str
    location: str
    distance_m: int
    skill_match: bool
    avg_rating: float
    total_score: float
    score_breakdown: Dict[str, float]


class DispatchRecommendOut(BaseModel):
    order_id: str
    required_skill: str
    location: str
    candidates: List[CandidateOut]
    recommendation: str


class ChannelItem(BaseModel):
    key: str
    name: str


class ChannelsOut(BaseModel):
    channels: List[ChannelItem]
    categories: List[ChannelItem]


class OverviewOut(BaseModel):
    total_orders: int
    pending_dispatch: int
    overdue_orders: int
    avg_rating: float
    staff_idle: int


class AckOut(BaseModel):
    success: bool = True
    code: int = 200
    message: str = "ok"
    data: Optional[Dict[str, Any]] = None
