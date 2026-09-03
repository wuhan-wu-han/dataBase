<template>
  <div class="layout" :class="{ 'is-flush': isFlush }">
    <Sidebar :collapsed="collapsed" @toggle="toggleCollapsed" />

    <!-- 移动端：遮罩 + 抽屉式导航（复用同一个 Sidebar 组件，不做第二套菜单） -->
    <transition name="fade-scrim">
      <div v-if="mobileNav" class="layout__scrim" @click="mobileNav = false"></div>
    </transition>
    <transition name="slide-nav">
      <div v-show="mobileNav" class="layout__mobilenav">
        <Sidebar :collapsed="false" @toggle="mobileNav = false" @navigate="mobileNav = false" />
      </div>
    </transition>

    <main class="layout__main">
      <!-- 顶部玻璃栏：平台名 + 英文副标题 + 右侧信息 -->
      <header class="layout__topbar">
        <div class="layout__topbar-left">
          <!-- 移动端菜单按钮 -->
          <button
            class="layout__navbtn"
            type="button"
            aria-label="打开导航菜单"
            @click="mobileNav = true"
          >
            <el-icon :size="20"><Menu /></el-icon>
          </button>
          <div class="layout__brand">
            <h1 class="layout__brand-title">安塞区城市安全生命线管网AI智慧平台</h1>
            <p class="layout__brand-subtitle">AI-Powered Urban Lifeline Security Platform</p>
          </div>
        </div>
        <div class="layout__topbar-right">
          <!-- 当前时间 -->
          <div class="topbar-info">
            <el-icon :size="16"><Clock /></el-icon>
            <span class="topbar-info__text">{{ currentTime }}</span>
          </div>
          <!-- 在线设备数 -->
          <div class="topbar-info">
            <el-icon :size="16"><Monitor /></el-icon>
            <span class="topbar-info__text">在线设备 <strong>{{ onlineDevices }}</strong></span>
          </div>
          <!-- 用户头像 -->
          <div class="topbar-avatar">
            <span>管</span>
          </div>
        </div>
      </header>

      <!-- Mock 提示条：任一模块接口未连通时显示，避免演示数据被误认为真实数据 -->
      <div v-if="hasMockData" class="layout__mockbar">
        <el-icon :size="15"><WarningFilled /></el-icon>
        <span class="layout__mockbar-label">当前使用演示数据（Mock）</span>
        <span class="layout__mockbar-modules">{{ mockLabels }}</span>
        <span class="layout__mockbar-hint">该模块接口未连通，数据非真实后端数据</span>
      </div>

      <!-- 内容区：Vue Transition 淡入淡出 300ms -->
      <div class="layout__content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Clock, Monitor, WarningFilled, Menu } from '@element-plus/icons-vue'
import Sidebar from './Sidebar.vue'
import { hasMockData, mockModules } from '@/utils/mockMode'

const route = useRoute()

/**
 * 全出血页面（如 /gis 综合态势）：内容区去掉内边距、锁定视口高度，
 * 由页面自身接管内部滚动，地图得以铺满顶栏以下的全部区域。
 */
const isFlush = computed(() => !!route.meta?.fullBleed)

const mockLabels = computed(() => mockModules.value.map((m) => m.label).join('、'))

// 折叠状态持久化 key
const STORAGE_KEY = 'app_sidebar_collapsed'
const collapsed = ref(readCollapsed())
function toggleCollapsed() {
  collapsed.value = !collapsed.value
}
watch(collapsed, (val) => {
  try {
    window.localStorage.setItem(STORAGE_KEY, String(val))
  } catch (e) {
    // localStorage 不可用时静默降级
  }
})
function readCollapsed() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === 'true'
  } catch (e) {
    return false
  }
}

// ===== 移动端抽屉导航 =====
const mobileNav = ref(false)
// 路由切换后自动收起，避免从抽屉点进页面后抽屉仍盖在内容上
watch(() => route.fullPath, () => { mobileNav.value = false })

// ===== 顶部时间 =====
const currentTime = ref('')
let clockTimer = null
function updateClock() {
  const now = new Date()
  const y = now.getFullYear()
  const mo = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const h = String(now.getHours()).padStart(2, '0')
  const mi = String(now.getMinutes()).padStart(2, '0')
  const s = String(now.getSeconds()).padStart(2, '0')
  currentTime.value = `${y}-${mo}-${d} ${h}:${mi}:${s}`
}

// ===== 在线设备数 =====
// TODO: 设备在线率无后端接口，使用 mock 值 1,287 台占位
const onlineDevices = ref(1287)

onMounted(() => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
})
onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
})
</script>

<style scoped>
.layout {
  display: flex;
  width: 100%;
  min-height: 100vh;
  background-color: var(--app-bg);
}

/* 全出血模式：整页锁定视口高度，滚动交给页面内部 */
.layout.is-flush {
  height: 100vh;
  height: 100dvh;
  min-height: 0;
  overflow: hidden;
}

/* 右侧主区 */
.layout__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.layout.is-flush .layout__main {
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

/* 顶部栏：玻璃材质 + 平台名 + 右侧信息 */
.layout__topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 16px 32px;
  background-color: rgba(255, 255, 255, 0.72);
  -webkit-backdrop-filter: blur(24px) saturate(1.8);
  backdrop-filter: blur(24px) saturate(1.8);
  border-bottom: 1px solid var(--app-border);
}

.layout__topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

/* 移动端菜单按钮：桌面隐藏 */
.layout__navbtn {
  display: none;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  padding: 0;
  color: var(--app-text-1);
  background-color: transparent;
  border: 1px solid var(--app-border-strong);
  border-radius: 10px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}
.layout__navbtn:hover {
  background-color: var(--app-hover);
}

.layout__brand {
  min-width: 0;
  flex: 1;
}
.layout__brand-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--app-text-1);
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.layout__brand-subtitle {
  margin: 2px 0 0 0;
  font-size: 11px;
  color: var(--app-text-4);
  letter-spacing: 0.04em;
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.layout__topbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-shrink: 0;
}

.topbar-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--app-text-3);
  font-size: 13px;
  white-space: nowrap;
}
.topbar-info__text {
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.01em;
}
.topbar-info__text strong {
  color: var(--app-text-1);
  font-weight: 600;
  margin-left: 2px;
}

/* 用户头像 */
.topbar-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0071E3 0%, #5856D6 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 113, 227, 0.25);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  flex-shrink: 0;
}
.topbar-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 14px rgba(0, 113, 227, 0.35);
}

/* Mock 提示条 */
.layout__mockbar {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 32px;
  font-size: 13px;
  color: #8A5A00;
  background-color: rgba(255, 149, 0, 0.12);
  border-bottom: 1px solid rgba(255, 149, 0, 0.24);
}
.layout__mockbar :deep(.el-icon) {
  color: var(--app-color-orange);
  flex-shrink: 0;
}
.layout__mockbar-label {
  font-weight: 600;
  flex-shrink: 0;
  white-space: nowrap;
}
.layout__mockbar-modules {
  padding: 1px 8px;
  border-radius: var(--app-radius-tag);
  background-color: rgba(255, 149, 0, 0.18);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.layout__mockbar-hint {
  color: var(--app-text-4);
  font-size: 12px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 内容区 */
.layout__content {
  flex: 1;
  min-width: 0;
  padding: 24px 32px;
  box-sizing: border-box;
  overflow-x: hidden;
}
.layout.is-flush .layout__content {
  flex: 1 1 auto;
  min-height: 0;
  padding: 0;
  overflow: hidden;
}

/* ===== 移动端导航抽屉 ===== */
.layout__scrim {
  position: fixed;
  inset: 0;
  z-index: 55;
  background-color: rgba(0, 0, 0, 0.28);
  -webkit-backdrop-filter: blur(2px);
  backdrop-filter: blur(2px);
}
.layout__mobilenav {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  z-index: 60;
  width: 240px;
  max-width: 82vw;
  box-shadow: 8px 0 32px rgba(0, 0, 0, 0.16);
}
/* 抽屉里的 Sidebar 撑满抽屉，不再自己 sticky */
.layout__mobilenav :deep(.sidebar) {
  width: 100%;
  height: 100%;
  position: static;
  border-right: 0;
}

.fade-scrim-enter-active,
.fade-scrim-leave-active {
  transition: opacity 0.25s ease;
}
.fade-scrim-enter-from,
.fade-scrim-leave-to {
  opacity: 0;
}
.slide-nav-enter-active,
.slide-nav-leave-active {
  transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-nav-enter-from,
.slide-nav-leave-to {
  transform: translateX(-100%);
}

/* ===== 响应式 ===== */
@media (max-width: 1024px) {
  .layout__topbar {
    gap: 16px;
    padding: 14px 20px;
  }
  .layout__mockbar {
    padding: 9px 20px;
  }
  .layout__content {
    padding: 20px;
  }
  /* 这一段仍有 241px 桌面侧栏，顶栏很紧：先收起时间/在线设备数与英文副标题，
     否则平台标题会被省略号截到只剩一百多像素 */
  .layout__topbar-right .topbar-info {
    display: none;
  }
  .layout__brand-subtitle {
    display: none;
  }
}

@media (max-width: 767px) {
  /* 隐藏固定桌面侧栏，改用抽屉导航 */
  .layout > .sidebar {
    display: none;
  }
  .layout__navbtn {
    display: inline-flex;
  }
  .layout__topbar {
    gap: 10px;
    padding: 10px 14px;
  }
  .layout__brand-title {
    font-size: 14px;
    white-space: normal;
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  .layout__brand-subtitle {
    display: none;
  }
  .layout__topbar-right {
    gap: 10px;
  }
  /* 窄屏顶栏只保留头像，时间/在线设备数不再挤占标题空间 */
  .layout__topbar-right .topbar-info {
    display: none;
  }
  .layout__mockbar {
    padding: 8px 14px;
    font-size: 12px;
    gap: 6px;
  }
  .layout__mockbar-hint {
    display: none;
  }
  .layout__content {
    padding: 14px;
  }
}
</style>
