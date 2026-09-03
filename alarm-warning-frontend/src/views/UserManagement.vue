<template>
  <section class="users-page">
    <div class="page-head"><div><h2>用户管理</h2><p>管理平台账号、状态和 RBAC 角色</p></div><el-button type="primary" @click="openCreate">新增用户</el-button></div>
    <el-card shadow="never">
      <el-table v-loading="loading" :data="users">
        <el-table-column prop="username" label="用户名" min-width="130" />
        <el-table-column prop="displayName" label="姓名" min-width="130" />
        <el-table-column label="角色" min-width="150"><template #default="{ row }"><el-tag v-for="r in row.roles" :key="r">{{ roleName(r) }}</el-tag></template></el-table-column>
        <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '启用' : '停用' }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="230" fixed="right"><template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="warning" @click="openReset(row)">重置密码</el-button>
        </template></el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="editorVisible" :title="editing ? '编辑用户' : '新增用户'" width="460px">
      <el-form label-position="top">
        <el-form-item label="用户名"><el-input v-model.trim="form.username" :disabled="editing" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model.trim="form.displayName" /></el-form-item>
        <el-form-item v-if="!editing" label="初始密码"><el-input v-model="form.password" type="password" show-password /></el-form-item>
        <el-form-item label="角色"><el-select v-model="form.roles" multiple style="width:100%"><el-option v-for="r in roles" :key="r.code" :label="r.name" :value="r.code" /></el-select></el-form-item>
        <el-form-item v-if="editing" label="账号状态"><el-switch v-model="form.enabled" active-text="启用" inactive-text="停用" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="editorVisible=false">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="resetVisible" title="重置密码" width="420px">
      <p>正在重置账号 <strong>{{ selected?.username }}</strong> 的密码</p>
      <el-input v-model="newPassword" type="password" show-password placeholder="至少 8 位，包含字母和数字" />
      <template #footer><el-button @click="resetVisible=false">取消</el-button><el-button type="primary" :loading="saving" @click="resetPassword">确认重置</el-button></template>
    </el-dialog>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createUser, getRoles, getUsers, resetUserPassword, updateUser } from '@/api/auth'
const users=ref([]), roles=ref([]), loading=ref(false), saving=ref(false), editorVisible=ref(false), resetVisible=ref(false), editing=ref(false), selected=ref(null), newPassword=ref('')
const form=reactive({ username:'', displayName:'', password:'', roles:['viewer'], enabled:true })
const roleName=(code)=>roles.value.find(r=>r.code===code)?.name||code
async function load(){ loading.value=true; try{ [users.value,roles.value]=await Promise.all([getUsers(),getRoles()]) }catch(e){ ElMessage.error(e.response?.data?.detail||'加载失败') }finally{ loading.value=false } }
function openCreate(){ editing.value=false; Object.assign(form,{username:'',displayName:'',password:'',roles:['viewer'],enabled:true}); editorVisible.value=true }
function openEdit(row){ editing.value=true; selected.value=row; Object.assign(form,{username:row.username,displayName:row.displayName,password:'',roles:[...row.roles],enabled:row.enabled}); editorVisible.value=true }
async function save(){ if(!form.username||!form.displayName||!form.roles.length||(!editing.value&&!form.password)) return ElMessage.warning('请完整填写用户信息'); saving.value=true; try{ if(editing.value) await updateUser(selected.value.id,{displayName:form.displayName,roles:form.roles,enabled:form.enabled}); else await createUser({username:form.username,displayName:form.displayName,password:form.password,roles:form.roles}); ElMessage.success('保存成功'); editorVisible.value=false; await load() }catch(e){ ElMessage.error(e.response?.data?.detail||'保存失败') }finally{ saving.value=false } }
function openReset(row){ selected.value=row; newPassword.value=''; resetVisible.value=true }
async function resetPassword(){ if(!newPassword.value) return; saving.value=true; try{ await resetUserPassword(selected.value.id,newPassword.value); ElMessage.success('密码已重置'); resetVisible.value=false }catch(e){ ElMessage.error(e.response?.data?.detail||'重置失败') }finally{ saving.value=false } }
onMounted(load)
</script>

<style scoped>
.users-page{display:flex;flex-direction:column;gap:20px}.page-head{display:flex;align-items:center;justify-content:space-between}.page-head h2{margin:0;color:var(--app-text-1)}.page-head p{margin:7px 0 0;color:var(--app-text-3)}.el-tag+.el-tag{margin-left:6px}:deep(.el-card){border:0;border-radius:var(--app-radius-card);box-shadow:var(--app-shadow-card)}
</style>
