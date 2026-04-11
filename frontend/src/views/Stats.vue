<template>
  <div class="stats-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><DataAnalysis /></el-icon>
        学习中心
      </h1>
      <div class="header-actions">
        <el-radio-group v-model="timeRange" size="small" @change="loadData">
          <el-radio-button value="7">近7天</el-radio-button>
          <el-radio-button value="30">近30天</el-radio-button>
          <el-radio-button value="90">近90天</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 概览统计 -->
    <el-row :gutter="20" class="overview-row">
      <el-col :span="6">
        <div class="overview-card">
          <div class="overview-icon blue">
            <el-icon :size="28"><Reading /></el-icon>
          </div>
          <div class="overview-info">
            <div class="overview-value">{{ overview.totalWords }}</div>
            <div class="overview-label">累计单词</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="overview-card">
          <div class="overview-icon purple">
            <el-icon :size="28"><ChatDotRound /></el-icon>
          </div>
          <div class="overview-info">
            <div class="overview-value">{{ overview.totalConversations }}</div>
            <div class="overview-label">AI 对话</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="overview-card">
          <div class="overview-icon green">
            <el-icon :size="28"><Edit /></el-icon>
          </div>
          <div class="overview-info">
            <div class="overview-value">{{ overview.totalWritings }}</div>
            <div class="overview-label">写作练习</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="overview-card">
          <div class="overview-icon orange">
            <el-icon :size="28"><Trophy /></el-icon>
          </div>
          <div class="overview-info">
            <div class="overview-value">{{ overview.streakDays }}</div>
            <div class="overview-label">连续学习(天)</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="16">
        <div class="page-card chart-card">
          <div class="chart-header">
            <h3>学习趋势</h3>
          </div>
          <div class="chart-container" ref="trendChartRef"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="page-card chart-card">
          <div class="chart-header">
            <h3>学习分布</h3>
          </div>
          <div class="chart-container" ref="pieChartRef"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 详细数据 -->
    <el-row :gutter="20" class="detail-row">
      <el-col :span="12">
        <div class="page-card">
          <div class="detail-header">
            <h3>每日学习时长(分钟)</h3>
          </div>
          <div class="chart-container" ref="barChartRef"></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="page-card">
          <div class="detail-header">
            <h3>能力雷达图</h3>
          </div>
          <div class="chart-container" ref="radarChartRef"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 学习记录 -->
    <div class="page-card records-card">
      <div class="records-header">
        <h3>最近学习记录</h3>
        <el-button type="primary" size="small" @click="exportData">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
      </div>
      <el-table :data="learningRecords" stripe>
        <el-table-column prop="date" label="日期" width="180" />
        <el-table-column prop="type" label="学习类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.type)">{{ getTypeText(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="学习内容" min-width="200" />
        <el-table-column prop="duration" label="时长(分钟)" width="100" />
        <el-table-column prop="score" label="得分" width="100">
          <template #default="{ row }">
            <span v-if="row.score" :class="getScoreClass(row.score)">{{ row.score }}分</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { statisticsApi } from '../api'
import {
  DataAnalysis, Reading, ChatDotRound, Edit, Trophy, Download
} from '@element-plus/icons-vue'

// 时间范围
const timeRange = ref('7')

// 概览数据
const overview = ref({
  totalWords: 156,
  totalConversations: 28,
  totalWritings: 12,
  streakDays: 7
})

// 学习记录
const learningRecords = ref([
  { date: '2024-01-15 14:30', type: 'pronunciation', content: '发音练习 - The quick brown fox', duration: 15, score: 85 },
  { date: '2024-01-15 10:00', type: 'vocabulary', content: '添加新单词 5 个', duration: 10, score: null },
  { date: '2024-01-14 20:00', type: 'chat', content: 'AI 对话 - 日常英语', duration: 20, score: null },
  { date: '2024-01-14 16:00', type: 'writing', content: '写作练习 - 议论文', duration: 25, score: 78 },
  { date: '2024-01-14 14:00', type: 'listening', content: '听力训练 - 听写模式', duration: 15, score: 92 }
])

// 图表引用
const trendChartRef = ref<HTMLElement | null>(null)
const pieChartRef = ref<HTMLElement | null>(null)
const barChartRef = ref<HTMLElement | null>(null)
const radarChartRef = ref<HTMLElement | null>(null)

let trendChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null
let barChart: echarts.ECharts | null = null
let radarChart: echarts.ECharts | null = null

// 加载数据
const loadData = async () => {
  try {
    const res = await statisticsApi.getTrend(parseInt(timeRange.value))
    if (res.data) {
      updateCharts(res.data)
    }
  } catch (e) {
    // 使用默认数据
    updateCharts(getDefaultData())
  }
}

// 默认数据
const getDefaultData = () => {
  const days = parseInt(timeRange.value)
  const dates = []
  const words = []
  const conversations = []
  const writings = []
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(`${date.getMonth() + 1}-${date.getDate()}`)
    words.push(Math.floor(Math.random() * 10) + 5)
    conversations.push(Math.floor(Math.random() * 3) + 1)
    writings.push(Math.floor(Math.random() * 2))
  }
  
  return { dates, words, conversations, writings }
}

// 更新图表
const updateCharts = (data: any) => {
  nextTick(() => {
    initTrendChart(data)
    initPieChart()
    initBarChart(data)
    initRadarChart()
  })
}

// 初始化趋势图
const initTrendChart = (data: any) => {
  if (!trendChartRef.value) return

  // 安全获取数据
  const safeData = data || { dates: [], words: [], conversations: [], writings: [] }

  if (trendChart) {
    trendChart.dispose()
  }

  trendChart = echarts.init(trendChartRef.value)
  trendChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['单词', '对话', '写作']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: safeData.dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '单词',
        type: 'line',
        smooth: true,
        data: safeData.words,
        itemStyle: { color: '#409EFF' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      },
      {
        name: '对话',
        type: 'line',
        smooth: true,
        data: safeData.conversations,
        itemStyle: { color: '#67C23A' }
      },
      {
        name: '写作',
        type: 'line',
        smooth: true,
        data: safeData.writings,
        itemStyle: { color: '#E6A23C' }
      }
    ]
  })
}

// 初始化饼图
const initPieChart = () => {
  if (!pieChartRef.value) return
  
  if (pieChart) {
    pieChart.dispose()
  }
  
  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '学习分布',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: [
          { value: 45, name: '单词学习', itemStyle: { color: '#409EFF' } },
          { value: 25, name: '口语对话', itemStyle: { color: '#67C23A' } },
          { value: 15, name: '写作练习', itemStyle: { color: '#E6A23C' } },
          { value: 10, name: '听力训练', itemStyle: { color: '#F56C6C' } },
          { value: 5, name: '发音评测', itemStyle: { color: '#909399' } }
        ]
      }
    ]
  })
}

// 初始化柱状图
const initBarChart = (data: any) => {
  if (!barChartRef.value) return
  
  if (barChart) {
    barChart.dispose()
  }

  // 安全获取日期数据
  const dates = data?.dates || []
  const durations = dates.map(() => Math.floor(Math.random() * 60) + 10)
  
  barChart = echarts.init(barChartRef.value)
  barChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.dates,
      axisLabel: { rotate: 45 }
    },
    yAxis: {
      type: 'value',
      name: '分钟'
    },
    series: [
      {
        name: '学习时长',
        type: 'bar',
        barWidth: '60%',
        data: durations,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ]),
          borderRadius: [5, 5, 0, 0]
        }
      }
    ]
  })
}

// 初始化雷达图
const initRadarChart = () => {
  if (!radarChartRef.value) return
  
  if (radarChart) {
    radarChart.dispose()
  }
  
  radarChart = echarts.init(radarChartRef.value)
  radarChart.setOption({
    tooltip: {},
    radar: {
      indicator: [
        { name: '词汇量', max: 100 },
        { name: '听力', max: 100 },
        { name: '口语', max: 100 },
        { name: '阅读', max: 100 },
        { name: '写作', max: 100 }
      ],
      radius: '60%'
    },
    series: [
      {
        name: '能力分布',
        type: 'radar',
        data: [
          {
            value: [75, 82, 68, 90, 72],
            name: '当前能力',
            itemStyle: { color: '#409EFF' },
            areaStyle: { color: 'rgba(64, 158, 255, 0.3)' }
          },
          {
            value: [85, 75, 80, 85, 78],
            name: '目标能力',
            itemStyle: { color: '#67C23A' },
            areaStyle: { color: 'rgba(103, 194, 58, 0.2)' }
          }
        ]
      }
    ]
  })
}

// 获取类型标签
const getTypeTag = (type: string) => {
  const map: Record<string, string> = {
    'vocabulary': 'success',
    'chat': 'primary',
    'writing': 'warning',
    'listening': 'danger',
    'pronunciation': 'info'
  }
  return map[type] || 'info'
}

// 获取类型文本
const getTypeText = (type: string) => {
  const map: Record<string, string> = {
    'vocabulary': '单词学习',
    'chat': 'AI 对话',
    'writing': '写作练习',
    'listening': '听力训练',
    'pronunciation': '发音评测'
  }
  return map[type] || type
}

// 获取分数样式
const getScoreClass = (score: number) => {
  if (score >= 90) return 'score-high'
  if (score >= 75) return 'score-mid'
  return 'score-low'
}

// 导出数据
const exportData = () => {
  const report = `
AI 英语学习系统 - 学习报告
============================
报告周期: 近${timeRange.value}天

累计单词: ${overview.value.totalWords}
AI 对话: ${overview.value.totalConversations}次
写作练习: ${overview.value.totalWritings}次
连续学习: ${overview.value.streakDays}天

最近学习记录:
${learningRecords.value.map(r => `${r.date} - ${getTypeText(r.type)} - ${r.content}`).join('\n')}
  `.trim()
  
  navigator.clipboard.writeText(report).then(() => {
    ElMessage.success('报告已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('导出失败')
  })
}

// 窗口大小变化时重新调整图表
const handleResize = () => {
  trendChart?.resize()
  pieChart?.resize()
  barChart?.resize()
  radarChart?.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
  radarChart?.dispose()
})
</script>

<style scoped>
.stats-page {
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

.overview-row {
  margin-bottom: 20px;
}

.overview-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.overview-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.overview-icon.blue {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.overview-icon.purple {
  background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);
}

.overview-icon.green {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
}

.overview-icon.orange {
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
}

.overview-info {
  flex: 1;
}

.overview-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.overview-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  height: 350px;
}

.chart-header,
.detail-header {
  margin-bottom: 16px;
}

.chart-header h3,
.detail-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chart-container {
  height: 280px;
}

.detail-row {
  margin-bottom: 20px;
}

.records-card {
  margin-top: 20px;
}

.records-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.records-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.score-high {
  color: #67C23A;
  font-weight: 600;
}

.score-mid {
  color: #409EFF;
  font-weight: 500;
}

.score-low {
  color: #E6A23C;
}
</style>