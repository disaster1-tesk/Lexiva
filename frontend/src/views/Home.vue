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
        <span>连续学习 <strong>7</strong> 天</span>
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
        <div class="stat-card yellow">
          <div class="stat-icon">
            <el-icon :size="32"><Microphone /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalPractice }}</div>
            <div class="stat-label">发音练习</div>
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
              <el-icon :size="24"><component :is="item.icon" /></el-icon>
            </div>
            <div class="action-label">{{ item.label }}</div>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { statisticsApi } from '../api'
import {
  Reading, ChatDotRound, Edit, Microphone,
  Sunrise, Notebook, Headset
} from '@element-plus/icons-vue'

const router = useRouter()

// 统计数据
const stats = ref({
  totalWords: 156,
  totalConversations: 28,
  totalWritings: 12,
  totalPractice: 45
})

// 快捷入口
const quickActions = [
  { path: '/chat', label: 'AI 对话', icon: 'ChatDotRound', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { path: '/pronunciation', label: '发音评测', icon: 'Microphone', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { path: '/listening', label: '听力训练', icon: 'Headset', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { path: '/vocabulary', label: '单词本', icon: 'Notebook', color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' },
  { path: '/writing', label: '写作批改', icon: 'Edit', color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' }
]

// 最近活动
const recentActivities = [
  {
    time: '2024-01-15 14:30',
    title: '完成发音练习',
    desc: '练习了 "The quick brown fox" 句子',
    icon: 'Microphone',
    color: '#67C23A'
  },
  {
    time: '2024-01-15 10:00',
    title: '学习新单词',
    desc: '添加了 5 个新单词到单词本',
    icon: 'Notebook',
    color: '#409EFF'
  },
  {
    time: '2024-01-14 20:00',
    title: 'AI 对话练习',
    desc: '与 AI 进行了 15 分钟的英语对话',
    icon: 'ChatDotRound',
    color: '#E6A23C'
  },
  {
    time: '2024-01-14 16:00',
    title: '写作练习',
    desc: '提交了一篇 150 字的英语作文',
    icon: 'Edit',
    color: '#909399'
  }
]

// 获取统计数据
onMounted(async () => {
  try {
    const res = await statisticsApi.getSummary()
    if (res.data) {
      stats.value = {
        totalWords: res.data.total_words || 0,
        totalConversations: res.data.total_conversations || 0,
        totalWritings: res.data.total_writings || 0,
        totalPractice: res.data.total_pronunciation || 0
      }
    }
  } catch (e) {
    console.log('使用默认统计数据')
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
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
  color: #fff;
}

.action-label {
  font-size: 14px;
  color: #606266;
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