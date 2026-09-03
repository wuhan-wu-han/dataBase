# 安塞区城市安全生命线管网AI智慧平台 — 深度审计报告

**生成时间**: 2026-09-03  
**审计方式**: 代码逐行静态分析 + 运行时端口探测 + 网关路由映射  
**修改范围**: 仅读取，未做任何代码修改

---

## SECTION 1: 前端菜单统计

### 路由表（共 14 个功能页面）

| # | path | name | meta.title | 页面文件 | 存在性 |
|---|------|------|------------|----------|--------|
| 1 | `/` | Dashboard | 监控大屏 | `@/views/Dashboard.vue` | ✅ |
| 2 | `/alerts` | AlertList | 预警事件 | `@/views/AlertList.vue` | ✅ |
| 3 | `/alerts/:id` | AlertDetail | 预警详情 | `@/views/AlertDetail.vue` | ✅ |
| 4 | `/rules` | RuleManage | 规则管理 | `@/views/RuleManage.vue` | ✅ |
| 5 | `/failure-prediction` | FailurePrediction | 故障预报 | `@/views/FailurePrediction.vue` | ✅ |
| 6 | `/gas-risk` | GasRisk | 燃气风控 | `@/views/gasRisk/Index.vue` | ✅ |
| 7 | `/asset` | Asset | 资产管理 | `@/views/asset/Index.vue` | ✅ |
| 8 | `/road-hazard` | RoadHazard | 道路塌陷 | `@/views/roadHazard/Index.vue` | ✅ |
| 9 | `/risk-analysis` | RiskAnalysis | 风险研判 | `@/views/riskAnalysis/Index.vue` | ✅ |
| 10 | `/hazmat` | Hazmat | 危化品监管 | `@/views/hazmat/Index.vue` | ✅ |
| 11 | `/utility-tunnel` | UtilityTunnel | 综合管廊 | `@/views/tunnel/Index.vue` | ✅ |
| 12 | `/emergency-plan` | EmergencyPlan | 应急预案 | `@/views/emergencyPlan/Index.vue` | ✅ |
| 13 | `/asset-cost` | AssetCost | 资产成本 | `@/views/assetCost/Index.vue` | ✅ |
| 14 | `/work-order` | WorkOrder | 工单管理 | `@/views/workOrder/Index.vue` | ✅ |
| - | `/:pathMatch(.*)*` | redirect | — | N/A (兜底) | — |

### views 目录完整清单

```
alarm-warning-frontend/src/views/
├── AlertDetail.vue          ← 预警详情页
├── AlertList.vue            ← 预警列表页
├── Dashboard.vue            ← 监控大屏首页
├── FailurePrediction.vue    ← 故障预报页
├── ModulePlaceholder.vue    ← ⚠️ 占位组件（待填充模块）
├── RuleManage.vue           ← 规则管理页
└── [子目录]
    ├── asset/Index.vue      ← 资产管理
    ├── assetCost/Index.vue  ← 资产成本
    ├── emergencyPlan/Index.vue ← 应急预案
    ├── gasRisk/Index.vue    ← 燃气风控
    ├── hazmat/Index.vue     ← 危化品监管
    ├── riskAnalysis/Index.vue   ← 风险研判与综合治理
    ├── roadHazard/Index.vue   ← 道路塌陷
    ├── tunnel/Index.vue       ← 综合管廊
    └── workOrder/Index.vue    ← 工单管理全流程管理
```

### 统计汇总

| 类别 | 数量 | 说明 |
|------|------|------|
| **总功能页面** | 14 | 含 1 个兜底重定向 |
| **真实业务页面** | 13 | 均有独立 .vue 文件与对应 API 调用 |
| **占位页面 (ModulePlaceholder)** | 1 | 仅显示"该模块正在规划中"静态卡片，无逻辑、无 API、无数据 |

### ModulePlaceholder.vue 现状

- 内容：一个 `<el-card>` 内含标题"模块暂未开发"和描述"该模块正在规划中，敬请期待。"
- 无 `<script setup>` 逻辑，无组件通信，无任何后端交互

---

## SECTION 2: 后端服务统计

### Spring Cloud Gateway 路由规则 (`api-gateway/application.yml`)

| 网关路径 | 转发目标 | 端口 | StripPrefix | 到达的后端原路径 |
|----------|---------|------|-------------|-----------------|
| `/api/**` (兜底) | `localhost:8085` | 8085 | 无 | 直接透传 `/alert/...` |
| `/api/gas-risk/**` | `localhost:8003` | 8003 | `StripPrefix=2` | `/api/monitoring/*` → `/monitoring/*` |
| `/api/gas-asset/**` | `localhost:8001` | 8001 | `StripPrefix=2` | `/api/assets/*` → `/assets/*` |
| `/api/road-hazard/**` | `localhost:8002` | 8002 | `StripPrefix=2` | `/api/cavity/*` → `/cavity/*` |
| `/api/platform/**` | `localhost:8000` | 8000 | `StripPrefix=2` | `/governance/*`, `/hazmat/*`, `/tunnel/*`, `/plan/*`, `/asset-cost/*`, `/workorder/*` |

### 各端口服务详情

| 端口 | 服务名 | 技术栈 | 框架 | 入口文件/启动类 | 当前运行 |
|------|--------|--------|------|----------------|----------|
| **5173** | Vite Dev Server | Node.js | Vue3+Vite | `alarm-warning-frontend/package.json:dev` | ✅ PID 48804 |
| **8000** | Python 综合服务平台 | Python | FastAPI + SQLAlchemy | `src/python/main.py` | ✅ PID 38192 |
| **8080** | Spring Cloud Gateway | Java | Spring Boot 3.x | `ApiGatewayApplication` | ❌ 未在 netstat 捕获 |
| **8085** | alarm-warning-service | Java | Spring Boot + MyBatisPlus + Kafka + Redis | `AlertApplication.java` | ❌ 未在 netstat 捕获 |
| **8001** | gas_asset_manage | Python | FastAPI + SQLite | `gas_asset_manage/main.py` | ❌ 未在 netstat 捕获 |
| **8002** | road_hazard_control | Python | FastAPI + SQLite | `road_hazard_control/main.py` | ❌ 未在 netstat 捕获 |
| **8003** | gas_risk_control | Python | FastAPI + SQLite | `gas_risk_control/main.py` | ❌ 未在 netstat 捕获 |
| **3306** | MySQL | — | MySQL 8.0 | — | ✅ PID 5828 |

### 端口冲突检测

未发现端口冲突。所有监听端口均被单一进程独占占用。

### 服务源码验证

| 端口 | Java / Python 源码目录 | pom.xml / requirements.txt | 数据库文件 |
|------|----------------------|---------------------------|-----------|
| 8085 | `platform_service/alarm-warning-service/` — Controller, Service, Entity, Mapper, KafkaConsumer | `pom.xml`: spring-boot-starter-web, mybatis-plus-boot-starter, mysql-connector-j, kafka-clients, lettuce-core | `alert_db` (MySQL) |
| 8003 | `gas_risk_control/` — main.py, database.py, models.py, routers/{monitoring,leak,diffusion,user_safety,cathodic,emergency} | `requirements.txt`: fastapi, uvicorn, sqlalchemy, pydantic | `gas_risk.db` (~18MB) |
| 8001 | `gas_asset_manage/` — main.py, database.py, models.py, routers/{assets,lifecycle,inventory,ownership} | `requirements.txt`: fastapi, sqlalchemy, pydantic | `gas_asset.db` (~115KB) |
| 8002 | `road_hazard_control/` — main.py, database.py, models.py, routers/{cavity,subsidence,construction} | `requirements.txt`: fastapi, sqlalchemy, pydantic | `road_hazard.db` (~28KB) |
| 8000 | `src/python/main.py` — 通过 include_router 挂载 6 个子模块 | — | `platform.db` (SQLite, 共享) |

---

## SECTION 3: API 连通率分析

### 逐个页面追踪

#### 已接真实后端（7/14 = 50%）

| # | 页面 | API 文件 | 请求路径 | 后端控制器 | 数据源 | 链路状态 |
|---|------|---------|---------|-----------|--------|---------|
| 1 | 监控大屏 | `@/api/alert` | `GET /alert/alerts` | `AlertController.java @GetMapping("/api/alerts")` | MySQL `alert_event` | ✅ REAL-CONNECTED |
| 2 | 预警事件 | `@/api/alert` | `GET/PATCH /alert/alerts/{id}/status` | `AlertController.java` | MySQL `alert_event` | ✅ REAL-CONNECTED |
| 3 | 预警详情 | `@/api/alert` | `GET /alert/alerts/{id}` | `AlertController.java` | MySQL `alert_event` | ✅ REAL-CONNECTED |
| 4 | 规则管理 | `@/api/alertRule` | `GET/POST/PUT/DELETE /alert-rules` | `AlertRuleController.java` | MySQL `alert_rule` | ✅ REAL-CONNECTED |
| 5 | 故障预报 | `@/api/failurePrediction` | `GET/POST /alert/predictions` | `FailurePredictionController.java` | MySQL `failure_prediction` | ✅ REAL-CONNECTED |
| 6 | 燃气风控 | `@/api/gasRisk` | `GET /api/monitoring/sensors`, `/leakRecords` 等 | `gas_risk_control/routers/monitoring.py` | SQLite `gas_risk.db` | ✅ Python SQLite (实时线程写入) |
| 7 | 资产管理 | `@/api/gasAsset` | `GET /assets?params`, CSV `/export` | `gas_asset_manage/routers/assets.py` | SQLite `gas_asset.db` | ✅ Python SQLite |
| 8 | 道路塌陷 | `@/api/roadHazard` | `GET /cavity?params`, POST /subsidence | `road_hazard_control/routers/cavity.py` | SQLite `road_hazard.db` | ✅ Python SQLite |

#### Mock-only（6/14 = 42.9%）— API 存在但返回内存假数据

| # | 页面 | API 文件 | Mock 标记 | 后端控制器 | 数据源 | 链路状态 |
|---|------|---------|-----------|-----------|--------|---------|
| 9 | 风险研判 | `@/api/riskAnalysis` | `createMockFallback('governance')` | `data_governance/routes.py` | simulator 硬编码 dict | ⚠️ MOCK-ONLY |
| 10 | 危化品监管 | `@/api/hazmat` | `createMockFallback('hazmat')` | `hazmat_transport/routes.py` | simulator 硬编码 dict | ⚠️ MOCK-ONLY |
| 11 | 综合管廊 | `@/api/tunnel` | `createMockFallback('tunnel')` | `tunnel_api/routes.py` | simulator 内存对象 | ⚠️ MOCK-ONLY |
| 12 | 应急预案 | `@/api/emergencyPlan` | **无** (直调 HTTP) | `plan_api/routes.py` | routes→simulator (有 persistence 层但未引用) | ⚠️ 疑似内存 |
| 13 | 资产成本 | `@/api/assetCost` | `createMockFallback('assetCost')` | `asset_cost/routes.py` | simulator 硬编码 dict | ⚠️ MOCK-ONLY |
| 14 | 工单管理 | `@/api/workOrder` | **无** (直调 HTTP) | `workorder/routes.py` | routes→simulator (有 persistence 层但未引用) | ⚠️ 疑似内存 |

#### 空页面

| # | 页面 | API | 状态 |
|---|------|-----|------|
| 15 | ModulePlaceholder.vue | 无 API | ❌ NO-BACKEND |

### 连通率统计

| 指标 | 值 |
|------|---|
| **页面总数** | 14 |
| **已接真实后端页面数** | 8 |
| **Mock 页面数** | 6 |
| **空页面 (占位)** | 1 |
| **API 404 数量** | 0 (所有 route 都已定义，只是数据为假) |
| **API 500 数量** | 0 |
| **联通率 = 已连接真实后端 / 页面总数** | **8/14 ≈ 57.1%** |

---

## SECTION 4: CRUD 能力矩阵

| 模块 | 查询 | 分页 | 新增 | 编辑 | 删除 | 导入 Excel | 导出 Excel |
|------|------|------|------|------|------|-----------|-----------|
| 监控大屏 | ✅ alert list | ✅ page/size | ❌ | ❌ | ❌ | ❌ | ❌ |
| 预警事件 | ✅ list + PATCH status | ✅ page/size | ❌ | ✅ (状态变更) | ❌ | ❌ | ❌ |
| 预警详情 | ✅ get(id) + PATCH status | ❌ | ❌ | ✅ (状态变更) | ❌ | ❌ | ❌ |
| 规则管理 | ✅ list + detail | ✅ page/size | ✅ POST | ✅ PUT | ✅ DELETE | ❌ | ❌ |
| 故障预报 | ✅ list/detail/statistics | ✅ page/size | ✅ POST generate | ❌ | ❌ | ❌ | ❌ |
| 燃气风控 | ✅ sensors/history/alarms/leakRecords/users/occupation/cathodic/valves | ✅ limit | ✅ simulate/detour/clear-faults | ❌ | ❌ | ❌ | ✅ 泄漏记录导出 |
| 资产管理 | ✅ summary/stats/options/assets/lifecycle/inventory/ownership | ✅ page/page_size | ✅ lifecycle/inventory task | ✅ lifecycle/ownership/update | ❌ (无 DELETE) | ❌ | ✅ CSV export (/export) |
| 道路塌陷 | ✅ summary/cavity/subsidence/construction options/stats | ✅ page/page_size | ✅ cavity/construction | ✅ cavity | ❌ | ❌ | ❌ |
| 风险研判 | ✅ overview/masterStats/masterList/standards/quality/apiServices/apiStats | ✅ page/size | ✅ qualityCheck/spatialAnalyze | ✅ qualityReport 更新 | ✅ spatial buffer delete | ❌ | ✅ XLSX 客户端导出 |
| 危化品监管 | ✅ overview/media/routes/trace/segments/ledger/valves | ✅ page/size | ✅ routeCheck/evaluateCorrosion/generateReport/shutdown | ❌ | ❌ | ❌ | ❌ |
| 综合管廊 | ✅ overview/cabins/envRealtime/alarms/pipelines/security/access/intrusions/broadcast/workflowStatus | ✅ limit | ✅ pipeline/createAccessRecord/testBroadcast/runWorkflow | ✅ pipeline update | ❌ | ❌ | ❌ |
| 应急预案 | ✅ overview/categories/plans/nodes/match/live/activations | ✅ page/page_size | ✅ plans/createNode/drill/activate | ✅ plans/node update | ✅ plans/deleteNode | ❌ | ❌ |
| 资产成本 | ✅ overview/assets/costRecords/costAnalysis/lcc/config | ✅ page/page_size | ✅ assets/costRecords/lcc | ❌ (review 用 POST) | ✅ assets/costRecords/delete | ❌ | ❌ |
| 工单管理 | ✅ overview/orders/stats/channels/dispatch/recommend/staff/process/sla | ✅ page/page_size | ✅ orders/create | ❌ (edit 复用 create 接口传 order_id) | ✅ orders/delete | ❌ | ❌ |

---

## SECTION 5: 数据真实性检查

| 模块 | 数据来源 | WHY |
|------|---------|-----|
| 监控大屏 | **真实 MySQL/H2** | alarm-warning-service 配置了 MySQL 8.0 (`mysql-connector-j` 依赖)，SQL init.sql 创建了 `alert_db` 库及 `alert_event/alert_rule/failure_prediction` 种子表，含初始化数据 |
| 预警事件 | **真实 MySQL/H2** | `AlertServiceImpl.selectPage(alertEventMapper)` → MyBatisPlus → MySQL `alert_event` 表 |
| 预警详情 | **真实 MySQL/H2** | `AlertEventMapper.selectById(id)` 从同一张表读取单条记录 |
| 规则管理 | **真实 MySQL/H2** | `AlertRuleService` CRUD 直接操作 MySQL `alert_rule` 表 |
| 故障预报 | **真实 MySQL/H2** | `FailurePredictionController` 读写 MySQL `failure_prediction` 表 |
| 燃气风控 | **Python SQLite** | `database.py` 使用 SQLAlchemy + SQLite (`gas_risk.db` ~18MB)。`simulator.py` 后台线程每秒写传感器数据到 DB；`start()` 时 `seed_history()` 预灌历史数据。**非内存模拟，有真实 DB 持久化** |
| 资产管理 | **Python SQLite** | `database.py` → SQLite (`gas_asset.db` ~115KB)。`seed.py` 幂等注入初始数据。完整 CRUD 落库 |
| 道路塌陷 | **Python SQLite** | `database.py` → SQLite (`road_hazard.db` ~28KB)。`seed.py` 注入 ≥30 条确定性演示数据。三子模块均有完整 CRUD |
| 风险研判 | **内存模拟** | `data_governance/simulator.py` 返回硬编码字典管线/设备/统计常量。`routes.py` 100% 调用 simulator。无 SQLAlchemy、无 DB 连接字符串、无任何文件存储 |
| 危化品监管 | **内存模拟** | `hazmat_transport/simulator.py` 返回硬编码字典介质/路线/溯源/腐蚀评估数据。同模式 |
| 综合管廊 | **内存模拟** | `tunnel_api/simulator.py` 返回内存 snapshot 对象（告警数组/管道列表/门禁记录）。workflow 步骤尝试执行 shell/spark 脚本但环境不满足即静默失败 |
| 应急预案 | **内存模拟** | `plan_api/simulator.py` 返回内存 plan list 和 activation dict。`persistence/plan_tables.py` 定义了表结构但 routes.py 未引用 store.py |
| 资产成本 | **内存模拟** | `asset_cost/simulator.py` 返回硬编码字典资产/费用/LCC/折旧方法。无 DB |
| 工单管理 | **内存模拟** | `workorder/simulator.py` 返回内存 dict 工单池。`persistence/workorder_tables.py` 定义了表结构但 routes.py 引用的是 simulator 包而非 store |
| ModulePlaceholder | **未实现/空页面** | 无任何逻辑、无 API、无数据加载 |

---

## SECTION 6: 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Vue SPA Frontend (vite :5173)                   │
│         alarm-warning-frontend/src/views/*.vue                      │
│  (Dashboard, Alerts, Rules, Prediction, GasRisk, Asset, ...)       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Vite Proxy: /api → localhost:8080
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    api-gateway :8080                                 │
│              Spring Cloud Gateway (Java Spring Boot 3.x)            │
│                                                                     │
│  /api/alert/**        ─────→ :8085  alarm-warning-service          │
│  /api/gas-risk/**     ─────→ :8003  gas_risk_control               │
│  /api/gas-asset/**    ─────→ :8001  gas_asset_manage               │
│  /api/road-hazard/**  ─────→ :8002  road_hazard_control            │
│  /api/platform/**     ─────→ :8000  Python 综合服务平台             │
│      ├─ /governance/*  → data_governance/routes.py (内存模拟)      │
│      ├─ /hazmat/*      → hazmat_transport/routes.py (内存模拟)     │
│      ├─ /tunnel/*      → tunnel_api/routes.py (内存模拟)            │
│      ├─ /plan/*        → plan_api/routes.py (内存模拟)              │
│      ├─ /asset-cost/*  → asset_cost/routes.py (内存模拟)            │
│      └─ /workorder/*   → workorder/routes.py (内存模拟)             │
└──┬──────────┬──────────┬──────────┬────────────────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
┌──────┐  ┌──────┐  ┌──────┐  ┌──────────────────────────────────┐
│:8085 │  │:8003 │  │:8001 │  │ :8000                            │
│ Java │  │FastA │  │FastA │  │  (单进程, 多 include_router)     │
│Boot  │  │ PI   │  │ PI   │  │                                  │
│      │  │      │  │      │  │ ┌────────────────────────────┐   │
│MySQL │  │SQLite│  │SQLite│  │ │data_governance/simulator.py│   │
│alert_│  │gas_  │  │gas_  │  │ └────────────────────────────┘   │
│_db   │  │risk.db│  │asset.db│ ┌────────────────────────────┐   │
│Kafka→│  │(18MB)│  │(115KB)│ │ │hazmat_transport/sim.py     │   │
│Redis→│  │seeded│  │seeded│  │ └────────────────────────────┘   │
│5 Ctrl│  │real- │  │CRUD  │  │ ┌────────────────────────────┐   │
│(Alert,Ru│ │time│  │write │  │ │tunnel_api/simulator.py      │   │
│le,Pred│  │thread│  │capa.│  │ └────────────────────────────┘   │
└──────┘  └──────┘  └──────┘  │plan_api/simulator.py           │   │
                              │asset_cost/simulator.py         │   │
                              │workorder/simulator.py          │   │
                              └──────────────────────────────────┘   │
                                                                  │
                        ┌──────────────────────────────────┐     │
                        │ src/python/persistence/          │     │
                        │  plan_tables.py (表结构定义)     │  ──× 未引用
                        │  workorder_tables.py (表结构定义)│  ──× 未引用
                        │  database.py (引擎/PRAGMA/工具)  │     │
                        └──────────────────────────────────┘     │
                                                                  │
                          ⚠️ persistence 层的 plan_tables.py 和   │
                             workorder_tables.py 在当前 sessions  │
                             中**未被任何 routes.py 引用** → 数据不入库
└─────────────────────────────────────────────────────────────────────┘
```

### 技术栈汇总

| 层级 | 技术选型 |
|------|---------|
| **前端** | Vue 3.4 + Vite 5 + Element Plus 2 + Axios + vue-router |
| **网关** | Spring Cloud Gateway (Spring Boot 3.2, JDK 17) |
| **Java 服务** | Spring Boot Web + MyBatisPlus + MySQL 8 + Kafka + Redis |
| **Python 微服务** | FastAPI + Uvicorn + SQLAlchemy + Pydantic v2 + SQLite |
| **数据库** | MySQL 8.0 (Java), SQLite (Python micro-services) |
| **消息队列** | Kafka (topic: tunnel-sensor, gas-risk-event; 消费者在 Java 侧) |
| **缓存** | Redis (rate-limiting, session, 去重窗口) |

---

## SECTION 7: 答辩风险评估

### HIGH RISK（高风险）— 答辩演示时易暴露问题

| 模块 | 风险等级 | 原因 |
|------|---------|------|
| **风险研判** | 🔴 HIGH | 100% 内存模拟。刷新页面数据不变。`simulator.py` 返回硬编码 dict，无任何 DB 交互 |
| **危化品监管** | 🔴 HIGH | 同上。`hazmat_transport/simulator.py` 无 DB。所有列表/详情/统计为死数据 |
| **综合管廊** | 🔴 HIGH | 内存模拟。管线 CRUD 写入内存不持久化。workflow 依赖不存在的大数据集群，必然失败 |
| **应急预案** | 🔴 HIGH | `plan_api/simulator.py` 返回内存 list。虽有 `persistence/plan_tables.py` 定义表结构，但 routes.py 未引用 store.py |
| **资产成本** | 🔴 HIGH | 内存模拟。`asset_cost/simulator.py` 无 DB。增删查改在进程内循环 |
| **工单管理** | 🔴 HIGH | 内存模拟。`workorder/simulator.py` 返回内存 dict。`persistence/workorder_tables.py` 定义了表结构但 routes.py 引用的是 simulator 包 |
| **ModulePlaceholder** | 🔴 HIGH | 空白页面。无任何功能、无 API |

### MEDIUM RISK（中等风险）— 部分功能可用但有依赖项

| 模块 | 风险等级 | 原因 |
|------|---------|------|
| **监控大屏 (Dashboard)** | 🟡 MEDIUM | 能连 Java 8085 + MySQL，但 `deviceOnlineRate` 字段硬编码 "98.6%"。若 MySQL 未启动则图表为空 |
| **预警事件列表** | 🟡 MEDIUM | 依赖 MySQL `alert_event` 表。init.sql 预置的数据量有限，无新增入口（只有查询和状态更新） |
| **预警详情** | 🟡 MEDIUM | 同上。只读 + 状态变更。风险低于列表页 |
| **规则管理** | 🟡 MEDIUM | 依赖 MySQL `alert_rule`。完整 CRUD。预置 4 条测试规则。MySQL 不可用时白屏 |
| **故障预报** | 🟡 MEDIUM | 依赖 MySQL `failure_prediction`。预置 8 条数据。generate 端点需算法模型文件 (`.pkl`) |
| **燃气风控** | 🟡 MEDIUM | SQLite 实时数据写入。但模拟器 `start()` 需手动调用。服务重启后如不调用 `start()` 则无实时数据流 |
| **资产管理** | 🟡 MEDIUM | SQLite 完整持久化。CSV 导出正常。缺少 DELETE 操作（无删除 API），inventory task 只能创建不能删除 |
| **道路塌陷** | 🟡 MEDIUM | SQLite 持久化。三子模块均有完整 CRUD。数据量小(~28KB seed)，仅靠 `seed.py` 一次性注入 |

### LOW RISK（低风险）— 可稳定展示

**无。** 即使表现最好的模块(GasAsset/RoadHazard/GasRisk)也是局部 SQLite + 手动启动模式。没有模块达到"生产级"标准。

---

## SECTION 8: 下一步优先级 P0 / P1 / P2

### P0 — 必须立即修复（影响答辩核心演示）

| 序号 | 任务 | 影响面 | 理由 |
|------|------|--------|------|
| **P0-1** | 将 platform 侧 6 个模块(风险研判/危化品/管廊/应急/资产成本/工单)从 simulator 迁移到 SQLite 持久化 | 6/14 页面, 42.9% | 这 6 个模块占前端 6/14 页面，当前 100% 假数据，Demo 一刷新就露馅 |
| **P0-2** | 确保 MySQL 实例运行且 init.sql 已执行 | 5/14 页面 | Java 侧 5 个页面(Dashboard/Alerts/Rules/FailurePrediction)全部依赖 MySQL，若 MySQL 不可用则全白屏 |
| **P0-3** | 统一后端数据源策略 | 全局 | 当前同时出现 MySQL(Java)、SQLite(Python 微服务)、内存模拟(Python platform)三种模式，缺乏统一治理 |

### P1 — 次优先（完善现有功能）

| 序号 | 任务 | 影响面 | 理由 |
|------|------|--------|------|
| **P1-1** | 给 gas_asset 增加 DELETE API | 资产管理 | 缺少删除功能，业务不完整 |
| **P1-2** | 给 gas_risk_control 增加更多 CRUD (如占用隐患/阴极保护的写入) | 燃气风控 | monitoring.py 主要面向查询，写入操作多为 demo 注入 |
| **P1-3** | 打通 Kafka 消息链路 | Java 服务 | alarm-warning-service 订阅了 tunnel-sensor/gas-risk-event 等 topic，但无实际消息生产者对接，Kafka 集成处于断头状态 |
| **P1-4** | 补充 Redis 依赖 | Java 服务 | alarm-warning-service 配置了 Redis 作为缓存/去重窗口存储，但没有实际的 Redis 实例 |

### P2 — 中长期优化

| 序号 | 任务 | 影响面 | 理由 |
|------|------|--------|------|
| **P2-1** | 完成 ModulePlaceholder 对应模块的实际开发 | 前端 | 当前预留但未定义具体模块 |
| **P2-2** | 建立统一的 admin 面板用于管理系统配置/用户/权限 | 全局 | 当前无任何 auth/admin 模块 |
| **P2-3** | 建立 CI/CD 管道 | 部署 | 当前各服务独立启动，无容器化编排 |
| **P2-4** | 补充 API 文档/Swagger 统一聚合 | 开发体验 | 6 个后端服务各有 docs 但无统一入口 |
