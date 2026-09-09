<template>
  <el-dialog :model-value="modelValue" title="发送告警通知" width="580px" @update:model-value="$emit('update:modelValue', $event)">
    <el-form label-position="top" v-loading="loading">
      <el-form-item label="接收人员" required>
        <el-select v-model="form.userIds" multiple filterable placeholder="请选择已绑定联系方式的用户" style="width: 100%">
          <el-option v-for="user in recipients" :key="user.id" :value="user.id" :label="recipientLabel(user)" />
        </el-select>
      </el-form-item>
      <el-form-item label="通知通道" required>
        <el-checkbox-group v-model="form.channels">
          <el-checkbox value="EMAIL">邮件</el-checkbox>
          <el-checkbox value="SMS">短信</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
      <el-form-item label="通知标题" required><el-input v-model.trim="form.subject" maxlength="200" /></el-form-item>
      <el-form-item label="通知内容" required><el-input v-model="form.content" type="textarea" :rows="10" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="sending" @click="submit">发送通知</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getNotificationRecipients, sendNotification } from '@/api/notification'
import { formatDateTime } from '@/utils/format'

const props = defineProps({ modelValue: Boolean, alert: { type: Object, default: null } })
const emit = defineEmits(['update:modelValue', 'sent'])
const recipients = ref([])
const loading = ref(false)
const sending = ref(false)
const form = reactive({ userIds: [], channels: ['EMAIL'], subject: '', content: '' })

function levelName(level) {
  return { RED: '高风险', ORANGE: '较高风险', YELLOW: '中风险', BLUE: '低风险' }[level] || level || '告警'
}

function buildContent(alert) {
  return [
    `告警编号：${alert.alertEventCode || alert.id || '-'}`,
    `风险等级：${levelName(alert.alertLevel)}`,
    `设备编号：${alert.deviceId || '-'}`,
    `设备类型：${alert.deviceType || '-'}`,
    `所属区域：${alert.areaId || alert.zone || '-'}`,
    `监测指标：${alert.metricKey || '-'}`,
    `当前值：${alert.metricValue ?? '-'}`,
    `阈值：${alert.thresholdValue ?? '-'}`,
    `发生时间：${formatDateTime(alert.eventTimestamp)}`,
    `当前状态：${alert.alertStatus || '-'}`
  ].join('\n')
}

function recipientLabel(user) {
  const contacts = [user.email, user.phone].filter(Boolean).join(' / ')
  return `${user.displayName}（${contacts || '未绑定联系方式'}）`
}

async function prepare() {
  if (!props.alert) return
  form.userIds = []
  form.channels = ['EMAIL']
  form.subject = `【城市生命线平台】【${levelName(props.alert.alertLevel)}】${props.alert.rootCauseDesc || props.alert.metricKey || '设备告警'}`
  form.content = buildContent(props.alert)
  loading.value = true
  try {
    recipients.value = await getNotificationRecipients()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '接收人员加载失败')
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!form.userIds.length || !form.channels.length || !form.subject || !form.content.trim()) {
    ElMessage.warning('请选择接收人员和通知通道，并填写通知内容')
    return
  }
  sending.value = true
  try {
    const result = await sendNotification({
      alertId: String(props.alert.alertEventCode || props.alert.id),
      userIds: form.userIds,
      channels: form.channels,
      subject: form.subject,
      content: form.content,
      alertLevel: props.alert.alertLevel,
      businessType: props.alert.deviceType,
      areaId: props.alert.areaId
    })
    const success = result.items?.filter((item) => item.status === 'SUCCESS').length || 0
    const failed = result.items?.filter((item) => item.status === 'FAILED').length || 0
    ElMessage.success(`已创建 ${result.created} 条通知，成功 ${success} 条${failed ? `，失败 ${failed} 条` : ''}`)
    emit('sent', result)
    emit('update:modelValue', false)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '通知发送失败')
  } finally {
    sending.value = false
  }
}

watch(() => props.modelValue, (open) => { if (open) prepare() })
</script>
