<template>
  <div class="vocabulary-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Notebook /></el-icon>
        智能单词本
      </h1>
      <div class="header-actions">
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加单词
        </el-button>
        <el-button @click="startReview" type="success">
          <el-icon><Reading /></el-icon>
          开始复习
          <el-tag size="small" type="danger" v-if="toReviewCount > 0">{{ toReviewCount }}</el-tag>
        </el-button>
        <el-button @click="showAIGenerateDialog = true" type="info">
          <el-icon><MagicStick /></el-icon>
          AI生成
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总单词数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card orange">
          <div class="stat-value">{{ stats.mastered }}</div>
          <div class="stat-label">已掌握</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card green">
          <div class="stat-value">{{ stats.learning }}</div>
          <div class="stat-label">学习中</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card yellow">
          <div class="stat-value">{{ stats.needReview }}</div>
          <div class="stat-label">待复习</div>
        </div>
      </el-col>
    </el-row>

    <!-- 单词列表 -->
    <div class="page-card">
      <!-- 搜索和筛选 -->
      <div class="toolbar">
        <el-input
          v-model="searchWord"
          placeholder="搜索单词..."
          prefix-icon="Search"
          clearable
          style="width: 300px"
          @input="filterWords"
        />
        <el-select v-model="filterStatus" placeholder="筛选状态" style="width: 150px" @change="filterWords">
          <el-option label="全部" value="" />
          <el-option label="学习中" value="learning" />
          <el-option label="已掌握" value="mastered" />
          <el-option label="待复习" value="review" />
        </el-select>
      </div>

      <!-- 单词表格 -->
      <el-table :data="filteredWords" stripe style="width: 100%">
        <el-table-column prop="word" label="单词" width="150">
          <template #default="{ row }">
            <span class="word-text">{{ row.word }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="phonetic" label="音标" width="150" />
        <el-table-column prop="translation" label="释义" min-width="150" />
        <el-table-column prop="level" label="难度" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="nextReview" label="下次复习" width="150" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="playPronunciation(row.word)">
              <el-icon><VideoPlay /></el-icon>
            </el-button>
            <el-button size="small" type="primary" @click="editWord(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button size="small" type="danger" @click="deleteWord(row.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalWords"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="showAddDialog" :title="editingWord ? '编辑单词' : '添加单词'" width="500px">
      <el-form :model="wordForm" label-width="80px">
        <el-form-item label="单词">
          <el-input v-model="wordForm.word" placeholder="请输入单词" />
        </el-form-item>
        <el-form-item label="音标">
          <el-input v-model="wordForm.phonetic" placeholder="请输入音标" />
        </el-form-item>
        <el-form-item label="释义">
          <el-input v-model="wordForm.translation" type="textarea" :rows="2" placeholder="请输入释义" />
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="wordForm.level">
            <el-option label="简单" value="简单" />
            <el-option label="中等" value="中等" />
            <el-option label="困难" value="困难" />
          </el-select>
        </el-form-item>
        <el-form-item label="例句">
          <el-input v-model="wordForm.example" type="textarea" :rows="2" placeholder="请输入例句（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveWord">保存</el-button>
      </template>
    </el-dialog>

    <!-- 复习对话框 -->
    <el-dialog v-model="showReviewDialog" title="单词复习" width="600px" :close-on-click-modal="false">
      <div v-if="reviewWords.length === 0" class="no-review">
        <el-empty description="暂无待复习的单词" />
      </div>
      
      <div v-else class="review-content">
        <div class="progress-info">
          <span>进度: {{ currentReviewIndex + 1 }} / {{ reviewWords.length }}</span>
          <el-progress :percentage="((currentReviewIndex + 1) / reviewWords.length) * 100" :show-text="false" />
        </div>

        <!-- 复习卡片 -->
        <div class="review-card" v-if="currentReviewWord">
          <div class="review-word">{{ currentReviewWord.word }}</div>
          <div class="review-phonetic">{{ currentReviewWord.phonetic }}</div>
          <div class="review-translation">{{ currentReviewWord.translation }}</div>
          
          <div class="review-actions">
            <el-button @click="playPronunciation(currentReviewWord.word)">
              <el-icon><VideoPlay /></el-icon>
              播放发音
            </el-button>
          </div>

          <!-- 复习结果 -->
          <div class="review-result" v-if="showReviewResult">
            <div class="result-buttons">
              <el-button 
                v-for="result in reviewResults" 
                :key="result.value"
                :type="result.type"
                @click="submitReviewResult(result.value)"
              >
                {{ result.label }}
              </el-button>
            </div>
          </div>
          
          <div v-else class="show-answer-btn">
            <el-button type="primary" size="large" @click="showReviewResult = true">
              显示答案
            </el-button>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="closeReview">关闭</el-button>
      </template>
    </el-dialog>

    <!-- AI生成单词对话框 -->
    <el-dialog v-model="showAIGenerateDialog" title="AI生成单词" width="600px" :close-on-click-modal="false">
      <el-form label-width="80px">
        <el-form-item label="主题">
          <el-select v-model="generateForm.topic" placeholder="选择主题">
            <el-option label="日常英语" value="daily" />
            <el-option label="商务英语" value="business" />
            <el-option label="考研英语" value="exam" />
            <el-option label="雅思词汇" value="ielts" />
            <el-option label="托福词汇" value="toefl" />
            <el-option label="科技词汇" value="technology" />
            <el-option label="医学词汇" value="medical" />
          </el-select>
        </el-form-item>
        <el-form-item label="单词数量">
          <el-slider v-model="generateForm.count" :min="5" :max="20" show-input />
        </el-form-item>
      </el-form>

      <!-- 生成中显示进度条 -->
      <div v-if="isGenerating" class="generate-progress">
        <el-progress :percentage="generateProgress" :status="generateProgress === 100 ? 'success' : ''" />
        <div class="progress-text">{{ generateStatus }}</div>
      </div>

      <!-- 生成完成后展示结果 -->
      <div v-if="generatedWords.length > 0" class="generated-preview">
        <div class="preview-header">生成的单词（勾选加入默写）</div>
        <div class="word-list">
          <div v-for="(word, idx) in generatedWords" :key="idx" class="word-item">
            <el-checkbox v-model="word.selected" />
            <div class="word-info">
              <span class="word-text">{{ word.word }}</span>
              <span class="word-phonetic">{{ word.phonetic }}</span>
              <span class="word-meaning">{{ word.meaning }}</span>
              <el-tag size="small" type="info">{{ word.type }}</el-tag>
            </div>
            <el-button size="small" circle @click="playPronunciation(word.word)">
              <el-icon><VideoPlay /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showAIGenerateDialog = false">取消</el-button>
        <el-button type="primary" @click="startGenerate" :loading="isGenerating">
          {{ generatedWords.length > 0 ? '重新生成' : '开始生成' }}
        </el-button>
        <el-button type="success" @click="startSpellTest" :disabled="selectedGeneratedWords.length === 0">
          开始默写 ({{ selectedGeneratedWords.length }}个)
        </el-button>
        <el-button type="warning" @click="addToVocabulary" :disabled="selectedGeneratedWords.length === 0">
          <el-icon><Plus /></el-icon>
          加入单词本 ({{ selectedGeneratedWords.length }}个)
        </el-button>
      </template>
    </el-dialog>

    <!-- 默写模式对话框 -->
    <el-dialog v-model="showSpellDialog" title="单词默写" width="650px" :close-on-click-modal="false">
      <div v-if="spellWords.length === 0" class="spell-start-form">
        <el-form label-width="80px">
          <el-form-item label="选择主题">
            <el-select v-model="generateForm.topic" placeholder="选择默写主题">
              <el-option label="日常英语" value="daily" />
              <el-option label="商务英语" value="business" />
              <el-option label="考研英语" value="exam" />
              <el-option label="雅思词汇" value="ielts" />
              <el-option label="托福词汇" value="toefl" />
              <el-option label="科技词汇" value="technology" />
              <el-option label="医学词汇" value="medical" />
              <el-option label="英语短语" value="phrasal_verbs" />
              <el-option label="习语表达" value="idioms" />
            </el-select>
          </el-form-item>
          <el-form-item label="单词数量">
            <el-slider v-model="generateForm.count" :min="5" :max="20" :marks="{5: '5', 10: '10', 15: '15', 20: '20'}" show-input />
          </el-form-item>
        </el-form>

        <!-- 加载状态 -->
        <div v-if="isGenerating" class="generate-progress">
          <el-progress :percentage="generateProgress" :status="generateProgress === 100 ? 'success' : ''" />
          <div class="progress-text">{{ generateStatus }}</div>
        </div>
      </div>

      <div v-else class="spell-content">
        <!-- 进度信息 -->
        <div class="spell-progress">
          <div class="progress-header">
            <span>主题: {{ getTopicName(generateForm.topic) }}</span>
            <span>进度: {{ currentSpellIndex + 1 }} / {{ spellWords.length }}</span>
          </div>
          <el-progress :percentage="((currentSpellIndex + 1) / spellWords.length) * 100" :show-text="false" style="margin-top: 8px" />
        </div>

        <div class="spell-card" v-if="currentSpellWord">
          <!-- 显示中文含义，让用户拼写英文 -->
          <div class="spell-meaning">{{ currentSpellWord.meaning }}</div>
          <div class="spell-type">类型: {{ currentSpellWord.type }}</div>

          <!-- 播放发音按钮 -->
          <div class="spell-audio">
            <el-button type="primary" @click="playPronunciation(currentSpellWord.word)">
              <el-icon><VideoPlay /></el-icon>
              播放发音
            </el-button>
          </div>

          <!-- 音标跟读功能 -->
          <div class="phonetic-record">
            <el-button type="warning" @click="startRecord" :icon="Microphone" :class="{ 'recording': isRecording }">
              {{ isRecording ? '录音中...' : '跟读音标' }}
            </el-button>
            <div v-if="recordResult" class="record-result">
              <div class="result-row">
                <span class="result-label">你的发音:</span>
                <span class="result-value">{{ recordResult.text }}</span>
              </div>
              <div class="result-row">
                <span class="result-label">评分:</span>
                <el-tag :type="recordResult.score >= 80 ? 'success' : recordResult.score >= 60 ? 'warning' : 'danger'">
                  {{ recordResult.score }}分
                </el-tag>
              </div>
              <div v-if="recordResult.issues && recordResult.issues.length" class="result-issues">
                <span v-for="(issue, i) in recordResult.issues" :key="i">{{ issue }}</span>
              </div>
            </div>
          </div>

          <!-- 拼写输入框 -->
          <div class="spell-input">
            <el-input
              v-model="spellAnswer"
              placeholder="请输入单词拼写"
              size="large"
              @keyup.enter="submitSpell"
              :disabled="showSpellResult"
            />
          </div>

          <!-- 拼写结果 -->
          <div v-if="showSpellResult" class="spell-result">
            <el-alert
              :type="spellResult.correct ? 'success' : 'error'"
              :title="spellResult.correct ? '拼写正确！' : '拼写错误'"
              show-icon
              :closable="false"
            />
            <div class="correct-answer">正确答案: {{ currentSpellWord.word }}</div>
            <div v-if="!spellResult.correct" class="your-answer">你的答案: {{ spellAnswer }}</div>
          </div>

          <div class="spell-actions">
            <el-button v-if="!showSpellResult" type="primary" @click="submitSpell" :disabled="!spellAnswer">
              提交
            </el-button>
            <el-button v-if="showSpellResult" type="primary" @click="nextSpellWord">
              {{ isLastSpellWord ? '查看结果' : '下一题' }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- 默写完成面板 -->
      <div v-if="showSpellSummary" class="spell-summary">
        <h3>默写完成！</h3>
        <div class="summary-stats">
          <div class="stat-item correct">
            <span class="stat-num">{{ spellCorrectCount }}</span>
            <span class="stat-label">正确</span>
          </div>
          <div class="stat-item wrong">
            <span class="stat-num">{{ spellWrongCount }}</span>
            <span class="stat-label">错误</span>
          </div>
          <div class="stat-item rate">
            <span class="stat-num">{{ spellAccuracy }}%</span>
            <span class="stat-label">正确率</span>
          </div>
        </div>
        
        <div class="summary-actions">
          <el-button type="success" @click="continueSpellTest">
            <el-icon><Plus /></el-icon>
            继续默写更多
          </el-button>
          <el-button type="primary" @click="restartSpellTest">
            <el-icon><RefreshRight /></el-icon>
            重新开始
          </el-button>
        </div>
      </div>

      <template #footer>
        <el-button @click="closeSpell">关闭</el-button>
        <el-button v-if="spellWords.length === 0" type="primary" @click="startSpellTest" :disabled="isGenerating">
          {{ isGenerating ? 'AI生成中...' : '开始默写' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { vocabApi, listeningApi } from '../api'
import {
  Notebook, Plus, Reading, Search, VideoPlay,
  Edit, Delete, MagicStick, Microphone, RefreshRight,
  EditPen
} from '@element-plus/icons-vue'

// 统计数据
const stats = ref({
  total: 0,
  mastered: 0,
  learning: 0,
  needReview: 0
})

// 单词列表
const allWords = ref<any[]>([])
const filteredWords = ref<any[]>([])
const searchWord = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const filteredTotal = ref(0)  // 过滤后的总记录数

// 待复习数量
const toReviewCount = ref(0)

// 添加/编辑对话框
const showAddDialog = ref(false)
const editingWord = ref<any>(null)
const wordForm = ref({
  word: '',
  phonetic: '',
  translation: '',
  level: '简单',
  example: ''
})

// 复习对话框
const showReviewDialog = ref(false)
const reviewWords = ref<any[]>([])
const currentReviewIndex = ref(0)
const currentReviewWord = computed(() => reviewWords.value[currentReviewIndex.value])
const showReviewResult = ref(false)
const reviewResults = [
  { label: '不认识', value: 'forgot', type: 'danger' },
  { label: '模糊', value: '模糊', type: 'warning' },
  { label: '认识', value: 'remember', type: 'success' }
]

// AI生成单词
const showAIGenerateDialog = ref(false)
const generateForm = ref({
  topic: 'daily',
  count: 10
})

// 主题名称映射
const getTopicName = (topic: string) => {
  const map: Record<string, string> = {
    'daily': '日常英语',
    'business': '商务英语',
    'exam': '考研英语',
    'ielts': '雅思词汇',
    'toefl': '托福词汇',
    'technology': '科技词汇',
    'medical': '医学词汇',
    'phrasal_verbs': '英语短语',
    'idioms': '习语表达'
  }
  return map[topic] || topic
}

const isGenerating = ref(false)
const generateProgress = ref(0)
const generateStatus = ref('')
const generatedWords = ref<any[]>([])

// 默写模式（直接开始默写）
const showSpellDialog = ref(false)
const spellWords = ref<any[]>([])
const currentSpellIndex = ref(0)
const currentSpellWord = computed(() => spellWords.value[currentSpellIndex.value])
const spellAnswer = ref('')
const showSpellResult = ref(false)
const spellResult = ref<any>({})
const spellResults: any[] = []
const showSpellSummary = ref(false)  // 新增：默写完成面板
const alreadySpellWords = ref<string[]>([])  // 已默写过的单词（用于继续生成）

// 音标跟读
const isRecording = ref(false)
const recordResult = ref<any>(null)
let mediaRecorder: any = null
let audioChunks: Blob[] = []
let recordingStartTime = 0  // 录音开始时间

// 加载单词列表
const loadWords = async () => {
  try {
    const res = await vocabApi.getList()
    // 后端返回格式: { code: 0, data: { items: [...], total } }
    const items = res.data?.data?.items || res.data?.items || []
    const total = res.data?.data?.total || res.data?.total || 0
    
    // 转换后端字段名为前端字段
    allWords.value = items.map((w: any) => ({
      id: w.id,
      word: w.word,
      phonetic: w.phonetic,
      translation: w.meaning || '',
      level: getLevelFromStrength(w.memory_strength),
      status: getStatusFromStrength(w.memory_strength, w.next_review),
      nextReview: w.next_review ? new Date(w.next_review).toLocaleDateString() : '-',
      reviewedCount: w.reviewed_count || 0,
      correctCount: w.correct_count || 0
    }))
    // 更新统计数据
    stats.value.total = total
    stats.value.mastered = allWords.value.filter(w => w.status === 'mastered').length
    stats.value.learning = allWords.value.filter(w => w.status === 'learning').length
    filterWords()
  } catch (e) {
    // 使用默认数据
    allWords.value = getDefaultWords()
    stats.value.total = allWords.value.length
    filterWords()
  }
}

// 默认单词数据
const getDefaultWords = () => {
  return [
    { id: 1, word: 'abandon', phonetic: '/əˈbændən/', translation: 'v. 放弃，遗弃', level: '中等', status: 'learning', nextReview: '2024-01-16' },
    { id: 2, word: 'benefit', phonetic: '/ˈbenɪfɪt/', translation: 'n. 利益，好处', level: '简单', status: 'mastered', nextReview: '-' },
    { id: 3, word: 'calculate', phonetic: '/ˈkælkjʊleɪt/', translation: 'v. 计算，估算', level: '中等', status: 'learning', nextReview: '2024-01-15' },
    { id: 4, word: 'delegate', phonetic: '/ˈdelɪɡeɪt/', translation: 'n. 代表 v. 委派', level: '困难', status: 'review', nextReview: '2024-01-14' },
    { id: 5, word: 'enhance', phonetic: '/ɪnˈhɑːns/', translation: 'v. 加强，提高', level: '困难', status: 'learning', nextReview: '2024-01-17' },
    { id: 6, word: 'fundamental', phonetic: '/ˌfʌndəˈmentl/', translation: 'adj. 基础的，根本的', level: '中等', status: 'mastered', nextReview: '-' },
    { id: 7, word: 'generate', phonetic: '/ˈdʒenəreɪt/', translation: 'v. 产生，生成', level: '中等', status: 'review', nextReview: '2024-01-14' },
    { id: 8, word: 'implement', phonetic: '/ˈɪmplɪment/', translation: 'v. 实施，执行 n. 工具', level: '困难', status: 'learning', nextReview: '2024-01-18' }
  ]
}

// 筛选单词
const filterWords = () => {
  let result = allWords.value
  
  if (searchWord.value) {
    result = result.filter(w => 
      w.word.toLowerCase().includes(searchWord.value.toLowerCase()) ||
      w.translation.includes(searchWord.value)
    )
  }
  
  if (filterStatus.value) {
    result = result.filter(w => w.status === filterStatus.value)
  }
  
  // 保存过滤后的总数用于分页
  filteredTotal.value = result.length
  
  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  filteredWords.value = result.slice(start, start + pageSize.value)
}

const totalWords = computed(() => filteredTotal.value)

// AI生成单词计算属性
const selectedGeneratedWords = computed(() => generatedWords.value.filter(w => w.selected))

const isLastSpellWord = computed(() => currentSpellIndex.value >= spellWords.value.length - 1)

const spellCorrectCount = computed(() => spellResults.filter(r => r.correct).length)
const spellWrongCount = computed(() => spellResults.filter(r => !r.correct).length)
const spellAccuracy = computed(() => {
  const total = spellResults.length
  return total > 0 ? Math.round((spellCorrectCount.value / total) * 100) : 0
})

const handleSizeChange = (size: number) => {
  pageSize.value = size
  filterWords()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  filterWords()
}

// 获取难度类型
const getLevelType = (level: string) => {
  const map: Record<string, string> = {
    '简单': 'success',
    '中等': 'warning',
    '困难': 'danger'
  }
  return map[level] || 'info'
}

// 获取状态类型
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    'mastered': 'success',
    'learning': 'warning',
    'review': 'danger'
  }
  return map[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    'mastered': '已掌握',
    'learning': '学习中',
    'review': '待复习'
  }
  return map[status] || '未知'
}

// 根据记忆强度获取难度等级
const getLevelFromStrength = (strength: number) => {
  if (strength >= 4.0) return '简单'
  if (strength >= 2.5) return '中等'
  return '困难'
}

// 根据记忆强度和下次复习时间获取状态
const getStatusFromStrength = (strength: number, nextReview: string | null) => {
  if (strength >= 4.0) return 'mastered'
  if (nextReview && new Date(nextReview) <= new Date()) return 'review'
  return 'learning'
}

// 播放发音
const playPronunciation = async (word: string) => {
  try {
    const res = await listeningApi.tts(word, 1.0, 'en-US-AriaNeural')
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
      ElMessage.error('发音播放失败')
    }
  } catch (e) {
    ElMessage.error('发音播放失败')
  }
}

// 编辑单词
const editWord = (word: any) => {
  editingWord.value = word
  wordForm.value = { ...word }
  showAddDialog.value = true
}

// 删除单词
const deleteWord = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个单词吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    try {
      await vocabApi.delete(id)
    } catch (e) {
      // 本地删除
    }
    
    allWords.value = allWords.value.filter(w => w.id !== id)
    stats.value.total = allWords.value.length
    filterWords()
    ElMessage.success('删除成功')
  } catch (e) {
    // 用户取消
  }
}

// 保存单词
const saveWord = async () => {
  if (!wordForm.value.word || !wordForm.value.translation) {
    ElMessage.warning('请填写必填项')
    return
  }
  
  try {
    if (editingWord.value) {
      // 编辑
      try {
        // await vocabApi.update(...)
      } catch (e) {
        // 本地更新
      }
      const idx = allWords.value.findIndex(w => w.id === editingWord.value.id)
      if (idx !== -1) {
        allWords.value[idx] = { ...editingWord.value, ...wordForm.value }
      }
    } else {
      // 添加
      const newWord = {
        id: Date.now(),
        ...wordForm.value,
        status: 'learning',
        nextReview: '2024-01-15'
      }
      try {
        await vocabApi.add(wordForm.value.word)
      } catch (e) {
        // 本地添加
      }
      allWords.value.unshift(newWord)
    }
    
    stats.value.total = allWords.value.length
    filterWords()
    showAddDialog.value = false
    ElMessage.success('保存成功')
    
    // 重置表单
    editingWord.value = null
    wordForm.value = { word: '', phonetic: '', translation: '', level: '简单', example: '' }
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

// 加载待复习单词
const loadToReviewWords = async () => {
  try {
    const res = await vocabApi.toReview()
    // 后端返回格式: { code: 0, data: { items: [...], total } }
    const items = res.data?.data?.items || res.data?.items || []
    toReviewCount.value = items.length
  } catch (e) {
    toReviewCount.value = allWords.value.filter(w => w.status === 'review').length
  }
}

// 开始复习
const startReview = () => {
  reviewWords.value = allWords.value.filter(w => w.status === 'review')
  if (reviewWords.value.length === 0) {
    reviewWords.value = allWords.value.slice(0, 5)
  }
  currentReviewIndex.value = 0
  showReviewResult.value = false
  showReviewDialog.value = true
}

// 提交复习结果
const submitReviewResult = async (result: string) => {
  const word = currentReviewWord.value
  
  try {
    await vocabApi.review(word.id, result)
  } catch (e) {
    // 本地更新
  }
  
  // 更新状态
  if (result === 'remember') {
    word.status = 'mastered'
    word.nextReview = '-'
  } else if (result === 'forgot') {
    word.status = 'review'
    word.nextReview = '今天'
  } else {
    word.nextReview = '1天后'
  }
  
  // 下一题
  if (currentReviewIndex.value < reviewWords.value.length - 1) {
    currentReviewIndex.value++
    showReviewResult.value = false
  } else {
    ElMessage.success('复习完成！')
    closeReview()
  }
}

// 关闭复习
const closeReview = () => {
  showReviewDialog.value = false
  showReviewResult.value = false
  currentReviewIndex.value = 0
  filterWords()
}

// 开始AI生成
const startGenerate = async () => {
  isGenerating.value = true
  generateProgress.value = 0
  generateStatus.value = '正在连接AI服务...'
  generatedWords.value = []

  try {
    const res = await vocabApi.generate({
      topic: generateForm.value.topic,
      count: generateForm.value.count
    })

    generateProgress.value = 30
    generateStatus.value = 'AI正在生成单词...'

    // 解析返回的单词
    const words = res.data?.data?.words || res.data?.words || []
    generatedWords.value = words.map((w: any) => ({
      ...w,
      selected: true
    }))

    generateProgress.value = 100
    generateStatus.value = '生成完成！'
  } catch (e: any) {
    ElMessage.error(e.message || '生成失败，请重试')
    generateStatus.value = '生成失败'
  } finally {
    isGenerating.value = false
  }
}

// 开始AI生成（用于默写模式）
const startAIForSpell = async () => {
  isGenerating.value = true
  generateProgress.value = 0
  generateStatus.value = '正在连接AI服务...'
  spellWords.value = []

  try {
    const res = await vocabApi.generate({
      topic: generateForm.value.topic,
      count: generateForm.value.count,
      exclude_words: alreadySpellWords.value  // 排除已默写过的单词
    })

    generateProgress.value = 50
    generateStatus.value = 'AI正在生成单词...'

    // 解析返回的单词，直接进入默写
    const words = res.data?.data?.words || res.data?.words || []
    if (words.length === 0) {
      ElMessage.error('未能生成单词，请重试')
      return
    }

    spellWords.value = words.map((w: any) => ({
      ...w,
      selected: true
    }))
    
    // 记录已生成的单词（用于继续生成时排除）
    words.forEach((w: any) => {
      if (!alreadySpellWords.value.includes(w.word)) {
        alreadySpellWords.value.push(w.word)
      }
    })

    generateProgress.value = 100
    generateStatus.value = '开始默写!'

    // 自动开始默写
    currentSpellIndex.value = 0
    spellAnswer.value = ''
    showSpellResult.value = false
    recordResult.value = null
    spellResults.length = 0
    showSpellSummary.value = false
  } catch (e: any) {
    ElMessage.error(e.message || '生成失败，请重试')
    generateStatus.value = '生成失败'
  } finally {
    isGenerating.value = false
  }
}

// 开始默写（从AI生成对话框中选择单词）
const startSpellTest = () => {
  if (generatedWords.value.length > 0) {
    // 使用AI生成对话框中已选择的单词
    const selected = selectedGeneratedWords.value
    if (selected.length === 0) {
      ElMessage.warning('请选择要默写的单词')
      return
    }
    // 设置默写单词
    spellWords.value = selected.map((w: any) => ({
      ...w,
      word: w.word,
      meaning: w.meaning,
      phonetic: w.phonetic,
      type: w.type
    }))
    // 关闭AI生成对话框，打开默写对话框
    showAIGenerateDialog.value = false
    showSpellDialog.value = true
    currentSpellIndex.value = 0
    spellAnswer.value = ''
    showSpellResult.value = false
    recordResult.value = null
    spellResults.length = 0
    showSpellSummary.value = false
    ElMessage.success(`已选择 ${selected.length} 个单词开始默写`)
  } else {
    // 兼容旧代码：直接进入默写模式（会调用AI生成）
    startAIForSpell()
  }
}

// 添加选中的单词到单词本
const addToVocabulary = async () => {
  const selected = selectedGeneratedWords.value
  if (selected.length === 0) {
    ElMessage.warning('请选择要添加的单词')
    return
  }

  try {
    // 准备单词数据
    const wordsData = selected.map((w: any) => ({
      word: w.word,
      phonetic: w.phonetic || '',
      meaning: w.meaning || '',
      type: w.type || ''
    }))

    const res = await vocabApi.batchAdd(wordsData)

    // 解析返回结果
    const results = res.data?.data?.results || []
    const addedWords = results.filter((r: any) => r.status === 'added').map((r: any) => r.word)
    const skippedWords = results.filter((r: any) => r.status === 'skipped').map((r: any) => r.word)

    // 关闭对话框并刷新单词列表
    showAIGenerateDialog.value = false
    loadWords()

    // 根据结果类型显示不同消息
    if (addedWords.length > 0 && skippedWords.length === 0) {
      ElMessage.success(`成功添加 ${addedWords.length} 个单词到单词本`)
    } else if (addedWords.length > 0 && skippedWords.length > 0) {
      ElMessage.warning(`添加了 ${addedWords.length} 个单词，${skippedWords.length} 个已存在`)
    } else {
      ElMessage.info('所选单词均已存在，无需重复添加')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '添加失败，请重试')
  }
}

// 继续默写更多单词
const continueSpellTest = async () => {
  showSpellSummary.value = false
  await startAIForSpell()
}

// 重新开始
const restartSpellTest = () => {
  alreadySpellWords.value = []  // 清空已默写记录
  spellWords.value = []
  currentSpellIndex.value = 0
  showSpellSummary.value = false
  generateProgress.value = 0
  generateStatus.value = ''
}

// 提交拼写
const submitSpell = async () => {
  const word = currentSpellWord.value

  try {
    const res = await vocabApi.spellCheck({
      word: word.word,
      answer: spellAnswer.value
    })
    spellResult.value = res.data?.data || res.data
    showSpellResult.value = true

    spellResults.push({
      correct: spellResult.value.correct,
      answer: spellAnswer.value
    })
  } catch (e) {
    // 本地比对
    const correct = spellAnswer.value.toLowerCase().trim() === word.word.toLowerCase()
    spellResult.value = {
      correct,
      correct_answer: word.word
    }
    showSpellResult.value = true

    spellResults.push({
      correct,
      answer: spellAnswer.value
    })
  }
}

// 打开默写对话框（从"单词默写"按钮进入）
const openSpellDialog = () => {
  // 显式重置为默认值，防止状态污染
  generateForm.value = {
    topic: 'daily',
    count: 10
  }
  alreadySpellWords.value = []  // 清空历史
  spellWords.value = []  // 清空当前单词
  currentSpellIndex.value = 0
  showSpellSummary.value = false
  showSpellResult.value = false
  spellResult.value = {}
  spellAnswer.value = ''
  generateProgress.value = 0
  generateStatus.value = ''
  generatedWords.value = []  // 清空AI生成的单词
  showSpellDialog.value = true
}

// 下一题
const nextSpellWord = () => {
  if (currentSpellIndex.value < spellWords.value.length - 1) {
    currentSpellIndex.value++
    spellAnswer.value = ''
    showSpellResult.value = false
    recordResult.value = null
    spellResult.value = {}
  } else {
    // 默写完成，显示总结面板
    showSpellSummary.value = true
  }
}

// 关闭默写
const closeSpell = () => {
  showSpellDialog.value = false
  showSpellResult.value = false
  showSpellSummary.value = false
  currentSpellIndex.value = 0
  spellAnswer.value = ''
  recordResult.value = null
  spellResults.length = 0
  // 清空已默写单词记录（除非是手动关闭）
  // alreadySpellWords.value = []  // 可选：是否保留继续默写的能力
}

// 音标跟读
const startRecord = async () => {
  if (isRecording.value) {
    // 停止录音
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop()
    }
    isRecording.value = false
    return
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    // 固定使用 WebM 格式（所有浏览器都支持）
    let mimeType = 'audio/webm'
    mediaRecorder = new MediaRecorder(stream, { mimeType })
    
    // 验证 MediaRecorder 初始化是否成功
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
      stream.getTracks().forEach(track => track.stop())
      throw new Error('MediaRecorder 初始化失败')
    }
    
    audioChunks = []

    mediaRecorder.ondataavailable = (e: any) => {
      audioChunks.push(e.data)
    }

    mediaRecorder.onstop = async () => {
      // 检查录音时长
      const recordingDuration = Date.now() - recordingStartTime
      if (recordingDuration < 500) {
        isRecording.value = false
        ElMessage.warning('录音时间太短，请确保完整录音后重试')
        stream.getTracks().forEach(track => track.stop())
        return
      }
      
      const blobType = mimeType.includes('mp4') ? 'audio/mp4' : 'audio/webm'
      const audioBlob = new Blob(audioChunks, { type: blobType })
      const reader = new FileReader()
      reader.onload = async () => {
        const base64 = (reader.result as string).split(',')[1]

        try {
          const res = await vocabApi.phoneticCheck({
            word: currentSpellWord.value.word,
            phonetic: currentSpellWord.value.phonetic,
            audio: base64
          })
          recordResult.value = res.data?.data || res.data
        } catch (e: any) {
          ElMessage.error(e.message || '评测失败')
        }
      }
      reader.readAsDataURL(audioBlob)

      // 停止所有轨道
      stream.getTracks().forEach(track => track.stop())
    }

    mediaRecorder.start()
    recordingStartTime = Date.now()
    isRecording.value = true

    // 3秒后自动停止
    setTimeout(() => {
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop()
        isRecording.value = false
      }
    }, 3000)
  } catch (e: any) {
    isRecording.value = false  // 确保异常时重置状态
    // 区分不同错误类型
    if (e.name === 'NotAllowedError' || e.name === 'PermissionDeniedError') {
      ElMessage.error('麦克风权限被拒绝，请点击浏览器地址栏左侧的锁定图标允许访问')
    } else if (e.name === 'NotFoundError' || e.name === 'DevicesNotFoundError') {
      ElMessage.error('未找到麦克风设备，请确保已连接麦克风')
    } else if (e.name === 'NotReadableError' || e.name === 'TrackStartError') {
      ElMessage.error('麦克风已被其他应用占用，请关闭其他录音应用')
    } else {
      ElMessage.error('无法访问麦克风，请检查系统权限设置')
    }
  }
}

// 监听复习对话框打开
import { watch } from 'vue'
watch(showReviewDialog, (val) => {
  if (val) {
    startReview()
  }
})

onMounted(() => {
  loadWords()
  loadToReviewWords()
})
</script>

<style scoped>
.vocabulary-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  color: #fff;
  text-align: center;
}

.stat-card.orange {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card.green {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-card.yellow {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 4px;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.word-text {
  font-weight: 500;
  color: #303133;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.no-review {
  padding: 40px 0;
}

.review-content {
  padding: 20px 0;
}

.progress-info {
  margin-bottom: 20px;
  font-size: 14px;
  color: #606266;
}

.review-card {
  text-align: center;
  padding: 40px 20px;
  background: #f5f7fa;
  border-radius: 12px;
}

.review-word {
  font-size: 36px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 12px;
}

.review-phonetic {
  font-size: 18px;
  color: #909399;
  margin-bottom: 12px;
}

.review-translation {
  font-size: 20px;
  color: #606266;
  margin-bottom: 20px;
}

.review-actions {
  margin-bottom: 20px;
}

.show-answer-btn {
  margin-top: 20px;
}

.result-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
}

/* AI生成对话框样式 */
.generate-progress {
  margin: 20px 0;
  text-align: center;
}

.progress-text {
  margin-top: 10px;
  color: #606266;
  font-size: 14px;
}

.generated-preview {
  margin-top: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.preview-header {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 12px;
}

.word-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.word-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.word-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.word-info .word-text {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.word-info .word-phonetic {
  font-size: 14px;
  color: #909399;
}

.word-info .word-meaning {
  font-size: 14px;
  color: #606266;
}

/* 拼写对话框样式 */
.spell-content {
  padding: 20px 0;
}

.spell-progress {
  margin-bottom: 20px;
  font-size: 14px;
  color: #606266;
}

.spell-card {
  text-align: center;
  padding: 30px 20px;
  background: #f5f7fa;
  border-radius: 12px;
}

.spell-meaning {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.spell-type {
  font-size: 14px;
  color: #909399;
  margin-bottom: 20px;
}

.spell-audio {
  margin-bottom: 20px;
}

.phonetic-record {
  margin-bottom: 20px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

.phonetic-record .recording {
  background: #f56c6c;
  border-color: #f56c6c;
  color: #fff;
}

.record-result {
  margin-top: 16px;
  text-align: left;
}

.result-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.result-label {
  color: #909399;
  font-size: 14px;
}

.result-value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

.result-issues {
  margin-top: 8px;
  font-size: 13px;
  color: #e6a23c;
}

.spell-input {
  margin-bottom: 20px;
}

.spell-input .el-input {
  max-width: 300px;
}

.spell-result {
  margin-bottom: 20px;
}

.correct-answer,
.your-answer {
  margin-top: 12px;
  font-size: 14px;
  color: #606266;
}

.spell-actions {
  margin-top: 20px;
}

/* 默写结果统计 */
.spell-summary {
  margin-top: 20px;
  text-align: center;
  padding: 20px;
  background: #f0f9eb;
  border-radius: 8px;
}

.spell-summary h3 {
  margin: 0 0 16px 0;
  color: #67c23a;
}

.summary-stats {
  display: flex;
  justify-content: center;
  gap: 30px;
}

.stat-item {
  text-align: center;
}

.stat-item .stat-num {
  display: block;
  font-size: 28px;
  font-weight: 700;
}

.stat-item .stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-item.correct .stat-num {
  color: #67c23a;
}

.stat-item.wrong .stat-num {
  color: #f56c6c;
}

.stat-item.rate .stat-num {
  color: #409eff;
}
</style>