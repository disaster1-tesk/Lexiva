<template>
  <div class="chat-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><ChatDotRound /></el-icon>
        AI 口语陪练
      </h1>
      <div class="scene-select">
        <el-select v-model="currentScene" placeholder="选择场景" @change="handleSceneChange">
          <el-option label="日常对话" value="daily" />
          <el-option label="旅行英语" value="travel" />
          <el-option label="商务英语" value="business" />
          <el-option label="学术讨论" value="academic" />
        </el-select>
      </div>
    </div>

    <!-- 对话区域 -->
    <div class="chat-container" ref="chatContainer">
      <div class="messages-wrapper">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <div class="welcome-avatar">
            <el-icon :size="48"><Service /></el-icon>
          </div>
          <div class="welcome-text">
            <h3>你好！我是你的 AI 英语陪练</h3>
            <p>我可以帮助你练习英语口语，纠正语法错误，提升表达水平。</p>
            <p>选择一个场景，让我们开始对话吧！</p>
          </div>
        </div>

        <!-- 消息列表 -->
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message-item"
          :class="{ 'is-user': msg.role === 'user', 'is-ai': msg.role === 'assistant' }"
        >
          <div class="message-avatar">
            <el-icon v-if="msg.role === 'user'" :size="24"><User /></el-icon>
            <el-icon v-else :size="24"><Service /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-bubble">
              <p v-html="formatMessage(msg.content)"></p>
              <!-- 语法纠错 -->
              <div v-if="msg.corrections && msg.corrections.length" class="corrections">
                <div class="correction-title">
                  <el-icon><Warning /></el-icon>
                  语法建议
                </div>
                <div v-for="(corr, i) in msg.corrections" :key="i" class="correction-item">
                  <span class="original">{{ corr.original }}</span>
                  <el-icon><Right /></el-icon>
                  <span class="corrected">{{ corr.corrected }}</span>
                </div>
              </div>
            </div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>

        <!-- 正在输入 -->
        <div v-if="isLoading" class="message-item is-ai">
          <div class="message-avatar">
            <el-icon :size="24"><Service /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-bubble loading">
              <div class="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-wrapper">
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="3"
          placeholder="用英语描述你想聊的话题..."
          @keydown.enter.ctrl="sendMessage"
          :disabled="isLoading"
        />
        <el-button
          type="primary"
          :loading="isLoading"
          @click="sendMessage"
          class="send-btn"
        >
          <el-icon><Promotion /></el-icon>
          发送
        </el-button>
      </div>
      <div class="input-tips">
        <span>提示：按 Ctrl + Enter 发送</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { chatApi } from '../api'
import { ChatDotRound, Service, User, Right, Warning, Promotion } from '@element-plus/icons-vue'

const messages = ref<Array<{
  role: string
  content: string
  time: string
  corrections?: Array<{ original: string; corrected: string }>
}>>([])

const userInput = ref('')
const isLoading = ref(false)
const currentScene = ref('daily')
const chatContainer = ref<HTMLElement | null>(null)

// 获取当前时间
const getCurrentTime = () => {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

// 格式化消息（简单的高亮处理）
const formatMessage = (content: string) => {
  return content.replace(/\n/g, '<br>')
}

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim()) {
    ElMessage.warning('请输入内容')
    return
  }
  if (isLoading.value) return

  const userMessage = userInput.value.trim()
  userInput.value = ''

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: userMessage,
    time: getCurrentTime()
  })

  isLoading.value = true
  scrollToBottom()

  try {
    const res = await chatApi.send(userMessage, currentScene.value)
    // 后端返回 reply 字段，兼容 response
    const replyText = res.data?.reply || res.data?.response || '抱歉，我理解你的意思了。'
    const corrections = res.data?.corrections || []
    
    // 添加AI回复
    messages.value.push({
      role: 'assistant',
      content: replyText,
      time: getCurrentTime(),
      corrections: corrections
    })
  } catch (error: any) {
    ElMessage.error('发送失败: ' + (error.message || '请稍后重试'))
    messages.value.push({
      role: 'assistant',
      content: '抱歉，发生了错误。请稍后重试。',
      time: getCurrentTime()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

// 切换场景
const handleSceneChange = (scene: string) => {
  currentScene.value = scene
  // 可以添加系统提示来切换场景
}

// 加载历史记录
onMounted(async () => {
  try {
    const res = await chatApi.getHistory()
    if (res.data && res.data.history) {
      messages.value = res.data.history.map((item: any) => ({
        role: item.role,
        content: item.content,
        time: item.time || getCurrentTime(),
        corrections: item.corrections || []
      }))
    }
  } catch (e) {
    console.log('无历史记录')
  }
})
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 140px);
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

.chat-container {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  overflow-y: auto;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.messages-wrapper {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.welcome-message {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7eb 100%);
  border-radius: 12px;
  margin-bottom: 20px;
}

.welcome-avatar {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.welcome-text h3 {
  font-size: 18px;
  color: #303133;
  margin-bottom: 8px;
}

.welcome-text p {
  font-size: 14px;
  color: #606266;
  margin-top: 4px;
}

.message-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.message-item.is-user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.is-user .message-avatar {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  color: #fff;
}

.is-ai .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.message-content {
  max-width: 70%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
}

.is-user .message-bubble {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  color: #fff;
}

.is-ai .message-bubble {
  background: #f5f7fa;
}

.message-bubble.loading {
  padding: 16px 24px;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #909399;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.is-user .message-time {
  text-align: right;
}

.corrections {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #dcdfe6;
}

.correction-title {
  font-size: 12px;
  color: #E6A23C;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
}

.correction-item {
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.correction-item .original {
  color: #F56C6C;
  text-decoration: line-through;
}

.correction-item .el-icon {
  color: #67C23A;
}

.correction-item .corrected {
  color: #67C23A;
  font-weight: 500;
}

.input-area {
  margin-top: 20px;
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper .el-textarea {
  flex: 1;
}

.send-btn {
  height: 80px;
  padding: 0 24px;
}

.input-tips {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  text-align: right;
}
</style>