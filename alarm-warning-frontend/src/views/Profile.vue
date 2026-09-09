<template>
  <section class="profile-page">
    <div class="profile-head">
      <div><h2>个人中心</h2><p>维护联系方式和告警通知偏好</p></div>
      <el-tag type="success" effect="plain">{{ authState.user?.displayName }}</el-tag>
    </div>

    <div class="profile-grid" v-loading="loading">
      <el-card shadow="never">
        <template #header><strong>联系方式</strong></template>
        <el-form label-position="top" @submit.prevent>
          <el-form-item label="登录账号"><el-input :model-value="authState.user?.username" disabled /></el-form-item>
          <el-form-item label="电子邮箱">
            <el-input v-model.trim="contact.email" placeholder="name@example.com" clearable />
          </el-form-item>
          <el-form-item label="手机号码">
            <el-input v-model.trim="contact.phone" maxlength="11" placeholder="请输入 11 位手机号" clearable />
          </el-form-item>
          <el-form-item label="负责部门/区域">
            <el-input v-model.trim="contact.departmentId" placeholder="可选，用于区域通知" clearable />
          </el-form-item>
          <el-button type="primary" :loading="contactSaving" @click="saveContact">保存联系方式</el-button>
        </el-form>
      </el-card>

      <el-card shadow="never">
        <template #header><strong>通知偏好</strong></template>
        <div class="preference-row">
          <div><b>邮件通知</b><span>告警达到指定等级时发送邮件</span></div>
          <el-switch v-model="preference.emailEnabled" />
        </div>
        <div class="preference-row">
          <div><b>短信通知</b><span>通过绑定手机号接收告警短信</span></div>
          <el-switch v-model="preference.smsEnabled" />
        </div>
        <div class="preference-field">
          <label>最低通知等级</label>
          <el-select v-model="preference.minAlertLevel" style="width: 100%">
            <el-option label="低风险（蓝色）" value="BLUE" />
            <el-option label="中风险（黄色）" value="YELLOW" />
            <el-option label="较高风险（橙色）" value="ORANGE" />
            <el-option label="高风险（红色）" value="RED" />
          </el-select>
        </div>
        <div class="preference-row">
          <div><b>仅负责区域</b><span>只接收与负责部门或区域匹配的告警</span></div>
          <el-switch v-model="preference.areaOnly" />
        </div>
        <el-button type="primary" :loading="preferenceSaving" @click="savePreference">保存通知偏好</el-button>
      </el-card>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { authState, setCurrentUser } from '@/stores/auth'
import {
  getCurrentUser,
  getNotificationPreference,
  updateMyContact,
  updateNotificationPreference
} from '@/api/auth'

const loading = ref(false)
const contactSaving = ref(false)
const preferenceSaving = ref(false)
const contact = reactive({ email: '', phone: '', departmentId: '' })
const preference = reactive({ emailEnabled: true, smsEnabled: false, minAlertLevel: 'ORANGE', areaOnly: false })

async function load() {
  loading.value = true
  try {
    const token = sessionStorage.getItem('rbac_access_token')
    const [user, settings] = await Promise.all([getCurrentUser(token), getNotificationPreference()])
    setCurrentUser(user)
    Object.assign(contact, { email: user.email || '', phone: user.phone || '', departmentId: user.departmentId || '' })
    Object.assign(preference, settings)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '个人信息加载失败')
  } finally {
    loading.value = false
  }
}

async function saveContact() {
  contactSaving.value = true
  try {
    const user = await updateMyContact(contact)
    setCurrentUser(user)
    ElMessage.success('联系方式已保存')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '联系方式保存失败')
  } finally {
    contactSaving.value = false
  }
}

async function savePreference() {
  preferenceSaving.value = true
  try {
    await updateNotificationPreference(preference)
    ElMessage.success('通知偏好已保存')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '通知偏好保存失败')
  } finally {
    preferenceSaving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.profile-page { display: flex; flex-direction: column; gap: 20px; }
.profile-head { display: flex; align-items: center; justify-content: space-between; }
.profile-head h2 { margin: 0; color: var(--app-text-1); }
.profile-head p { margin: 7px 0 0; color: var(--app-text-3); }
.profile-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }
:deep(.el-card) { border: 0; border-radius: var(--app-radius-card); box-shadow: var(--app-shadow-card); }
.preference-row { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 15px 0; border-bottom: 1px solid var(--app-border); }
.preference-row div { display: flex; flex-direction: column; gap: 5px; }
.preference-row b, .preference-field label { color: var(--app-text-1); font-size: 14px; }
.preference-row span { color: var(--app-text-3); font-size: 12px; }
.preference-field { display: flex; flex-direction: column; gap: 9px; padding: 16px 0; }
@media (max-width: 900px) { .profile-grid { grid-template-columns: 1fr; } }
</style>
