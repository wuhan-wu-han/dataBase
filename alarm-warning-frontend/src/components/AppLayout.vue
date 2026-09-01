<template>
  <div class="layout">
    <Sidebar :collapsed="collapsed" @toggle="toggleCollapsed" />
    <main class="layout__main">
      <!-- 顶部玻璃栏：平台名 + 英文副标题 + 右侧信息 -->
      <header class="layout__topbar">
        <div class="layout__brand">
          <h1 class="layout__brand-title">安塞区城市安全生命线管网AI智慧平台</h1>
          <p class="layout__brand-subtitle">AI-Powered Urban Lifeline Security Platform</p>
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
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Clock, Monitor } from '@element-plus/icons-vue'
import Sidebar from './Sidebar.vue'

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

/* 右侧主区 */
.layout__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

/* 顶部栏：玻璃材质 + 平台名 + 右侧信息 */
.layout__topbar {
  position: sticky;
  top: 0;
  z-index: 20;
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
}
.topbar-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 14px rgba(0, 113, 227, 0.35);
}

/* 内容区 */
.layout__content {
  flex: 1;
  padding: 24px 32px;
  box-sizing: border-box;
  overflow-x: hidden;
}
</style>
