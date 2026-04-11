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
        <el-button @click="showReviewDialog = true" type="success">
          <el-icon><Reading /></el-icon>
          开始复习
          <el-tag size="small" type="danger" v-if="toReviewCount > 0">{{ toReviewCount }}</el-tag>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { vocabApi, listeningApi } from '../api'
import {
  Notebook, Plus, Reading, Search, VideoPlay,
  Edit, Delete
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

// 加载单词列表
const loadWords = async () => {
  try {
    const res = await vocabApi.getList()
    if (res.data && res.data.words) {
      allWords.value = res.data.words
      // 更新统计数据
      stats.value.total = allWords.value.length
      stats.value.mastered = allWords.value.filter(w => w.status === 'mastered').length
      stats.value.learning = allWords.value.filter(w => w.status === 'learning').length
    }
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
  
  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  filteredWords.value = result.slice(start, start + pageSize.value)
}

const totalWords = computed(() => filteredWords.value.length)

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

// 播放发音
const playPronunciation = async (word: string) => {
  try {
    const res = await listeningApi.tts(word, 1.0, 'en-US-AriaNeural')
    if (res.data && res.data.audio) {
      // 解码 base64 音频数据
      const byteCharacters = atob(res.data.audio)
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
    if (res.data && res.data.words) {
      toReviewCount.value = res.data.words.length
    }
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
</style>