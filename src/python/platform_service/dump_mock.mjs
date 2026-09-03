// 将前端 Mock 数据导出为 JSON，供 Python 种子脚本消费（一次性工具）
import { writeFileSync } from 'fs'
import workorder from '../../../alarm-warning-frontend/src/mock/workorder.js'
import emergencyPlan from '../../../alarm-warning-frontend/src/mock/emergencyPlan.js'

writeFileSync('seed_workorder.json', JSON.stringify(workorder, null, 2))
writeFileSync('seed_emergency.json', JSON.stringify(emergencyPlan, null, 2))
console.log('OK: seed_workorder.json / seed_emergency.json')
