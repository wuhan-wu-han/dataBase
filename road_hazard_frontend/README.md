# 道路地下隐患防控可视化大屏（road_hazard_frontend）

天信城市生命线管网 AI 智慧平台 —— 道路地下隐患防控模块前端。
基于 **Vue 3 + TypeScript + Vite 4 + Element Plus + ECharts** 的浅色系可视化大屏，
与后端 `road_hazard_control`（端口 8002）配套运行。

## 功能

- **顶部统计卡片**：空洞总数 / 高风险空洞 / 沉降监测点 / 危险点位 / 施工评估项目 / 高风险项目
- **地下空洞风险评估**：风险等级与区域分布图表；台账查询（关键字/区域/等级/状态）、
  录入雷达与渗漏数据并自动判定风险、编辑后自动重算
- **道路沉降监测**：塌陷风险分布与月度趋势图；监测点融合风险总览（累计沉降/速率/加速趋势），
  历史观测曲线弹窗，新增观测自动累计
- **施工影响评估**：风险等级与工法分布图；评估档案查询与详情抽屉，
  录入施工信息自动计算土体/管网/综合评分

## 运行

```bash
cd road_hazard_frontend
npm install          # 建议：--registry=https://registry.npmmirror.com
npm run build        # 产物输出到 dist/
npm run dev          # 开发模式，默认端口 5173
```

生产部署可将 `dist/` 交由任意静态服务器托管，例如：

```bash
# 使用后端解释器快速静态托管（端口 5191）
python -m http.server 5191 --directory road_hazard_frontend/dist
```

> 前端通过绝对地址 `http://localhost:8002` 调用后端（见 `src/api/base.ts`），
> 后端已开启 CORS（`allow_origins=["*"]`），无需代理。

## 目录结构

```
road_hazard_frontend/
├── index.html
├── package.json / tsconfig.json / vite.config.ts
└── src/
    ├── main.ts                 # Vue + Element Plus（中文）入口
    ├── App.vue                 # 头部 + 统计卡片 + 三大功能页签
    ├── api/                    # axios 封装（base 8002）与接口定义
    ├── types/                  # TS 类型
    ├── utils/                  # 图表配色/配置、格式化
    ├── styles/main.css         # 浅色主题样式
    └── components/
        ├── StatCards.vue       # 顶部统计卡片
        ├── CavityPanel.vue     # 功能1 地下空洞
        ├── SubsidencePanel.vue # 功能2 道路沉降
        └── ConstructionPanel.vue # 功能3 施工影响
```

## 依赖

vue、element-plus、echarts、axios（运行时）；vite 4、@vitejs/plugin-vue、typescript（构建），
均为开源组件。
