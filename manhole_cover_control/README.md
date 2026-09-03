# 市政井盖全生命周期管控子模块（manhole_cover_control）

天信城市生命线管网 AI 智慧平台 —— 市政井盖全生命周期管控模块后端。
基于 **FastAPI + SQLite**，实现井盖从在线监测、电子档案、工单闭环处置、
被盗追踪到防坠网运维的完整数字化管控，内置确定性演示数据（90+ 条），可独立运行。

## 功能

| 功能 | 路由前缀 | 说明 |
|---|---|---|
| 状态实时监测 | `/api/monitor` | 采集倾角/位移/破损/井下水位/有毒气体多维数据；实时指标展示；异常按阈值自动产生告警并自动生成待派发工单（同类未闭环告警去重） |
| 一井一档数字档案 | `/api/archive` | 每处井盖独立电子台账：基础信息、权属单位、运维履历、维修更换历史；新增/编辑/多条件查询 |
| 隐患闭环处置 | `/api/orders` | 告警 → 派发工单 → 现场处置上报 → 整改核验 → 闭环销号归档；核验不通过退回重新上报；全程联动告警与井盖状态 |
| 被盗追踪管理 | `/api/theft` | 异动轨迹存储与回放、最新位置定位追踪、公安联动记录（报案/立案/侦破/追回） |
| 防坠网台账管理 | `/api/safety-net` | 安装登记、破损登记、维修/更换运维台账，状态与维修次数联动 |

### 告警阈值规则（models.py 可调）

| 指标 | 阈值 | 告警类型 | 等级 |
|---|---|---|---|
| 位移 | ≥30mm | 被盗异动 | 高 |
| 位移 | ≥10mm | 位移异常 | 中 |
| 倾角 | ≥15° | 倾角异常 | 高 |
| 破损 | 破损 / 轻微裂缝 | 井盖破损 / 轻微裂缝 | 高 / 低 |
| 水位 | ≥80cm | 水位告警 | 中 |
| 有毒气体 | ≥10ppm | 有毒气体告警 | 高 |

### 工单状态机

```
待派发 → 处置中 → 待核验 → 已核验 → 已闭环
              ↑________|（核验不通过退回）
```

## 目录结构

```
manhole_cover_control/
├── main.py                 # FastAPI 入口（端口 8003，启动自动建表+播种）
├── database.py             # SQLite 连接与 9 张业务表（WAL 模式）
├── models.py               # Pydantic 模型 + 告警阈值判定
├── seed.py                 # 确定性演示数据（12 井盖档案 / 36 期监测 / 7 告警工单
│                           #   全阶段 / 被盗轨迹 6 点 + 公安记录 / 10 防坠网 / 8 维修履历）
├── routers/
│   ├── monitor.py          # 功能1 实时监测
│   ├── archive.py          # 功能2 一井一档
│   ├── orders.py           # 功能3 闭环处置
│   ├── theft.py            # 功能4 被盗追踪
│   └── safety_net.py       # 功能5 防坠网台账
├── requirements.txt
└── manhole_cover.db        # SQLite 数据库（首次启动自动生成）
```

## 运行

```bash
cd manhole_cover_control
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows
.venv/Scripts/python main.py                    # 默认端口 8003
```

- 接口文档：http://localhost:8003/docs
- 首次启动自动建表并注入演示数据（幂等）。
- 更换端口：`PORT=8010 python main.py`。

## 主要接口

```
GET  /api/summary                          大屏统计
POST /api/monitor/data                     采集监测数据（异常自动告警+建单）
GET  /api/monitor/latest                   全部井盖实时指标（only_abnormal 过滤）
GET  /api/monitor/history?manhole_id=      单井盖监测历史
GET  /api/monitor/alarms | /alarm-trend | /stats
GET  /api/archive                          档案多条件查询（keyword/district/type/status/owner_unit）
POST /api/archive | PUT /api/archive/{id}  新增建档 / 编辑
GET  /api/archive/{id}                     档案详情（履历+告警+防坠网+最新监测）
POST /api/archive/{id}/repairs             登记维修/更换履历
GET  /api/orders                           工单列表
POST /api/orders/{id}/dispatch|report|verify|close   闭环流转
GET  /api/orders/{id} | /stats
GET  /api/theft/cases | /tracks?manhole_id= | /locate/{manhole_id}
POST /api/theft/tracks | /police           上报轨迹点 / 公安报案
PUT  /api/theft/police/{id}                更新公安进展（追回联动井盖状态）
GET  /api/safety-net | /{id} | /stats      防坠网台账
POST /api/safety-net | /{id}/maintain      安装登记 / 破损·维修·更换
```

## 依赖

fastapi、uvicorn[standard]、pydantic（见 requirements.txt），均为开源组件。
