# 供水管网精细化管控大屏（前端 water_supply_frontend）

城市生命线管网 AI 智慧平台 — 供水管道运行监控、漏损治理、水质溯源、压力调度、爆管风险评估。

## 技术栈
- Vue3 + TypeScript + Vite4 + Element Plus + ECharts（浅色系可视化大屏）
- Node 16 验证通过（Vite 4.5.3）

## 目录结构
```
water_supply_frontend/
├── src/
│   ├── api/            # axios 封装与全部接口
│   ├── components/     # StatCards + 7 个功能面板
│   │   ├── MonitorPanel.vue    # 功能1 实时运行监测
│   │   ├── DmaPanel.vue        # 功能2 DMA分区漏损
│   │   ├── QualityPanel.vue    # 功能3 水质全流程溯源
│   │   ├── PressurePanel.vue   # 功能4 智能压力调度
│   │   ├── SecondaryPanel.vue  # 功能5 二次供水管控
│   │   ├── HydrantPanel.vue    # 功能6 消防栓专项管理
│   │   └── BurstPanel.vue      # 功能7 爆管影响分析
│   ├── styles/main.css # 浅色主题样式
│   ├── types/          # TS 类型定义
│   ├── utils/          # chart.ts / format.ts
│   ├── App.vue
│   └── main.ts
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts      # dev 端口 5193，/api 代理到 8004
```

## 启动步骤
```bash
# 0. 先启动后端（端口 8004），见 water_supply_control/README.md

# 1. 安装依赖
npm install

# 2. 开发模式
npm run dev          # http://localhost:5193

# 3. 构建 + 静态预览
npm run build
npx vite preview --port 5193
```

## 页面结构
- 顶部：6 张统计指标卡（管道总数/未处理告警/平均漏损率/水质异常/消防栓/爆管高风险）
- 7 个 Tab：实时监测、DMA漏损、水质溯源、压力调度、二次供水、消防栓、爆管分析
- 每个 Tab：趋势/分布图表 + 业务明细台账表格 + 增改查/处置操作弹窗
