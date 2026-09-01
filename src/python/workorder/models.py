#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工单全流程管理子模块 - 数据模型与种子数据

内容：
1. 多渠道工单接入：预警自动生成、巡检上报、用户报修、政务转办
2. 智能派单：根据位置、技能、忙闲状态自动分派最优运维人员
3. 过程跟踪：接单、到场、处置、验收、评价全流程可视化
4. 时效管控：超时预警、超期升级，保障处置响应效率
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


def to_dict(model) -> Dict[str, Any]:
    """pydantic v1/v2 兼容的模型转 dict"""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ==============================================================================
# 常量定义
# ==============================================================================

# 工单接入渠道
CHANNELS = {
    "alarm": {"name": "预警自动生成", "source": "在线监测预警系统"},
    "patrol": {"name": "巡检上报", "source": "移动巡检终端"},
    "user": {"name": "用户报修", "source": "服务热线/公众号"},
    "government": {"name": "政务转办", "source": "12345政务平台"},
}

# 优先级与SLA时限（小时）
PRIORITIES = {
    "urgent": {"name": "紧急", "sla_hours": 2},
    "high": {"name": "高", "sla_hours": 8},
    "medium": {"name": "中", "sla_hours": 24},
    "low": {"name": "低", "sla_hours": 72},
}

# 处置流程节点
PROCESS_STEPS = [
    {"code": "pending", "name": "待派单", "desc": "工单生成，等待派单"},
    {"code": "assigned", "name": "已派单", "desc": "已分派运维人员"},
    {"code": "accepted", "name": "已接单", "desc": "运维人员确认接单"},
    {"code": "onsite", "name": "已到场", "desc": "运维人员到达现场"},
    {"code": "resolved", "name": "已处置", "desc": "完成现场处置"},
    {"code": "verified", "name": "已验收", "desc": "报修方/管理员验收通过"},
    {"code": "closed", "name": "已关闭", "desc": "评价完成，工单归档"},
]

_STEP_CODE_TO_NAME = {s["code"]: s["name"] for s in PROCESS_STEPS}

# 工单类别与所需技能
ORDER_CATEGORIES = {
    "electrical": {"name": "电气故障", "skill": "电气维修"},
    "pipeline": {"name": "管道泄漏", "skill": "管道抢修"},
    "instrument": {"name": "仪表异常", "skill": "仪表调试"},
    "hvac": {"name": "暖通故障", "skill": "暖通空调"},
    "civil": {"name": "土建破损", "skill": "土建维修"},
    "it": {"name": "网络设备故障", "skill": "弱电网络"},
    "fire": {"name": "消防设施异常", "skill": "消防设备"},
}

# 运维区域
LOCATIONS = [
    "综合管廊A段", "综合管廊B段", "机加工一车间", "装配车间",
    "动力站房", "办公楼", "厂区道路", "变电站",
]

# 评价星级概率
_RATING_CHOICES = [5, 5, 5, 4, 4, 5, 3]


# ==============================================================================
# 种子数据生成
# ==============================================================================

def seed_staff() -> List[Dict]:
    """运维人员：技能、忙闲状态、位置用于智能派单评分"""
    staff_defs = [
        ("STF-001", "张建国", ["电气维修", "仪表调试"], "综合管廊A段"),
        ("STF-002", "李卫东", ["管道抢修", "消防设备"], "综合管廊B段"),
        ("STF-003", "王志强", ["暖通空调", "土建维修"], "机加工一车间"),
        ("STF-004", "刘国栋", ["电气维修", "弱电网络"], "装配车间"),
        ("STF-005", "陈永福", ["管道抢修", "暖通空调"], "动力站房"),
        ("STF-006", "赵铁柱", ["土建维修", "消防设备"], "厂区道路"),
        ("STF-007", "孙明亮", ["仪表调试", "弱电网络"], "变电站"),
        ("STF-008", "周文斌", ["电气维修", "管道抢修"], "办公楼"),
        ("STF-009", "吴海燕", ["仪表调试", "暖通空调"], "综合管廊A段"),
        ("STF-010", "郑晓东", ["弱电网络", "消防设备"], "机加工一车间"),
        ("STF-011", "冯国庆", ["管道抢修", "电气维修"], "装配车间"),
        ("STF-012", "许志刚", ["土建维修", "弱电网络"], "动力站房"),
    ]
    statuses = ["idle", "busy", "idle", "idle", "busy", "off", "idle", "busy", "idle", "idle", "off", "idle"]
    staff = []
    for i, (sid, name, skills, loc) in enumerate(staff_defs):
        staff.append({
            "staff_id": sid,
            "name": name,
            "skills": skills,
            "status": statuses[i],
            "location": loc,
            "phone": "138%08d" % (10000000 + i * 137),
            "completed_orders": random.randint(20, 200),
            "avg_rating": round(random.uniform(4.2, 5.0), 2),
        })
    return staff


def _gen_process_history(created_at: datetime, status: str, assignee: Optional[Dict]) -> List[Dict]:
    """根据工单状态生成处置过程时间线"""
    steps = []
    t = created_at
    steps.append({"step": "pending", "step_name": "待派单", "at": _fmt(t), "operator": "系统", "note": "工单生成，等待派单"})

    reached = {"pending", "assigned", "accepted", "onsite", "resolved", "verified", "closed"}
    if status not in reached:
        return steps
    order_seq = ["pending", "assigned", "accepted", "onsite", "resolved", "verified", "closed"]
    idx = order_seq.index(status)

    t += timedelta(minutes=random.randint(2, 15))
    steps.append({"step": "assigned", "step_name": "已派单", "at": _fmt(t),
                  "operator": "智能派单引擎", "note": "自动分派至 %s" % (assignee["name"] if assignee else "值班员")})
    for code in order_seq[2: idx + 1]:
        t += timedelta(minutes=random.randint(5, 90))
        notes = {
            "accepted": "运维人员确认接单",
            "onsite": "已到达现场，开始排查",
            "resolved": "处置完成，功能恢复正常",
            "verified": "验收通过，处置结果确认",
            "closed": "用户评价完成，工单归档",
        }
        steps.append({"step": code, "step_name": _STEP_CODE_TO_NAME[code], "at": _fmt(t),
                      "operator": assignee["name"] if assignee else "运维人员", "note": notes[code]})
    return steps


def seed_orders(staff: List[Dict]) -> List[Dict]:
    """工单：多渠道、多优先级、多状态，部分超时用于时效管控演示"""
    channel_keys = list(CHANNELS.keys())
    category_keys = list(ORDER_CATEGORIES.keys())
    priority_keys = list(PRIORITIES.keys())
    orders = []
    now = datetime.now()

    # 状态分布：2待派单 / 6处置中 / 9已完成 / 3超时未处置 / 2升级中
    status_plan = ["pending", "pending",
                   "accepted", "onsite", "resolved", "onsite", "accepted", "onsite",
                   "closed", "closed", "closed", "verified", "closed", "closed", "closed", "verified", "closed",
                   "onsite", "accepted", "onsite",
                   "escalated", "escalated"]

    for i, status in enumerate(status_plan):
        channel = random.choice(channel_keys)
        category = random.choice(category_keys)
        priority = random.choice(priority_keys)
        created_at = now - timedelta(hours=random.uniform(1, 96))
        # 超时/升级工单：创建时间设为超过SLA时限
        if status in ("escalated",) or (status in ("accepted", "onsite") and i >= 19):
            created_at = now - timedelta(hours=PRIORITIES[priority]["sla_hours"] * random.uniform(1.5, 3.0))

        assignee = None
        if status not in ("pending",):
            assignee = staff[i % len(staff)]

        sla_hours = PRIORITIES[priority]["sla_hours"]
        rating = random.choice(_RATING_CHOICES) if status == "closed" else None
        resolved_at = None
        if status in ("verified", "closed"):
            resolved_at = created_at + timedelta(hours=random.uniform(0.5, sla_hours))

        orders.append({
            "order_id": "WO-2026%04d" % (1001 + i),
            "title": "%s-%s" % (ORDER_CATEGORIES[category]["name"], LOCATIONS[i % len(LOCATIONS)]),
            "channel": channel,
            "category": category,
            "required_skill": ORDER_CATEGORIES[category]["skill"],
            "priority": priority,
            "status": status,
            "location": LOCATIONS[i % len(LOCATIONS)],
            "description": "%s：%s 发现异常，请及时处理。" % (
                CHANNELS[channel]["source"], LOCATIONS[i % len(LOCATIONS)]),
            "reporter": CHANNELS[channel]["source"],
            "created_at": _fmt(created_at),
            "sla_deadline": _fmt(created_at + timedelta(hours=sla_hours)),
            "sla_hours": sla_hours,
            "assignee": assignee["name"] if assignee else None,
            "assignee_id": assignee["staff_id"] if assignee else None,
            "resolved_at": _fmt(resolved_at) if resolved_at else None,
            "rating": rating,
            "escalated": status == "escalated",
            "process": _gen_process_history(created_at, "closed" if status == "escalated" else status, assignee),
        })
    return orders


def seed_sla_rules() -> List[Dict]:
    """时效管控规则：各级别响应时限、预警阈值、升级策略"""
    return [
        {"priority": "urgent", "priority_name": "紧急", "response_hours": 2,
         "warning_threshold": 0.8, "escalate_multiplier": 2.0,
         "escalate_target": "运维中心主任", "desc": "紧急工单2小时内响应，超80%时限预警，超2倍时限自动升级至运维中心主任"},
        {"priority": "high", "priority_name": "高", "response_hours": 8,
         "warning_threshold": 0.8, "escalate_multiplier": 2.0,
         "escalate_target": "运维主管", "desc": "高优工单8小时内响应，超80%时限预警，超2倍时限自动升级至运维主管"},
        {"priority": "medium", "priority_name": "中", "response_hours": 24,
         "warning_threshold": 0.8, "escalate_multiplier": 2.0,
         "escalate_target": "班组负责人", "desc": "中优工单24小时内响应，超80%时限预警，超2倍时限升级至班组负责人"},
        {"priority": "low", "priority_name": "低", "response_hours": 72,
         "warning_threshold": 0.8, "escalate_multiplier": 2.0,
         "escalate_target": "班组负责人", "desc": "低优工单72小时内响应，超80%时限预警，超2倍时限升级至班组负责人"},
    ]


# ==============================================================================
# Pydantic 请求模型
# ==============================================================================

class OrderCreateRequest(BaseModel):
    title: str
    channel: str = "user"
    category: str = "electrical"
    priority: str = "medium"
    location: Optional[str] = None
    description: Optional[str] = None


class DispatchAssignRequest(BaseModel):
    order_id: str
    staff_id: str


class ProcessAdvanceRequest(BaseModel):
    order_id: str
    step: str
    note: Optional[str] = None
    rating: Optional[int] = None


class OrderQueryRequest(BaseModel):
    channel: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    location: Optional[str] = None
