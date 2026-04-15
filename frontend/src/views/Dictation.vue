<template>
  <div class="dictation-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><EditPen /></el-icon>
        单词默写
      </h1>
    </div>

    <!-- 主题选择 -->
    <div class="page-card" v-if="!practiceStarted">
      <h3 class="section-title">选择默写主题</h3>
      
      <!-- AI生成模式开关 -->
      <div class="ai-mode-toggle">
        <el-switch v-model="useAIGenerate" />
        <span class="toggle-label">使用AI生成单词</span>
        <el-tooltip content="开启后，AI将根据主题生成新单词进行默写" placement="top">
          <el-icon><QuestionFilled /></el-icon>
        </el-tooltip>
      </div>
      
      <div class="theme-grid" :class="{ 'disabled': useAIGenerate }">
        <div 
          v-for="theme in themes" 
          :key="theme.id"
          class="theme-card"
          :class="{ active: selectedTheme === theme.id }"
          @click="!useAIGenerate && selectTheme(theme.id)"
        >
          <div class="theme-name">{{ theme.name }}</div>
          <div class="theme-count">{{ theme.word_count }} 个单词</div>
        </div>
      </div>

      <!-- 自定义主题 -->
      <div class="custom-theme">
        <el-input
          v-model="customTheme"
          placeholder="或输入自定义主题..."
          @keyup.enter="startPractice"
        >
          <template #prepend>自定义</template>
        </el-input>
      </div>

      <!-- 默写设置 -->
      <div class="practice-settings">
        <el-form label-width="100px">
          <el-form-item label="单词数量">
            <el-slider v-model="wordCount" :min="5" :max="15" :step="1" show-input />
          </el-form-item>
          <el-form-item label="默写模式">
            <el-checkbox-group v-model="selectedModes">
              <el-checkbox value="en2zh">英译中</el-checkbox>
              <el-checkbox value="zh2en">中译英</el-checkbox>
              <el-checkbox value="spelling">拼写练习</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-form>
      </div>

      <div class="start-button">
        <el-button type="primary" size="large" @click="startPractice" :disabled="!canStart" :loading="isGenerating">
          {{ isGenerating ? (useAIGenerate ? 'AI生成中...' : '生成中...') : (useAIGenerate ? 'AI生成并开始默写' : '开始默写') }}
        </el-button>
      </div>
    </div>

    <!-- 默写练习 -->
    <div class="page-card practice-area" v-if="practiceStarted && currentQuestion">
      <div class="progress-bar">
        <el-progress 
          :percentage="((currentIndex + 1) / questions.length) * 100" 
          :show-text="false"
        />
        <div class="progress-text">
          第 {{ currentIndex + 1 }} / {{ questions.length }} 题
        </div>
      </div>

      <div class="question-card">
        <div class="question-type">
          <el-tag :type="getModeType(currentQuestion.type)">
            {{ getModeText(currentQuestion.type) }}
          </el-tag>
        </div>

        <div class="question-text" v-if="currentQuestion.type === 'en2zh'">
          <div class="word-display">{{ currentQuestion.word }}</div>
          <div class="phonetic">{{ currentQuestion.phonetic }}</div>
        </div>

        <div class="question-text" v-if="currentQuestion.type === 'zh2en'">
          <div class="meaning-display">{{ currentQuestion.meaning }}</div>
        </div>

        <div class="question-text" v-if="currentQuestion.type === 'spelling'">
          <div class="word-display">{{ currentQuestion.word }}</div>
          <el-button @click="playAudio" type="info">
            <el-icon><VideoPlay /></el-icon>
            播放发音
          </el-button>
        </div>

        <!-- 用户答案输入 -->
        <div class="answer-input">
          <el-input
            v-model="userAnswer"
            :placeholder="getPlaceholder(currentQuestion.type)"
            size="large"
            @keyup.enter="submitAnswer"
            :disabled="answered"
          />
        </div>

        <!-- 答题结果 -->
        <div class="answer-result" v-if="answered">
          <el-alert 
            :type="result.correct ? 'success' : 'error'" 
            :title="result.correct ? '回答正确！' : '回答错误'"
            show-icon
            :closable="false"
          />
          <div class="correct-answer" v-if="!result.correct">
            正确答案: <strong>{{ result.correct_answer }}</strong>
          </div>
          <div class="explanation" v-if="result.explanation">
            {{ result.explanation }}
          </div>
        </div>

        <div class="action-buttons">
          <el-button 
            v-if="!answered" 
            type="primary" 
            size="large" 
            @click="submitAnswer"
            :disabled="!userAnswer"
          >
            提交答案
          </el-button>
          <el-button 
            v-else 
            type="primary" 
            size="large" 
            @click="nextQuestion"
          >
            {{ isLast ? '查看结果' : '下一题' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- 练习结果 -->
    <div class="page-card result-area" v-if="showResult">
      <h3 class="section-title">默写结果</h3>
      
      <div class="result-summary">
        <div class="result-card correct">
          <div class="result-value">{{ correctCount }}</div>
          <div class="result-label">正确</div>
        </div>
        <div class="result-card wrong">
          <div class="result-value">{{ wrongCount }}</div>
          <div class="result-label">错误</div>
        </div>
        <div class="result-card rate">
          <div class="result-value">{{ accuracy }}%</div>
          <div class="result-label">正确率</div>
        </div>
      </div>

      <div class="result-details">
        <h4>错题列表:</h4>
        <el-table :data="wrongQuestions" stripe>
          <el-table-column prop="word" label="单词" />
          <el-table-column prop="yourAnswer" label="你的答案" />
          <el-table-column prop="correctAnswer" label="正确答案" />
        </el-table>
      </div>

      <div class="result-actions">
        <!-- AI生成模式下的继续按钮 -->
        <el-button v-if="useAIGenerate" type="success" @click="continueAIGenerate" :loading="isGenerating">
          <el-icon><MagicStick /></el-icon>
          继续默写更多
        </el-button>
        <el-button type="primary" @click="restartPractice">重新默写</el-button>
        <el-button @click="goBack">返回选择</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { EditPen, VideoPlay, MagicStick, QuestionFilled } from '@element-plus/icons-vue'
import { dictationApi, vocabApi, listeningApi } from '../api'

// 主题列表
const themes = ref([
  { id: 'travel', name: '旅行', word_count: 15 },
  { id: 'shopping', name: '购物', word_count: 15 },
  { id: 'work', name: '工作', word_count: 15 },
  { id: 'daily', name: '日常生活', word_count: 15 },
  { id: 'food', name: '食物', word_count: 15 },
  { id: 'health', name: '健康', word_count: 15 },
  { id: 'technology', name: '科技', word_count: 15 },
  { id: 'education', name: '教育', word_count: 15 }
])

const selectedTheme = ref('')
const customTheme = ref('')
const wordCount = ref(10)
const selectedModes = ref(['en2zh', 'zh2en', 'spelling'])

// AI生成相关状态
const useAIGenerate = ref(false)  // 是否使用AI生成模式
const isGenerating = ref(false)
const aiGeneratedWords = ref<any[]>([])  // AI生成的单词
const alreadySpelledWords = ref<string[]>([])  // 已默写过的单词（用于继续生成）

const practiceStarted = ref(false)
const questions = ref<any[]>([])
const currentIndex = ref(0)
const currentQuestion = computed(() => questions.value[currentIndex.value])
const answered = ref(false)
const userAnswer = ref('')
const result = ref<any>({})
const showResult = ref(false)

const results: any[] = []
const wrongQuestions = ref<any[]>([])

const correctCount = computed(() => results.filter(r => r.correct).length)
const wrongCount = computed(() => results.filter(r => !r.correct).length)
const accuracy = computed(() => {
  const total = results.length
  return total > 0 ? Math.round((correctCount.value / total) * 100) : 0
})
const isLast = computed(() => currentIndex.value >= questions.value.length - 1)

const canStart = computed(() => {
  return (selectedTheme.value || customTheme.value) && selectedModes.value.length > 0
})

const selectTheme = (id: string) => {
  selectedTheme.value = selectedTheme.value === id ? '' : id
}

const getModeType = (mode: string) => {
  const map: Record<string, string> = {
    'en2zh': 'primary',
    'zh2en': 'success',
    'spelling': 'warning'
  }
  return map[mode] || 'info'
}

const getModeText = (mode: string) => {
  const map: Record<string, string> = {
    'en2zh': '英译中',
    'zh2en': '中译英',
    'spelling': '拼写练习'
  }
  return map[mode] || mode
}

const getPlaceholder = (mode: string) => {
  if (mode === 'en2zh') return '请输入中文含义'
  if (mode === 'zh2en') return '请输入英文单词'
  return '请拼写单词'
}

const playAudio = async () => {
  // 调用 TTS 播放
  if (currentQuestion.value?.word) {
    try {
      const res = await listeningApi.tts(currentQuestion.value.word, 1.0, 'en-US-AriaNeural')
      // API 返回格式: { code: 0, data: { success: true, audio: "..." } }
      if (res.data && res.data.data && res.data.data.audio) {
        // 解码 base64 音频数据
        const byteCharacters = atob(res.data.data.audio)
        const byteNumbers = new Array(byteCharacters.length)
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i)
        }
        const byteArray = new Uint8Array(byteNumbers)
        const blob = new Blob([byteArray], { type: 'audio/mpeg' })
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        audio.play()
      } else {
        // 备用：使用浏览器 speech synthesis
        fallbackPlayAudio(currentQuestion.value.word)
      }
    } catch (e) {
      // 备用：使用浏览器 speech synthesis
      fallbackPlayAudio(currentQuestion.value.word)
    }
  }
}

// 备用播放方法：使用浏览器 speech synthesis
const fallbackPlayAudio = (word: string) => {
  const utterance = new SpeechSynthesisUtterance(word)
  utterance.lang = 'en-US'
  speechSynthesis.speak(utterance)
}

const startPractice = async () => {
  const theme = customTheme.value || selectedTheme.value
  if (!theme) {
    ElMessage.warning('请选择或输入主题')
    return
  }

  // 如果使用AI生成模式
  if (useAIGenerate.value) {
    await startAIGeneratePractice()
    return
  }

  try {
    const res = await dictationApi.generate({
      theme,
      word_count: wordCount.value,
      modes: selectedModes.value
    })
    
    // 后端返回 { code: 0, data: { questions: [...] } }
    if (res.data?.data?.questions) {
      questions.value = res.data.data.questions
      practiceStarted.value = true
      showResult.value = false
      currentIndex.value = 0
      answered.value = false
      userAnswer.value = ''
      results.length = 0
      wrongQuestions.value = []
    } else if (res.data?.questions) {
      questions.value = res.data.questions
      practiceStarted.value = true
      showResult.value = false
      currentIndex.value = 0
      answered.value = false
      userAnswer.value = ''
      results.length = 0
      wrongQuestions.value = []
    }
  } catch (e) {
    ElMessage.error('生成默写题目失败')
  }
}

// AI生成并开始默写
const startAIGeneratePractice = async () => {
  const theme = customTheme.value || selectedTheme.value
  if (!theme) {
    ElMessage.warning('请选择或输入主题')
    return
  }

  isGenerating.value = true
  try {
    const res = await vocabApi.generate({
      topic: theme,
      count: wordCount.value,
      exclude_words: alreadySpelledWords.value
    })

    // 解析返回的单词
    const words = res.data?.data?.words || res.data?.words || []
    if (words.length === 0) {
      ElMessage.error('未能生成单词，请重试')
      return
    }

    // 记录已生成的单词（用于继续生成时排除）
    words.forEach((w: any) => {
      if (!alreadySpelledWords.value.includes(w.word)) {
        alreadySpelledWords.value.push(w.word)
      }
    })

    // 转换为题目格式
    questions.value = words.map((w: any, idx: number) => ({
      id: `q_${idx}`,
      word: w.word,
      type: 'spelling',
      question: '请听发音并拼写单词',
      phonetic: w.phonetic,
      meaning: w.meaning,
      type_info: w.type
    }))

    practiceStarted.value = true
    showResult.value = false
    currentIndex.value = 0
    answered.value = false
    userAnswer.value = ''
    results.length = 0
    wrongQuestions.value = []
    
    ElMessage.success(`已生成 ${words.length} 个单词，开始默写！`)
  } catch (e: any) {
    ElMessage.error(e.message || 'AI生成单词失败')
  } finally {
    isGenerating.value = false
  }
}

// 继续生成更多单词
const continueAIGenerate = async () => {
  showResult.value = false
  await startAIGeneratePractice()
}

const submitAnswer = async () => {
  if (!userAnswer.value || answered.value) return

  // AI生成模式使用本地判断
  if (useAIGenerate.value) {
    const correct = userAnswer.value.toLowerCase().trim() === 
      (currentQuestion.value.word || '').toLowerCase().trim()
    result.value = {
      correct,
      correct_answer: currentQuestion.value.word,
      explanation: currentQuestion.value.meaning || ''
    }
    answered.value = true
    
    results.push({
      correct,
      answer: userAnswer.value,
      word: currentQuestion.value.word || currentQuestion.value.meaning
    })
    
    if (!correct) {
      wrongQuestions.value.push({
        word: currentQuestion.value.word || currentQuestion.value.meaning,
        yourAnswer: userAnswer.value,
        correctAnswer: currentQuestion.value.word
      })
    }
    return
  }

  try {
    const res = await dictationApi.submit({
      question_id: currentQuestion.value.id,
      answer: userAnswer.value,
      mode: currentQuestion.value.type
    })
    
    // 后端返回 { code: 0, data: {...} }
    if (res.data?.data) {
      result.value = res.data.data
      answered.value = true
      
      results.push({
        correct: res.data.data.correct,
        answer: userAnswer.value,
        word: currentQuestion.value.word || currentQuestion.value.meaning
      })
      
      if (!res.data.data.correct) {
        wrongQuestions.value.push({
          word: currentQuestion.value.word || currentQuestion.value.meaning,
          yourAnswer: userAnswer.value,
          correctAnswer: res.data.data.correct_answer
        })
      }
    } else if (res.data) {
      result.value = res.data
      answered.value = true
      
      results.push({
        correct: res.data.correct,
        answer: userAnswer.value,
        word: currentQuestion.value.word || currentQuestion.value.meaning
      })
      
      if (!res.data.correct) {
        wrongQuestions.value.push({
          word: currentQuestion.value.word || currentQuestion.value.meaning,
          yourAnswer: userAnswer.value,
          correctAnswer: res.data.correct_answer
        })
      }
    }
  } catch (e) {
    // 本地判断
    const correct = userAnswer.value.toLowerCase().trim() === 
      (currentQuestion.value.word || '').toLowerCase().trim()
    result.value = {
      correct,
      correct_answer: currentQuestion.value.word,
      explanation: correct ? '正确！' : `正确答案是: ${currentQuestion.value.word}`
    }
    answered.value = true
  }
}

const nextQuestion = () => {
  if (isLast.value) {
    showResult.value = true
    practiceStarted.value = false
  } else {
    currentIndex.value++
    answered.value = false
    userAnswer.value = ''
    result.value = {}
  }
}

const restartPractice = () => {
  startPractice()
}

const goBack = () => {
  practiceStarted.value = false
  showResult.value = false
  selectedTheme.value = ''
  customTheme.value = ''
}
</script>

<style scoped>
.dictation-page {
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

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 20px;
}

.theme-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.theme-grid.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.ai-mode-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f0f9eb;
  border-radius: 8px;
}

.toggle-label {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.theme-card {
  padding: 16px;
  border: 2px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  text-align: center;
  transition: all 0.3s;
}

.theme-card:hover {
  border-color: #409eff;
}

.theme-card.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.theme-name {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.theme-count {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.custom-theme {
  margin-bottom: 20px;
}

.practice-settings {
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.start-button {
  text-align: center;
}

.practice-area {
  padding: 20px;
}

.progress-bar {
  margin-bottom: 20px;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  color: #606266;
}

.question-card {
  max-width: 600px;
  margin: 0 auto;
  padding: 30px;
  background: #f5f7fa;
  border-radius: 12px;
}

.question-type {
  text-align: center;
  margin-bottom: 20px;
}

.question-text {
  text-align: center;
  margin-bottom: 30px;
}

.word-display {
  font-size: 36px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 12px;
}

.phonetic {
  font-size: 18px;
  color: #909399;
}

.meaning-display {
  font-size: 28px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 20px;
}

.answer-input {
  margin-bottom: 20px;
}

.answer-result {
  margin-bottom: 20px;
}

.correct-answer {
  margin-top: 12px;
  font-size: 16px;
  color: #f56c6c;
}

.explanation {
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

.action-buttons {
  text-align: center;
}

.result-area {
  padding: 20px;
}

.result-summary {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 30px;
}

.result-card {
  padding: 20px 40px;
  border-radius: 12px;
  text-align: center;
  color: #fff;
}

.result-card.correct {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.result-card.wrong {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
}

.result-card.rate {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
}

.result-value {
  font-size: 36px;
  font-weight: 700;
}

.result-label {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 4px;
}

.result-details {
  margin-bottom: 20px;
}

.result-actions {
  text-align: center;
}
</style>