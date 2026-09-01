<template>
  <router-view />
</template>

<script setup>
// 根组件，提供全局背景
</script>

<style>
/* 全局基础样式 - 深蓝黑渐变 + 网格纹理 */
html, body, #app {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  background:
    /* 网格纹理 */
    linear-gradient(rgba(24, 144, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(24, 144, 255, 0.03) 1px, transparent 1px),
    /* 深蓝黑渐变 */
    radial-gradient(ellipse at 20% 50%, #0a1628 0%, #060d18 100%);
  background-size: 50px 50px, 50px 50px, 100% 100%;
  color: #e0e6ed;
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  overflow-x: hidden;
}

/* 全局滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: rgba(13, 27, 42, 0.5);
}
::-webkit-scrollbar-thumb {
  background: rgba(24, 144, 255, 0.3);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(24, 144, 255, 0.5);
}
</style>
