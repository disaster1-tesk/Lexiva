<template>
  <div class="grammar-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Reading /></el-icon>
        语法学习
      </h1>
      <div class="header-actions">
        <el-button type="primary" @click="showRecommend = true">
          AI 推荐
        </el-button>
        <el-button @click="showAIGenerateDialog = true" type="warning">
          <el-icon><MagicStick /></el-icon>
          AI生成语法
        </el-button>
      </div>
    </div>

    <!-- 语法分类 -->
    <div class="page-card" v-if="!currentTopic">
      <h3 class="section-title">选择语法分类</h3>
      <div class="category-grid">
        <div 
          v-for="cat in categories" 
          :key="cat.id"
          class="category-card"
          @click="selectCategory(cat.id)"
        >
          <div class="category-name">{{ cat.name }}</div>
          <div class="category-count">{{ cat.count }} 个语法点</div>
        </div>
      </div>

      <!-- 语法点列表 -->
      <div class="topic-list" v-if="selectedCategoryId">
        <h4 class="subsection-title">{{ currentCategoryName }}</h4>
        <div class="topic-grid">
          <div 
            v-for="topic in topics" 
            :key="topic.id"
            class="topic-card"
            @click="learnTopic(topic.id)"
          >
            <div class="topic-name">{{ topic.name }}</div>
            <div class="topic-desc">{{ topic.description }}</div>
            <div class="topic-meta">
              <el-tag size="small">{{ topic.example_count }} 个例句</el-tag>
              <el-tag size="small" type="success">{{ topic.exercise_count }} 道练习</el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 学习界面 -->
    <div class="page-card learn-area" v-if="currentTopic">
      <div class="learn-header">
        <el-button @click="backToList" text>
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h2 class="topic-title">{{ currentTopic.name }}</h2>
      </div>

      <!-- 语法讲解 -->
      <div class="explanation-section">
        <h3 class="subsection-title">语法讲解</h3>
        <p class="description">{{ currentTopic.description }}</p>
        <div class="formula" v-if="currentTopic.formula">
          <strong>公式：</strong> {{ currentTopic.formula }}
        </div>
      </div>

      <!-- 例句 -->
      <div class="examples-section">
        <h3 class="subsection-title">例句演示</h3>
        <ul class="example-list">
          <li v-for="(example, idx) in currentTopic.examples" :key="idx">
            {{ example }}
          </li>
        </ul>
      </div>

      <!-- 练习 -->
      <div class="exercises-section">
        <h3 class="subsection-title">练习测试</h3>
        
        <div class="exercise-card" v-if="currentExercise">
          <div class="exercise-progress">
            练习 {{ exerciseIndex + 1 }} / {{ currentTopic.exercises.length }}
          </div>
          
          <div class="exercise-content">
            <div class="exercise-question">{{ currentExercise.question }}</div>
            
            <!-- 选择题 -->
            <div class="options" v-if="currentExercise.options">
              <el-radio-group v-model="userAnswer">
                <el-radio 
                  v-for="opt in currentExercise.options" 
                  :key="opt"
                  :value="opt"
                >
                  {{ opt }}
                </el-radio>
              </el-radio-group>
            </div>
            
            <!-- 填空题 -->
            <div class="fill-blank" v-else-if="currentExercise.type === 'fill_blank'">
              <el-input
                v-model="userAnswer"
                placeholder="请输入答案"
                size="large"
              />
            </div>
            
            <!-- 改写题 -->
            <div class="rewrite" v-else-if="currentExercise.type === 'rewrite'">
              <el-input
                v-model="userAnswer"
                placeholder="请改写句子"
                size="large"
                type="textarea"
                :rows="2"
              />
            </div>
          </div>

          <!-- 答题结果 -->
          <div class="exercise-result" v-if="showResult">
            <el-alert 
              :type="exerciseResult.correct ? 'success' : 'error'" 
              :title="exerciseResult.correct ? '回答正确！' : '回答错误'"
              show-icon
              :closable="false"
            />
            <div class="result-explanation" v-if="exerciseResult.explanation">
              {{ exerciseResult.explanation }}
            </div>
          </div>

          <div class="exercise-actions">
            <el-button 
              v-if="!showResult" 
              type="primary" 
              @click="submitExercise"
              :disabled="!userAnswer"
            >
              提交答案
            </el-button>
            <el-button 
              v-if="showResult" 
              type="primary" 
              @click="nextExercise"
            >
              {{ isLastExercise ? '查看结果' : '下一题' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 练习结果 -->
    <div class="page-card result-area" v-if="showExerciseResult">
      <h3 class="section-title">练习完成！</h3>
      
      <div class="result-summary">
        <div class="result-card correct">
          <div class="result-value">{{ exerciseCorrect }}</div>
          <div class="result-label">正确</div>
        </div>
        <div class="result-card wrong">
          <div class="result-value">{{ exerciseWrong }}</div>
          <div class="result-label">错误</div>
        </div>
        <div class="result-card rate">
          <div class="result-value">{{ exerciseAccuracy }}%</div>
          <div class="result-label">正确率</div>
        </div>
      </div>

      <div class="result-actions">
        <el-button type="primary" @click="retryExercises">重新练习</el-button>
        <el-button @click="backToList">返回列表</el-button>
      </div>
    </div>

    <!-- AI 推荐对话框 -->
    <el-dialog v-model="showRecommend" title="AI 推荐" width="500px">
      <div v-if="recommendations.length === 0" class="loading">
        加载推荐中...
      </div>
      <div v-else class="recommend-list">
        <div 
          v-for="rec in recommendations" 
          :key="rec.id"
          class="recommend-card"
          @click="learnTopic(rec.id)"
        >
          <div class="rec-name">{{ rec.name }}</div>
          <div class="rec-category">{{ rec.category }}</div>
          <div class="rec-reason">{{ rec.reason }}</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showRecommend = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- AI生成语法对话框 -->
    <el-dialog v-model="showAIGenerateDialog" title="AI生成语法" width="600px" :close-on-click-modal="false">
      <el-form label-width="80px">
        <el-form-item label="语法分类">
          <el-select v-model="generateForm.category" placeholder="选择分类" filterable allow-create>
            <el-option label="时态" value="tenses" />
            <el-option label="从句" value="clauses" />
            <el-option label="非谓语" value="nonfinite" />
            <el-option label="语态" value="voice" />
            <el-option label="虚拟语气" value="subjunctive" />
            <el-option label="倒装句" value="inversion" />
            <el-option label="强调句" value="emphasis" />
            <el-option label="定语从句" value="relative_clause" />
            <el-option label="名词性从句" value="noun_clause" />
            <el-option label="状语从句" value="adverbial_clause" />
            <el-option label="比较级" value="comparative" />
            <el-option label="最高级" value="superlative" />
            <el-option label="情态动词" value="modal_verbs" />
            <el-option label="独立主格" value="absolute_construction" />
            <el-option label="省略句" value="ellipsis" />
          </el-select>
          <el-input
            v-if="!isPresetCategory"
            v-model="customCategory"
            placeholder="输入自定义分类"
            style="margin-top: 8px"
            @keyup.enter="applyCustomCategory"
          >
            <template #append>
              <el-button @click="applyCustomCategory">使用</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="语法点数量">
          <el-slider v-model="generateForm.count" :min="1" :max="5" show-input />
        </el-form-item>
      </el-form>

      <!-- 进度条 -->
      <div v-if="isGenerating" class="generate-progress">
        <el-progress :percentage="generateProgress" :status="generateProgress === 100 ? 'success' : ''" />
        <div class="progress-text">{{ generateStatus }}</div>
      </div>

      <!-- 生成结果预览 -->
      <div v-if="generatedTopics.length > 0" class="generated-preview">
        <div class="preview-header">生成的语法点（点击开始学习）</div>
        <div class="topic-list">
          <div 
            v-for="(topic, idx) in generatedTopics" 
            :key="idx" 
            class="topic-item"
            @click="learnAIGeneratedTopic(topic)"
          >
            <div class="topic-name">{{ topic.name }}</div>
            <div class="topic-desc">{{ topic.description }}</div>
            <div class="topic-meta">
              <el-tag size="small">{{ topic.exercises?.length || 0 }} 道练习</el-tag>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showAIGenerateDialog = false">关闭</el-button>
        <el-button type="primary" @click="startGenerate" :loading="isGenerating">
          {{ generatedTopics.length > 0 ? '重新生成' : '开始生成' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Reading, ArrowLeft, MagicStick } from '@element-plus/icons-vue'
import { grammarApi } from '../api'

// 分类列表
const categories = ref<any[]>([])
const selectedCategoryId = ref('')
const topics = ref<any[]>([])
const currentCategoryName = ref('')

// 学习内容
const currentTopic = ref<any>(null)
const currentExercise = ref<any>(null)
const exerciseIndex = ref(0)
const userAnswer = ref('')
const showResult = ref(false)
const exerciseResult = ref<any>({})
const showExerciseResult = ref(false)
const exerciseResults: any[] = []

// AI 推荐
const showRecommend = ref(false)
const recommendations = ref<any[]>([])

// AI生成语法
const showAIGenerateDialog = ref(false)
const generateForm = ref({
  category: 'tenses',
  count: 1
})
const customCategory = ref('')  // 自定义分类输入
const isGenerating = ref(false)
const generateProgress = ref(0)
const generateStatus = ref('')
const generatedTopics = ref<any[]>([])

// 预设分类列表（用于判断是否为自定义）
const presetCategories = [
  'tenses', 'clauses', 'nonfinite', 'voice', 'subjunctive', 'inversion', 'emphasis',
  'relative_clause', 'noun_clause', 'adverbial_clause', 'comparative', 'superlative',
  'modal_verbs', 'absolute_construction', 'ellipsis'
]

// 判断当前分类是否为预设
const isPresetCategory = computed(() => {
  return presetCategories.includes(generateForm.value.category)
})

// 应用自定义分类
const applyCustomCategory = () => {
  if (customCategory.value.trim()) {
    generateForm.value.category = customCategory.value.trim()
    ElMessage.success(`已选择分类: ${customCategory.value.trim()}`)
  }
}

const isLastExercise = computed(() => {
  if (!currentTopic.value) return true
  return exerciseIndex.value >= currentTopic.value.exercises?.length - 1
})

const exerciseCorrect = computed(() => exerciseResults.filter(r => r.correct).length)
const exerciseWrong = computed(() => exerciseResults.filter(r => !r.correct).length)
const exerciseAccuracy = computed(() => {
  const total = exerciseResults.length
  return total > 0 ? Math.round((exerciseCorrect.value / total) * 100) : 0
})

// 加载分类
const loadCategories = async () => {
  try {
    const res = await grammarApi.getTopics()
    // 后端返回 { code: 0, data: [...] }
    if (res.data?.data) {
      categories.value = res.data.data
    } else if (res.data) {
      categories.value = res.data
    }
  } catch (e) {
    // 默认数据
    categories.value = [
      { id: 'tenses', name: '时态', count: 3 },
      { id: 'clauses', name: '从句', count: 2 },
      { id: 'nonfinite', name: '非谓语', count: 2 },
      { id: 'voice', name: '语态', count: 1 }
    ]
  }
}

// 选择分类
const selectCategory = async (id: string) => {
  selectedCategoryId.value = id
  
  try {
    const res = await grammarApi.getTopicsByCategory(id)
    // 后端返回 { code: 0, data: { category, topics } }
    if (res.data?.data) {
      currentCategoryName.value = res.data.data.category || ''
      topics.value = res.data.data.topics || []
    } else if (res.data) {
      currentCategoryName.value = res.data.category || ''
      topics.value = res.data.topics || []
    }
  } catch (e) {
    // 默认数据
    topics.value = []
  }
}

// 学习语法点
const learnTopic = async (id: string) => {
  showRecommend.value = false
  
  try {
    const res = await grammarApi.learn(id)
    // 后端返回 { code: 0, data: {...} }
    if (res.data?.data) {
      currentTopic.value = res.data.data
      exerciseIndex.value = 0
      userAnswer.value = ''
      showResult.value = false
      showExerciseResult.value = false
      exerciseResults.length = 0
      
      if (res.data.data.exercises?.length > 0) {
        currentExercise.value = res.data.data.exercises[0]
      }
    } else if (res.data) {
      currentTopic.value = res.data
      exerciseIndex.value = 0
      userAnswer.value = ''
      showResult.value = false
      showExerciseResult.value = false
      exerciseResults.length = 0
      
      if (res.data.exercises?.length > 0) {
        currentExercise.value = res.data.exercises[0]
      }
    }
  } catch (e) {
    ElMessage.error('加载语法点失败')
  }
}

// 提交练习
const submitExercise = async () => {
  if (!userAnswer.value || !currentTopic.value) return

  try {
    const res = await grammarApi.submitExercise({
      topic_id: currentTopic.value.id,
      exercise_id: exerciseIndex.value,
      answer: userAnswer.value
    })
    
    // 后端返回 { code: 0, data: {...} }
    if (res.data?.data) {
      exerciseResult.value = res.data.data
      showResult.value = true
      
      exerciseResults.push({
        correct: res.data.data.correct,
        answer: userAnswer.value
      })
    } else if (res.data) {
      exerciseResult.value = res.data
      showResult.value = true
      
      exerciseResults.push({
        correct: res.data.correct,
        answer: userAnswer.value
      })
    }
  } catch (e) {
    // 本地判断
    const correct = userAnswer.value.toLowerCase().trim() === 
      currentExercise.value?.answer?.toLowerCase().trim()
    exerciseResult.value = {
      correct,
      correct_answer: currentExercise.value?.answer,
      explanation: correct ? '正确！' : `正确答案是: ${currentExercise.value?.answer}`
    }
    showResult.value = true
  }
}

// 下一题
const nextExercise = () => {
  if (isLastExercise.value) {
    showExerciseResult.value = true
    currentTopic.value = null
  } else {
    exerciseIndex.value++
    currentExercise.value = currentTopic.value.exercises[exerciseIndex.value]
    userAnswer.value = ''
    showResult.value = false
    exerciseResult.value = {}
  }
}

// 重试
const retryExercises = () => {
  if (currentTopic.value) {
    exerciseIndex.value = 0
    userAnswer.value = ''
    showResult.value = false
    showExerciseResult.value = false
    exerciseResults.length = 0
    
    if (currentTopic.value.exercises?.length > 0) {
      currentExercise.value = currentTopic.value.exercises[0]
    }
  }
}

// 返回列表
const backToList = () => {
  currentTopic.value = null
  selectedCategoryId.value = ''
}

// 加载 AI 推荐
const loadRecommendations = async () => {
  try {
    const res = await grammarApi.recommend()
    // 后端返回 { code: 0, data: [...] }
    if (res.data?.data) {
      recommendations.value = res.data.data
    } else if (res.data) {
      recommendations.value = res.data
    }
  } catch (e) {
    recommendations.value = []
  }
}

// 开始AI生成语法
const startGenerate = async () => {
  isGenerating.value = true
  generateProgress.value = 0
  generateStatus.value = '正在连接AI服务...'
  generatedTopics.value = []

  try {
    const res = await grammarApi.generate({
      category: generateForm.value.category,
      count: generateForm.value.count
    })

    generateProgress.value = 30
    generateStatus.value = 'AI正在生成语法点...'

    // 解析返回的语法点
    const topics = res.data?.data?.topics || res.data?.topics || []
    generatedTopics.value = topics

    generateProgress.value = 100
    generateStatus.value = '生成完成！'
  } catch (e: any) {
    ElMessage.error(e.message || '生成失败，请重试')
    generateStatus.value = '生成失败'
  } finally {
    isGenerating.value = false
  }
}

// 学习AI生成的语法点
const learnAIGeneratedTopic = (topic: any) => {
  currentTopic.value = topic
  exerciseIndex.value = 0
  userAnswer.value = ''
  showResult.value = false
  showExerciseResult.value = false
  showAIGenerateDialog.value = false
  exerciseResults.length = 0

  if (topic.exercises?.length > 0) {
    currentExercise.value = topic.exercises[0]
  }
}

onMounted(() => {
  loadCategories()
  loadRecommendations()
})
</script>

<style scoped>
.grammar-page {
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

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 20px;
}

.subsection-title {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 16px;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 30px;
}

.category-card {
  padding: 20px;
  border: 2px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  text-align: center;
  transition: all 0.3s;
}

.category-card:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.category-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.category-count {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.topic-list {
  margin-top: 30px;
}

.topic-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.topic-card {
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.topic-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.topic-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.topic-desc {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
}

.topic-meta {
  display: flex;
  gap: 8px;
}

.learn-area {
  padding: 20px;
}

.learn-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.topic-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.explanation-section,
.examples-section,
.exercises-section {
  margin-bottom: 30px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.description {
  font-size: 16px;
  color: #606266;
  line-height: 1.8;
}

.formula {
  margin-top: 12px;
  padding: 12px;
  background: #fff;
  border-radius: 4px;
  font-size: 14px;
  color: #409eff;
}

.example-list {
  padding-left: 20px;
  margin: 0;
}

.example-list li {
  font-size: 15px;
  color: #303133;
  line-height: 2;
  margin-bottom: 8px;
}

.exercise-card {
  padding: 24px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.exercise-progress {
  font-size: 14px;
  color: #909399;
  margin-bottom: 16px;
}

.exercise-question {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 20px;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.options :deep(.el-radio) {
  padding: 12px 16px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.fill-blank,
.rewrite {
  margin-bottom: 20px;
}

.exercise-result {
  margin: 20px 0;
}

.result-explanation {
  margin-top: 12px;
  font-size: 14px;
  color: #606266;
}

.exercise-actions {
  margin-top: 20px;
}

.result-area {
  padding: 20px;
  text-align: center;
}

.result-summary {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin: 30px 0;
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

.result-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.loading {
  padding: 40px;
  text-align: center;
  color: #909399;
}

.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommend-card {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.recommend-card:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.rec-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.rec-category {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.rec-reason {
  font-size: 14px;
  color: #67c23a;
  margin-top: 8px;
}

/* AI生成对话框样式 */
.header-actions {
  display: flex;
  gap: 12px;
}

.generate-progress {
  margin: 20px 0;
  text-align: center;
}

.generate-progress .progress-text {
  margin-top: 10px;
  color: #606266;
  font-size: 14px;
}

.generated-preview {
  margin-top: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.generated-preview .preview-header {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 12px;
}

.generated-preview .topic-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px;
}

.generated-preview .topic-item {
  padding: 16px;
  background: #fff;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.generated-preview .topic-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: #409eff;
  transform: scaleY(0);
  transition: transform 0.3s ease;
}

.generated-preview .topic-item:hover {
  background: #f0f9ff;
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
  transform: translateY(-2px);
}

.generated-preview .topic-item:hover::before {
  transform: scaleY(1);
}

.generated-preview .topic-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.generated-preview .topic-desc {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.generated-preview .topic-meta {
  display: flex;
  gap: 8px;
}
</style>