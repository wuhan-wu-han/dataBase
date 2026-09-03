"""智能助手工具集 —— 把平台现有只读接口 + 模块跳转注册为大模型 function-calling 工具

设计原则：
1. 只读：仅暴露 GET 查询与跳转，绝不含任何写操作（新建/派单/删除），杜绝误操作。
2. 复用契约：工具执行 = 用 httpx 回调本服务已有的 REST 接口（与前端走同一套路径），
   不重复实现业务逻辑，后端接口一旦变化助手自动跟随。
3. 参数名严格对齐各模块 routes.py 的查询参数，保证过滤真实生效。
"""
import httpx

from . import config

# 模块中文名 → 前端路由路径（与 Sidebar.vue 菜单完全一致）
MODULE_ROUTES = {
    "监控大屏": "/",
    "综合态势": "/gis",
    "AI预警中心": "/alerts",
    "故障预测中心": "/failure-prediction",
    "风险研判中心": "/risk-analysis",
    "燃气风控": "/gas-risk",
    "危化品监管": "/hazmat",
    "综合管廊": "/utility-tunnel",
    "道路塌陷": "/road-hazard",
    "应急预案": "/emergency-plan",
    "资产管理": "/asset",
    "资产成本": "/asset-cost",
    "工单管理": "/work-order",
}

# 常见口语别名 → 规范模块名（提升跳转命中率）
_MODULE_ALIASES = {
    "工单": "工单管理", "预案": "应急预案", "应急": "应急预案",
    "资产": "资产成本", "成本": "资产成本", "管廊": "综合管廊",
    "危废": "危化品监管", "危化品": "危化品监管", "化学品": "危化品监管",
    "风险": "风险研判中心", "研判": "风险研判中心", "大屏": "监控大屏",
    "首页": "监控大屏", "态势": "综合态势", "地图": "综合态势", "gis": "综合态势",
    "预警": "AI预警中心", "告警中心": "AI预警中心", "燃气": "燃气风控",
    "道路": "道路塌陷", "塌陷": "道路塌陷", "故障预测": "故障预测中心",
}


def _clean(params):
    """剔除 None / 空串，避免把无效过滤传给接口"""
    return {k: v for k, v in (params or {}).items() if v is not None and v != ""}


def _get(path, params=None):
    """回调本服务接口（自调用）。失败不抛异常，返回 {_error:...} 让模型如实转述。"""
    url = config.INTERNAL_BASE + path
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(url, params=_clean(params))
        if r.status_code != 200:
            return {"_error": "接口 %s 返回 HTTP %d" % (path, r.status_code)}
        return r.json()
    except httpx.HTTPError as exc:
        return {"_error": "调用 %s 失败：%s（后端服务是否已启动？）" % (path, exc)}


def _get_teammate(service, path, params=None):
    """回调队友独立服务接口（不同端口）。失败返回 {_error:...}。"""
    base = config.TEAMMATE_SERVICES.get(service)
    if not base:
        return {"_error": "未配置服务：%s" % service}
    url = base + path
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(url, params=_clean(params))
        if r.status_code != 200:
            return {"_error": "接口 %s%s 返回 HTTP %d" % (service, path, r.status_code)}
        return r.json()
    except httpx.HTTPError as exc:
        return {"_error": "调用 %s%s 失败：%s（%s 服务是否已启动？）" % (service, path, exc, service)}


# ==================== 工具执行器 ====================
def h_workorder_overview(a):
    return _get("/workorder/overview")


def h_workorders(a):
    return _get("/workorder/orders", {
        "channel": a.get("channel"), "status": a.get("status"),
        "priority": a.get("priority"), "location": a.get("location"),
        "page": a.get("page", 1), "page_size": a.get("page_size", 10),
    })


def h_workorder_stats(a):
    return _get("/workorder/orders/stats")


def h_plan_overview(a):
    return _get("/plan/overview")


def h_plans(a):
    return _get("/plan/plans", {
        "category": a.get("category"), "status": a.get("status"),
        "keyword": a.get("keyword"), "page": a.get("page", 1),
        "page_size": a.get("page_size", 10),
    })


def h_plan_categories(a):
    return _get("/plan/categories")


def h_asset_overview(a):
    return _get("/asset-cost/overview")


def h_assets(a):
    return _get("/asset-cost/assets", {
        "category": a.get("category"), "region": a.get("region"),
        "status": a.get("status"), "page": a.get("page", 1),
        "page_size": a.get("page_size", 10),
    })


def h_asset_cost_analysis(a):
    return _get("/asset-cost/cost-analysis")


def h_tunnel_overview(a):
    return _get("/tunnel/overview")


def h_tunnel_alarms(a):
    return _get("/tunnel/alarms", {
        "cabin": a.get("cabin"), "status": a.get("status"),
        "metric": a.get("metric"), "page": a.get("page", 1),
        "page_size": a.get("page_size", 10),
    })


def h_tunnel_alarm_stats(a):
    return _get("/tunnel/alarms/stats")


def h_hazmat_overview(a):
    return _get("/hazmat/overview")


def h_hazmat_media(a):
    return _get("/hazmat/media", {
        "hw_code": a.get("hw_code"), "status": a.get("status"),
        "page": a.get("page", 1), "page_size": a.get("page_size", 10),
    })


def h_governance_overview(a):
    return _get("/governance/overview")


def h_governance_master_stats(a):
    return _get("/governance/master/stats")


def h_governance_master(a):
    dt = a.get("data_type")
    if not dt:
        return {"_error": "缺少 data_type，可选：pipeline/equipment/personnel/organization/geo_space"}
    return _get("/governance/master/%s" % dt, {
        "status": a.get("status"), "zone": a.get("zone"),
        "department": a.get("department"),
    })


# ---------- 队友模块：燃气资产管理 (gas_asset_manage :8001) ----------
def h_gas_asset_summary(a):
    return _get_teammate("gas_asset", "/assets/summary")


def h_gas_asset_list(a):
    return _get_teammate("gas_asset", "/assets", {
        "keyword": a.get("keyword"), "category": a.get("category"),
        "status": a.get("status"), "page": a.get("page", 1),
        "page_size": a.get("page_size", 10),
    })


def h_gas_asset_stats(a):
    return _get_teammate("gas_asset", "/assets/stats")


def h_gas_asset_inventory(a):
    return _get_teammate("gas_asset", "/inventory/stats")


# ---------- 队友模块：道路塌陷 (road_hazard_control :8002) ----------
def h_road_cavity_stats(a):
    return _get_teammate("road_hazard", "/cavity/stats")


def h_road_cavity_list(a):
    return _get_teammate("road_hazard", "/cavity", {
        "keyword": a.get("keyword"), "district": a.get("district"),
        "risk_level": a.get("risk_level"), "status": a.get("status"),
        "page": a.get("page", 1), "page_size": a.get("page_size", 10),
    })


def h_road_subsidence_stats(a):
    return _get_teammate("road_hazard", "/subsidence/stats")


def h_road_construction_stats(a):
    return _get_teammate("road_hazard", "/construction/stats")


# ---------- 队友模块：燃气风控 (gas_risk_control :8003) ----------
def h_gas_monitor_sensors(a):
    return _get_teammate("gas_risk", "/monitoring/sensors")


def h_gas_monitor_realtime(a):
    return _get_teammate("gas_risk", "/monitoring/realtime")


def h_gas_monitor_alarms(a):
    return _get_teammate("gas_risk", "/monitoring/alarms")


def h_gas_leak_records(a):
    return _get_teammate("gas_risk", "/leak/records")


def h_gas_third_party_warnings(a):
    return _get_teammate("gas_risk", "/third-party/warnings")


def h_gas_occupation_stats(a):
    return _get_teammate("gas_risk", "/occupation/stats")


# ---------- 队友模块：供水管网 (water_supply_control :8004) ----------
def h_water_monitor_latest(a):
    return _get_teammate("water_supply", "/monitor/latest")


def h_water_monitor_alarms(a):
    return _get_teammate("water_supply", "/monitor/alarms", {
        "status": a.get("status"), "level": a.get("level"),
        "page": a.get("page", 1), "page_size": a.get("page_size", 10),
    })


def h_water_alarm_stats(a):
    return _get_teammate("water_supply", "/monitor/stats")


def h_water_dma_zones(a):
    return _get_teammate("water_supply", "/dma/zones")


def h_water_quality_stats(a):
    return _get_teammate("water_supply", "/quality/stats")


def h_water_burst_stats(a):
    return _get_teammate("water_supply", "/burst/stats/summary")


# ---------- 队友模块：井盖管控 (manhole_cover_control :8005) ----------
def h_manhole_monitor_stats(a):
    return _get_teammate("manhole_cover", "/monitor/stats")


def h_manhole_alarms(a):
    return _get_teammate("manhole_cover", "/monitor/alarms", {
        "status": a.get("status"), "level": a.get("level"),
        "page": a.get("page", 1), "page_size": a.get("page_size", 10),
    })


def h_manhole_archive_stats(a):
    return _get_teammate("manhole_cover", "/archive/stats")


def h_manhole_orders_stats(a):
    return _get_teammate("manhole_cover", "/orders/stats")


def h_navigate(a):
    """返回跳转意图，由前端执行 router.push（不在后端跳转）"""
    name = (a.get("module") or "").strip()
    if not name:
        return {"_error": "缺少 module 参数", "available": list(MODULE_ROUTES)}
    # 精确 → 别名 → 双向子串模糊
    if name in MODULE_ROUTES:
        return {"path": MODULE_ROUTES[name], "label": name}
    if name in _MODULE_ALIASES:
        canon = _MODULE_ALIASES[name]
        return {"path": MODULE_ROUTES[canon], "label": canon}
    low = name.lower()
    for canon, path in MODULE_ROUTES.items():
        if canon.lower() == low or name in canon or canon in name:
            return {"path": path, "label": canon}
    for alias, canon in _MODULE_ALIASES.items():
        if alias in name or name in alias:
            return {"path": MODULE_ROUTES[canon], "label": canon}
    return {"_error": "未识别的模块：%s" % name, "available": list(MODULE_ROUTES)}


# 工具名 → 执行器
HANDLERS = {
    # 自有模块（:8000）
    "query_workorder_overview": h_workorder_overview,
    "query_workorders": h_workorders,
    "query_workorder_stats": h_workorder_stats,
    "query_plan_overview": h_plan_overview,
    "query_plans": h_plans,
    "query_plan_categories": h_plan_categories,
    "query_asset_overview": h_asset_overview,
    "query_assets": h_assets,
    "query_asset_cost_analysis": h_asset_cost_analysis,
    "query_tunnel_overview": h_tunnel_overview,
    "query_tunnel_alarms": h_tunnel_alarms,
    "query_tunnel_alarm_stats": h_tunnel_alarm_stats,
    "query_hazmat_overview": h_hazmat_overview,
    "query_hazmat_media": h_hazmat_media,
    "query_governance_overview": h_governance_overview,
    "query_governance_master_stats": h_governance_master_stats,
    "query_governance_master": h_governance_master,
    # 队友模块：燃气资产(:8001)
    "query_gas_asset_summary": h_gas_asset_summary,
    "query_gas_asset_list": h_gas_asset_list,
    "query_gas_asset_stats": h_gas_asset_stats,
    "query_gas_asset_inventory": h_gas_asset_inventory,
    # 队友模块：道路塌陷(:8002)
    "query_road_cavity_stats": h_road_cavity_stats,
    "query_road_cavity_list": h_road_cavity_list,
    "query_road_subsidence_stats": h_road_subsidence_stats,
    "query_road_construction_stats": h_road_construction_stats,
    # 队友模块：燃气风控(:8003)
    "query_gas_monitor_sensors": h_gas_monitor_sensors,
    "query_gas_monitor_realtime": h_gas_monitor_realtime,
    "query_gas_monitor_alarms": h_gas_monitor_alarms,
    "query_gas_leak_records": h_gas_leak_records,
    "query_gas_third_party_warnings": h_gas_third_party_warnings,
    "query_gas_occupation_stats": h_gas_occupation_stats,
    # 队友模块：供水管网(:8004)
    "query_water_monitor_latest": h_water_monitor_latest,
    "query_water_monitor_alarms": h_water_monitor_alarms,
    "query_water_alarm_stats": h_water_alarm_stats,
    "query_water_dma_zones": h_water_dma_zones,
    "query_water_quality_stats": h_water_quality_stats,
    "query_water_burst_stats": h_water_burst_stats,
    # 队友模块：井盖管控(:8005)
    "query_manhole_monitor_stats": h_manhole_monitor_stats,
    "query_manhole_alarms": h_manhole_alarms,
    "query_manhole_archive_stats": h_manhole_archive_stats,
    "query_manhole_orders_stats": h_manhole_orders_stats,
    # 通用
    "navigate_to_module": h_navigate,
}


def execute(name, args):
    fn = HANDLERS.get(name)
    if not fn:
        return {"_error": "未知工具：%s" % name}
    try:
        return fn(args or {})
    except Exception as exc:  # 工具内部任何异常都不应让整个对话 500
        return {"_error": "工具 %s 执行异常：%s" % (name, exc)}


# ==================== 工具 JSON Schema（OpenAI function 格式）====================
def _fn(name, desc, props=None, required=None):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": props or {},
                "required": required or [],
            },
        },
    }


_STR = {"type": "string"}
_INT = {"type": "integer"}

TOOL_SCHEMAS = [
    _fn("query_workorder_overview",
        "查询【工单管理】总览KPI：总工单数、待派单、超期、平均评分、空闲人员等。用户问工单整体情况/有多少工单时用。"),
    _fn("query_workorders",
        "按条件查询【工单】列表。用户要查具体工单、按状态/优先级/渠道/位置筛选工单时用。",
        {"channel": {**_STR, "description": "接入渠道，如 热线/巡查/App"},
         "status": {**_STR, "description": "工单状态：pending/assigned/onsite/resolved/closed"},
         "priority": {**_STR, "description": "优先级：urgent/high/medium/low"},
         "location": {**_STR, "description": "位置关键词"},
         "page": {**_INT, "description": "页码，默认1"},
         "page_size": {**_INT, "description": "每页条数，默认10，0=全部"}}),
    _fn("query_workorder_stats",
        "查询【工单】统计分布：按渠道/状态/优先级/趋势的聚合数据。用户问工单分布/占比/趋势时用。"),
    _fn("query_plan_overview",
        "查询【应急预案】总览KPI：预案总数、启用数、今日匹配次数、今日演练次数等。"),
    _fn("query_plans",
        "按条件查询【应急预案】列表。用户要查具体预案、按类别/状态/关键词筛选用。",
        {"category": {**_STR, "description": "预案类别代码"},
         "status": {**_STR, "description": "状态：active/draft/deprecated"},
         "keyword": {**_STR, "description": "名称/标签关键词"},
         "page": {**_INT}, "page_size": {**_INT}}),
    _fn("query_plan_categories",
        "查询【应急预案】8大类目录与各类别预案数量统计。"),
    _fn("query_asset_overview",
        "查询【资产成本】总览KPI：资产总数、原值、净值、累计折旧等。用户问资产整体/总值时用。"),
    _fn("query_assets",
        "按条件查询【资产】列表。用户要查具体资产、按分类/区域/状态筛选用。",
        {"category": {**_STR, "description": "资产分类"},
         "region": {**_STR, "description": "所属区域"},
         "status": {**_STR, "description": "资产状态，如 在用/闲置/报废"},
         "page": {**_INT}, "page_size": {**_INT}}),
    _fn("query_asset_cost_analysis",
        "查询【运维成本分析】：各类/各区域运维成本聚合。用户问运维成本/花费时用。"),
    _fn("query_tunnel_overview",
        "查询【综合管廊】总览KPI：传感器总数、在线率、今日告警、环境健康分等。"),
    _fn("query_tunnel_alarms",
        "按条件查询【综合管廊告警】列表。用户要查管廊告警、按舱室/状态/指标筛选用。",
        {"cabin": {**_STR, "description": "舱室/区段"},
         "status": {**_STR, "description": "告警状态：未处理/处理中/已处理"},
         "metric": {**_STR, "description": "监测指标，如 温度/湿度/甲烷"},
         "page": {**_INT}, "page_size": {**_INT}}),
    _fn("query_tunnel_alarm_stats",
        "查询【综合管廊告警】统计分布。用户问管廊告警按类型/舱室/级别的分布时用。"),
    _fn("query_hazmat_overview",
        "查询【危化品监管】总览KPI：介质数、告警介质数、输送路径数、合规率等。"),
    _fn("query_hazmat_media",
        "按条件查询【危废介质】列表。用户要查危废介质、按危废代码/状态筛选用。",
        {"hw_code": {**_STR, "description": "危废代码"},
         "status": {**_STR, "description": "介质状态"},
         "page": {**_INT}, "page_size": {**_INT}}),
    _fn("query_governance_overview",
        "查询【数据治理】总览KPI：主数据总量、数据管道数、设备/人员/组织数等。"),
    _fn("query_governance_master_stats",
        "查询【数据治理】五大主数据(管网/设备/人员/组织机构/地理空间)的数量统计概览。"),
    _fn("query_governance_master",
        "查询【数据治理】某类主数据明细列表。用户要看具体某类主数据时用。",
        {"data_type": {**_STR, "enum": ["pipeline", "equipment", "personnel", "organization", "geo_space"],
                       "description": "主数据类型：pipeline管网/equipment设备/personnel人员/organization组织机构/geo_space地理空间"},
         "status": {**_STR}, "zone": {**_STR, "description": "所属区域"},
         "department": {**_STR, "description": "所属部门"}},
        ["data_type"]),

    # ---------- 队友模块：燃气资产管理 ----------
    _fn("query_gas_asset_summary",
        "查询【资产管理】总览KPI：资产总数、管线总长度、在用资产数、产权清晰率等。用户问资产概况/有多少资产时用。"),
    _fn("query_gas_asset_list",
        "按条件查询【资产台账】列表。用户要查具体资产记录、按分类/状态筛选用。",
        {"keyword": {**_STR, "description": "资产名称/编号关键词"},
         "category": {**_STR, "description": "资产分类"},
         "status": {**_STR, "description": "资产状态"},
         "page": {**_INT}, "page_size": {**_INT}}),
    _fn("query_gas_asset_stats",
        "查询【资产】五维分类统计：管径/材质/年代/权属/区域分布。用户问资产构成/分布时用。"),
    _fn("query_gas_asset_inventory",
        "查询【资产盘点】统计：盘点匹配率、差异分布等。用户问盘点情况/资产核查时用。"),

    # ---------- 队友模块：道路塌陷 ----------
    _fn("query_road_cavity_stats",
        "查询【道路塌陷】空洞隐患统计：按风险等级/区域/状态的分布。用户问空洞隐患整体情况时用。"),
    _fn("query_road_cavity_list",
        "按条件查询【空洞隐患台账】列表。用户要查具体空洞记录、按区域/风险等级/状态筛选用。",
        {"keyword": {**_STR, "description": "编号/位置关键词"},
         "district": {**_STR, "description": "所属区域"},
         "risk_level": {**_STR, "description": "风险等级：high/medium/low"},
         "status": {**_STR, "description": "处置状态"},
         "page": {**_INT}, "page_size": {**_INT}}),
    _fn("query_road_subsidence_stats",
        "查询【道路沉降】监测统计：风险分布/区域统计/月度趋势。用户问沉降监测情况时用。"),
    _fn("query_road_construction_stats",
        "查询【施工评估】风险统计：在建工程对道路的影响评估。用户问施工风险/在建工程时用。"),

    # ---------- 队友模块：燃气风控 ----------
    _fn("query_gas_monitor_sensors",
        "查询【燃气风控】监测站点列表：各站点位置、状态。用户问有哪些监测站/站点分布时用。"),
    _fn("query_gas_monitor_realtime",
        "查询【燃气风控】实时监测数据：各站点最新压力/浓度/温度等。用户问当前燃气数据/实时压力/浓度时用。"),
    _fn("query_gas_monitor_alarms",
        "查询【燃气风控】实时告警记录。用户问燃气告警/报警信息时用。"),
    _fn("query_gas_leak_records",
        "查询【燃气泄漏】历史记录。用户问泄漏事件/泄漏历史时用。"),
    _fn("query_gas_third_party_warnings",
        "查询【第三方施工预警】：当前各管段的第三方施工扰动情况。用户问第三方施工/外力破坏风险时用。"),
    _fn("query_gas_occupation_stats",
        "查询【占压隐患】统计：占压数量/整改率/风险分布。用户问管道占压/隐患整改时用。"),

    # ---------- 队友模块：供水管网 ----------
    _fn("query_water_monitor_latest",
        "查询【供水管网】最新监测数据：各管段最新压力/流量/水质等。用户问供水当前状态/水压/流量时用。"),
    _fn("query_water_monitor_alarms",
        "按条件查询【供水管网】告警列表。用户问供水告警/水管异常时用。",
        {"status": {**_STR, "description": "告警状态"},
         "level": {**_STR, "description": "告警级别"},
         "page": {**_INT}, "page_size": {**_INT}}),
    _fn("query_water_alarm_stats",
        "查询【供水管网】告警统计：按类型/级别的分布。用户问供水告警分布/趋势时用。"),
    _fn("query_water_dma_zones",
        "查询【供水DMA分区】列表：各分区计量数据。用户问供水分区/DMA/漏损时用。"),
    _fn("query_water_quality_stats",
        "查询【供水水质】监测站点统计。用户问水质达标率/水质监测情况时用。"),
    _fn("query_water_burst_stats",
        "查询【爆管风险】统计：爆管案例数/风险分布。用户问爆管/管道破裂风险时用。"),

    # ---------- 队友模块：井盖管控 ----------
    _fn("query_manhole_monitor_stats",
        "查询【井盖管控】监测与告警统计：井盖总数/在线率/告警分布。用户问井盖整体情况时用。"),
    _fn("query_manhole_alarms",
        "按条件查询【井盖】风险告警列表。用户问井盖告警/异动报警时用。",
        {"status": {**_STR, "description": "告警状态"},
         "level": {**_STR, "description": "告警级别"},
         "page": {**_INT}, "page_size": {**_INT}}),
    _fn("query_manhole_archive_stats",
        "查询【井盖档案】统计：按区域/类型/状态/权属的分布。用户问井盖台账/档案分布时用。"),
    _fn("query_manhole_orders_stats",
        "查询【井盖工单】统计：处置率/工单分布。用户问井盖维修工单/处置情况时用。"),

    _fn("navigate_to_module",
        "跳转/打开平台的某个功能模块页面。用户说“去/打开/跳转到XX模块”“我想看XX页面”时用。返回跳转路径由前端执行。",
        {"module": {**_STR, "enum": list(MODULE_ROUTES),
                    "description": "目标模块名，必须是枚举之一：%s" % "、".join(MODULE_ROUTES)}},
        ["module"]),
]
