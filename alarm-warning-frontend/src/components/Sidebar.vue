<template>
  <aside class="sidebar" :class="{ 'is-collapsed': collapsed }">
    <!-- 品牌/Logo 区 -->
    <div class="sidebar__brand">
      <div class="sidebar__logo">
        <el-icon :size="22"><component :is="brandIcon" /></el-icon>
      </div>
      <div v-show="!collapsed" class="sidebar__brand-text">
        <div class="sidebar__brand-title">城市生命线</div>
        <div class="sidebar__brand-subtitle">Urban Lifeline</div>
      </div>
    </div>

    <!-- 菜单列表 -->
    <nav class="sidebar__menu">
      <router-link
        v-for="item in menus"
        :key="item.path"
        :to="item.path"
        class="sidebar__item"
        :class="{ 'is-active': isActive(item) }"
        :title="item.title"
      >
        <el-icon :size="20" class="sidebar__item-icon">
          <component :is="item.icon" />
        </el-icon>
        <span v-show="!collapsed" class="sidebar__item-text">{{ item.title }}</span>
      </router-link>
    </nav>

    <!-- 底部折叠按钮 -->
    <div class="sidebar__footer" @click="$emit('toggle')">
      <el-icon :size="16">
        <component :is="collapsed ? expandIcon : collapseIcon" />
      </el-icon>
      <span v-show="!collapsed" class="sidebar__footer-text">收起菜单</span>
    </div>
  </aside>
</template>

<script setup>
import { useRoute } from 'vue-router'
import {
  Odometer, Bell, TrendCharts, DataAnalysis,
  Aim, Box, Grid, MapLocation, AlarmClock,
  OfficeBuilding, Coin, Tickets,
  Fold, Expand
} from '@element-plus/icons-vue'

defineProps({
  collapsed: { type: Boolean, default: false }
})

defineEmits(['toggle'])

const route = useRoute()
const brandIcon = Odometer
const collapseIcon = Fold
const expandIcon = Expand

// 菜单清单（12 项，按用户最新要求）：
// 监控大屏 / AI预警中心 / 故障预测中心 / 风险研判中心 / 燃气风控 / 危化品监管 /
// 综合管廊 / 道路塌陷 / 应急预案 / 资产管理 / 资产成本 / 工单管理
const menus = [
  { path: '/',                   title: '监控大屏',     icon: Odometer },
  { path: '/alerts',             title: 'AI预警中心',   icon: Bell },
  { path: '/failure-prediction', title: '故障预测中心', icon: TrendCharts },
  { path: '/risk-analysis',      title: '风险研判中心', icon: DataAnalysis },
  { path: '/gas-risk',           title: '燃气风控',     icon: Aim },
  { path: '/hazmat',             title: '危化品监管',   icon: Box },
  { path: '/utility-tunnel',     title: '综合管廊',     icon: Grid },
  { path: '/road-hazard',        title: '道路塌陷',     icon: MapLocation },
  { path: '/emergency-plan',     title: '应急预案',     icon: AlarmClock },
  { path: '/asset',              title: '资产管理',     icon: OfficeBuilding },
  { path: '/asset-cost',         title: '资产成本',     icon: Coin },
  { path: '/work-order',         title: '工单管理',     icon: Tickets }
]

// 高亮规则：根路径精确匹配，其余前缀匹配（/alerts/123 高亮 AI预警中心）
function isActive(item) {
  if (item.path === '/') return route.path === '/'
  return route.path === item.path || route.path.startsWith(item.path + '/')
}
</script>

<style scoped>
.sidebar {
  width: 240px;
  height: 100vh;
  position: sticky;
  top: 0;
  /* 玻璃材质侧边栏 */
  background-color: rgba(255, 255, 255, 0.72);
  -webkit-backdrop-filter: blur(24px) saturate(1.8);
  backdrop-filter: blur(24px) saturate(1.8);
  border-right: 1px solid var(--app-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  z-index: 10;
}
.sidebar.is-collapsed {
  width: 76px;
}

/* 品牌区 */
.sidebar__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 20px;
  border-bottom: 1px solid var(--app-border);
}
.sidebar__logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  /* Apple 风格渐变 logo */
  background: linear-gradient(135deg, #0071E3 0%, #5856D6 100%);
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.25);
}
.sidebar__brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.sidebar__brand-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--app-text-1);
  white-space: nowrap;
  letter-spacing: -0.01em;
}
.sidebar__brand-subtitle {
  font-size: 11px;
  color: var(--app-text-4);
  letter-spacing: 0.04em;
  white-space: nowrap;
}

/* 菜单容器 */
.sidebar__menu {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 10px;
}

/* 菜单项 */
.sidebar__item {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 44px;
  margin: 2px 0;
  padding: 0 14px;
  border-radius: 16px;
  color: var(--app-text-2);
  text-decoration: none;
  cursor: pointer;
  position: relative;
  transition: background-color 0.2s ease, color 0.2s ease;
}
.sidebar__item:hover {
  background-color: var(--app-hover);
  color: var(--app-text-1);
}
/* Apple 风格激活态：浅蓝背景 + 左侧蓝色标识条 */
.sidebar__item.is-active {
  background-color: var(--app-primary-soft);
  color: var(--app-primary);
  font-weight: 500;
}
.sidebar__item.is-active::before {
  content: '';
  position: absolute;
  left: 4px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 18px;
  background-color: var(--app-primary);
  border-radius: 2px;
}
.sidebar__item-icon {
  flex-shrink: 0;
}
.sidebar__item-text {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 折叠态居中菜单项内容 */
.is-collapsed .sidebar__item {
  justify-content: center;
  padding: 0;
}
.is-collapsed .sidebar__item.is-active::before {
  display: none;
}
.is-collapsed .sidebar__brand {
  justify-content: center;
  padding: 20px 0;
}

/* 底部折叠按钮 */
.sidebar__footer {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 48px;
  padding: 0 20px;
  border-top: 1px solid var(--app-border);
  color: var(--app-text-3);
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s ease, color 0.2s ease;
}
.sidebar__footer:hover {
  background-color: var(--app-hover);
  color: var(--app-text-2);
}
.is-collapsed .sidebar__footer {
  justify-content: center;
  padding: 0;
}
.sidebar__footer-text {
  font-size: 13px;
  white-space: nowrap;
}
</style>
