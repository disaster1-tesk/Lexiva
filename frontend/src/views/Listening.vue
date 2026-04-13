<template>
  <div class="listening-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Headset /></el-icon>
        听力训练
      </h1>
    </div>

    <!-- 听力模式选择 -->
    <el-tabs v-model="activeTab" class="mode-tabs">
      <el-tab-pane label="自由听力" name="free">
        <template #label>
          <span class="tab-label">
            <el-icon><VideoPlay /></el-icon>
            自由听力
          </span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="听写模式" name="dictation">
        <template #label>
          <span class="tab-label">
            <el-icon><EditPen /></el-icon>
            听写模式
          </span>
        </template>
      </el-tab-pane>
      <el-tab-pane label="材料库" name="materials">
        <template #label>
          <span class="tab-label">
            <el-icon><FolderOpened /></el-icon>
            材料库
          </span>
        </template>
      </el-tab-pane>
    </el-tabs>

    <!-- 自由听力 -->
    <div v-if="activeTab === 'free'" class="free-listening">
      <div class="page-card">
        <h3 class="section-title">输入文本播放</h3>
        <el-input
          v-model="freeText"
          type="textarea"
          :rows="4"
          placeholder="输入英文文本，我将用AI语音为你朗读..."
        />
        
        <!-- 播放控制 -->
        <div class="play-controls">
          <div class="control-row">
            <div class="control-item">
              <span class="label">语速:</span>
              <el-slider v-model="speed" :min="0.5" :max="2" :step="0.1" show-stops />
              <span class="value">{{ speed }}x</span>
            </div>
          </div>
          <div class="control-row">
            <div class="control-item">
              <span class="label">声音:</span>
              <el-select v-model="selectedVoice" placeholder="选择声音">
                <el-option label="Aria (美音-女)" value="en-US-AriaNeural" />
                <el-option label="Guy (美音-男)" value="en-US-GuyNeural" />
                <el-option label="Sonia (英音-女)" value="en-GB-SoniaNeural" />
                <el-option label="Ryan (英音-男)" value="en-GB-RyanNeural" />
                <el-option label="Jenny (澳音-女)" value="en-AU-JennyNeural" />
              </el-select>
            </div>
          </div>
          
          <div class="btn-group">
          <!-- 进度条 -->
          <el-progress
            v-if="isPlaying"
            :percentage="progress"
            :stroke-width="4"
            :show-text="false"
            status="exception"
            class="tts-progress"
          />
          <el-button type="primary" @click="playAudio" :loading="isPlaying">
            <el-icon><VideoPlay /></el-icon>
            播放
          </el-button>
          <el-button @click="stopAudio" :disabled="!isPlaying">
            <el-icon><VideoPause /></el-icon>
            停止
          </el-button>
        </div>
        </div>

        <!-- 音频播放器 -->
        <div v-if="audioUrl" class="audio-player">
          <audio ref="audioPlayer" :src="audioUrl" controls @ended="isPlaying = false"></audio>
        </div>
      </div>

      <!-- 常用句子 -->
      <div class="page-card quick-sentences">
        <h3 class="section-title">常用句子</h3>
        <div class="sentence-tags">
          <el-tag
            v-for="sentence in quickSentences"
            :key="sentence"
            class="sentence-tag"
            @click="freeText = sentence"
          >
            {{ sentence }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 听写模式 -->
    <div v-if="activeTab === 'dictation'" class="dictation-mode">
      <div class="page-card">
        <h3 class="section-title">听写练习</h3>
        <div class="dictation-content">
          <!-- 播放控制 -->
          <div class="dictation-controls">
            <el-button type="primary" size="large" @click="playDictation" :loading="isPlaying">
              <el-icon><VideoPlay /></el-icon>
              播放听力材料
            </el-button>
            <el-button size="large" @click="replayDictation" :disabled="isPlaying">
              <el-icon><Refresh /></el-icon>
              重播
            </el-button>
          </div>

          <!-- 当前句子 -->
          <div v-if="currentDictation" class="current-sentence">
            <el-tag type="info" effect="plain">难度: {{ currentDictation.difficulty }}</el-tag>
            <div class="sentence-display" v-if="showAnswer">
              {{ currentDictation.text }}
            </div>
          </div>

          <!-- 用户输入 -->
          <div class="dictation-input">
            <h4>请输入你听到的内容:</h4>
            <el-input
              v-model="userAnswer"
              type="textarea"
              :rows="4"
              placeholder="请输入你听到的英文..."
              :disabled="hasSubmitted"
            />
            <div class="dictation-actions">
              <el-button type="primary" @click="submitAnswer" :disabled="!userAnswer || hasSubmitted">
                提交答案
              </el-button>
              <el-button @click="showAnswer = true" :disabled="hasSubmitted">
                显示原文
              </el-button>
            </div>
          </div>

          <!-- 评分结果 -->
          <div v-if="dictationResult" class="dictation-result">
            <el-result
              :icon="dictationResult.score >= 60 ? 'success' : 'warning'"
              :title="`得分: ${dictationResult.score}分`"
            >
              <template #sub-title>
                <div class="result-detail">
                  <p>原文: {{ dictationResult.reference || dictationResult.original }}</p>
                  <p>你的答案: {{ dictationResult.user_input || dictationResult.userAnswer }}</p>
                  <p v-if="dictationResult.errors && dictationResult.errors.length">
                    错误: {{ dictationResult.errors.map((e: any) => e.expected).join(', ') }}
                  </p>
                  <p>准确率: {{ dictationResult.accuracy || dictationResult.accuracyRate }}%</p>
                </div>
              </template>
              <template #extra>
                <el-button type="primary" @click="nextDictation">下一题</el-button>
              </template>
            </el-result>
          </div>
        </div>
      </div>
    </div>

    <!-- 材料库 -->
    <div v-if="activeTab === 'materials'" class="materials-library">
      <el-row :gutter="20">
        <el-col :span="8" v-for="material in materials" :key="material.id">
          <div class="material-card" @click="selectMaterial(material)">
            <div class="material-header">
              <el-tag :type="getDifficultyType(material.difficulty)">
                {{ material.difficulty_label || material.difficulty }}
              </el-tag>
            </div>
            <h4>{{ material.title }}</h4>
            <p class="material-preview">{{ material.text }}</p>
            <div class="material-footer">
              <span><el-icon><Clock /></el-icon> 听力练习</span>
              <el-button type="primary" size="small" @click.stop="playMaterial(material)">
                <el-icon><VideoPlay /></el-icon> 播放
              </el-button>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listeningApi } from '../api'
import {
  Headset, VideoPlay, VideoPause, EditPen,
  FolderOpened, Refresh, Clock
} from '@element-plus/icons-vue'

// // 标签页
const activeTab = ref('free')

// // 自由听力
const freeText = ref('')
const speed = ref(1.0)
const selectedVoice = ref('en-US-AriaNeural')
const isPlaying = ref(false)
const audioUrl = ref('')
const audioPlayer = ref<HTMLAudioElement | null>(null)

// 模拟进度条
const progress = ref(0)
let progressTimer: ReturnType<typeof setInterval> | null = null

const startProgress = () => {
  progress.value = 0
  progressTimer = setInterval(() => {
    progress.value = (progress.value + 10) % 100
  }, 300)
}

const stopProgress = () => {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
  progress.value = 0
}

// // 常用句子
const quickSentences = [
  'The quick brown fox jumps over the lazy dog.',
  'Practice makes perfect.',
  'Where there is a will, there is a way.',
  'Actions speak louder than words.',
  'Knowledge is power.',
  'Time and tide wait for no man.'
]

// // 播放音频
const playAudio = async () => {
  if (!freeText.value.trim()) {
    ElMessage.warning('请输入要播放的文本')
    return
  }

  isPlaying.value = true
  startProgress()
  try {
    const res = await listeningApi.tts(freeText.value, speed.value, selectedVoice.value)
    // 后端返回: { code: 0, data: { success, audio, ... } }
    const audioData = res.data?.data
    if (audioData && audioData.success && audioData.audio) {
      // 解码 base64 音频数据
      const byteCharacters = atob(audioData.audio)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const blob = new Blob([byteArray], { type: 'audio/mpeg' })
      audioUrl.value = URL.createObjectURL(blob)
      ElMessage.success('音频生成成功')
    } else {
      // 后端返回错误
      const errorMsg = audioData?.error || res.data?.message || '音频生成失败'
      ElMessage.error(errorMsg)
    }
  } catch (e: any) {
    ElMessage.error('音频生成失败: ' + (e.response?.data?.detail || e.message || '请检查网络连接'))
  } finally {
    isPlaying.value = false
    stopProgress()
  }
}

const stopAudio = () => {
  if (audioPlayer.value) {
    audioPlayer.value.pause()
    audioPlayer.value.currentTime = 0
  }
  isPlaying.value = false
}

// // 听写模式
const currentDictation = ref<any>(null)
const userAnswer = ref('')
const showAnswer = ref(false)
const hasSubmitted = ref(false)
const dictationResult = ref<any>(null)

// // 听写材料 - 使用后端API数据
const loadDictationMaterials = async () => {
  try {
    const res = await listeningApi.getMaterials()
    if (res.data && res.data.data && res.data.data.length > 0) {
      return res.data.data
    }
  } catch (e) {
    console.error('Failed to load materials:', e)
  }
  // 备用本地数据
  return [
    { id: 1, difficulty: 'beginner', difficulty_label: '初级', text: 'Good morning! How are you today?', translation: '早上好！你今天好吗？' },
    { id: 2, difficulty: 'intermediate', difficulty_label: '中级', text: 'I would like to travel around the world.', translation: '我想环游世界。' },
    { id: 3, difficulty: 'advanced', difficulty_label: '高级', text: 'Although he was tired, he still finished the project on time.', translation: '虽然他累了，但仍按时完成了项目。' }
  ]
}

// 初始化材料
const dictationMaterials = ref<any[]>([])
loadDictationMaterials().then(data => {
  dictationMaterials.value = data
})

const playDictation = async () => {
  if (!currentDictation.value) {
    currentDictation.value = dictationMaterials.value[0]
  }
  
  isPlaying.value = true
  try {
    const res = await listeningApi.tts(currentDictation.value.text, 0.8, 'en-US-AriaNeural')
    // 后端返回格式: { code: 0, data: { success, audio, text } }
    const audioData = res.data?.data || res.data
    if (audioData && audioData.success && audioData.audio) {
      // 解码 base64 音频数据
      const byteCharacters = atob(audioData.audio)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const blob = new Blob([byteArray], { type: 'audio/mpeg' })
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audio.play()
      audio.onended = () => {
        isPlaying.value = false
      }
    } else {
      ElMessage.error(audioData?.error || '音频生成失败，请稍后重试')
      isPlaying.value = false
    }
  } catch (e: any) {
    ElMessage.error('播放失败: ' + (e.message || '请检查网络连接'))
    isPlaying.value = false
  }
}

const replayDictation = () => {
  playDictation()
}

const submitAnswer = async () => {
  if (!currentDictation.value || !userAnswer.value.trim()) {
    ElMessage.warning('请输入你的答案')
    return
  }
  
  hasSubmitted.value = true
  try {
    const res = await listeningApi.dictation(currentDictation.value.text, userAnswer.value)
    // 后端返回格式: { code: 0, data: { score, accuracy, correct_words, total_words, errors, reference, user_input } }
    if (res.data && res.data.data) {
      dictationResult.value = res.data.data
    } else if (res.data) {
      dictationResult.value = res.data
    }
  } catch (e: any) {
    // 简单的本地比对
    const original = currentDictation.value.text.toLowerCase()
    const answer = userAnswer.value.toLowerCase()
    const words1 = original.split(' ')
    const words2 = answer.split(' ')
    const errors: any[] = []
    let correct_words = 0
    
    words1.forEach((w: string, i: number) => {
      if (i < words2.length && w === words2[i]) {
        correct_words++
      } else {
        errors.push({
          position: i,
          expected: w,
          actual: words2[i] || '[missing]'
        })
      }
    })
    
    const accuracy = Math.round(correct_words / words1.length * 100)
    const score = Math.max(0, accuracy)
    dictationResult.value = {
      score,
      accuracy,
      correct_words,
      total_words: words1.length,
      errors,
      reference: currentDictation.value.text,
      user_input: userAnswer.value
    }
  }
}

const nextDictation = () => {
  const idx = dictationMaterials.findIndex(m => m.id === currentDictation.value?.id)
  const nextIdx = (idx + 1) % dictationMaterials.length
  currentDictation.value = dictationMaterials.value[nextIdx]
  userAnswer.value = ''
  showAnswer.value = false
  hasSubmitted.value = false
  dictationResult.value = null
}

// // 材料库 - 从后端加载
const materials = ref<any[]>([])

const loadMaterials = async () => {
  try {
    const res = await listeningApi.getMaterials()
    if (res.data && res.data.data) {
      materials.value = res.data.data
    }
  } catch (e) {
    console.error('Failed to load materials:', e)
  }
}

loadMaterials()

const selectMaterial = (material: any) => {
  activeTab.value = 'dictation'
  currentDictation.value = { ...material }
}

const playMaterial = async (material: any) => {
  isPlaying.value = true
  try {
    const res = await listeningApi.tts(material.text, 1.0, 'en-US-AriaNeural')
    const audioData = res.data?.data || res.data
    if (audioData && audioData.success && audioData.audio) {
      // 解码 base64 音频数据
      const byteCharacters = atob(audioData.audio)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const blob = new Blob([byteArray], { type: 'audio/mpeg' })
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audio.play()
      audio.onended = () => {
        isPlaying.value = false
      }
    } else {
      ElMessage.error(audioData?.error || '音频生成失败，请稍后重试')
      isPlaying.value = false
    }
  } catch (e: any) {
    ElMessage.error('播放失败: ' + (e.message || '请检查网络连接'))
    isPlaying.value = false
  }
}

const getDifficultyType = (difficulty: string) => {
  const map: Record<string, string> = {
    'beginner': 'success',
    'intermediate': 'warning', 
    'advanced': 'danger',
    '初级': 'success',
    '中级': 'warning',
    '高级': 'danger'
  }
  return map[difficulty] || 'info'
}
</script>

<style scoped>
.listening-page {
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

.mode-tabs {
  margin-bottom: 20px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.free-listening .page-card {
  margin-bottom: 20px;
}

.play-controls {
  margin-top: 20px;
}

.control-row {
  margin-bottom: 16px;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-item .label {
  width: 50px;
  font-size: 14px;
  color: #606266;
}

.control-item .el-slider {
  flex: 1;
}

.control-item .value {
  width: 40px;
  font-size: 14px;
  color: #409EFF;
}

.btn-group {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tts-progress {
  width: 100%;
}

.audio-player {
  margin-top: 20px;
}

.audio-player audio {
  width: 100%;
}

.quick-sentences {
  margin-top: 20px;
}

.sentence-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.sentence-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.sentence-tag:hover {
  transform: scale(1.05);
}

.dictation-content {
  padding: 20px 0;
}

.dictation-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.current-sentence {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.sentence-display {
  margin-top: 12px;
  font-size: 18px;
  color: #303133;
  font-weight: 500;
}

.dictation-input {
  margin-bottom: 20px;
}

.dictation-input h4 {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
}

.dictation-actions {
  margin-top: 12px;
  display: flex;
  gap: 12px;
}

.dictation-result {
  margin-top: 20px;
}

.result-detail {
  text-align: left;
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
}

.materials-library {
  margin-top: 20px;
}

.material-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
}

.material-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.material-header {
  margin-bottom: 12px;
}

.material-card h4 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 8px;
}

.material-preview {
  font-size: 14px;
  color: #606266;
  margin-bottom: 16px;
  line-height: 1.6;
}

.material-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.material-footer span {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}
</style>