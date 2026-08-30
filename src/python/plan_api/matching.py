#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字化预案管理子模块 - 预案智能匹配（纯函数，无状态）

匹配规则：
1. 门控：类别必须命中；预案状态为 active；告警级别在预案适用区间内
2. 评分（百分制）：类别 40 + 级别贴合 25 + 位置贴合 20 + 优先级 10 + 时效 5
3. 排序：(-总分, 优先级升序, 修订时间降序, plan_id 升序)
4. 输出：评分明细 + 中文原因；零候选时返回兜底提示
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import (
    FALLBACK_MESSAGE,
    METRIC_CATEGORY_MAP,
    PLAN_CATEGORIES,
)

# 管廊环境告警码（51xxx）→类别 的兜底映射表
# 与 tunnel_api/models.ENV_ALARM_CODES 对齐：51001/51011/...为预警，51002/51012/...为严重
_TUNNEL_ALARM_CATEGORY = {
    51001: "FIRE", 51002: "FIRE",        # temperature
    51011: "WEATHER", 51012: "WEATHER",  # humidity
    51021: "TOXIC", 51022: "TOXIC",      # o2
    51031: "TOXIC", 51032: "TOXIC",      # co
    51041: "TOXIC", 51042: "LEAK",       # h2s（严重按泄漏处置升级）
    51051: "LEAK", 51052: "LEAK",        # ch4
    51061: "FLOOD", 51062: "BURST",      # water_level（严重按爆管处置升级）
    51071: "FIRE", 51072: "FIRE",        # smoke
}


def _resolve_alarm_code_map() -> Dict[int, str]:
    """优先从管廊模块构建告警码→类别映射，失败时用本地兜底表"""
    try:
        try:
            from tunnel_api.models import ENV_ALARM_CODES
        except ImportError:
            from src.python.tunnel_api.models import ENV_ALARM_CODES
        mapping = {}
        for metric, codes in ENV_ALARM_CODES.items():
            category = METRIC_CATEGORY_MAP.get(metric)
            if not category:
                continue
            for code in codes.values() if isinstance(codes, dict) else codes:
                mapping[int(code)] = category
        if mapping:
            return mapping
    except Exception:
        pass
    return dict(_TUNNEL_ALARM_CATEGORY)


def derive_category(context: Dict[str, Any]) -> Optional[str]:
    """从匹配上下文推导预案类别：显式 category > metric > alarm_code"""
    category = (context.get("category") or "").strip().upper()
    if category and category in PLAN_CATEGORIES:
        return category
    metric = (context.get("metric") or "").strip().lower()
    if metric and metric in METRIC_CATEGORY_MAP:
        return METRIC_CATEGORY_MAP[metric]
    alarm_code = context.get("alarm_code")
    if alarm_code is not None:
        try:
            return _resolve_alarm_code_map().get(int(alarm_code))
        except (TypeError, ValueError):
            return None
    return None


def _parse_ts(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return None


def _scope_match(scope_list: List[str], value: Optional[str]) -> int:
    """作用域匹配：精确命中 10，通配或无位置信息 6，不命中 0"""
    if not value:
        return 6
    if "*" in scope_list:
        return 6
    if value in scope_list:
        return 10
    return 0


def match_plans(context: Dict[str, Any], plans: List[Dict[str, Any]],
                top_n: int = 3) -> Dict[str, Any]:
    """
    执行预案匹配。

    Args:
        context: {category?, metric?, alarm_code?, level, cabin?, zone?}
        plans: 全量预案列表
        top_n: 返回候选数上限

    Returns:
        {category, category_name, level, cabin, zone, candidates, fallback, fallback_message}
    """
    category = derive_category(context)
    try:
        level = int(context.get("level") or 1)
    except (TypeError, ValueError):
        level = 1
    level = max(1, min(2, level))
    cabin = context.get("cabin") or None
    zone = context.get("zone") or None

    result = {
        "category": category,
        "category_name": PLAN_CATEGORIES[category]["name"] if category else None,
        "level": level,
        "cabin": cabin,
        "zone": zone,
        "candidates": [],
        "fallback": False,
        "fallback_message": None,
    }

    if not category:
        result["fallback"] = True
        result["fallback_message"] = "无法识别预警类别，" + FALLBACK_MESSAGE
        return result

    now = datetime.now()
    scored = []
    for plan in plans:
        # 门控 1：类别
        if plan.get("category") != category:
            continue
        # 门控 2：状态
        if plan.get("status") != "active":
            continue
        # 门控 3：级别区间
        level_min = plan.get("level_min", 1)
        level_max = plan.get("level_max", 2)
        if not (level_min <= level <= level_max):
            continue

        reasons = []
        # 1) 类别命中 40 分
        s_category = 40
        reasons.append("类别命中：%s" % PLAN_CATEGORIES[category]["name"])

        # 2) 级别贴合 25 分
        span = level_max - level_min
        if span <= 0:
            s_level = 25
            reasons.append("级别精确匹配（仅适用%s级）" % ("预警" if level == 1 else "严重"))
        elif level_min < level < level_max:
            s_level = 25
            reasons.append("级别位于预案适用区间正中")
        else:
            s_level = 15
            reasons.append("级别位于预案适用区间边缘")

        # 3) 位置贴合 20 分（舱 10 + 区段 10）
        s_cabin = _scope_match(plan.get("scope_cabins") or ["*"], cabin)
        s_zone = _scope_match(plan.get("scope_zones") or ["*"], zone)
        if s_cabin == 10:
            reasons.append("舱室精确命中：%s" % cabin)
        if s_zone == 10:
            reasons.append("区段精确命中：%s" % zone)
        # 明确不命中（精确作用域且不含目标）→ 淘汰
        if (cabin and s_cabin == 0) or (zone and s_zone == 0):
            continue
        s_location = s_cabin + s_zone

        # 4) 优先级 10 分（数值越小优先级越高）
        priority = int(plan.get("priority") or 5)
        s_priority = max(0, 11 - priority)
        if priority <= 3:
            reasons.append("高优先级预案（P%d）" % priority)

        # 5) 时效 5 分（近 30 天修订满分，90 天线性衰减）
        updated = _parse_ts(plan.get("updated_at"))
        if updated is None:
            s_recency = 0
        else:
            days = max(0, (now - updated).days)
            if days <= 30:
                s_recency = 5
                reasons.append("近期修订（%d 天前），经验较新" % days)
            elif days >= 90:
                s_recency = 0
            else:
                s_recency = round(5 * (90 - days) / 60.0, 1)

        epoch = updated.timestamp() if updated else 0.0

        total = s_category + s_level + s_location + s_priority + s_recency
        scored.append({
            "plan": plan,
            "total": round(total, 1),
            "score_detail": {
                "category": s_category,
                "level_fit": s_level,
                "location": s_location,
                "priority": s_priority,
                "recency": s_recency,
            },
            "reasons": reasons,
            "priority": priority,
            "epoch": epoch,
            "updated_at": plan.get("updated_at") or "",
            "plan_id": plan.get("plan_id") or "",
        })

    if not scored:
        result["fallback"] = True
        result["fallback_message"] = (
            "类别「%s」级别 %d 无可用预案，" % (PLAN_CATEGORIES[category]["name"], level)
            + FALLBACK_MESSAGE
        )
        return result

    scored.sort(key=lambda item: (
        -item["total"],
        item["priority"],
        -item["epoch"],  # updated_at 降序
        item["plan_id"],
    ))

    candidates = []
    for rank, item in enumerate(scored[:max(1, top_n)], start=1):
        plan = item["plan"]
        candidates.append({
            "rank": rank,
            "plan_id": plan.get("plan_id"),
            "plan_name": plan.get("plan_name"),
            "category": plan.get("category"),
            "priority": plan.get("priority"),
            "status": plan.get("status"),
            "level_range": [plan.get("level_min"), plan.get("level_max")],
            "scope_cabins": plan.get("scope_cabins"),
            "scope_zones": plan.get("scope_zones"),
            "commander": plan.get("commander"),
            "objective": plan.get("objective"),
            "node_count": len(plan.get("flow_nodes") or []),
            "updated_at": plan.get("updated_at"),
            "score": item["total"],
            "score_detail": item["score_detail"],
            "reasons": item["reasons"],
        })

    result["candidates"] = candidates
    return result


def match_plans_json(context: Dict[str, Any], plans: List[Dict[str, Any]],
                     top_n: int = 3) -> Dict[str, Any]:
    """match_plans 的净化版出口（防 numpy 等类型泄漏）"""
    return json.loads(json.dumps(match_plans(context, plans, top_n), ensure_ascii=False))
