# 资产数字化台账子模块（后端）

天信城市生命线管网 AI 智慧平台 · 燃气管网资产数字化台账服务。
基于 **FastAPI + SQLite**，为前端数据可视化大屏提供资产台账、全生命周期档案、
资产盘点、资产权属四大功能的 REST API 与内置演示数据。

## 功能概览

| # | 功能 | 说明 |
|---|------|------|
| 1 | 资产全景台账 | 60 条管段资产主数据（编号/名称/管径/材质/年代/权属/区域/长度/压力等级/状态/位置/坐标），五维分类统计、多条件筛选检索、CSV 导出 |
| 2 | 全生命周期档案 | 采购→施工→运维→改造→报废时间线，每阶段记录时间/责任单位/描述/附件/费用，支持新增与编辑 |
| 3 | 资产盘点 | 扫码盘点与巡检盘点两种方式；生成任务→账实核对→标记差异→差异处理（补录/修正/报废）→完成闭环 |
| 4 | 资产权属管理 | 产权/运维/监管三方责任登记，责任矩阵热力数据，产权性质/单位分布统计，权属不清资产预警与补录 |

## 目录结构

```
gas_asset_manage/
├── main.py            # FastAPI 入口（含 CORS、路由注册、启动时初始化+播种）
├── database.py        # SQLite 连接与 5 张表结构（assets / lifecycle_records /
│                      #   inventory_tasks / inventory_items / ownership）
├── seed.py            # 确定性演示数据：60 条资产、生命周期、盘点任务、权属
├── models.py          # Pydantic 请求模型与阶段枚举
├── routers/
│   ├── assets.py      # 功能 1：资产台账（列表/筛选/统计/导出/详情）
│   ├── lifecycle.py   # 功能 2：全生命周期档案
│   ├── inventory.py   # 功能 3：资产盘点
│   └── ownership.py   # 功能 4：资产权属管理
└── requirements.txt
```

## 快速启动

```bash
# 1. 创建虚拟环境并安装依赖（需 Python 3.10+）
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 2. 启动服务（默认 8001 端口）
.venv\Scripts\python main.py
```

启动时自动建表并播种演示数据（幂等，重复启动不会重复插入）。
交互文档：http://localhost:8001/docs

## 主要接口

### 1. 资产全景台账 `/api/assets`
- `GET /api/assets` 资产列表：`keyword` 模糊搜索 + `diameter/material/owner_unit/region/status/year_from/year_to` 多条件筛选 + 分页
- `GET /api/assets/options` 筛选下拉选项（去重值）
- `GET /api/assets/summary` 大屏指标：资产总数/总长度/在役/停用/待报废/盘点完成率/权属清晰率
- `GET /api/assets/stats` 五维分类统计：管径/材质/年代/权属单位/区域（另含压力等级、状态）
- `GET /api/assets/export` 导出 CSV（含 BOM，Excel 直接打开不乱码）
- `GET /api/assets/{id}` 资产详情（含权属信息与生命周期阶段汇总）

### 2. 全生命周期档案 `/api/lifecycle`
- `GET /api/lifecycle/stages` 标准阶段定义
- `GET /api/lifecycle/{asset_id}` 单资产完整时间线 + 费用合计
- `GET /api/lifecycle` 记录查询（可按阶段过滤）
- `POST /api/lifecycle` 新增阶段记录
- `PUT /api/lifecycle/{record_id}` 编辑阶段记录

### 3. 资产盘点 `/api/inventory`
- `POST /api/inventory/tasks` 生成盘点任务（扫码/巡检，按区域圈定范围）
- `POST /api/inventory/tasks/{id}/scan` 扫码核对单件资产（账外资产自动记盘盈）
- `POST /api/inventory/tasks/{id}/patrol` 巡检批量核对
- `PUT /api/inventory/items/{id}` 差异处理（补录/修正/报废，报废联动资产状态）
- `POST /api/inventory/tasks/{id}/finish` 完成盘点（校验未核对/未处理项）
- `GET /api/inventory/tasks`、`GET /api/inventory/tasks/{id}` 任务列表/详情
- `GET /api/inventory/diff` 差异清单与处理跟踪
- `GET /api/inventory/stats` 差异处理状态分布与账实一致率

### 4. 资产权属管理 `/api/ownership`
- `GET /api/ownership` 权属列表（含是否清晰标记）
- `GET /api/ownership/matrix` 三方责任矩阵（产权/运维/监管 × 区域，热力图数据）
- `GET /api/ownership/unclear` 权属不清资产预警（产权/运维/监管任一缺失）
- `GET /api/ownership/stats` 清晰率/产权性质/各单位分布
- `GET /api/ownership/{asset_id}` 单资产权属
- `PUT /api/ownership/{asset_id}` 权属补录/修正

## 演示数据说明

`seed.py` 使用固定随机种子（20260831），每次重建数据库生成一致的演示数据：

- 60 条管段资产：覆盖 5 个区域、6 种管径、4 种材质、1990s–2020s 四个年代，
  材质按建设年代合理分布（早期以铸铁/钢管为主，近年以 PE 管为主）；
- 状态分布：在役 52、停用 3、待报废 5；
- 生命周期：每条资产含采购、施工及 1–3 次运维记录，约 30% 有改造记录，待报废资产含报废申请；
- 盘点：3 个历史任务（2 个已完成），含账实一致/状态不符/盘亏/盘盈多种差异与处理状态；
- 权属：13 条资产存在产权/运维/监管信息缺失，用于预警演示；盘点完成率 66.7%，权属清晰率 78.3%。

重置数据：停止服务后删除 `gas_asset.db*` 再启动即可。

## 技术要点

- SQLite 开启 WAL，逐请求连接，`CREATE TABLE IF NOT EXISTS` 保证幂等；
- 盘点状态机：核对结果（待核对/一致/状态不符/盘亏/盘盈）× 处理状态（待核对/无差异/待处理/补录/修正/报废），任务状态（执行中/差异处理中/已完成）由业务自动流转；
- 权属清晰判定：产权单位、运维单位、监管单位三方均非空；
- 无任何付费第三方服务，全部使用标准库 + FastAPI 生态。
