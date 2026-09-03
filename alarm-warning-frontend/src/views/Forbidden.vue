<template>
  <main class="forbidden">
    <el-result icon="warning" title="无权访问" sub-title="当前账号没有访问该功能的权限">
      <template #extra><el-button type="primary" @click="$router.push('/')">返回首页</el-button></template>
    </el-result>
  </main>
</template>

<style scoped>
.forbidden { min-height: 100vh; display: grid; place-items: center; background: var(--app-bg); }
</style>

