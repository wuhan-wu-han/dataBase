# 燃气管网安全风控系统（前端）

纯静态前端：HTML + CSS + JavaScript + ECharts（已内置 `js/lib/echarts.min.js`，无需联网）。

## 使用方式

1. 先启动后端：`cd ../gas_risk_control && python main.py`（默认 http://localhost:8000）
2. 用浏览器直接打开 `index.html`；
   或用静态服务器托管本目录：`python -m http.server 3000` 后访问 http://localhost:3000

> 后端地址默认 `http://localhost:8000`，如需修改，在浏览器控制台执行：
> `localStorage.setItem('apiBase', 'http://你的地址:端口')`

## 页面与功能对应

| 页面 | 对应功能 |
|------|----------|
| index.html | 1 实时安全监测（仪表、趋势曲线、报警、故障注入） |
| leak.html | 2 微泄漏精准定位（浓度扩散反演 + 压力波时差法） |
| diffusion.html | 3 泄漏扩散仿真（浓度热力图 + 爆炸危险范围） |
| third-party.html | 4 第三方破坏预警（扰动分布 + 分区告警） |
| user-safety.html | 5 用户端用气安全（风险扫描 + 异常注入） |
| occupation.html | 6 占压隐患管理（台账 + 整改闭环时间线） |
| cathodic.html | 7 阴极保护监测（电位/电流评价 + 历史趋势） |
| emergency.html | 8 应急联动关阀（关阀方案 + 阀门拓扑 + 执行/恢复） |
