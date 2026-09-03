#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""应急预案管理 —— SQLite 读写适配层

与 workorder.store 同一套思路：simulator 继续在内存 dict 上做业务计算，
本层负责「启动时还原」与「变更后写回」。嵌套结构（流程节点、资源、动作、
匹配候选）按关系表拆列存储，数组/对象类字段以 JSON 文本落列。
"""

import traceback
from typing import Any, Dict, List

try:                                                  # 从 src/python 目录启动
    from persistence import DB_PATH, SessionLocal, from_json, init_db, to_json
    from persistence.plan_tables import (
        PlanActivation,
        PlanActivationNode,
        PlanCounter,
        PlanDailyStat,
        PlanEvent,
        PlanFlowNode,
        PlanLiveMatch,
        PlanMatchedAlarm,
        PlanRecord,
    )
except ImportError:                                   # 从仓库根目录以包路径启动
    from src.python.persistence import DB_PATH, SessionLocal, from_json, init_db, to_json
    from src.python.persistence.plan_tables import (
        PlanActivation,
        PlanActivationNode,
        PlanCounter,
        PlanDailyStat,
        PlanEvent,
        PlanFlowNode,
        PlanLiveMatch,
        PlanMatchedAlarm,
        PlanRecord,
    )

COUNTER_KEYS = ("match_seq", "activation_seq", "event_seq")


def _log_error(action: str, exc: Exception) -> None:
    print("[plan.store] %s 失败：%s" % (action, exc))
    traceback.print_exc()


def ensure_schema() -> None:
    init_db()


# ==============================================================================
# 行 ↔ dict 映射
# ==============================================================================

_PLAN_TEXT_FIELDS = ("plan_name", "category", "objective", "commander",
                     "version_note", "created_at", "updated_at")
_PLAN_INT_FIELDS = ("level_min", "level_max", "priority")


def _plan_from_row(row: PlanRecord, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    plan = {key: getattr(row, key) for key in _PLAN_TEXT_FIELDS}
    plan.update({key: getattr(row, key) for key in _PLAN_INT_FIELDS})
    plan["plan_id"] = row.plan_id
    plan["status"] = row.status
    plan["scope_cabins"] = from_json(row.scope_cabins)
    plan["scope_zones"] = from_json(row.scope_zones)
    plan["tags"] = from_json(row.tags)
    plan["flow_nodes"] = nodes
    return plan


def _node_from_row(row: PlanFlowNode) -> Dict[str, Any]:
    return {
        "node_id": row.node_id,
        "seq": row.seq,
        "node_type": row.node_type,
        "title": row.title,
        "desc": row.desc,
        "deadline_min": row.deadline_min,
        "responsible": from_json(row.responsible, {}),
        "resources": from_json(row.resources),
        "actions": from_json(row.actions),
        "exit_condition": row.exit_condition,
    }


# ==============================================================================
# 读取：库 → 内存
# ==============================================================================

def has_data() -> bool:
    db = SessionLocal()
    try:
        return db.query(PlanRecord).count() > 0
    finally:
        db.close()


def load_plans() -> Dict[str, Dict[str, Any]]:
    db = SessionLocal()
    try:
        nodes_by_plan: Dict[str, List[Dict[str, Any]]] = {}
        node_rows = db.query(PlanFlowNode).order_by(PlanFlowNode.plan_id,
                                                    PlanFlowNode.seq).all()
        for row in node_rows:
            nodes_by_plan.setdefault(row.plan_id, []).append(_node_from_row(row))
        plans = {}
        for row in db.query(PlanRecord).order_by(PlanRecord.plan_id).all():
            plans[row.plan_id] = _plan_from_row(row, nodes_by_plan.get(row.plan_id, []))
        return plans
    finally:
        db.close()


def load_activations() -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        nodes_by_act: Dict[str, List[Dict[str, Any]]] = {}
        for row in db.query(PlanActivationNode).order_by(PlanActivationNode.activation_id,
                                                         PlanActivationNode.id).all():
            nodes_by_act.setdefault(row.activation_id, []).append({
                "node_id": row.node_id, "title": row.title, "node_type": row.node_type,
                "status": row.status, "finished_at": row.finished_at,
            })
        acts = []
        for row in db.query(PlanActivation).order_by(PlanActivation.activation_id).all():
            acts.append({
                "activation_id": row.activation_id, "plan_id": row.plan_id,
                "plan_name": row.plan_name, "category": row.category,
                "category_name": row.category_name, "trigger": row.trigger,
                "alarm_id": row.alarm_id, "status": row.status,
                "activated_at": row.activated_at, "finished_at": row.finished_at,
                "nodes": nodes_by_act.get(row.activation_id, []),
            })
        return acts
    finally:
        db.close()


def load_live_matches() -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = db.query(PlanLiveMatch).order_by(PlanLiveMatch.id).all()
        return [{
            "match_id": r.match_id, "time": r.time, "alarm_id": r.alarm_id,
            "alarm": from_json(r.alarm, {}), "category": r.category,
            "category_name": r.category_name,
            "best": from_json(r.best, None) if r.best else None,
            "candidates": from_json(r.candidates),
            "fallback": bool(r.fallback), "fallback_message": r.fallback_message,
            "auto_acked": bool(r.auto_acked),
        } for r in rows]
    finally:
        db.close()


def load_events(limit: int = 200) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = db.query(PlanEvent).order_by(PlanEvent.id.desc()).limit(limit).all()
        events = [{
            "event_id": r.event_id, "time": r.time, "type": r.event_type,
            "level": r.level, "ref_id": r.ref_id,
            "description": r.description, "payload": from_json(r.payload, {}),
        } for r in reversed(rows)]
        return events
    finally:
        db.close()


def load_counters() -> Dict[str, int]:
    db = SessionLocal()
    try:
        values = {r.name: r.value for r in db.query(PlanCounter).all()}
        return {key: int(values.get(key, 0) or 0) for key in COUNTER_KEYS}
    finally:
        db.close()


def load_daily(day: str) -> Dict[str, int]:
    db = SessionLocal()
    try:
        row = db.query(PlanDailyStat).filter(PlanDailyStat.day == day).first()
        if row is None:
            return {"match_count": 0, "drill_count": 0}
        return {"match_count": row.match_count or 0, "drill_count": row.drill_count or 0}
    finally:
        db.close()


def load_matched_alarm_ids() -> List[str]:
    db = SessionLocal()
    try:
        return [r.alarm_id for r in db.query(PlanMatchedAlarm).all()]
    finally:
        db.close()


# ==============================================================================
# 写入：内存 → 库
# ==============================================================================

def seed_plans(plans: List[Dict[str, Any]]) -> None:
    """首次把种子预案整体落库"""
    db = SessionLocal()
    try:
        for plan in plans:
            _add_plan_row(db, plan)
            _write_flow_nodes(db, plan)
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("种子预案落库", exc)
        raise
    finally:
        db.close()


def _add_plan_row(db, plan: Dict[str, Any]) -> PlanRecord:
    row = db.query(PlanRecord).filter(PlanRecord.plan_id == plan["plan_id"]).first()
    if row is None:
        row = PlanRecord(plan_id=plan["plan_id"])
        db.add(row)
    for key in _PLAN_TEXT_FIELDS:
        setattr(row, key, plan.get(key))
    for key in _PLAN_INT_FIELDS:
        setattr(row, key, plan.get(key))
    row.status = plan.get("status")
    row.scope_cabins = to_json(plan.get("scope_cabins"))
    row.scope_zones = to_json(plan.get("scope_zones"))
    row.tags = to_json(plan.get("tags"))
    db.flush()                                          # 父行先落库，子表外键才成立
    return row


def _write_flow_nodes(db, plan: Dict[str, Any]) -> None:
    db.query(PlanFlowNode).filter(PlanFlowNode.plan_id == plan["plan_id"]).delete()
    for node in plan.get("flow_nodes") or []:
        db.add(PlanFlowNode(
            plan_id=plan["plan_id"], node_id=node.get("node_id"), seq=node.get("seq", 1),
            node_type=node.get("node_type"), title=node.get("title"),
            desc=node.get("desc"), deadline_min=node.get("deadline_min"),
            responsible=to_json(node.get("responsible") or {}),
            resources=to_json(node.get("resources")), actions=to_json(node.get("actions")),
            exit_condition=node.get("exit_condition"),
        ))


def upsert_plan(plan: Dict[str, Any]) -> None:
    """预案主体 + 流程节点全量刷新（节点增删后 seq 会整体重排，重写比增量更可靠）"""
    db = SessionLocal()
    try:
        _add_plan_row(db, plan)
        _write_flow_nodes(db, plan)
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("写入预案 %s" % plan.get("plan_id"), exc)
    finally:
        db.close()


def delete_plan(plan_id: str) -> None:
    db = SessionLocal()
    try:
        db.query(PlanFlowNode).filter(PlanFlowNode.plan_id == plan_id).delete()
        db.query(PlanRecord).filter(PlanRecord.plan_id == plan_id).delete()
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("删除预案 %s" % plan_id, exc)
    finally:
        db.close()


def insert_event(event: Dict[str, Any], keep: int) -> None:
    db = SessionLocal()
    try:
        db.add(PlanEvent(
            event_id=event["event_id"], time=event.get("time"),
            event_type=event.get("type"), level=event.get("level", 0),
            ref_id=event.get("ref_id"), description=event.get("description"),
            payload=to_json(event.get("payload") or {}),
        ))
        keep_ids = [r[0] for r in db.query(PlanEvent.id).order_by(PlanEvent.id.desc())
                    .limit(keep).all()]
        if keep_ids:
            db.query(PlanEvent).filter(~PlanEvent.id.in_(keep_ids)).delete(synchronize_session=False)
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("写入事件流", exc)
    finally:
        db.close()


def insert_activation(activation: Dict[str, Any]) -> None:
    db = SessionLocal()
    try:
        _add_activation_row(db, activation)
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("写入激活实例 %s" % activation.get("activation_id"), exc)
    finally:
        db.close()


def _add_activation_row(db, activation: Dict[str, Any]) -> None:
    row = db.query(PlanActivation).filter(
        PlanActivation.activation_id == activation["activation_id"]).first()
    if row is None:
        row = PlanActivation(activation_id=activation["activation_id"])
        db.add(row)
    for key in ("plan_id", "plan_name", "category", "category_name", "trigger",
                "alarm_id", "status", "activated_at", "finished_at"):
        setattr(row, key, activation.get(key))
    db.flush()                                          # 父行先落库，子表外键才成立
    db.query(PlanActivationNode).filter(
        PlanActivationNode.activation_id == activation["activation_id"]).delete()
    for node in activation.get("nodes") or []:
        db.add(PlanActivationNode(
            activation_id=activation["activation_id"], node_id=node.get("node_id"),
            title=node.get("title"), node_type=node.get("node_type"),
            status=node.get("status"), finished_at=node.get("finished_at"),
        ))


def upsert_activation(activation: Dict[str, Any]) -> None:
    """节点完成 / 实例完结时刷新整条实例（节点数量小，全量重写）"""
    db = SessionLocal()
    try:
        _add_activation_row(db, activation)
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("更新激活实例 %s" % activation.get("activation_id"), exc)
    finally:
        db.close()


def insert_live_match(match: Dict[str, Any], keep: int) -> None:
    db = SessionLocal()
    try:
        db.add(PlanLiveMatch(
            match_id=match.get("match_id"), time=match.get("time"),
            alarm_id=match.get("alarm_id"), alarm=to_json(match.get("alarm") or {}),
            category=match.get("category"), category_name=match.get("category_name"),
            best=to_json(match["best"]) if match.get("best") else None,
            candidates=to_json(match.get("candidates")),
            fallback=bool(match.get("fallback")),
            fallback_message=match.get("fallback_message"),
            auto_acked=bool(match.get("auto_acked")),
        ))
        keep_ids = [r[0] for r in db.query(PlanLiveMatch.id).order_by(PlanLiveMatch.id.desc())
                    .limit(keep).all()]
        if keep_ids:
            db.query(PlanLiveMatch).filter(
                ~PlanLiveMatch.id.in_(keep_ids)).delete(synchronize_session=False)
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("写入实时匹配", exc)
    finally:
        db.close()


def set_counters(values: Dict[str, int]) -> None:
    db = SessionLocal()
    try:
        for key in COUNTER_KEYS:
            if key not in values:
                continue
            row = db.query(PlanCounter).filter(PlanCounter.name == key).first()
            if row is None:
                db.add(PlanCounter(name=key, value=int(values[key])))
            else:
                row.value = int(values[key])
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("写入序列号", exc)
    finally:
        db.close()


def set_daily(day: str, match_count: int, drill_count: int) -> None:
    db = SessionLocal()
    try:
        row = db.query(PlanDailyStat).filter(PlanDailyStat.day == day).first()
        if row is None:
            db.add(PlanDailyStat(day=day, match_count=match_count, drill_count=drill_count))
        else:
            row.match_count = match_count
            row.drill_count = drill_count
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("写入当日统计", exc)
    finally:
        db.close()


def add_matched_alarms(alarm_ids: List[str], at: str) -> None:
    if not alarm_ids:
        return
    db = SessionLocal()
    try:
        existing = {r.alarm_id for r in db.query(PlanMatchedAlarm).all()}
        for alarm_id in alarm_ids:
            if alarm_id in existing:
                continue
            db.add(PlanMatchedAlarm(alarm_id=alarm_id, matched_at=at))
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("写入已匹配告警", exc)
    finally:
        db.close()
