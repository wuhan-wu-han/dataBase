# 道路地下隐患防控子模块（road_hazard_control）

天信城市生命线管网 AI 智慧平台 —— 道路地下隐患防控模块后端。
基于 **FastAPI + SQLite**，覆盖地下空洞、道路沉降、施工影响三类道路塌陷
隐患的风险评估与台账管理，内置确定性演示数据，可独立运行。

## 功能

| 功能 | 路由前缀 | 说明 |
|---|---|---|
| 地下空洞风险评估 | `/api/cavity` | 录入地质雷达波速/异常面积、渗漏指数、空洞体积，自动计算 0-100 风险评分并判定低/中/高风险；台账新增、修改（自动重算）、查询、统计 |
| 道路沉降监测 | `/api/subsidence` | 多期沉降观测数据融合：按监测点留存历史，计算累计沉降量、近期速率（mm/月）与加速趋势，融合判定塌陷风险；新增观测自动累计 |
| 施工影响评估 | `/api/construction` | 录入施工项目（工法、开挖深度、与管线距离），自动评估土体风险、管网风险与综合评分，形成评估档案 |
| 大屏汇总 | `/api/summary` | 顶部统计卡片数据 |

### 风险判定规则

- **空洞风险评分**：异常区面积分档（40/30/18/6）+ 渗漏指数分档（30/20/10/0）
  + 空洞体积分档（30/20/10/0）；≥60 高风险、≥35 中风险、其余低风险。
- **沉降融合判定**：累计 ≥50mm 或速率 ≥6mm/月 → 高风险（塌陷风险）；
  累计 ≥30mm 或速率 ≥3 → 中风险（快速发展）；累计 ≥15 或速率 ≥1.2 → 低风险
  （缓慢发展）；其余稳定。最新一期增量大于上一期时标注"（加速）"。
- **施工影响评估**：土体风险 = 开挖深度 × 9 × 工法权重（明挖 1.0 / 打桩 0.9 /
  顶管 0.8 / 定向钻 0.6 / 非开挖修复 0.5）；管网风险按距管线距离分档
  （<1.5m→90、<3m→65、<6m→40、其余 15）× 工法权重；综合评分取两者均值。

## 目录结构

```
road_hazard_control/
├── main.py                 # FastAPI 入口（端口 8002，启动自动建表+播种）
├── database.py             # SQLite 连接与建表（WAL 模式）
├── models.py               # Pydantic 模型 + 三类风险评分函数
├── seed.py                 # 确定性演示数据（14 空洞 + 8 监测点 41 期观测 + 10 施工评估）
├── routers/
│   ├── cavity.py           # 功能1 地下空洞
│   ├── subsidence.py       # 功能2 道路沉降
│   └── construction.py     # 功能3 施工影响
├── requirements.txt
└── road_hazard.db          # SQLite 数据库（首次启动自动生成）
```

## 运行

```bash
cd road_hazard_control
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows
.venv/Scripts/python main.py                    # 默认端口 8002
```

- 接口文档：http://localhost:8002/docs
- 首次启动自动建表并注入演示数据（幂等，重复启动不会重复播种）。
- 更换端口：`PORT=8010 python main.py`（Windows: `set PORT=8010 && python main.py`）。

## 主要接口

```
GET  /api/summary                        大屏统计
GET  /api/cavity                         空洞列表（keyword/district/risk_level/status/分页）
POST /api/cavity                         新增空洞（自动风险评估）
PUT  /api/cavity/{id}                    修改空洞（自动重算风险）
GET  /api/cavity/{id} | /stats | /options
GET  /api/subsidence/points              监测点融合风险总览
GET  /api/subsidence/history?point_code= 监测点历史观测
POST /api/subsidence/records             新增观测（自动累计+日期校验）
GET  /api/subsidence/stats | /options
GET  /api/construction                   评估档案列表（分页+过滤）
POST /api/construction                   新增施工评估（自动评分）
GET  /api/construction/{id} | /stats | /options
```

## 依赖

fastapi、uvicorn[standard]、pydantic（见 requirements.txt），均为开源组件。
