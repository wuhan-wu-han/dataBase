"""种子数据灌入 —— 直接读取由 dump_mock.mjs 导出的 Mock JSON

保证首次启动即拥有与前端 Mock 完全一致的展示数据，之后所有增删改均落 SQLite。
幂等：仅当目标表为空时灌入。
"""
import json
import os

from database import SessionLocal
import models_workorder as W
import models_emergency as E

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    path = os.path.join(BASE_DIR, name)
    if not os.path.exists(path):
        print(f"⚠️  缺少 {name}，跳过对应种子数据")
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def seed_all():
    db = SessionLocal()
    try:
        _seed_workorder(db)
        _seed_emergency(db)
        db.commit()
        print("✅ 种子数据灌入完成（已存在的表将跳过）")
    except Exception as exc:
        db.rollback()
        print(f"❌ 种子数据灌入失败: {exc}")
        raise
    finally:
        db.close()


# ==================== 工单管理 ====================
def _seed_workorder(db):
    data = _load('seed_workorder.json')
    if not data:
        return

    if db.query(W.WorkOrder).count() == 0:
        for o in data['orders']:
            db.add(W.WorkOrder(
                order_id=o['order_id'], title=o['title'], channel=o['channel'],
                category=o['category'], priority=o['priority'], status=o['status'],
                location=o.get('location'), assignee=o.get('assignee'),
                reporter=o.get('reporter'), created_at=o.get('created_at'),
                sla_hours=o.get('sla_hours', 24), sla_deadline=o.get('sla_deadline'),
                resolved_at=o.get('resolved_at'), rating=o.get('rating'),
                escalated=bool(o.get('escalated')), description=o.get('description'),
                required_skill=o.get('required_skill'),
                distance_base=_dist_for(o['order_id']),
            ))

    if db.query(W.OrderTimeline).count() == 0:
        # Mock 仅提供 WO-2026-0001 的完整时间线，其余工单补齐创建记录
        first = data['process']['timeline']
        for t in first:
            db.add(W.OrderTimeline(order_id='WO-2026-0001', step=t['step'],
                                   step_name=t['step_name'], at=t['at'],
                                   operator=t['operator'], note=t.get('note', '')))
        done = {r.order_id for r in db.query(W.OrderTimeline.order_id).distinct()}
        for o in data['orders']:
            if o['order_id'] in done:
                continue
            db.add(W.OrderTimeline(order_id=o['order_id'], step='created',
                                   step_name='工单创建',
                                   at=(o.get('created_at') or '').replace('T', ''),
                                   operator='系统', note='自动创建'))
            if o['status'] in ('assigned', 'onsite', 'resolved', 'closed') and o.get('assignee'):
                db.add(W.OrderTimeline(order_id=o['order_id'], step='dispatched',
                                       step_name='派单',
                                       at=(o.get('created_at') or '').replace('T', ''),
                                       operator='调度中心',
                                       note=f"指派给{o['assignee']}"))

    if db.query(W.Staff).count() == 0:
        workload = {w['staff_id']: w for w in data['staffWorkload']['workload']}
        for s in data['staff']['staff']:
            w = workload.get(s['staff_id'], {})
            db.add(W.Staff(
                staff_id=s['staff_id'], name=s['name'],
                skills=','.join(s['skills']), status=s['status'],
                location=s.get('location'), phone=s.get('phone'),
                completed_orders=s.get('completed_orders', 0),
                avg_rating=s.get('avg_rating', 0.0),
                active_orders=w.get('active_orders', 0),
                distance_m=_staff_distance(s['staff_id']),
            ))

    if db.query(W.SlaRule).count() == 0:
        for r in data['slaRules']['rules']:
            db.add(W.SlaRule(
                priority=r['priority'], priority_name=r['priority_name'],
                response_hours=r['response_hours'],
                warning_threshold=r['warning_threshold'],
                escalate_multiplier=r['escalate_multiplier'],
                escalate_target=r['escalate_target'], desc=r['desc'],
            ))


def det_distance(key):
    """确定性距离：同一 ID 每次启动结果一致，避免派单评分抖动"""
    h = sum(ord(c) * (i + 7) for i, c in enumerate(str(key)))
    return 300 + (h * 137) % 6000


_dist_for = det_distance
_staff_distance = det_distance


# ==================== 应急预案 ====================
def _seed_emergency(db):
    data = _load('seed_emergency.json')
    if not data:
        return

    if db.query(E.PlanCategory).count() == 0:
        for c in data['categories']['categories']:
            db.add(E.PlanCategory(
                code=c['code'], name=c['name'], description=c.get('description'),
                sensor_metrics=json.dumps(c.get('sensor_metrics', []), ensure_ascii=False),
                drill_alarm_code=c.get('drill_alarm_code'),
            ))

    if db.query(E.EmergencyPlan).count() == 0:
        for p in data['plans']['plans']:
            db.add(E.EmergencyPlan(
                plan_id=p['plan_id'], plan_name=p['plan_name'], category=p['category'],
                level_min=p.get('level_min', 1), level_max=p.get('level_max', 1),
                priority=p.get('priority', 5), status=p.get('status', 'active'),
                commander=p.get('commander'),
                scope_cabins=json.dumps(p.get('scope_cabins', []), ensure_ascii=False),
                scope_zones=json.dumps(p.get('scope_zones', []), ensure_ascii=False),
                tags=json.dumps(p.get('tags', []), ensure_ascii=False),
                objective=p.get('objective'),
                created_at=p.get('created_at'), updated_at=p.get('updated_at'),
            ))
            for n in p.get('flow_nodes', []):
                db.add(E.FlowNode(
                    node_id=n['node_id'], plan_id=p['plan_id'], seq=n.get('seq', 1),
                    node_type=n.get('node_type'), title=n.get('title'),
                    desc=n.get('desc'), deadline_min=n.get('deadline_min', 30),
                    exit_condition=n.get('exit_condition'),
                ))

    if db.query(E.LiveMatch).count() == 0:
        for m in data['liveMatches']['matches']:
            db.add(E.LiveMatch(
                time=m.get('time'), alarm_id=m.get('alarm_id'),
                alarm_desc=(m.get('alarm') or {}).get('alarm_desc'),
                metric=(m.get('alarm') or {}).get('metric'),
                category_name=m.get('category_name'),
                best_plan_name=(m.get('best') or {}).get('plan_name'),
                best_score=(m.get('best') or {}).get('score', 0.0),
                auto_acked=bool(m.get('auto_acked')), fallback=bool(m.get('fallback')),
            ))

    if db.query(E.Activation).count() == 0:
        for a in data['activations']['activations']:
            db.add(E.Activation(
                activation_id=a['activation_id'], plan_id=a.get('plan_id'),
                plan_name=a.get('plan_name'), category_name=a.get('category_name'),
                trigger=a.get('trigger'), status=a.get('status', 'running'),
                activated_at=a.get('activated_at'), finished_at=a.get('finished_at'),
            ))
            for i, n in enumerate(a.get('nodes', [])):
                db.add(E.ActivationNode(
                    activation_id=a['activation_id'], node_id=n['node_id'], seq=i + 1,
                    node_type=n.get('node_type'), title=n.get('title'),
                    status=n.get('status', 'pending'), finished_at=n.get('finished_at'),
                ))


# ==================== 以下模块在后续阶段补齐 ====================
if __name__ == '__main__':
    seed_all()
