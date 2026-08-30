#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字化预案管理子模块 - 运行状态引擎

职责：
1. 持有全部可变状态：预案库、事件流、激活实例、实时匹配（锁保护）
2. 后台守护线程 10s 刷新：轮询管廊未处理告警 → 智能匹配 → 实时匹配流
3. 管廊耦合：函数内惰性导入（绝不顶层导入），不可用时优雅降级
4. 激活/演练：预案实例化、节点推进、完结登记

部署约束：依赖单 worker 部署（进程内全局状态）。
"""

import json
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from .matching import derive_category, match_plans
from .models import (
    DRILL_ALARM_CODES,
    LEVEL_NAMES,
    PLAN_CATEGORIES,
    now_str,
    seed_plans,
)

PLAN_REFRESH_SECONDS = 10
MAX_LIVE_MATCHES = 50
MAX_EVENTS = 200
MAX_MATCHED_ALARM_MEMORY = 500
AUTO_ACK_SCORE = 70  # 最优匹配分达到该值时联动确认管廊告警

_lock = threading.RLock()

# ---- 可变状态 ----
_plans: Dict[str, Dict[str, Any]] = {}
_events: List[Dict[str, Any]] = []
_activations: List[Dict[str, Any]] = []
_live_matches: List[Dict[str, Any]] = []
_matched_alarm_ids: set = set()
_match_seq = 0
_activation_seq = 0
_event_seq = 0
_today = ""
_today_match_count = 0
_today_drill_count = 0
_tunnel_linked = False
_tunnel_module = None
_tunnel_resolved = False


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _roll_day_locked() -> None:
    """跨天重置当日计数（调用方持锁）"""
    global _today, _today_match_count, _today_drill_count
    today = _today_str()
    if today != _today:
        _today = today
        _today_match_count = 0
        _today_drill_count = 0


def _sanitize(obj: Any) -> Any:
    """json 往返净化，防止 numpy 等类型泄漏到响应"""
    return json.loads(json.dumps(obj, ensure_ascii=False, default=str))


# ==============================================================================
# 管廊耦合（惰性导入 + 缓存 + 优雅降级）
# ==============================================================================

def _resolve_tunnel():
    """双路径惰性导入管廊模拟器模块；成功缓存，失败每轮重试"""
    global _tunnel_module, _tunnel_resolved, _tunnel_linked
    if _tunnel_resolved and _tunnel_module is not None:
        return _tunnel_module
    module = None
    try:
        from tunnel_api import simulator as module  # noqa
    except Exception:
        try:
            from src.python.tunnel_api import simulator as module  # noqa
        except Exception:
            module = None
    _tunnel_module = module
    _tunnel_resolved = module is not None
    _tunnel_linked = module is not None
    return module


def fetch_unhandled_tunnel_alarms() -> List[Dict[str, Any]]:
    """读取管廊快照中未处理告警；任何异常都返回空列表（降级）"""
    try:
        module = _resolve_tunnel()
        if module is None:
            return []
        snapshot = module.get_snapshot()
        alarms = (snapshot or {}).get("alarms") or []
        return [a for a in alarms if a.get("status") == "未处理"]
    except Exception:
        return []


# ==============================================================================
# 事件流
# ==============================================================================

def _add_event_locked(etype: str, ref_id: str, description: str,
                      level: int = 0, payload: Optional[Dict[str, Any]] = None) -> None:
    global _event_seq
    _event_seq += 1
    _events.append({
        "event_id": "EVT-%05d" % _event_seq,
        "time": now_str(),
        "type": etype,
        "level": level,
        "ref_id": ref_id,
        "description": description,
        "payload": payload or {},
    })
    if len(_events) > MAX_EVENTS:
        del _events[: len(_events) - MAX_EVENTS]


# ==============================================================================
# 预案库操作（调用方持锁）
# ==============================================================================

def _next_plan_id_locked(category: str) -> str:
    existing = [int(p["plan_id"].split("-")[-1]) for p in _plans.values()
                if p.get("category") == category and p.get("plan_id", "").startswith("EP-%s-" % category)]
    return "EP-%s-%03d" % (category, (max(existing) + 1) if existing else 1)


def _renumber_nodes_locked(plan: Dict[str, Any]) -> None:
    nodes = sorted(plan.get("flow_nodes") or [], key=lambda n: (n.get("seq") or 0, n.get("node_id") or ""))
    for idx, node in enumerate(nodes, start=1):
        node["seq"] = idx
        node["node_id"] = "FN-%02d" % idx
    plan["flow_nodes"] = nodes


def _touch_locked(plan: Dict[str, Any]) -> None:
    plan["updated_at"] = now_str()


# ==============================================================================
# 匹配与实时联动
# ==============================================================================

def run_match(context: Dict[str, Any], top_n: int = 3) -> Dict[str, Any]:
    """手动匹配（纯查询），计入当日匹配数并落事件流"""
    global _today_match_count
    with _lock:
        _roll_day_locked()
        plans = list(_plans.values())
    result = match_plans(context, plans, top_n=top_n)
    with _lock:
        _today_match_count += 1
        best = result["candidates"][0] if result.get("candidates") else None
        _add_event_locked(
            "match_manual" if not context.get("_source") else "match_" + str(context["_source"]),
            best["plan_id"] if best else "-",
            ("实时告警匹配" if context.get("_source") == "live" else "手动匹配") +
            ("：%s（%s 分）" % (best["plan_name"], best["score"]) if best else "：无候选，转人工决策"),
            level=int(context.get("level") or 1),
            payload={"category": result.get("category"), "cabin": context.get("cabin"),
                     "zone": context.get("zone"), "top_n": len(result.get("candidates") or [])},
        )
    return result


def _alarm_to_context(alarm: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "alarm_code": alarm.get("alarm_code"),
        "metric": alarm.get("metric"),
        "level": alarm.get("level", 1),
        "cabin": alarm.get("cabin"),
        "zone": alarm.get("zone_code") or alarm.get("zone"),
        "_source": "live",
        "_alarm": alarm,
    }


def _poll_tunnel_alarms() -> None:
    """一轮实时联动：拉未处理告警 → 匹配 → 入流 → （高分时）联动确认"""
    global _match_seq, _today_match_count, _tunnel_linked
    alarms = fetch_unhandled_tunnel_alarms()
    to_ack: List[str] = []

    with _lock:
        _roll_day_locked()
        _tunnel_linked = _tunnel_module is not None
        plans = list(_plans.values())
        for alarm in alarms:
            alarm_id = alarm.get("alarm_id")
            if not alarm_id or alarm_id in _matched_alarm_ids:
                continue
            context = _alarm_to_context(alarm)
            result = match_plans(context, plans, top_n=3)
            best = result["candidates"][0] if result.get("candidates") else None
            if best and best.get("score", 0) >= AUTO_ACK_SCORE:
                to_ack.append(alarm_id)
            _match_seq += 1
            _today_match_count += 1
            _live_matches.append({
                "match_id": "LM-%05d" % _match_seq,
                "time": now_str(),
                "alarm_id": alarm_id,
                "alarm": {
                    "alarm_code": alarm.get("alarm_code"),
                    "alarm_desc": alarm.get("alarm_desc"),
                    "metric": alarm.get("metric"),
                    "level": alarm.get("level"),
                    "severity": alarm.get("severity") or LEVEL_NAMES.get(alarm.get("level"), ""),
                    "cabin": alarm.get("cabin"),
                    "zone": alarm.get("zone_code") or alarm.get("zone"),
                    "timestamp": alarm.get("timestamp"),
                },
                "category": result.get("category"),
                "category_name": result.get("category_name"),
                "best": best,
                "candidates": result.get("candidates") or [],
                "fallback": result.get("fallback", False),
                "fallback_message": result.get("fallback_message"),
                "auto_acked": alarm_id in to_ack,
            })
            _matched_alarm_ids.add(alarm_id)
            _add_event_locked(
                "match_live", best["plan_id"] if best else "-",
                "管廊告警[%s] %s 匹配%s" % (
                    alarm_id,
                    alarm.get("alarm_desc") or alarm.get("metric"),
                    ("→ " + best["plan_name"] + "（%s 分）" % best["score"]) if best else "无候选，转人工决策",
                ),
                level=int(alarm.get("level") or 1),
                payload={"alarm_id": alarm_id, "cabin": alarm.get("cabin"),
                         "zone": alarm.get("zone_code") or alarm.get("zone")},
            )
        if len(_live_matches) > MAX_LIVE_MATCHES:
            del _live_matches[: len(_live_matches) - MAX_LIVE_MATCHES]
        if len(_matched_alarm_ids) > MAX_MATCHED_ALARM_MEMORY:
            _matched_alarm_ids.clear()
            _matched_alarm_ids.update(m["alarm_id"] for m in _live_matches)

    # 联动确认放在预案锁外，避免与管廊锁交叉持锁
    if to_ack:
        try:
            module = _resolve_tunnel()
            if module is not None:
                for alarm_id in to_ack:
                    module.acknowledge_alarm(alarm_id)
        except Exception:
            pass


def refresh_loop() -> None:
    """后台刷新主循环，单次异常不杀循环"""
    while True:
        try:
            _poll_tunnel_alarms()
        except Exception:
            pass
        threading.Event().wait(PLAN_REFRESH_SECONDS)


# ==============================================================================
# 激活与演练
# ==============================================================================

def activate_plan(plan_id: str, alarm_id: Optional[str] = None,
                  trigger_label: str = "") -> Dict[str, Any]:
    global _activation_seq
    with _lock:
        plan = _plans.get(plan_id)
        if plan is None:
            raise ValueError("预案不存在：%s" % plan_id)
        if plan.get("status") != "active":
            raise ValueError("预案状态为「%s」，仅启用中的预案可激活" % plan.get("status"))
        _activation_seq += 1
        activation = {
            "activation_id": "ACT-%05d" % _activation_seq,
            "plan_id": plan_id,
            "plan_name": plan.get("plan_name"),
            "category": plan.get("category"),
            "category_name": PLAN_CATEGORIES.get(plan.get("category"), {}).get("name"),
            "trigger": trigger_label or ("告警联动 %s" % alarm_id if alarm_id else "手动激活"),
            "alarm_id": alarm_id,
            "status": "running",
            "activated_at": now_str(),
            "finished_at": None,
            "nodes": [
                {
                    "node_id": node.get("node_id"),
                    "title": node.get("title"),
                    "node_type": node.get("node_type"),
                    "status": "pending",
                    "finished_at": None,
                }
                for node in (plan.get("flow_nodes") or [])
            ],
        }
        _activations.append(activation)
        _add_event_locked(
            "activate", plan_id,
            "预案激活：%s（%s）" % (plan.get("plan_name"), activation["trigger"]),
            level=2,
            payload={"activation_id": activation["activation_id"]},
        )
        return _sanitize(dict(activation))


def mark_node_done(activation_id: str, node_id: str) -> Dict[str, Any]:
    with _lock:
        activation = next((a for a in _activations if a["activation_id"] == activation_id), None)
        if activation is None:
            raise ValueError("激活实例不存在：%s" % activation_id)
        if activation["status"] == "finished":
            raise ValueError("该实例已完结")
        node = next((n for n in activation["nodes"] if n["node_id"] == node_id), None)
        if node is None:
            raise ValueError("节点不存在：%s" % node_id)
        if node["status"] == "done":
            raise ValueError("节点已完成：%s" % node_id)
        node["status"] = "done"
        node["finished_at"] = now_str()
        done = sum(1 for n in activation["nodes"] if n["status"] in ("done", "skipped"))
        return _sanitize({"activation_id": activation_id, "node_id": node_id,
                          "progress": "%d/%d" % (done, len(activation["nodes"]))})


def finish_activation(activation_id: str) -> Dict[str, Any]:
    with _lock:
        activation = next((a for a in _activations if a["activation_id"] == activation_id), None)
        if activation is None:
            raise ValueError("激活实例不存在：%s" % activation_id)
        if activation["status"] == "finished":
            raise ValueError("该实例已完结")
        pending = [n for n in activation["nodes"] if n["status"] == "pending"]
        if pending:
            raise ValueError("尚有 %d 个节点未完成，请先完成或跳过" % len(pending))
        activation["status"] = "finished"
        activation["finished_at"] = now_str()
        _add_event_locked(
            "finish", activation["plan_id"],
            "处置完结：%s（%s）" % (activation.get("plan_name"), activation_id),
            payload={"activation_id": activation_id},
        )
        return _sanitize(dict(activation))


def run_drill(category: str, level: int = 1, cabin: Optional[str] = None,
              zone: Optional[str] = None, description: str = "",
              activate_best: bool = True) -> Dict[str, Any]:
    """演练：生成 52xxx 演练事件，执行匹配，可选激活最优预案"""
    global _today_drill_count
    category = (category or "").strip().upper()
    if category not in PLAN_CATEGORIES:
        raise ValueError("未知预案类别：%s" % category)
    level = max(1, min(2, int(level or 1)))
    alarm_code = DRILL_ALARM_CODES[category]
    context = {
        "category": category,
        "level": level,
        "cabin": cabin,
        "zone": zone,
        "_source": "drill",
    }
    result = run_match(context, top_n=3)
    activation = None
    with _lock:
        _roll_day_locked()
        _today_drill_count += 1
        _add_event_locked(
            "drill", str(alarm_code),
            "演练事件：%s（%s，级别 %s%s）" % (
                PLAN_CATEGORIES[category]["name"],
                description or "桌面演练",
                LEVEL_NAMES.get(level, ""),
                "，位置 %s-%s" % (cabin, zone) if cabin or zone else "",
            ),
            level=level,
            payload={"alarm_code": alarm_code, "category": category},
        )
    if activate_best and result.get("candidates"):
        best = result["candidates"][0]
        activation = activate_plan(
            best["plan_id"],
            trigger_label="演练触发（52%03d）" % (DRILL_ALARM_CODES[category] - 52000),
        )
    return {"drill_alarm_code": alarm_code, "match": result, "activation": activation}


# ==============================================================================
# 快照
# ==============================================================================

def get_overview() -> Dict[str, Any]:
    with _lock:
        _roll_day_locked()
        plans = list(_plans.values())
        active_count = sum(1 for p in plans if p.get("status") == "active")
        categories_covered = {p.get("category") for p in plans}
        running = [a for a in _activations if a["status"] == "running"]
        finished = [a for a in _activations if a["status"] == "finished"]
        scores = [m["best"]["score"] for m in _live_matches
                  if m.get("best") and isinstance(m["best"].get("score"), (int, float))]
        return _sanitize({
            "total_plans": len(plans),
            "active_plans": active_count,
            "draft_plans": sum(1 for p in plans if p.get("status") == "draft"),
            "categories_total": len(PLAN_CATEGORIES),
            "categories_covered": len(categories_covered),
            "today_match_count": _today_match_count,
            "today_drill_count": _today_drill_count,
            "running_activations": len(running),
            "finished_activations": len(finished),
            "avg_match_score": round(sum(scores) / len(scores), 1) if scores else None,
            "tunnel_linked": _tunnel_linked,
            "unhandled_tunnel_alarms": len(fetch_unhandled_tunnel_alarms()),
            "node_count": sum(len(p.get("flow_nodes") or []) for p in plans),
            "generated_at": now_str(),
        })


def get_category_stats() -> List[Dict[str, Any]]:
    with _lock:
        plans = list(_plans.values())
    stats = []
    for code, meta in PLAN_CATEGORIES.items():
        cat_plans = [p for p in plans if p.get("category") == code]
        stats.append({
            "code": code,
            "name": meta["name"],
            "description": meta["description"],
            "sensor_metrics": meta["sensor_metrics"],
            "drill_alarm_code": DRILL_ALARM_CODES[code],
            "plan_count": len(cat_plans),
            "active_count": sum(1 for p in cat_plans if p.get("status") == "active"),
        })
    return _sanitize(stats)


def list_plans(category: Optional[str] = None, status: Optional[str] = None,
               keyword: Optional[str] = None) -> List[Dict[str, Any]]:
    with _lock:
        plans = list(_plans.values())
    if category:
        plans = [p for p in plans if p.get("category") == category.upper()]
    if status:
        plans = [p for p in plans if p.get("status") == status]
    if keyword:
        kw = keyword.strip()
        plans = [p for p in plans if kw in (p.get("plan_name") or "") or kw in (p.get("objective") or "")]
    plans.sort(key=lambda p: (p.get("category") or "", int(p.get("priority") or 9), p.get("plan_id") or ""))
    return _sanitize(plans)


def get_plan(plan_id: str) -> Dict[str, Any]:
    with _lock:
        plan = _plans.get(plan_id)
        return _sanitize(dict(plan)) if plan else None


def create_plan(data: Dict[str, Any]) -> Dict[str, Any]:
    category = (data.get("category") or "").strip().upper()
    if category not in PLAN_CATEGORIES:
        raise ValueError("未知预案类别：%s（可选：%s）" % (category, ",".join(PLAN_CATEGORIES)))
    status = data.get("status") or "draft"
    if status not in ("active", "draft", "deprecated"):
        raise ValueError("非法状态：%s" % status)
    level_min = int(data.get("level_min") or 1)
    level_max = int(data.get("level_max") or 2)
    if not (1 <= level_min <= level_max <= 2):
        raise ValueError("级别区间非法：需满足 1 <= level_min <= level_max <= 2")
    priority = int(data.get("priority") or 5)
    if not (1 <= priority <= 9):
        raise ValueError("优先级需在 1-9 之间")
    with _lock:
        plan_id = _next_plan_id_locked(category)
        plan = {
            "plan_id": plan_id,
            "plan_name": (data.get("plan_name") or "").strip(),
            "category": category,
            "level_min": level_min,
            "level_max": level_max,
            "priority": priority,
            "status": status,
            "scope_cabins": data.get("scope_cabins") or ["*"],
            "scope_zones": data.get("scope_zones") or ["*"],
            "objective": data.get("objective") or "",
            "commander": data.get("commander") or "",
            "tags": data.get("tags") or [],
            "version_note": data.get("version_note") or "",
            "flow_nodes": [],
            "created_at": now_str(),
            "updated_at": now_str(),
        }
        _plans[plan_id] = plan
        _add_event_locked("plan_create", plan_id, "新建预案：%s" % plan["plan_name"])
        return _sanitize(dict(plan))


def update_plan(plan_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    with _lock:
        plan = _plans.get(plan_id)
        if plan is None:
            raise ValueError("预案不存在：%s" % plan_id)
        if data.get("category") is not None:
            category = str(data["category"]).strip().upper()
            if category not in PLAN_CATEGORIES:
                raise ValueError("未知预案类别：%s" % category)
            plan["category"] = category
        if data.get("status") is not None:
            if data["status"] not in ("active", "draft", "deprecated"):
                raise ValueError("非法状态：%s" % data["status"])
            plan["status"] = data["status"]
        level_min = data.get("level_min") if data.get("level_min") is not None else plan["level_min"]
        level_max = data.get("level_max") if data.get("level_max") is not None else plan["level_max"]
        if not (1 <= int(level_min) <= int(level_max) <= 2):
            raise ValueError("级别区间非法：需满足 1 <= level_min <= level_max <= 2")
        plan["level_min"] = int(level_min)
        plan["level_max"] = int(level_max)
        if data.get("priority") is not None:
            priority = int(data["priority"])
            if not (1 <= priority <= 9):
                raise ValueError("优先级需在 1-9 之间")
            plan["priority"] = priority
        for field in ("plan_name", "objective", "commander", "version_note"):
            if data.get(field) is not None:
                plan[field] = str(data[field])
        for field in ("scope_cabins", "scope_zones", "tags"):
            if data.get(field) is not None:
                plan[field] = data[field]
        _touch_locked(plan)
        _add_event_locked("plan_update", plan_id, "修订预案：%s" % plan["plan_name"])
        return _sanitize(dict(plan))


def delete_plan(plan_id: str) -> None:
    with _lock:
        plan = _plans.pop(plan_id, None)
        if plan is None:
            raise ValueError("预案不存在：%s" % plan_id)
        _add_event_locked("plan_delete", plan_id, "删除预案：%s" % plan.get("plan_name"))


def add_flow_node(plan_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    with _lock:
        plan = _plans.get(plan_id)
        if plan is None:
            raise ValueError("预案不存在：%s" % plan_id)
        if data.get("node_type") not in ("detect", "notify", "isolate", "rescue", "restore", "verify"):
            raise ValueError("非法节点类型：%s" % data.get("node_type"))
        node = {
            "node_id": "",
            "seq": data.get("seq") or len(plan["flow_nodes"]) + 1,
            "node_type": data["node_type"],
            "title": data.get("title") or "",
            "desc": data.get("desc") or "",
            "deadline_min": int(data.get("deadline_min") or 30),
            "responsible": data.get("responsible") or {"org": "", "role": "", "contact": "", "cooperators": []},
            "resources": data.get("resources") or [],
            "actions": data.get("actions") or [],
            "exit_condition": data.get("exit_condition") or "",
        }
        plan["flow_nodes"].append(node)
        _renumber_nodes_locked(plan)
        _touch_locked(plan)
        _add_event_locked("node_add", plan_id, "新增流程节点：%s（%s）" % (node["title"], plan_id))
        return _sanitize(dict(plan))


def update_flow_node(plan_id: str, node_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    with _lock:
        plan = _plans.get(plan_id)
        if plan is None:
            raise ValueError("预案不存在：%s" % plan_id)
        node = next((n for n in plan["flow_nodes"] if n["node_id"] == node_id), None)
        if node is None:
            raise ValueError("节点不存在：%s" % node_id)
        if data.get("node_type") is not None:
            if data["node_type"] not in ("detect", "notify", "isolate", "rescue", "restore", "verify"):
                raise ValueError("非法节点类型：%s" % data["node_type"])
            node["node_type"] = data["node_type"]
        for field in ("title", "desc", "exit_condition"):
            if data.get(field) is not None:
                node[field] = str(data[field])
        if data.get("deadline_min") is not None:
            node["deadline_min"] = int(data["deadline_min"])
        if data.get("seq") is not None:
            node["seq"] = int(data["seq"])
        for field in ("responsible", "resources", "actions"):
            if data.get(field) is not None:
                node[field] = data[field]
        _renumber_nodes_locked(plan)
        _touch_locked(plan)
        _add_event_locked("node_update", plan_id, "修订流程节点：%s（%s）" % (node["title"], plan_id))
        return _sanitize(dict(plan))


def delete_flow_node(plan_id: str, node_id: str) -> Dict[str, Any]:
    with _lock:
        plan = _plans.get(plan_id)
        if plan is None:
            raise ValueError("预案不存在：%s" % plan_id)
        before = len(plan["flow_nodes"])
        plan["flow_nodes"] = [n for n in plan["flow_nodes"] if n["node_id"] != node_id]
        if len(plan["flow_nodes"]) == before:
            raise ValueError("节点不存在：%s" % node_id)
        _renumber_nodes_locked(plan)
        _touch_locked(plan)
        _add_event_locked("node_delete", plan_id, "删除流程节点：%s（%s）" % (node_id, plan_id))
        return _sanitize(dict(plan))


def list_activations(status: Optional[str] = None) -> List[Dict[str, Any]]:
    with _lock:
        activations = list(_activations)
    if status:
        activations = [a for a in activations if a.get("status") == status]
    return _sanitize(list(reversed(activations)))


def get_live_matches(limit: int = 20) -> List[Dict[str, Any]]:
    with _lock:
        matches = list(_live_matches)
    return _sanitize(list(reversed(matches))[:max(1, limit)])


def get_events(limit: int = 50) -> List[Dict[str, Any]]:
    with _lock:
        events = list(_events)
    return _sanitize(list(reversed(events))[:max(1, limit)])


# ==============================================================================
# 引擎启动
# ==============================================================================

def initialize() -> None:
    """加载种子预案（幂等）"""
    with _lock:
        if _plans:
            return
        for plan in seed_plans():
            _plans[plan["plan_id"]] = plan
        _add_event_locked("system", "-", "预案引擎初始化，载入种子预案 %d 份" % len(_plans))


_engine_started = False


def start_engine() -> None:
    """启动后台刷新线程（幂等，守护线程，异常兜底由循环内部承担）"""
    global _engine_started
    with _lock:
        if _engine_started:
            return
        _engine_started = True
    initialize()
    thread = threading.Thread(target=refresh_loop, name="plan-engine-refresh", daemon=True)
    thread.start()
