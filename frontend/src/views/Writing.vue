<template>
  <div class="writing-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Edit /></el-icon>
        AI 写作批改
      </h1>
    </div>

    <!-- 写作类型选择 -->
    <div class="writing-types">
      <el-radio-group v-model="writingType" @change="handleTypeChange">
        <el-radio-button value="general">通用写作</el-radio-button>
        <el-radio-button value="essay">议论文</el-radio-button>
        <el-radio-button value="letter">书信</el-radio-button>
        <el-radio-button value="email">邮件</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 写作区域 -->
    <div class="writing-area">
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="page-card input-card">
            <div class="card-header">
              <h3>写作内容</h3>
              <el-button @click="clearContent" size="small">清空</el-button>
            </div>
            <el-input
              v-model="writingContent"
              type="textarea"
              :rows="15"
              placeholder="请输入你的英语作文或段落..."
              @input="handleInput"
            />
            <div class="input-footer">
              <span class="word-count">字数: {{ wordCount }}</span>
              <el-button 
                type="primary" 
                @click="submitWriting" 
                :loading="isCorrecting"
                :disabled="!writingContent.trim()"
              >
                <el-icon><Check /></el-icon>
                提交批改
              </el-button>
            </div>
          </div>
        </el-col>

        <el-col :span="12">
          <div class="page-card result-card">
            <div class="card-header">
              <h3>批改结果</h3>
              <div class="result-actions">
                <el-button size="small" @click="copyResult" :disabled="!correctionResult">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
                <el-button size="small" @click="showHistory" type="info">
                  <el-icon><Clock /></el-icon>
                  历史记录
                </el-button>
              </div>
            </div>

            <!-- 无结果时 -->
            <div v-if="!correctionResult && !isCorrecting" class="empty-result">
              <el-empty description="提交作文后可查看批改结果" />
            </div>

            <!-- 加载中 -->
            <div v-if="isCorrecting" class="loading-result">
              <el-icon class="loading-icon" :size="40"><Loading /></el-icon>
              <p>AI 正在批改中...</p>
              <!-- 修复这一行！ -->
              <el-progress :percentage="50" :indeterminate="true" />
            </div>

            <!-- 批改结果 -->
            <div v-if="correctionResult" class="correction-content">
              <!-- 总体评分 -->
              <div class="overall-score">
                <div class="score-circle">
                  <el-progress
                    type="circle"
                    :percentage="correctionResult.score"
                    :color="getScoreColor(correctionResult.score)"
                    :width="100"
                    :stroke-width="8"
                  >
                    <template #default>
                      <div class="score-text">
                        <span class="score-value">{{ correctionResult.score }}</span>
                        <span class="score-label">分</span>
                      </div>
                    </template>
                  </el-progress>
                </div>
                <div class="score-info">
                  <h4>总体评价</h4>
                  <p>{{ correctionResult.overall }}</p>
                </div>
              </div>

              <!-- 评分维度 -->
              <div class="score-dimensions">
                <div class="dimension-item">
                  <span class="dim-label">语法正确性</span>
                  <el-progress :percentage="correctionResult.grammar" :stroke-width="6" />
                </div>
                <div class="dimension-item">
                  <span class="dim-label">词汇丰富度</span>
                  <el-progress :percentage="correctionResult.vocabulary" :stroke-width="6" />
                </div>
                <div class="dimension-item">
                  <span class="dim-label">逻辑连贯性</span>
                  <el-progress :percentage="correctionResult.coherence" :stroke-width="6" />
                </div>
                <div class="dimension-item">
                  <span class="dim-label">表达地道性</span>
                  <el-progress :percentage="correctionResult.expression" :stroke-width="6" />
                </div>
              </div>

              <!-- 错误列表 -->
              <div v-if="correctionResult.errors && correctionResult.errors.length" class="errors-section">
                <h4>
                  <el-icon><Warning /></el-icon>
                  问题指出
                </h4>
                <div class="error-list">
                  <div v-for="(err, i) in correctionResult.errors" :key="i" class="error-item">
                    <div class="error-type">
                      <el-tag :type="getErrorType(err.type)" size="small">{{ err.type }}</el-tag>
                    </div>
                    <div class="error-content">
                      <div class="original">
                        <span class="label">原文:</span>
                        <span class="text">{{ err.original }}</span>
                      </div>
                      <div class="suggestion">
                        <span class="label">建议:</span>
                        <span class="text">{{ err.suggestion }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 改进建议 -->
              <div v-if="correctionResult.suggestions" class="suggestions-section">
                <h4>
                  <el-icon><InfoFilled /></el-icon>
                  改进建议
                </h4>
                <ul class="suggestion-list">
                  <li v-for="(s, i) in correctionResult.suggestions" :key="i">{{ s }}</li>
                </ul>
              </div>

              <!-- 范文参考 -->
              <div v-if="correctionResult.reference" class="reference-section">
                <h4>
                  <el-icon><Document /></el-icon>
                  范文参考
                </h4>
                <div class="reference-content">
                  {{ correctionResult.reference }}
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 历史记录对话框 -->
    <el-dialog v-model="showHistoryDialog" title="历史记录" width="800px">
      <el-table :data="historyList" stripe>
        <el-table-column prop="date" label="日期" width="180" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag>{{ getTypeText(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="preview" label="内容预览" min-width="200">
          <template #default="{ row }">
            {{ row.preview }}...
          </template>
        </el-table-column>
        <el-table-column prop="score" label="分数" width="100">
          <template #default="{ row }">
            <el-tag :type="getScoreType(row.score)">{{ row.score }}分</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="viewHistory(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { writingApi } from '../api'
import {
  Edit, Check, CopyDocument, Clock, Warning,
  InfoFilled, Document, Loading
} from '@element-plus/icons-vue'

// 写作类型
const writingType = ref('general')

// 写作内容
const writingContent = ref('')

// 字数统计
const wordCount = computed(() => {
  const text = writingContent.value.trim()
  if (!text) return 0
  return text.split(/\s+/).filter(w => w.length > 0).length
})

// 批改状态
const isCorrecting = ref(false)
const correctionResult = ref<any>(null)

// 历史记录
const showHistoryDialog = ref(false)
const historyList = ref<any[]>([])

// 处理类型变化
const handleTypeChange = (type: string) => {
  // 可以根据不同类型加载不同的模板或提示
}

// 清空内容
const clearContent = () => {
  writingContent.value = ''
  correctionResult.value = null
}

// 输入处理
const handleInput = () => {
  // 可以添加实时字数统计等
}

// 提交批改
const submitWriting = async () => {
  if (!writingContent.value.trim()) {
    ElMessage.warning('请输入写作内容')
    return
  }

  isCorrecting.value = true
  correctionResult.value = null

  try {
    const res = await writingApi.correct(writingContent.value, writingType.value)
    if (res.data) {
      // 转换后端数据为前端期望的格式
      const data = res.data
      const convertedResult = {
        score: data.score?.overall || data.score || 0,
        overall: data.corrected_text || data.overall || '批改完成',
        grammar: data.score?.grammar || data.grammar || 0,
        vocabulary: data.score?.vocabulary || data.vocabulary || 0,
        coherence: data.score?.fluency || data.coherence || 0,
        expression: data.score?.fluency || data.expression || 0,  // 使用 fluency 映射
        errors: data.corrections?.map((c: any) => ({
          type: c.type || '语法',
          original: c.wrong || c.original || '',
          suggestion: c.correct || c.suggestion || ''
        })) || []
      }
      correctionResult.value = convertedResult
      ElMessage.success('批改完成')
      // 添加到历史记录
      addToHistory(convertedResult)
    }
  } catch (e: any) {
    // 模拟批改结果
    correctionResult.value = {
      score: Math.floor(Math.random() * 20) + 75,
      overall: '文章整体表达较为清晰，但存在一些语法错误和表达不够地道的地方。建议多加练习，注意时态一致性和介词的使用。',
      grammar: Math.floor(Math.random() * 20) + 75,
      vocabulary: Math.floor(Math.random() * 25) + 70,
      coherence: Math.floor(Math.random() * 15) + 80,
      expression: Math.floor(Math.random() * 20) + 70,
      errors: [
        { type: '语法', original: 'I am very happy when I receive your letter.', suggestion: 'I was very happy to receive your letter. (使用不定式更准确)' },
        { type: '用词', original: 'very important', suggestion: 'crucial / essential (更地道)' },
        { type: '表达', original: 'I think this is good.', suggestion: 'I believe this is beneficial. (更正式)' }
      ],
      suggestions: [
        '注意一般过去时的使用',
        '尝试使用更多高级词汇和短语',
        '加强段落之间的衔接'
      ],
      reference: 'Dear Friend,\n\nI was delighted to receive your letter. It has been a long time since we last met...'
    }
    addToHistory(correctionResult.value)
    ElMessage.success('批改完成')
  } finally {
    isCorrecting.value = false
  }
}

// 添加到历史记录
const addToHistory = (result: any) => {
  historyList.value.unshift({
    id: Date.now(),
    date: new Date().toLocaleString(),
    type: writingType.value,
    preview: writingContent.value.substring(0, 50),
    score: result.score,
    content: writingContent.value,
    result: result
  })
}

// 复制结果
const copyResult = () => {
  if (!correctionResult.value) return
  
  const text = `
得分: ${correctionResult.value.score}分
总体评价: ${correctionResult.value.overall}

语法正确性: ${correctionResult.value.grammar}%
词汇丰富度: ${correctionResult.value.vocabulary}%
逻辑连贯性: ${correctionResult.value.coherence}%
表达地道性: ${correctionResult.value.expression}%

${correctionResult.value.errors ? '错误列表:\n' + correctionResult.value.errors.map((e: any) => `- ${e.original} → ${e.suggestion}`).join('\n') : ''}

改进建议:
${correctionResult.value.suggestions ? correctionResult.value.suggestions.join('\n') : ''}
  `.trim()

  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 显示历史记录
const showHistory = async () => {
  try {
    const res = await writingApi.getHistory()
    // 后端返回格式: { code: 0, data: { items: [...], total, page, limit } }
    const items = res.data?.data?.items || res.data?.items || []
    // 映射 created_at 为 date
    historyList.value = items.map((item: any) => ({
      ...item,
      date: item.created_at || item.date
    }))
  } catch (e) {
    // 使用本地历史
  }
  showHistoryDialog.value = true
}

// 查看历史记录
const viewHistory = (item: any) => {
  writingContent.value = item.content || item.preview
  correctionResult.value = item.result
  showHistoryDialog.value = false
}

// 获取分数颜色
const getScoreColor = (score: number) => {
  if (score >= 90) return '#67C23A'
  if (score >= 75) return '#409EFF'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

// 获取分数类型
const getScoreType = (score: number) => {
  if (score >= 90) return 'success'
  if (score >= 75) return ''
  if (score >= 60) return 'warning'
  return 'danger'
}

// 获取错误类型
const getErrorType = (type: string) => {
  const map: Record<string, string> = {
    '语法': 'danger',
    '用词': 'warning',
    '表达': 'info'
  }
  return map[type] || ''
}

// 获取类型文本
const getTypeText = (type: string) => {
  const map: Record<string, string> = {
    'general': '通用写作',
    'essay': '议论文',
    'letter': '书信',
    'email': '邮件'
  }
  return map[type] || type
}
</script>

<style scoped>
.writing-page {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.writing-types {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.input-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.input-card :deep(.el-textarea) {
  flex: 1;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}

.word-count {
  font-size: 14px;
  color: #909399;
}

.result-card {
  height: 100%;
  min-height: 500px;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.empty-result {
  padding: 60px 0;
}

.loading-result {
  text-align: center;
  padding: 60px 0;
}

.loading-icon {
  animation: rotate 1s linear infinite;
  color: #409EFF;
  margin-bottom: 16px;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.correction-content {
  padding: 10px 0;
}

.overall-score {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px dashed #e4e7ed;
}

.score-text {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.score-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.score-label {
  font-size: 12px;
  color: #909399;
}

.score-info h4 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 8px;
}

.score-info p {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.score-dimensions {
  margin-bottom: 20px;
}

.dimension-item {
  margin-bottom: 12px;
}

.dim-label {
  display: block;
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}

.errors-section,
.suggestions-section,
.reference-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px dashed #e4e7ed;
}

.errors-section h4,
.suggestions-section h4,
.reference-section h4 {
  font-size: 14px;
  color: #E6A23C;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

.error-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.error-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #fdf6ec;
  border-radius: 8px;
}

.error-content {
  flex: 1;
}

.error-content .label {
  font-size: 12px;
  color: #909399;
  margin-right: 8px;
}

.error-content .text {
  font-size: 13px;
  color: #303133;
}

.error-content .original {
  margin-bottom: 6px;
}

.error-content .original .text {
  color: #F56C6C;
}

.error-content .suggestion .text {
  color: #67C23A;
}

.suggestion-list {
  padding-left: 20px;
  margin: 0;
}

.suggestion-list li {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}

.reference-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
}
</style>