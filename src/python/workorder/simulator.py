#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工单全流程管理子模块 - 模拟引擎

功能：
1. 多渠道工单接入：预警自动生成、巡检上报、用户报修、政务转办
2. 智能派单：技能匹配 + 忙闲状态 + 位置距离三维评分，自动推荐最优运维人员
3. 过程跟踪：接单、到场、处置、验收、评价全流程时间线
4. 时效管控：SLA监控、超时预警、超期升级
"""

import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import (
    CHANNELS,
    LOCATIONS,
    ORDER_CATEGORIES,
    PRIORITIES,
    PROCESS_STEPS,
    now_str,
    seed_orders,
    seed_sla_rules,
    seed_staff,
)

# ==============================================================================
# 内存数据状态
# ==============================================================================

_staff = seed_staff()
_state = {
    "orders": seed_orders(_staff),
    "staff": _staff,
    "sla_rules": seed_sla_rules(),
    "dispatch_logs": [],
    "order_seq": 2001,
}

# 区域坐标（用于派单距离评分）
_LOCATION_COORDS = {
    "综合管廊A段": (100, 500),
    "综合管廊B段": (150, 500),
    "机加工一车间": (300, 400),
    "装配车间": (400, 350),
    "动力站房": (250, 250),
    "办公楼": (500, 300),
    "厂区道路": (350, 200),
    "变电站": (200, 150),
}
_MAX_DIST = 500.0

_STEP_NAME = {s["code"]: s["name"] for s in PROCESS_STEPS}
_STEP_ORDER = [s["code"] for s in PROCESS_STEPS]


def _parse_time(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


# ==============================================================================
# 总览 KPI
# ==============================================================================

def get_overview() -> Dict[str, Any]:
    orders = _state["orders"]
    active = [o for o in orders if o["status"] not in ("verified", "closed")]
    completed = [o for o in orders if o["status"] in ("verified", "closed")]
    sla = _sla_status_all()
    overdue = [s for s in sla if s["sla_status"] in ("overdue", "escalated")]

    response_minutes = []
    for o in completed:
        created = _parse_time(o["created_at"])
        resolved = _parse_time(o.get("resolved_at"))
        if created and resolved:
            response_minutes.append((resolved - created).total_seconds() / 60)
    avg_response_min = round(sum(response_minutes) / len(response_minutes), 1) if response_minutes else 0

    ratings = [o["rating"] for o in orders if o.get("rating")]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0

    return {
        "total_orders": len(orders),
        "active_orders": len(active),
        "completed_orders": len(completed),
        "pending_dispatch": len([o for o in orders if o["status"] == "pending"]),
        "overdue_orders": len(overdue),
        "escalated_orders": len([o for o in orders if o.get("escalated")]),
        "avg_response_min": avg_response_min,
        "avg_rating": avg_rating,
        "staff_total": len(_state["staff"]),
        "staff_idle": len([s for s in _state["staff"] if s["status"] == "idle"]),
        "channel_stats": _channel_counts(),
        "updated_at": now_str(),
    }


def _channel_counts() -> List[Dict]:
    counts = {}
    for o in _state["orders"]:
        ch = o["channel"]
        counts[ch] = counts.get(ch, 0) + 1
    return [{"channel": ch, "channel_name": CHANNELS[ch]["name"], "count": cnt}
            for ch, cnt in counts.items()]


# ==============================================================================
# 工单管理
# ==============================================================================

def list_orders(filters: Optional[Dict] = None) -> List[Dict]:
    orders = _state["orders"]
    if filters:
        for key, val in filters.items():
            if val:
                orders = [o for o in orders if str(o.get(key, "")).lower() == str(val).lower()]
    return orders


def get_order(order_id: str) -> Optional[Dict]:
    for o in _state["orders"]:
        if o["order_id"] == order_id:
            return o
    return None


def create_order(title: str, channel: str, category: str, priority: str,
                 location: Optional[str], description: Optional[str]) -> Dict[str, Any]:
    if channel not in CHANNELS:
        raise ValueError("未知接入渠道：%s" % channel)
    if category not in ORDER_CATEGORIES:
        raise ValueError("未知工单类别：%s" % category)
    if priority not in PRIORITIES:
        raise ValueError("未知优先级：%s" % priority)

    _state["order_seq"] += 1
    now = datetime.now()
    sla_hours = PRIORITIES[priority]["sla_hours"]
    order = {
        "order_id": "WO-2026%04d" % _state["order_seq"],
        "title": title or "%s-新工单" % ORDER_CATEGORIES[category]["name"],
        "channel": channel,
        "category": category,
        "required_skill": ORDER_CATEGORIES[category]["skill"],
        "priority": priority,
        "status": "pending",
        "location": location or random.choice(LOCATIONS),
        "description": description or "%s 渠道上报异常，请及时处理。" % CHANNELS[channel]["source"],
        "reporter": CHANNELS[channel]["source"],
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "sla_deadline": (now + timedelta(hours=sla_hours)).strftime("%Y-%m-%d %H:%M:%S"),
        "sla_hours": sla_hours,
        "assignee": None,
        "assignee_id": None,
        "resolved_at": None,
        "rating": None,
        "escalated": False,
        "process": [{"step": "pending", "step_name": "待派单",
                     "at": now.strftime("%Y-%m-%d %H:%M:%S"),
                     "operator": "系统", "note": "工单生成，等待派单"}],
    }
    _state["orders"].insert(0, order)
    return order


def get_order_stats() -> Dict[str, Any]:
    orders = _state["orders"]
    by_status = {}
    by_priority = {}
    for o in orders:
        by_status[o["status"]] = by_status.get(o["status"], 0) + 1
        by_priority[o["priority"]] = by_priority.get(o["priority"], 0) + 1
    return {
        "total": len(orders),
        "by_channel": _channel_counts(),
        "by_status": [{"status": k, "status_name": _STEP_NAME.get(k, k), "count": v}
                      for k, v in by_status.items()],
        "by_priority": [{"priority": k, "priority_name": PRIORITIES[k]["name"], "count": v}
                        for k, v in by_priority.items()],
        "trend_7d": _order_trend(),
    }


def _order_trend() -> List[Dict]:
    trend = []
    for i in range(7):
        day = datetime.now() - timedelta(days=6 - i)
        trend.append({
            "date": day.strftime("%m-%d"),
            "created": random.randint(8, 30),
            "closed": random.randint(6, 26),
        })
    return trend


# ==============================================================================
# 智能派单
# ==============================================================================

def _distance(location_a: str, location_b: str) -> float:
    ca = _LOCATION_COORDS.get(location_a, (300, 300))
    cb = _LOCATION_COORDS.get(location_b, (300, 300))
    return math.sqrt((ca[0] - cb[0]) ** 2 + (ca[1] - cb[1]) ** 2)


def recommend_dispatch(order_id: Optional[str] = None,
                       required_skill: Optional[str] = None,
                       location: Optional[str] = None) -> Dict[str, Any]:
    """三维评分推荐最优运维人员：技能匹配40 + 忙闲状态30 + 位置距离30"""
    order = None
    if order_id:
        order = get_order(order_id)
        if order is None:
            raise ValueError("工单不存在：%s" % order_id)
        skill = order["required_skill"]
        loc = order["location"]
    else:
        skill = required_skill or "电气维修"
        loc = location or random.choice(LOCATIONS)

    candidates = []
    for s in _state["staff"]:
        skill_score = 40.0 if skill in s["skills"] else 0.0
        availability = {"idle": 30.0, "busy": 12.0, "off": 0.0}.get(s["status"], 0.0)
        dist = _distance(loc, s["location"])
        proximity_score = round(30.0 * max(0.0, 1.0 - dist / _MAX_DIST), 1)
        rating_bonus = round((s["avg_rating"] - 4.0) * 5, 1)
        total = round(skill_score + availability + proximity_score + rating_bonus, 1)
        candidates.append({
            "staff_id": s["staff_id"],
            "name": s["name"],
            "skills": s["skills"],
            "status": s["status"],
            "status_name": {"idle": "空闲", "busy": "忙碌", "off": "休息"}.get(s["status"], s["status"]),
            "location": s["location"],
            "distance_m": round(dist, 0),
            "skill_match": skill in s["skills"],
            "score_breakdown": {
                "skill": skill_score,
                "availability": availability,
                "proximity": proximity_score,
                "rating_bonus": rating_bonus,
            },
            "total_score": total,
            "avg_rating": s["avg_rating"],
        })
    candidates.sort(key=lambda c: (-c["total_score"], not c["skill_match"]))
    return {
        "order_id": order_id,
        "required_skill": skill,
        "location": loc,
        "recommendation": candidates[0]["staff_id"] if candidates else None,
        "candidates": candidates[:5],
        "algorithm": "技能匹配(40) + 忙闲状态(30) + 位置距离(30) + 评价加成",
        "calculated_at": now_str(),
    }


def assign_order(order_id: str, staff_id: str) -> Dict[str, Any]:
    order = get_order(order_id)
    if order is None:
        raise ValueError("工单不存在：%s" % order_id)
    staff = get_staff(staff_id)
    if staff is None:
        raise ValueError("运维人员不存在：%s" % staff_id)
    if order["status"] not in ("pending", "assigned"):
        raise ValueError("工单已进入处置流程，不可重复派单")

    order["assignee"] = staff["name"]
    order["assignee_id"] = staff_id
    order["status"] = "assigned"
    order["process"].append({
        "step": "assigned", "step_name": "已派单", "at": now_str(),
        "operator": "智能派单引擎", "note": "分派至 %s（%s）" % (staff["name"], staff_id),
    })
    staff["status"] = "busy"
    _state["dispatch_logs"].insert(0, {
        "order_id": order_id, "staff_id": staff_id, "staff_name": staff["name"],
        "dispatched_at": now_str(), "method": "manual_confirm",
    })
    return order


def get_dispatch_logs(limit: int = 20) -> List[Dict]:
    return _state["dispatch_logs"][:limit]


# ==============================================================================
# 运维人员管理
# ==============================================================================

def list_staff(status: Optional[str] = None) -> List[Dict]:
    staff = _state["staff"]
    if status:
        staff = [s for s in staff if s["status"] == status]
    return staff


def get_staff(staff_id: str) -> Optional[Dict]:
    for s in _state["staff"]:
        if s["staff_id"] == staff_id:
            return s
    return None


def get_staff_workload() -> List[Dict]:
    workload = []
    for s in _state["staff"]:
        active = [o for o in _state["orders"]
                  if o.get("assignee_id") == s["staff_id"] and o["status"] not in ("verified", "closed")]
        workload.append({
            "staff_id": s["staff_id"],
            "name": s["name"],
            "status": s["status"],
            "status_name": {"idle": "空闲", "busy": "忙碌", "off": "休息"}.get(s["status"], s["status"]),
            "active_orders": len(active),
            "completed_orders": s["completed_orders"],
            "avg_rating": s["avg_rating"],
        })
    workload.sort(key=lambda w: -w["active_orders"])
    return workload


# ==============================================================================
# 过程跟踪
# ==============================================================================

def get_process(order_id: str) -> Dict[str, Any]:
    order = get_order(order_id)
    if order is None:
        raise ValueError("工单不存在：%s" % order_id)
    return {
        "order_id": order_id,
        "title": order["title"],
        "status": order["status"],
        "status_name": _STEP_NAME.get(order["status"], order["status"]),
        "current_step_index": _STEP_ORDER.index(order["status"]) if order["status"] in _STEP_ORDER else 0,
        "steps": PROCESS_STEPS,
        "timeline": order["process"],
    }


def advance_process(order_id: str, step: str, note: Optional[str] = None,
                    rating: Optional[int] = None) -> Dict[str, Any]:
    """推进流程节点：接单→到场→处置→验收→评价关闭"""
    order = get_order(order_id)
    if order is None:
        raise ValueError("工单不存在：%s" % order_id)
    if step not in _STEP_NAME:
        raise ValueError("未知流程节点：%s" % step)

    cur_idx = _STEP_ORDER.index(order["status"]) if order["status"] in _STEP_ORDER else 0
    next_idx = _STEP_ORDER.index(step)
    if next_idx <= cur_idx:
        raise ValueError("流程节点不可回退或重复：%s" % step)
    if next_idx > cur_idx + 1:
        raise ValueError("请按顺序推进流程，当前节点：%s" % order["status"])
    if order["status"] == "pending":
        raise ValueError("工单尚未派单，请先派单")

    order["status"] = step
    record = {
        "step": step, "step_name": _STEP_NAME[step], "at": now_str(),
        "operator": order.get("assignee") or "运维人员",
        "note": note or _STEP_NAME[step],
    }
    if step == "resolved":
        order["resolved_at"] = now_str()
    if step == "closed":
        order["rating"] = rating if rating else random.choice([5, 5, 4, 5, 3])
        record["note"] = note or "用户评价 %d 星，工单归档" % order["rating"]
        if order.get("assignee_id"):
            s = get_staff(order["assignee_id"])
            if s:
                s["completed_orders"] += 1
                s["status"] = "idle"
    order["process"].append(record)
    return order


# ==============================================================================
# 时效管控（SLA）
# ==============================================================================

def list_sla_rules() -> List[Dict]:
    return _state["sla_rules"]


def _sla_status_all() -> List[Dict]:
    now = datetime.now()
    results = []
    for o in _state["orders"]:
        if o["status"] in ("verified", "closed"):
            continue
        created = _parse_time(o["created_at"])
        deadline = _parse_time(o["sla_deadline"])
        if not created or not deadline:
            continue
        elapsed_h = (now - created).total_seconds() / 3600
        sla_h = o["sla_hours"]
        ratio = elapsed_h / sla_h if sla_h else 0
        if o.get("escalated") or ratio >= 2.0:
            status = "escalated"
        elif ratio > 1.0:
            status = "overdue"
        elif ratio >= 0.8:
            status = "warning"
        else:
            status = "normal"
        results.append({
            "order_id": o["order_id"],
            "title": o["title"],
            "priority": o["priority"],
            "priority_name": PRIORITIES[o["priority"]]["name"],
            "status": o["status"],
            "status_name": _STEP_NAME.get(o["status"], o["status"]),
            "assignee": o.get("assignee"),
            "elapsed_hours": round(elapsed_h, 1),
            "sla_hours": sla_h,
            "sla_deadline": o["sla_deadline"],
            "sla_status": status,
            "sla_status_name": {"normal": "正常", "warning": "临期预警",
                                "overdue": "已超时", "escalated": "已升级"}[status],
            "remaining_hours": round(sla_h - elapsed_h, 1),
        })
    order_rank = {"escalated": 0, "overdue": 1, "warning": 2, "normal": 3}
    results.sort(key=lambda r: (order_rank[r["sla_status"]], -r["elapsed_hours"]))
    return results


def sla_monitor() -> Dict[str, Any]:
    items = _sla_status_all()
    summary = {"normal": 0, "warning": 0, "overdue": 0, "escalated": 0}
    for it in items:
        summary[it["sla_status"]] += 1
    return {
        "monitored": len(items),
        "summary": summary,
        "warning_count": summary["warning"],
        "overdue_count": summary["overdue"],
        "escalated_count": summary["escalated"],
        "items": items,
        "checked_at": now_str(),
    }


def escalate_order(order_id: str) -> Dict[str, Any]:
    """超期升级：标记工单升级并通知对应负责人"""
    order = get_order(order_id)
    if order is None:
        raise ValueError("工单不存在：%s" % order_id)
    if order["status"] in ("verified", "closed"):
        raise ValueError("工单已完成，无需升级")

    rule = None
    for r in _state["sla_rules"]:
        if r["priority"] == order["priority"]:
            rule = r
            break
    target = rule["escalate_target"] if rule else "运维主管"
    order["escalated"] = True
    order["process"].append({
        "step": order["status"], "step_name": "超期升级", "at": now_str(),
        "operator": "时效管控引擎",
        "note": "工单超出SLA时限，自动升级至 %s 督办" % target,
    })
    return {
        "order_id": order_id,
        "escalated_to": target,
        "priority_name": PRIORITIES[order["priority"]]["name"],
        "message": "工单已升级至 %s 督办，并同步短信通知处置人" % target,
        "escalated_at": now_str(),
        "order": order,
    }
