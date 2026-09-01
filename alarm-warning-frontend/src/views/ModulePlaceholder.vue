<template>
  <div class="placeholder">
    <!-- Apple 风格：玻璃大圆角卡片 + 副标题 + 三步蓝图 -->
    <div class="app-card placeholder__card">
      <div class="placeholder__icon">
        <el-icon :size="56"><DataAnalysis /></el-icon>
      </div>
      <div class="placeholder__label">Module</div>
      <h2 class="placeholder__title">{{ moduleName }}</h2>
      <p class="placeholder__desc">该模块正在规划中，敬请期待。</p>
      <p class="placeholder__sub">This module is under planning. Stay tuned.</p>
      <el-button class="placeholder__btn" @click="goHome">返回首页</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataAnalysis } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 模块名优先取路由 meta.moduleName，缺省回退到 title
const moduleName = computed(() => route.meta?.moduleName || route.meta?.title || '模块')

function goHome() {
  router.push('/')
}
</script>

<style scoped>
.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 160px); /* 减去顶部栏 + 内边距 */
  padding: 24px;
}
.placeholder__card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 56px 64px;
  max-width: 560px;
  width: 100%;
  text-align: center;
}
.placeholder__icon {
  width: 96px;
  height: 96px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 24px;
  background: var(--app-primary-soft);
  color: var(--app-primary);
  margin-bottom: 8px;
}
.placeholder__label {
  font-size: 11px;
  color: var(--app-text-4);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 600;
}
.placeholder__title {
  margin: 4px 0 0 0;
  font-size: 28px;
  font-weight: 600;
  color: var(--app-text-1);
  letter-spacing: -0.02em;
}
.placeholder__desc {
  margin: 8px 0 0 0;
  font-size: 15px;
  color: var(--app-text-3);
}
.placeholder__sub {
  margin: 2px 0 0 0;
  font-size: 12px;
  color: var(--app-text-4);
  letter-spacing: 0.01em;
}
.placeholder__btn {
  margin-top: 20px;
  border-radius: 980px;
  height: 36px;
  padding: 0 22px;
  background-color: var(--app-primary);
  color: #fff;
  border: none;
  font-weight: 500;
}
.placeholder__btn:hover {
  background-color: var(--app-primary-hover);
}
</style>
