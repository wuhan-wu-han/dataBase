<template>
  <!-- 统一页头：左侧标题/副标题，右侧操作区（slot） -->
  <header class="page-header">
    <div class="page-header__left">
      <h1 class="page-title">{{ title }}</h1>
      <p v-if="subtitle" class="page-header__subtitle">{{ subtitle }}</p>
    </div>
    <div class="page-header__right">
      <slot />
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' }
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 20px;
}
.page-header__left {
  min-width: 0;
}
.page-header__subtitle {
  margin: 6px 0 0 0;
  font-size: 13px;
  color: var(--app-text-3);
}
.page-header__right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
</style>
