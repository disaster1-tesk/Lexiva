<template>
  <div class="home-page">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-text">
        <h1>欢迎回来，Learner! 👋</h1>
        <p>今天也要继续加油学习英语哦～</p>
      </div>
      <div class="streak-badge">
        <el-icon><Sunrise /></el-icon>
        <span>连续学习 <strong>{{ stats.streakDays || 0 }}</strong> 天</span>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon :size="32"><Reading /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalWords }}</div>
            <div class="stat-label">累计单词</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card orange">
          <div class="stat-icon">
            <el-icon :size="32"><ChatDotRound /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalConversations }}</div>
            <div class="stat-label">AI 对话次数</div>
            <div class="stat-sub" v-if="stats.chatMinutes > 0">⏱ {{ stats.chatMinutes }} 分钟</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card green">
          <div class="stat-icon">
            <el-icon :size="32"><Edit /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalWritings }}</div>
            <div class="stat-label">写作练习</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card green">
          <div class="stat-icon">
            <el-icon :size="32"><Microphone /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.pronunciationScore > 0 ? Math.round(stats.pronunciationScore) + '分' : '--' }}</div>
            <div class="stat-label">发音评分</div>
            <div class="stat-sub" v-if="stats.totalPronunciations > 0">{{ stats.totalPronunciations }} 次练习</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <div class="quick-actions">
      <h2 class="section-title">快捷入口</h2>
      <el-row :gutter="16">
        <el-col :span="4" v-for="item in quickActions" :key="item.path">
          <div class="action-card" @click="router.push(item.path)">
            <div class="action-icon" :style="{ background: item.color }">
              <el-icon :size="28"><component :is="item.icon" /></el-icon>
            </div>
            <div class="action-label">{{ item.label }}</div>
            <div class="action-desc">{{ item.desc }}</div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 学习进度 -->
    <div class="progress-section">
      <h2 class="section-title">学习进度</h2>
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="page-card">
            <div class="progress-header">
              <span>今日目标</span>
              <el-tag type="success">进行中</el-tag>
            </div>
            <el-progress
              :percentage="70"
              :stroke-width="12"
              :color="'#409EFF'"
            />
            <div class="progress-detail">
              <span>已学习 7/10 个单词</span>
            </div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="page-card">
            <div class="progress-header">
              <span>本周目标</span>
              <el-tag type="warning">进行中</el-tag>
            </div>
            <el-progress
              :percentage="45"
              :stroke-width="12"
              :color="'#67C23A'"
            />
            <div class="progress-detail">
              <span>已学习 32/70 个单词</span>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 最近活动 -->
    <div class="recent-section">
      <h2 class="section-title">最近活动</h2>
      <div class="page-card">
        <el-timeline>
          <el-timeline-item
            v-for="(activity, index) in recentActivities"
            :key="index"
            :timestamp="activity.time"
            placement="top"
            :color="activity.color"
          >
            <el-card shadow="hover">
              <div class="activity-item">
                <el-icon :size="20" class="activity-icon">
                  <component :is="activity.icon" />
                </el-icon>
                <div class="activity-content">
                  <div class="activity-title">{{ activity.title }}</div>
                  <div class="activity-desc">{{ activity.desc }}</div>
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { statisticsApi } from '../api'
import {
  Reading, ChatDotRound, Edit, Microphone,
  Sunrise, Notebook, Headset, DataAnalysis
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

// 统计数据
const stats = ref({
  totalWords: 0,
  totalConversations: 0,
  totalWritings: 0,
  totalGrammar: 0,
  chatMinutes: 0,
  pronunciationScore: 0,
  totalPronunciations: 0,
  streakDays: 0
})

// 从路由动态获取所有模块作为快捷入口
const quickActions = computed(() => {
  const routes = router.getRoutes().filter(r => r.meta?.title && r.meta?.icon && r.path !== '/')
  return routes.map(r => ({
    path: r.path,
    label: r.meta.title || r.name,
    icon: r.meta.icon,
    color: r.meta.color || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    desc: r.meta.desc || ''
  }))
})

// 最近活动 - 从API获取
const recentActivities = ref<any[]>([])

// 格式化日期
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  return dateStr
}

// 转换后端活动数据为前端格式
const transformActivity = (activity: any) => {
  const colorMap: Record<string, string> = {
    chat: '#667eea',
    pronunciation: '#f5576c',
    writing: '#fa709a',
    word_reviewed: '#43e97b',
    word_added: '#4facfe',
    listening: '#00f2fe',
    grammar: '#a18cd1'
  }
  return {
    time: formatDate(activity.date),
    title: activity.title,
    desc: activity.description,
    icon: activity.icon,
    color: colorMap[activity.type] || '#409EFF'
  }
}

// 获取统计数据和活动记录
onMounted(async () => {
  try {
    // 获取统计数据
    const summaryRes = await statisticsApi.getSummary()
    const summaryData = summaryRes?.data?.data ?? summaryRes?.data ?? null
    if (summaryData) {
      stats.value = {
        totalWords: summaryData.total_words || 0,
        totalConversations: summaryData.total_conversations || 0,
        totalWritings: summaryData.total_writings || 0,
        totalGrammar: summaryData.total_grammar_learned || summaryData.total_grammar_exercises || 0,
        chatMinutes: summaryData.chat_minutes || 0,
        pronunciationScore: summaryData.pronunciation_avg_score || 0,
        totalPronunciations: summaryData.total_pronunciations || 0,
        streakDays: summaryData.streak_days || 0
      }
    }
    
    // 获取最近活动
    const activitiesRes = await statisticsApi.getActivities(7)
    const activitiesData = activitiesRes?.data?.data ?? activitiesRes?.data ?? []
    recentActivities.value = activitiesData.map(transformActivity).slice(0, 10)
  } catch (e) {
    console.log('获取数据失败，使用空数据', e)
    recentActivities.value = []
  }
})
</script>

<style scoped>
.home-page {
  padding: 0;
}

.welcome-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 30px;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.welcome-text h1 {
  font-size: 24px;
  margin-bottom: 8px;
}

.welcome-text p {
  font-size: 14px;
  opacity: 0.9;
}

.streak-badge {
  background: rgba(255,255,255,0.2);
  padding: 12px 20px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 16px;
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

.stat-card.purple {
  background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);
}

.stat-icon {
  width: 56px;
  height: 56px;
  background: rgba(255,255,255,0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
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

.stat-sub {
  font-size: 12px;
  opacity: 0.8;
  margin-top: 4px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.quick-actions {
  margin-bottom: 24px;
}

.action-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  border: 1px solid #f0f0f0;
}

.action-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 12px 32px rgba(0,0,0,0.12);
  border-color: transparent;
}

.action-card:active {
  transform: translateY(-4px) scale(0.98);
}

.action-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  color: #fff;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.action-card:hover .action-icon {
  transform: scale(1.15) rotate(5deg);
}

.action-label {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}

.action-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.progress-section {
  margin-bottom: 24px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: #606266;
}

.progress-detail {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.recent-section {
  margin-bottom: 24px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.activity-icon {
  color: #409EFF;
}

.activity-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.activity-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

:deep(.el-timeline-item__node) {
  background-color: #409EFF;
}
</style>