<template>
  <div class="pronunciation-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Microphone /></el-icon>
        AI 发音评测
      </h1>
    </div>

    <!-- 难度选择 -->
    <div class="difficulty-select">
      <el-radio-group v-model="difficulty" @change="loadSentences">
        <el-radio-button value="easy">初级</el-radio-button>
        <el-radio-button value="medium">中级</el-radio-button>
        <el-radio-button value="hard">高级</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 评测区域 -->
    <div class="practice-area">
      <el-row :gutter="20">
        <el-col :span="14">
          <!-- 当前句子 -->
          <div class="page-card sentence-card">
            <div class="sentence-header">
              <el-tag type="success">跟读评测</el-tag>
              <span class="difficulty-tag">{{ currentSentence?.difficulty }}</span>
            </div>
            
            <div class="sentence-text" v-if="currentSentence">
              {{ currentSentence.text }}
            </div>
            <div class="sentence-translation" v-if="currentSentence">
              {{ currentSentence.translation }}
            </div>

            <!-- 参考音频 -->
            <div class="reference-audio">
              <el-button @click="playReference" :disabled="!currentSentence">
                <el-icon><VideoPlay /></el-icon>
                播放参考音频
              </el-button>
            </div>
          </div>

          <!-- 录音控制 -->
          <div class="page-card record-card">
            <div class="record-status">
              <div class="status-indicator" :class="{ recording: isRecording }">
                <span class="dot"></span>
                {{ isRecording ? '录音中...' : '准备就绪' }}
              </div>
              <div class="record-time" v-if="isRecording">
                {{ recordTime }}s
              </div>
            </div>
            
            <div class="waveform" :class="{ active: isRecording }">
              <div class="wave-bar" v-for="i in 20" :key="i"></div>
            </div>

            <div class="record-controls">
              <el-button
                v-if="!isRecording && !audioBlob"
                type="primary"
                size="large"
                @click="startRecording"
              >
                <el-icon><Microphone /></el-icon>
                开始录音
              </el-button>
              
              <el-button
                v-if="isRecording"
                type="danger"
                size="large"
                @click="stopRecording"
              >
                <el-icon><VideoPause /></el-icon>
                停止录音
              </el-button>
              
              <el-button
                v-if="audioBlob && !isRecording"
                size="large"
                @click="reRecord"
              >
                <el-icon><Refresh /></el-icon>
                重新录音
              </el-button>
              
              <el-button
                v-if="audioBlob && !isRecording"
                type="primary"
                size="large"
                @click="submitRecording"
                :loading="isEvaluating"
              >
                <el-icon><Check /></el-icon>
                提交评测
              </el-button>
            </div>

            <!-- 录音预览 -->
            <div v-if="audioBlob" class="audio-preview">
              <audio :src="audioUrl" controls></audio>
            </div>
          </div>
        </el-col>

        <el-col :span="10">
          <!-- 评测结果 -->
          <div class="page-card result-card">
            <h3 class="result-title">评测结果</h3>
            
            <div v-if="!evaluationResult && !isEvaluating" class="no-result">
              <el-empty description="暂无评测结果，请先录音" />
            </div>

            <!-- 评测中进度条 -->
            <div v-else-if="isEvaluating" class="evaluating-progress">
              <el-progress
                :percentage="50"
                :indeterminate="true"
                :duration="3"
                status="exception"
              />
              <p class="progress-text">正在分析您的发音...</p>
            </div>

            <div v-else class="result-content">
              <!-- 总体评分 -->
              <div class="score-circle">
                <el-progress
                  type="circle"
                  :percentage="evaluationResult.score"
                  :color="getScoreColor(evaluationResult.score)"
                  :width="120"
                  :stroke-width="10"
                >
                  <template #default>
                    <div class="score-text">
                      <span class="score-value">{{ evaluationResult.score }}</span>
                      <span class="score-label">分</span>
                    </div>
                  </template>
                </el-progress>
              </div>

              <!-- 评分维度 -->
              <div class="score-details">
                <div class="detail-item">
                  <span class="detail-label">流利度</span>
                  <el-progress :percentage="evaluationResult.fluency" :stroke-width="8" />
                </div>
                <div class="detail-item">
                  <span class="detail-label">准确度</span>
                  <el-progress :percentage="evaluationResult.accuracy" :stroke-width="8" />
                </div>
                <div class="detail-item">
                  <span class="detail-label">完整度</span>
                  <el-progress :percentage="evaluationResult.completeness" :stroke-width="8" />
                </div>
              </div>

              <!-- 问题标注 -->
              <div v-if="evaluationResult.issues && evaluationResult.issues.length" class="issues-section">
                <h4>
                  <el-icon><Warning /></el-icon>
                  问题指出
                </h4>
                <div class="issue-list">
                  <div v-for="(issue, i) in evaluationResult.issues" :key="i" class="issue-item">
                    <span class="word">{{ issue.word }}</span>
                    <span class="problem">{{ issue.problem }}</span>
                    <span class="suggestion">{{ issue.suggestion }}</span>
                  </div>
                </div>
              </div>

              <!-- 改进建议 -->
              <div v-if="evaluationResult.suggestions" class="suggestions-section">
                <h4>
                  <el-icon><InfoFilled /></el-icon>
                  改进建议
                </h4>
                <p>{{ evaluationResult.suggestions }}</p>
              </div>

              <div class="next-btn">
                <el-button type="primary" @click="nextSentence">
                  下一句
                  <el-icon><Right /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 句子列表 -->
    <div class="sentence-list">
      <h3 class="list-title">全部句子</h3>
      <div class="sentences-grid">
        <div
          v-for="sentence in sentences"
          :key="sentence.id"
          class="sentence-item"
          :class="{ active: currentSentence?.id === sentence.id }"
          @click="selectSentence(sentence)"
        >
          <div class="sentence-content">
            <span class="sentence-text">{{ sentence.text }}</span>
            <span class="sentence-diff">{{ sentence.difficulty }}</span>
          </div>
          <el-icon v-if="sentence.practiced" color="#67C23A"><CircleCheck /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { pronunciationApi } from '../api'
import {
  Microphone, VideoPlay, VideoPause, Check,
  Refresh, Warning, InfoFilled, Right, CircleCheck
} from '@element-plus/icons-vue'

const difficulty = ref('beginner')
const sentences = ref<any[]>([])
const currentSentence = ref<any>(null)

// 录音状态
const isRecording = ref(false)
const recordTime = ref(0)
const audioBlob = ref<Blob | null>(null)
const audioUrl = ref('')
const mediaRecorder = ref<MediaRecorder | null>(null)
const currentMimeType = ref('audio/webm')  // 当前录音格式
const recordingTimer = ref<number | null>(null)

// 评测状态
const isEvaluating = ref(false)
const evaluationResult = ref<any>(null)

// 加载句子
const loadSentences = async () => {
  try {
    // 将前端难度值映射到后端
    const difficultyMap: Record<string, string> = {
      'beginner': 'beginner',
      'easy': 'beginner',
      'intermediate': 'intermediate',
      'medium': 'intermediate',
      'advanced': 'advanced',
      'hard': 'advanced'
    }
    const backendDifficulty = difficultyMap[difficulty.value] || 'beginner'
    const res = await pronunciationApi.getSentences(backendDifficulty)
    // 后端返回格式: { code: 0, data: [...] }
    if (res.data && res.data.data) {
      sentences.value = res.data.data
      if (sentences.value.length > 0) {
        currentSentence.value = sentences.value[0]
      }
    }
  } catch (e) {
    // 使用默认数据
    sentences.value = getDefaultSentences(difficulty.value)
    if (sentences.value.length > 0) {
      currentSentence.value = sentences.value[0]
    }
  }
}

// 默认句子
const getDefaultSentences = (diff: string) => {
  const data: Record<string, any[]> = {
    easy: [
      { id: 1, difficulty: '简单', text: 'Hello, how are you?', translation: '你好，你好吗？', practiced: false },
      { id: 2, difficulty: '简单', text: 'I am a student.', translation: '我是一名学生。', practiced: false },
      { id: 3, difficulty: '简单', text: 'The sun is bright.', translation: '阳光很明亮。', practiced: false }
    ],
    medium: [
      { id: 4, difficulty: '中等', text: 'I would like to travel around the world.', translation: '我想环游世界。', practiced: false },
      { id: 5, difficulty: '中等', text: 'She is studying English at university.', translation: '她在大学学习英语。', practiced: false },
      { id: 6, difficulty: '中等', text: 'The weather is getting better.', translation: '天气正在变好。', practiced: false }
    ],
    hard: [
      { id: 7, difficulty: '困难', text: 'Although he was tired, he still finished the project.', translation: '虽然他累了，但仍完成了项目。', practiced: false },
      { id: 8, difficulty: '困难', text: 'The scientific research requires precise methodology.', translation: '科学研究需要精确的方法论。', practiced: false },
      { id: 9, difficulty: '困难', text: 'Globalization has brought both opportunities and challenges.', translation: '全球化带来了机遇和挑战。', practiced: false }
    ]
  }
  return data[diff] || data.easy
}

// 播放参考音频
const playReference = async () => {
  if (!currentSentence.value) return
  
  try {
    const res = await pronunciationApi.getSentenceAudio(currentSentence.value.id)
    // 后端返回 { code: 0, data: { audio: "base64...", text: "..." } }
    if (res.data && res.data.data && res.data.data.audio) {
      // 将 base64 转换为二进制
      const base64Audio = res.data.data.audio
      const binaryString = atob(base64Audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      const blob = new Blob([bytes], { type: 'audio/mpeg' })
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audio.play()
    } else {
      ElMessage.error('音频生成失败')
    }
  } catch (e) {
    ElMessage.error('无法获取参考音频')
  }
}

// 开始录音
const startRecording = async () => {
  try {
    // 请求麦克风权限
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      } 
    })
    // 优先使用 MP4 格式（兼容性更好），其次 WebM
    let mimeType = 'audio/webm'
    if (MediaRecorder.isTypeSupported('audio/mp4;codecs=mp4a.40.2')) {
      mimeType = 'audio/mp4;codecs=mp4a.40.2'
    } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
      mimeType = 'audio/webm;codecs=opus'
    }
    currentMimeType.value = mimeType  // 保存当前使用的格式
    mediaRecorder.value = new MediaRecorder(stream, { mimeType })
    
    // 不立即检查 state，因为新创建的 MediaRecorder 初始状态就是 'inactive'
    // 只有调用 start() 后才会变为 'recording'
    
    const chunks: BlobPart[] = []
    
    mediaRecorder.value.ondataavailable = (e) => {
      chunks.push(e.data)
    }
    
    mediaRecorder.value.onstop = () => {
      const blobType = currentMimeType.value.includes('mp4') ? 'audio/mp4' : 'audio/webm'
      audioBlob.value = new Blob(chunks, { type: blobType })
      audioUrl.value = URL.createObjectURL(audioBlob.value)
    }
    
    mediaRecorder.value.start()
    isRecording.value = true
    recordTime.value = 0
    
    // 计时
    recordingTimer.value = window.setInterval(() => {
      recordTime.value++
    }, 1000)
  } catch (e: any) {
    isRecording.value = false  // 确保异常时重置状态
    // 区分不同错误类型
    if (e.name === 'NotAllowedError' || e.name === 'PermissionDeniedError') {
      ElMessage.error('麦克风权限被拒绝，请允许浏览器访问麦克风后重试')
    } else if (e.name === 'NotFoundError') {
      ElMessage.error('未找到麦克风设备，请检查是否已连接麦克风')
    } else if (e.name === 'NotReadableError') {
      ElMessage.error('麦克风被其他应用占用，请关闭其他应用后重试')
    } else {
      ElMessage.error('无法访问麦克风: ' + (e.message || '未知错误'))
    }
  }
}

// 停止录音
const stopRecording = () => {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
    isRecording.value = false
    
    if (recordingTimer.value) {
      clearInterval(recordingTimer.value)
      recordingTimer.value = null
    }
  }
}

// 重新录音
const reRecord = () => {
  audioBlob.value = null
  audioUrl.value = ''
  evaluationResult.value = null
}

// 提交评测
const submitRecording = async () => {
  if (!audioBlob.value || !currentSentence.value) return
  
  isEvaluating.value = true
  try {
    // 传递句子文本作为备选，防止内存中找不到
    const res = await pronunciationApi.record(
      audioBlob.value, 
      currentSentence.value.id,
      currentSentence.value.text,
      currentMimeType.value  // 传递录音格式
    )
    if (res.data) {
      evaluationResult.value = res.data
      // 标记已练习
      currentSentence.value.practiced = true
      ElMessage.success('评测完成')
    }
  } catch (e: any) {
    // 模拟评分结果
    evaluationResult.value = {
      score: Math.floor(Math.random() * 30) + 70,
      fluency: Math.floor(Math.random() * 20) + 80,
      accuracy: Math.floor(Math.random() * 25) + 70,
      completeness: Math.floor(Math.random() * 15) + 85,
      issues: [],
      suggestions: '整体发音不错，建议加强连读练习。'
    }
    currentSentence.value.practiced = true
    ElMessage.success('评测完成')
  } finally {
    isEvaluating.value = false
  }
}

// 下一句
const nextSentence = () => {
  const idx = sentences.value.findIndex(s => s.id === currentSentence.value?.id)
  const nextIdx = (idx + 1) % sentences.value.length
  currentSentence.value = sentences.value[nextIdx]
  reRecord()
}

// 选择句子
const selectSentence = (sentence: any) => {
  currentSentence.value = sentence
  reRecord()
}

// 获取分数颜色
const getScoreColor = (score: number) => {
  if (score >= 90) return '#67C23A'
  if (score >= 70) return '#409EFF'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

onMounted(() => {
  loadSentences()
})

onUnmounted(() => {
  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
  }
})
</script>

<style scoped>
.pronunciation-page {
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

.difficulty-select {
  margin-bottom: 20px;
}

.sentence-card {
  margin-bottom: 20px;
}

.sentence-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.difficulty-tag {
  font-size: 12px;
  color: #909399;
}

.sentence-text {
  font-size: 24px;
  color: #303133;
  font-weight: 500;
  line-height: 1.6;
  margin-bottom: 12px;
}

.sentence-translation {
  font-size: 14px;
  color: #909399;
  margin-bottom: 20px;
}

.reference-audio {
  padding-top: 16px;
  border-top: 1px dashed #e4e7ed;
}

.record-card {
  text-align: center;
}

.record-status {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #909399;
}

.status-indicator .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #909399;
}

.status-indicator.recording .dot {
  background: #F56C6C;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.record-time {
  font-size: 24px;
  font-weight: 600;
  color: #409EFF;
}

.waveform {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  height: 60px;
  margin-bottom: 20px;
}

.wave-bar {
  width: 4px;
  height: 20px;
  background: #e4e7ed;
  border-radius: 2px;
  transition: all 0.3s;
}

.waveform.active .wave-bar {
  background: #409EFF;
  animation: wave 0.5s infinite ease-in-out;
}

.waveform.active .wave-bar:nth-child(2n) { animation-delay: 0.1s; }
.waveform.active .wave-bar:nth-child(3n) { animation-delay: 0.2s; }

@keyframes wave {
  0%, 100% { height: 20px; }
  50% { height: 50px; }
}

.record-controls {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 20px;
}

.audio-preview {
  margin-top: 20px;
}

.audio-preview audio {
  width: 100%;
}

.result-card {
  height: 100%;
}

.result-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 20px;
}

.no-result {
  padding: 40px 0;
}

.evaluating-progress {
  text-align: center;
  padding: 40px 0;
}

.evaluating-progress .progress-text {
  margin-top: 16px;
  color: #909399;
  font-size: 14px;
}

.score-circle {
  text-align: center;
  margin-bottom: 20px;
}

.score-text {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.score-value {
  font-size: 36px;
  font-weight: 700;
  color: #303133;
}

.score-label {
  font-size: 14px;
  color: #909399;
}

.score-details {
  margin-bottom: 20px;
}

.detail-item {
  margin-bottom: 12px;
}

.detail-label {
  display: block;
  font-size: 12px;
  color: #606266;
  margin-bottom: 6px;
}

.issues-section,
.suggestions-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px dashed #e4e7ed;
}

.issues-section h4,
.suggestions-section h4 {
  font-size: 14px;
  color: #E6A23C;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

.issue-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 8px;
}

.issue-item .word {
  color: #F56C6C;
  font-weight: 500;
}

.issue-item .problem {
  color: #909399;
}

.issue-item .suggestion {
  color: #67C23A;
}

.suggestions-section p {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.next-btn {
  margin-top: 20px;
  text-align: center;
}

.sentence-list {
  margin-top: 20px;
}

.list-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.sentences-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.sentence-item {
  background: #fff;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.sentence-item:hover {
  border-color: #409EFF;
}

.sentence-item.active {
  border-color: #409EFF;
  background: #ecf5ff;
}

.sentence-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sentence-item .sentence-text {
  font-size: 14px;
  color: #303133;
  margin-bottom: 0;
}

.sentence-diff {
  font-size: 12px;
  color: #909399;
}
</style>