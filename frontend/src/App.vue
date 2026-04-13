<template>
  <el-container class="app-container">
    <!-- 左侧导航 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon :size="24"><Reading /></el-icon>
        <span>AI 英语学习</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        router
        :collapse="isCollapse"
      >
        <el-menu-item index="/home">
          <el-icon><House /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI 对话</span>
        </el-menu-item>
        <el-menu-item index="/pronunciation">
          <el-icon><Microphone /></el-icon>
          <span>发音评测</span>
        </el-menu-item>
        <el-menu-item index="/listening">
          <el-icon><Headset /></el-icon>
          <span>听力训练</span>
        </el-menu-item>
        <el-menu-item index="/vocabulary">
          <el-icon><Notebook /></el-icon>
          <span>单词本</span>
        </el-menu-item>
        <el-menu-item index="/dictation">
          <el-icon><EditPen /></el-icon>
          <span>单词默写</span>
        </el-menu-item>
        <el-menu-item index="/grammar">
          <el-icon><Reading /></el-icon>
          <span>语法学习</span>
        </el-menu-item>
        <el-menu-item index="/writing">
          <el-icon><Edit /></el-icon>
          <span>写作批改</span>
        </el-menu-item>
        <el-menu-item index="/stats">
          <el-icon><DataAnalysis /></el-icon>
          <span>学习中心</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧内容 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="toggleCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/home' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentRoute }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <el-tag type="info" effect="plain" class="ai-model-tag">
              <el-icon><Setting /></el-icon>
              {{ currentProvider }}
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-tag>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="/settings">
                  <el-icon><Setting /></el-icon>
                  AI 模型配置
                </el-dropdown-item>
                <el-dropdown-item command="/stats">
                  <el-icon><DataAnalysis /></el-icon>
                  学习统计
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-tag type="success" effect="dark">
            <el-icon><Timer /></el-icon>
            已连续学习 7 天
          </el-tag>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Reading, House, ChatDotRound, Microphone, Headset,
  Notebook, Edit, Fold, Expand, Timer, DataAnalysis, Setting, ArrowDown, EditPen
} from '@element-plus/icons-vue'
import { getAISettings } from '@/api/settings'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)
const currentProvider = ref('DeepSeek')

const loadProvider = async () => {
  try {
    const settings = await getAISettings()
    const names: Record<string, string> = {
      'deepseek': 'DeepSeek',
      'openai': 'OpenAI', 
      'ollama': 'Ollama'
    }
    currentProvider.value = names[settings.provider] || 'DeepSeek'
  } catch (e) {
    console.error('Failed to load provider:', e)
  }
}

const handleCommand = (command: string) => {
  router.push(command)
}

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

onMounted(() => {
  loadProvider()
})

const activeMenu = computed(() => route.path)

const currentRoute = computed(() => {
  const routeMap: Record<string, string> = {
    '/home': '首页',
    '/chat': 'AI 对话',
    '/pronunciation': '发音评测',
    '/listening': '听力训练',
    '/vocabulary': '单词本',
    '/dictation': '单词默写',
    '/grammar': '语法学习',
    '/writing': '写作批改',
    '/stats': '学习中心',
    '/settings': '设置'
  }
  return routeMap[route.path] || '首页'
})

</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.sidebar-menu {
  border-right: none;
  background: transparent;
}

:deep(.el-menu) {
  background: transparent;
}

:deep(.el-menu-item) {
  color: rgba(255,255,255,0.7);
  margin: 4px 8px;
  border-radius: 8px;
}

:deep(.el-menu-item:hover) {
  background: rgba(64, 158, 255, 0.2);
  color: #fff;
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #409EFF 0%, #66b1ff 100%);
  color: #fff;
}

.header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  font-size: 20px;
  color: #606266;
}

.collapse-btn:hover {
  color: #409EFF;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-model-tag {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>