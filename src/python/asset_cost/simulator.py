#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资产价值与成本管理子模块 - 模拟引擎

功能：
1. 资产台账管理（增删改查）
2. 折旧自动计算（直线法/双倍余额递减/年数总和）
3. 运维成本归集与统计分析
4. LCC 全生命周期成本计算
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from .models import (
    seed_assets, seed_cost_records, seed_lcc_analyses,
    calc_asset_values, ASSET_CATEGORIES, PIPE_MATERIALS, REGIONS,
    DEPR_METHODS, LCCAnalysisRequest,
)

_assets = seed_assets()
_cost_records = seed_cost_records()
_lcc_analyses = seed_lcc_analyses()


def _init_asset_db():
    """初始化数据库，空库注入种子，否则从 store 加载"""
    try:
        from . import store as _store
        _store.init_db()
        db_count = _count_store(_store.AssetCostAsset)
        if db_count == 0:
            # 空库：将种子写入 store
            for a in seed_assets():
                _store.create_asset(a)
            for r in seed_cost_records():
                _store.create_cost_record(r)
            for l in seed_lcc_analyses():
                _store.create_lcc(l)
        _reload_collections()
    except Exception as exc:
        print("[asset_cost] DB 初始化失败：%s" % exc)


def _count_store(model_cls):
    try:
        from persistence import SessionLocal
        db = SessionLocal()
        c = db.query(model_cls).count()
        db.close()
        return c
    except Exception:
        return 0


def _reload_collections():
    from . import store as _store
    global _assets, _cost_records, _lcc_analyses
    all_assets = []
    for p in range(1, 50):
        res = _store.list_assets(page=p, page_size=200)
        all_assets.extend(res.get("data", []))
    _assets = all_assets

    all_costs = []
    for p in range(1, 50):
        res = _store.list_cost_records(page=p, page_size=200)
        all_costs.extend(res.get("data", []))
    _cost_records = all_costs

    _lcc_analyses = _store.list_lcc()


_init_asset_db()


def get_overview() -> Dict:
    valued = calc_asset_values(_assets)
    total_original = sum(a["original_value"] for a in valued)
    total_net = sum(a["net_value"] for a in valued)
    total_depr = sum(a["accumulated_depr"] for a in valued)
    total_cost = sum(r["amount"] for r in _cost_records if r["approved"])

    by_category = {}
    for a in valued:
        cat = a["category_name"]
        if cat not in by_category:
            by_category[cat] = {"count": 0, "original_value": 0, "net_value": 0}
        by_category[cat]["count"] += 1
        by_category[cat]["original_value"] += a["original_value"]
        by_category[cat]["net_value"] += a["net_value"]

    by_region = {}
    for a in valued:
        r = a["region"]
        if r not in by_region:
            by_region[r] = {"count": 0, "original_value": 0, "net_value": 0}
        by_region[r]["count"] += 1
        by_region[r]["original_value"] += a["original_value"]
        by_region[r]["net_value"] += a["net_value"]

    return {
        "total_assets": len(valued),
        "total_original_value": round(total_original, 2),
        "total_net_value": round(total_net, 2),
        "total_accumulated_depr": round(total_depr, 2),
        "overall_depr_pct": round(total_depr / (total_original - sum(a["original_value"] * a["residual_rate"] for a in valued)) * 100, 1) if total_original > 0 else 0,
        "total_annual_cost": round(total_cost, 2),
        "cost_record_count": len(_cost_records),
        "by_category": {k: {kk: round(vv, 2) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in by_category.items()},
        "by_region": {k: {kk: round(vv, 2) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in by_region.items()},
        "lcc_analysis_count": len(_lcc_analyses),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def list_assets(page: int = 1, page_size: int = 20, category: Optional[str] = None,
                region: Optional[str] = None, status: Optional[str] = None) -> Dict:
    valued = calc_asset_values(_assets)
    filtered = valued
    if category:
        filtered = [a for a in filtered if a["category"] == category or a["category_name"] == category]
    if region:
        filtered = [a for a in filtered if a["region"] == region]
    if status:
        filtered = [a for a in filtered if a["status"] == status]

    total = len(filtered)
    start = (page - 1) * page_size
    items = filtered[start:start + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "items": [{k: round(v, 2) if isinstance(v, float) else v for k, v in a.items()} for a in items],
    }


def get_asset(asset_id: str) -> Optional[Dict]:
    for a in calc_asset_values(_assets):
        if a["asset_id"] == asset_id:
            costs = [r for r in _cost_records if r["asset_id"] == asset_id]
            total_cost = sum(c["amount"] for c in costs)
            return {
                **{k: round(v, 2) if isinstance(v, float) else v for k, v in a.items()},
                "cost_history": costs[-10:],
                "total_cost": round(total_cost, 2),
            }
    return None


def add_asset(data: Dict) -> Dict:
    idx = len(_assets) + 1
    cat_info = ASSET_CATEGORIES.get(data["category"], {"depr_years": 20, "residual_rate": 0.05, "name": data["category"]})
    asset = {
        "asset_id": f"AST-N{idx:03d}",
        "name": data["name"],
        "category": data["category"],
        "category_name": cat_info["name"],
        "region": data["region"],
        "material": data.get("material"),
        "material_name": PIPE_MATERIALS.get(data.get("material", ""), {}).get("name", "-"),
        "specs": data.get("specs", "-"),
        "original_value": data["original_value"],
        "install_date": data["install_date"],
        "depr_method": "STRAIGHT_LINE",
        "depr_years": cat_info["depr_years"],
        "residual_rate": cat_info["residual_rate"],
        "status": "在用",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _assets.append(asset)
    return asset


def delete_asset(asset_id: str) -> bool:
    for i, a in enumerate(_assets):
        if a["asset_id"] == asset_id:
            _assets.pop(i)
            return True
    return False


def review_asset(asset_id: str, approved: bool, comment: str = "") -> Optional[Dict]:
    for a in _assets:
        if a["asset_id"] == asset_id:
            a["status"] = "已审核" if approved else "已驳回"
            a["review_comment"] = comment
            a["review_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return a
    return None


def list_cost_records(page: int = 1, page_size: int = 20, cost_type: Optional[str] = None,
                      region: Optional[str] = None, asset_id: Optional[str] = None) -> Dict:
    filtered = _cost_records
    if cost_type:
        filtered = [r for r in filtered if r["cost_type"] == cost_type]
    if region:
        filtered = [r for r in filtered if r["region"] == region]
    if asset_id:
        filtered = [r for r in filtered if r["asset_id"] == asset_id]

    total = len(filtered)
    start = (page - 1) * page_size
    items = filtered[start:start + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "items": items,
    }


def add_cost_record(data: Dict) -> Dict:
    idx = len(_cost_records) + 1
    asset_region = "-"
    for a in _assets:
        if a["asset_id"] == data["asset_id"]:
            asset_region = a["region"]
            break
    record = {
        "record_id": f"COST-{idx:04d}",
        "asset_id": data["asset_id"],
        "cost_type": data["cost_type"],
        "amount": data["amount"],
        "description": data.get("description", ""),
        "region": asset_region,
        "record_date": data.get("record_date", datetime.now().strftime("%Y-%m-%d")),
        "approved": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _cost_records.append(record)
    return record


def delete_cost_record(record_id: str) -> bool:
    for i, r in enumerate(_cost_records):
        if r["record_id"] == record_id:
            _cost_records.pop(i)
            return True
    return False


def review_cost_record(record_id: str, approved: bool) -> Optional[Dict]:
    for r in _cost_records:
        if r["record_id"] == record_id:
            r["approved"] = approved
            r["review_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return r
    return None


def cost_analysis() -> Dict:
    by_type = {}
    for r in _cost_records:
        if not r["approved"]:
            continue
        ct = r["cost_type"]
        by_type.setdefault(ct, {"total": 0, "count": 0})
        by_type[ct]["total"] += r["amount"]
        by_type[ct]["count"] += 1

    by_region = {}
    for r in _cost_records:
        if not r["approved"]:
            continue
        rg = r["region"]
        by_region.setdefault(rg, {"total": 0, "count": 0})
        by_region[rg]["total"] += r["amount"]
        by_region[rg]["count"] += 1

    by_asset = {}
    for r in _cost_records:
        if not r["approved"]:
            continue
        aid = r["asset_id"]
        by_asset.setdefault(aid, {"total": 0, "count": 0})
        by_asset[aid]["total"] += r["amount"]
        by_asset[aid]["count"] += 1

    top_cost_assets = sorted(by_asset.items(), key=lambda x: x[1]["total"], reverse=True)[:10]

    monthly = {}
    for r in _cost_records:
        if not r["approved"]:
            continue
        m = r["record_date"][:7]
        monthly.setdefault(m, 0)
        monthly[m] += r["amount"]

    return {
        "by_type": {k: {"total": round(v["total"], 2), "count": v["count"]} for k, v in by_type.items()},
        "by_region": {k: {"total": round(v["total"], 2), "count": v["count"]} for k, v in by_region.items()},
        "top_cost_assets": [{"asset_id": k, "total_cost": round(v["total"], 2), "record_count": v["count"]} for k, v in top_cost_assets],
        "monthly_trend": {k: round(v, 2) for k, v in sorted(monthly.items())},
        "total_cost": round(sum(r["amount"] for r in _cost_records if r["approved"]), 2),
    }


def run_lcc_analysis(data: Dict) -> Dict:
    rate = data.get("discount_rate", 0.05)
    life = data.get("design_life", 30)
    materials = data.get("material_options", ["DUCTILE_IRON", "PE", "STEEL"])

    options = []
    for mat in materials:
        mat_info = PIPE_MATERIALS.get(mat, {"name": mat, "unit_cost": 1000, "life_years": 30})
        initial = mat_info["unit_cost"] * 100
        annual_maint = initial * 0.015
        annual_energy = initial * 0.005

        npv = initial
        for y in range(1, life + 1):
            npv += (annual_maint + annual_energy) / ((1 + rate) ** y)
            if mat_info["life_years"] < life and y == mat_info["life_years"]:
                npv += initial * 0.6 / ((1 + rate) ** y)

        options.append({
            "material": mat,
            "material_name": mat_info["name"],
            "initial_cost": round(initial, 2),
            "annual_maintenance": round(annual_maint, 2),
            "annual_energy": round(annual_energy, 2),
            "replacement_year": mat_info["life_years"] if mat_info["life_years"] < life else None,
            "npv": round(npv, 2),
            "total_lcc": round(npv, 2),
        })

    best = min(options, key=lambda x: x["npv"])
    for o in options:
        o["rank"] = sorted([x["npv"] for x in options]).index(o["npv"]) + 1
        o["saving_vs_worst"] = round(max(x["npv"] for x in options) - o["npv"], 2)

    idx = len(_lcc_analyses) + 1
    analysis = {
        "analysis_id": f"LCC-{idx:03d}",
        "project_name": data.get("project_name", f"LCC分析-{idx}"),
        "design_life": life,
        "discount_rate": rate,
        "options": options,
        "recommended": best["material"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _lcc_analyses.append(analysis)
    return analysis


def list_lcc_analyses() -> List[Dict]:
    return _lcc_analyses


def get_lcc_analysis(analysis_id: str) -> Optional[Dict]:
    for a in _lcc_analyses:
        if a["analysis_id"] == analysis_id:
            return a
    return None


def depreciation_schedule(asset_id: str) -> Optional[Dict]:
    for a in _assets:
        if a["asset_id"] != asset_id:
            continue
        orig = a["original_value"]
        residual = orig * a["residual_rate"]
        depreciable = orig - residual
        years = a["depr_years"]
        method = a["depr_method"]

        schedule = []
        if method == "STRAIGHT_LINE":
            annual = depreciable / years
            for y in range(1, years + 1):
                schedule.append({
                    "year": y,
                    "beginning_value": round(orig - annual * (y - 1), 2),
                    "depr_amount": round(annual, 2),
                    "accumulated": round(annual * y, 2),
                    "ending_value": round(orig - annual * y, 2),
                })
        elif method == "DOUBLE_DECLINING":
            rate = 2.0 / years
            book = orig
            accum = 0
            for y in range(1, years + 1):
                dep = book * rate
                if book - dep < residual:
                    dep = book - residual
                accum += dep
                schedule.append({
                    "year": y,
                    "beginning_value": round(book, 2),
                    "depr_amount": round(dep, 2),
                    "accumulated": round(accum, 2),
                    "ending_value": round(book - dep, 2),
                })
                book -= dep
        elif method == "SUM_OF_YEARS":
            soy_sum = years * (years + 1) / 2
            accum = 0
            for y in range(1, years + 1):
                frac = (years - y + 1) / soy_sum
                dep = depreciable * frac
                accum += dep
                schedule.append({
                    "year": y,
                    "beginning_value": round(orig - accum + dep, 2),
                    "depr_amount": round(dep, 2),
                    "accumulated": round(accum, 2),
                    "ending_value": round(orig - accum, 2),
                })

        return {
            "asset_id": asset_id,
            "asset_name": a["name"],
            "original_value": orig,
            "residual_value": round(residual, 2),
            "depreciable": round(depreciable, 2),
            "method": DEPR_METHODS.get(method, method),
            "years": years,
            "schedule": schedule,
        }
    return None


# ==============================================================================
# 持久化 CRUD 包装（调用 store 层）
# ==============================================================================

def _reload():
    """变更后重新从 store 加载"""
    global _assets, _cost_records, _lcc_analyses
    from . import store as _store
    all_assets = []
    for p in range(1, 50):
        res = _store.list_assets(page=p, page_size=200)
        all_assets.extend(res.get("data", []))
    _assets = all_assets
    all_costs = []
    for p in range(1, 50):
        res = _store.list_cost_records(page=p, page_size=200)
        all_costs.extend(res.get("data", []))
    _cost_records = all_costs
    _lcc_analyses = _store.list_lcc()


def add_asset_and_save(data: Dict) -> Dict:
    result = add_asset(data)
    try:
        from . import store as _store
        _store.create_asset({k: data.get(k) for k in (
            "asset_id", "name", "category", "category_name", "region",
            "material", "material_name", "specs", "original_value",
            "install_date", "depr_method", "depr_years", "residual_rate", "status",
        )})
        _reload()
    except Exception:
        pass
    return result


def delete_asset_and_save(asset_id: str) -> bool:
    result = delete_asset(asset_id)
    if result:
        try:
            from . import store as _store
            _store.delete_asset(asset_id)
            _reload()
        except Exception:
            pass
    return result


def review_asset_and_save(asset_id: str, approved: bool, comment: str = "") -> Optional[Dict]:
    result = review_asset(asset_id, approved, comment)
    if result:
        try:
            from . import store as _store
            _store.review_asset(asset_id, approved, comment)
            _reload()
        except Exception:
            pass
    return result


def add_cost_record_and_save(data: Dict) -> Dict:
    result = add_cost_record(data)
    try:
        from . import store as _store
        _store.create_cost_record({k: data.get(k) for k in (
            "record_id", "asset_id", "cost_type", "amount", "description",
            "region", "record_date",
        )})
        _reload()
    except Exception:
        pass
    return result


def delete_cost_record_and_save(record_id: str) -> bool:
    result = delete_cost_record(record_id)
    if result:
        try:
            from . import store as _store
            _store.delete_cost_record(record_id)
            _reload()
        except Exception:
            pass
    return result


def review_cost_record_and_save(record_id: str, approved: bool) -> Optional[Dict]:
    result = review_cost_record(record_id, approved)
    if result:
        try:
            from . import store as _store
            _store.review_cost_record(record_id, approved)
            _reload()
        except Exception:
            pass
    return result


def run_lcc_and_save(data: Dict) -> Dict:
    result = run_lcc_analysis(data)
    try:
        from . import store as _store
        _store.create_lcc(result)
        _reload()
    except Exception:
        pass
    return result
