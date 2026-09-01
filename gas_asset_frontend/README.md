# 资产数字化台账大屏（前端）

天信城市生命线管网 AI 智慧平台 · 资产数字化台账数据可视化大屏。
**Vue3 + TypeScript + Vite + Element Plus + ECharts**，整体采用淡色系（浅色背景）设计。

## 页面内容

- **顶部指标卡**：资产总数 / 管网总长度 / 在役资产 / 待报废资产 / 盘点完成率 / 权属清晰率；
- **资产分类统计图（五维）**：管径、材质、建设年代、权属单位、所属区域；
- **全生命周期档案**：采购→施工→运维→改造→报废阶段分布图与近期记录；资产明细的「档案」抽屉中可查看单资产完整时间线，并支持新增/编辑阶段记录；
- **资产盘点**：盘点任务列表（生成任务、扫码盘点模拟、巡检盘点批核、完成盘点），差异清单与处理跟踪（补录/修正/报废），差异处理状态分布图与账实一致率；
- **资产权属管理**：产权/运维/监管三方责任矩阵热力图，权属不清资产预警清单与在线补录；
- **资产明细台账**：关键字搜索 + 区域/管径/材质/状态多条件筛选 + 分页 + 一键导出 CSV。

## 目录结构

```
gas_asset_frontend/
├── index.html
├── vite.config.ts
├── tsconfig.json
└── src/
    ├── main.ts              # 入口（注册 Element Plus 中文语言包）
    ├── App.vue              # 大屏骨架：头部时钟、指标、图表、面板、明细表
    ├── api/                 # axios 封装，对接后端 :8001 全部接口
    ├── types/               # 与后端对应的 TypeScript 类型
    ├── utils/               # 图表配色/坐标轴样式、时间与标签格式化
    ├── styles/main.css      # 淡色系全局样式
    └── components/          # StatCards / DimensionCharts / LifecyclePanel /
                             #   InventoryPanel / OwnershipPanel / AssetTable /
                             #   AssetDetailDrawer / OwnershipFormDialog
```

## 运行

前置：后端服务 `gas_asset_manage` 已在 `http://localhost:8001` 启动（接口地址在
`src/api/base.ts` 中，如需修改请调整 `API_BASE`）。

```bash
# 安装依赖（已适配国内镜像）
npm install

# 开发模式（热更新，端口 5173）
npm run dev

# 生产构建 → dist/
npm run build
```

### 以本地静态服务打开大屏

构建后可用任意静态服务器托管 `dist/`，例如：

```bash
cd dist
python -m http.server 5180
# 浏览器打开 http://localhost:5180
```

## 技术说明

- Node 16 兼容：锁定 Vite 4 / @vitejs/plugin-vue 4 系列；
- 构建脚本使用 `vite build`（不强制 vue-tsc 类型检查，保证构建稳定），类型定义完整；
- 图表基于 ECharts 5，全部为淡色配色并随窗口自适应；
- 所有数据来自后端真实接口，内置演示数据（60 条资产）开箱即用；
- 无任何付费第三方服务。
