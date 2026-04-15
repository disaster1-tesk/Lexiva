<template>
  <div class="chat-page">
    <!-- 通话模式：全屏面板 -->
    <PhoneCallPanel 
      v-if="currentMode === 'phone'" 
      @exit="currentMode = 'chat'"
      @end="handleCallEnd"
    />

    <!-- 聊天模式 -->
    <template v-else>
      <div class="page-header">
        <h1 class="page-title">
          <el-icon><ChatDotRound /></el-icon>
          AI 口语陪练
        </h1>
        
        <!-- 模式切换 Tab -->
        <div class="mode-switch">
          <el-radio-group v-model="currentMode" @change="handleModeChange">
            <el-radio-button value="chat">
              <el-icon><ChatDotRound /></el-icon>
              聊天模式
            </el-radio-button>
            <el-radio-button value="phone">
              <el-icon><Phone /></el-icon>
              通话模式
            </el-radio-button>
          </el-radio-group>
        </div>

      </div>

      <!-- 对话区域 -->
      <div class="chat-container" ref="chatContainer">
      <div class="messages-wrapper">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <!-- 动态背景 -->
          <div class="welcome-bg">
            <div class="bg-grid"></div>
            <div class="bg-glow bg-glow-1"></div>
            <div class="bg-glow bg-glow-2"></div>
            <div class="bg-glow bg-glow-3"></div>
          </div>
          
          <div class="welcome-content">
            <div class="welcome-avatar">
              <div class="avatar-ring"></div>
              <div class="avatar-ring avatar-ring-2"></div>
              <el-icon :size="56"><Service /></el-icon>
              <!-- 头像光晕动画 -->
              <div class="avatar-pulse"></div>
            </div>
            <div class="welcome-text">
              <h3>
                <span class="title-highlight">AI 口语陪练</span>
              </h3>
              <p class="welcome-desc">随时随地练习英语，与 AI 进行自然的对话交流</p>
              <div class="feature-tags">
                <span class="feature-tag">
                  <el-icon><ChatDotRound /></el-icon>
                  智能对话
                </span>
                <span class="feature-tag">
                  <el-icon><Microphone /></el-icon>
                  语音输入
                </span>
                <span class="feature-tag">
                  <el-icon><Warning /></el-icon>
                  语法纠错
                </span>
              </div>
              <p class="welcome-tip">选择一个场景，让我们开始对话吧！</p>
              <p v-if="isRealtimeMode" class="welcome-voice-tip">
                <el-icon><Microphone /></el-icon>
                按住 🎤 按钮用语音说话
              </p>
            </div>
          </div>
          
          <!-- 场景选择卡片 -->
          <div class="scene-cards">
            <div 
              v-for="(item, key) in sceneCards" 
              :key="key"
              class="scene-card"
              :class="{ active: currentScene === key }"
              @click="handleSceneChange(key)"
            >
              <el-icon :size="24"><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <TransitionGroup name="message" tag="div" class="messages-list">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="message-item"
            :class="{ 'is-user': msg.role === 'user', 'is-ai': msg.role === 'assistant' }"
          >
            <div class="message-avatar">
              <div class="avatar-inner">
                <el-icon v-if="msg.role === 'user'" :size="20"><User /></el-icon>
                <el-icon v-else :size="20"><Service /></el-icon>
              </div>
            </div>
            <div class="message-content">
              <div class="message-bubble">
                <!-- 显示语音识别的文字（如果是语音输入） -->
                <div v-if="msg.recognizedText" class="recognized-text">
                  <el-icon><Microphone /></el-icon>
                  <span>{{ msg.recognizedText }}</span>
                </div>
                <!-- 流式输出时显示逐字打字效果，完成后显示 Markdown 格式 -->
                <p v-if="msg.isStreaming" class="streaming-content">
                  {{ getDisplayContent(msg) }}<span class="typing-cursor"></span>
                </p>
                <p v-else v-html="formatMessage(msg.content)"></p>
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
              <!-- 消息操作按钮 -->
              <div class="message-actions">
                <el-button v-if="msg.role === 'assistant'" link size="small" @click="copyMessage(msg.content)">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
                <!-- AI回复的语音播放按钮 -->
                <el-button 
                  v-if="msg.role === 'assistant' && msg.audio" 
                  link 
                  size="small" 
                  @click="playAudio(msg)"
                  :disabled="isPlayingAudio && playingMsgIndex === index"
                >
                  <el-icon><VideoPlay /></el-icon>
                  {{ isPlayingAudio && playingMsgIndex === index ? '播放中' : '播放语音' }}
                </el-button>
              </div>
              <div class="message-time">{{ msg.time }}</div>
            </div>
          </div>
        </TransitionGroup>

        <!-- 正在输入 -->
        <div v-if="isLoading" class="message-item is-ai">
          <div class="message-avatar">
            <el-icon :size="24"><Service /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-bubble loading">
              <span class="loading-text">AI 正在输入</span>
              <div class="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

        <!-- 快捷回复建议 -->
      <div v-if="quickReplies.length > 0" class="quick-replies">
        <span class="quick-replies-label">试试这些：</span>
        <div class="quick-replies-list">
          <el-button 
            v-for="reply in quickReplies" 
            :key="reply"
            size="small" 
            @click="userInput = reply"
          >
            {{ reply }}
          </el-button>
        </div>
      </div>
      </div>

      <div class="input-wrapper">
        <!-- 输入框区域 -->
        <div class="input-area">
          <el-input
            v-model="userInput"
            type="textarea"
            :rows="3"
            placeholder="用英语描述你想聊的话题..."
            @keydown.enter.ctrl="sendMessage"
            :disabled="isLoading || isRecording"
          />
        </div>
        
        <!-- 语音输入按钮 -->
        <div 
          class="voice-btn"
          :class="{ 'recording': isRecording }"
          @mousedown="startRecording"
          @mouseup="stopRecording"
          @mouseleave="cancelRecording"
          @touchstart.prevent="startRecording"
          @touchend.prevent="stopRecording"
          @touchcancel="cancelRecording"
          :disabled="isLoading"
        >
          <div class="voice-btn-icon">
            <el-icon :size="22"><Microphone /></el-icon>
            <div v-if="isRecording" class="recording-ring"></div>
          </div>
          <span class="voice-btn-text">{{ isRecording ? '松开发送' : '按住说话' }}</span>
          <!-- 录音动画 -->
          <div v-if="isRecording" class="recording-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
        
        <el-button
          type="primary"
          :loading="isLoading"
          @click="sendMessage"
          class="send-btn"
        >
          <el-icon><Promotion /></el-icon>
          <span>发送</span>
        </el-button>
      </div>
      <div class="input-tips">
        <span v-if="isRealtimeMode">
          <el-icon><Microphone /></el-icon>
          按住 🎤 说话 | Ctrl + Enter 发送
        </span>
        <span v-else>
          <el-icon><Promotion /></el-icon>
          Ctrl + Enter 发送
        </span>
      </div>
    </template>

    <div class="phone-only-area" v-if="currentMode === 'phone'">
      <!-- phone 模式专用区域，可放置通话控制按钮等 -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { chatApi } from '../api'
import { ChatDotRound, Service, User, Right, Warning, Promotion, CopyDocument, Microphone, VideoPlay, Phone, Sunrise, Suitcase, Briefcase, Notebook } from '@element-plus/icons-vue'
import PhoneCallPanel from './PhoneCallPanel.vue'

// 场景卡片配置
const sceneCards = {
  daily: { label: '日常对话', icon: 'ChatDotRound' },
  travel: { label: '旅行英语', icon: 'Suitcase' },
  business: { label: '商务英语', icon: 'Briefcase' },
  academic: { label: '学术讨论', icon: 'Notebook' }
}

const router = useRouter()

// 当前模式：chat 或 phone
const currentMode = ref<'chat' | 'phone'>('chat')

const messages = ref<Array<{
  role: string
  content: string
  time: string
  corrections?: Array<{ original: string; corrected: string }>
  recognizedText?: string  // 语音识别结果
  audio?: string  // AI回复的语音base64
}>>([])

const userInput = ref('')
const isLoading = ref(false)
const isStreaming = ref(false)  // 是否正在流式输出
const currentScene = ref('daily')
const chatContainer = ref<HTMLElement | null>(null)

// ===== 语音输入相关 =====
const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const audioChunks = ref<Blob[]>([])
const currentMimeType = ref('audio/webm')  // 当前录音格式
const recordingStartTime = ref<number>(0)  // 录音开始时间
let audioStream: MediaStream | null = null

// ===== 语音播放相关 =====
const isPlayingAudio = ref(false)
const playingMsgIndex = ref<number | null>(null)
let currentAudio: HTMLAudioElement | null = null

// ===== 实时语音模式 =====
const isRealtimeMode = ref(false)
let websocket: WebSocket | null = null
const interimText = ref('')  // 实时识别中间结果

// ===== 流式输出控制 =====
const displayContents = ref<Record<number, string>>({})  // 每个消息的显示内容
let typingTimer: number | null = null
let charIndexMap: Record<number, number> = {}  // 每个消息当前的字符索引
const TYPING_SPEED = 25  // 每个字符间隔(ms)，越小越快
const PAUSE_PUNCTUATION = ['.', ',', '!', '?', '。', '，', '！', '？', ';', '：']  // 停顿标点
const PAUSE_DELAY = 180  // 标点处停顿时间(ms)
const LONG_PAUSE_PUNCTUATION = ['.', '!', '?', '。', '！', '？']  // 长停顿标点
const LONG_PAUSE_DELAY = 300  // 长停顿时间(ms)

// 获取当前应该显示的内容（逐字打字效果）
const getDisplayContent = (msg: any) => {
  const index = messages.value.indexOf(msg)
  if (index === -1) return msg.content
  return displayContents.value[index] || ''
}

// 清空指定消息的显示内容
const clearDisplayContent = (index: number) => {
  delete displayContents.value[index]
}

// 流式打字效果函数 - 逐字符显示，模拟真实打字
const typeWriterEffect = (fullContent: string, msgIndex: number, startFrom: number = 0) => {
  // 如果是第一次开始，初始化字符索引
  if (charIndexMap[msgIndex] === undefined) {
    charIndexMap[msgIndex] = startFrom
  }
  
  let charIndex = charIndexMap[msgIndex]
  let isPaused = false
  let pauseEndTime = 0
  
  const typeChar = () => {
    // 如果已暂停，等待
    if (isPaused && Date.now() < pauseEndTime) {
      typingTimer = window.setTimeout(typeChar, 20)
      return
    }
    isPaused = false
    
    // 显示到当前字符
    const currentDisplay = fullContent.slice(0, charIndex + 1)
    displayContents.value[msgIndex] = currentDisplay
    
    charIndex++
    charIndexMap[msgIndex] = charIndex  // 保存当前索引
    
    // 检查是否完成
    if (charIndex >= fullContent.length) {
      // 打字完成，清除定时器
      if (typingTimer) {
        clearTimeout(typingTimer)
        typingTimer = null
      }
      delete charIndexMap[msgIndex]
      return
    }
    
    // 检查当前字符是否为需要停顿的标点
    const currentChar = fullContent[charIndex]
    if (PAUSE_PUNCTUATION.includes(currentChar)) {
      isPaused = true
      // 长句末标点停顿更久
      if (LONG_PAUSE_PUNCTUATION.includes(currentChar)) {
        pauseEndTime = Date.now() + LONG_PAUSE_DELAY
      } else {
        pauseEndTime = Date.now() + PAUSE_DELAY
      }
    }
    
    // 继续打字
    typingTimer = window.setTimeout(typeChar, TYPING_SPEED)
  }
  
  // 开始打字
  typeChar()
}

// 停止打字效果
const stopTypeWriter = () => {
  if (typingTimer) {
    clearTimeout(typingTimer)
    typingTimer = null
  }
}

// 处理模式切换 (Tab 切换)
const handleModeChange = (mode: string) => {
  if (mode === 'phone') {
    // 切换到通话模式
    currentMode.value = 'phone'
  } else {
    // 切换到聊天模式
    currentMode.value = 'chat'
  }
}

// 处理通话结束
const handleCallEnd = (data: { duration: number; messages: number }) => {
  console.log('通话结束:', data)
  currentMode.value = 'chat'
}

// 处理实时语音模式切换 (原有功能)
const handleRealtimeModeChange = (enabled: boolean) => {
  if (enabled) {
    connectWebSocket()
  } else {
    disconnectWebSocket()
  }
}

// 连接WebSocket
const connectWebSocket = () => {
  try {
    websocket = chatApi.createRealtimeChat()
    
    websocket.onopen = () => {
      console.log('WebSocket connected')
      // 发送初始化消息
      websocket?.send(JSON.stringify({
        type: 'init',
        client_id: `user_${Date.now()}`
      }))
      ElMessage.success('实时语音模式已开启')
    }
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleRealtimeMessage(data)
    }
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      ElMessage.error('实时语音连接失败')
    }
    
    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      if (isRealtimeMode.value) {
        ElMessage.warning('实时语音连接已断开')
      }
    }
  } catch (error) {
    console.error('Failed to create WebSocket:', error)
    ElMessage.error('无法建立实时语音连接')
  }
}

// 处理WebSocket消息
const handleRealtimeMessage = (data: any) => {
  if (data.type === 'connected') {
    // 连接成功
    return
  }
  
  if (data.type === 'interim') {
    // 实时识别中间结果
    interimText.value = data.recognized_text || ''
    return
  }
  
  if (data.type === 'text') {
    // AI完整回复
    interimText.value = ''
    
    // 添加用户消息（显示识别的文字）
    if (data.recognized_text) {
      messages.value.push({
        role: 'user',
        content: data.recognized_text,
        time: getCurrentTime(),
        recognizedText: data.recognized_text,
        corrections: []
      })
    }
    
    // 添加AI回复
    messages.value.push({
      role: 'assistant',
      content: data.reply || '抱歉，我理解你的意思了。',
      time: getCurrentTime(),
      corrections: data.corrections || [],
      audio: data.audio
    })
    
    // 如果有语音，自动播放
    if (data.audio) {
      playAudioByIndex(messages.value.length - 1, data.audio)
    }
    
    scrollToBottom()
  }
  
  if (data.type === 'error') {
    ElMessage.error(data.message || '发生错误')
  }
}

// 断开WebSocket
const disconnectWebSocket = () => {
  if (websocket) {
    websocket.close()
    websocket = null
  }
  interimText.value = ''
  ElMessage.info('已切换到普通模式')
}

// 在实时模式下发送音频流
const sendAudioStream = (audioData: string, isFinal: boolean = false) => {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({
      type: 'audio',
      data: audioData,
      is_final: isFinal,
      scene: currentScene.value
    }))
  }
}

// 获取当前时间
const getCurrentTime = () => {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

// 格式化消息（支持粗体、斜体、代码高亮）
const formatMessage = (content: string) => {
  if (!content) return ''
  
  let formatted = content
    // 转义HTML防止XSS
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // 换行
    .replace(/\n/g, '<br>')
    // **粗体**
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // *斜体*
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // `代码`
    .replace(/`(.+?)`/g, '<code class="inline-code">$1</code>')
    // 标题 ### -> h3, ## -> h2, # -> h1
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // 引用块
    .replace(/^&gt;\s*(.+)$/gm, '<blockquote>$1</blockquote>')
    // 列表
    .replace(/^-\s+(.+)$/gm, '<li>$1</li>')
    // 数字列表
    .replace(/^\d+\.\s+(.+)$/gm, '<li class="numbered">$1</li>')
  
  // 包裹连续的列表项为 ul（处理多行列表）
  formatted = formatted.replace(/(<li>.*?<\/li>)+/gs, '<ul>$&</ul>')
  
  return formatted
}

// 复制消息
const copyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 发送消息 - 使用流式 API
const sendMessage = async () => {
  if (!userInput.value.trim()) {
    ElMessage.warning('请输入内容')
    return
  }
  if (isLoading.value) return

  const userMessage = userInput.value.trim()
  userInput.value = ''

  // 添加用户消息
  const userMsg = {
    role: 'user',
    content: userMessage,
    time: getCurrentTime()
  }
  messages.value.push(userMsg)

  // 创建 AI 消息占位符（用于流式显示）
  const aiMsg = {
    role: 'assistant',
    content: '',
    time: getCurrentTime(),
    corrections: [],
    isStreaming: true  // 标记为流式输出中
  }
  const aiMsgIndex = messages.value.length  // 记录 AI 消息的索引
  messages.value.push(aiMsg)

  isLoading.value = true
  isStreaming.value = true
  scrollToBottom()

  try {
    const response = await chatApi.streamSend(userMessage, currentScene.value)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法读取响应')
    }

    const decoder = new TextDecoder()
    let fullContent = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue

          try {
            const parsed = JSON.parse(data)
            if (parsed.chunk) {
              fullContent += parsed.chunk
              // 更新完整内容用于最终渲染
              messages.value[aiMsgIndex].content = fullContent
              
              // 实时显示流式内容 - 立即更新显示内容，不等待
              if (!displayContents.value[aiMsgIndex]) {
                displayContents.value[aiMsgIndex] = ''
              }
              
              // 同时启动打字机效果，逐字符显示（但跳过已显示的字符）
              // 如果打字机未启动，从当前索引开始
              if (!typingTimer || !charIndexMap[aiMsgIndex]) {
                // 启动新的打字机效果
                const currentLen = displayContents.value[aiMsgIndex].length
                if (currentLen < fullContent.length) {
                  typeWriterEffect(fullContent, aiMsgIndex, currentLen)
                }
              }
              // 如果已有内容，直接追加显示（更接近实时流式效果）
              displayContents.value[aiMsgIndex] = fullContent
              
              scrollToBottom()
            }
            if (parsed.done && parsed.reply) {
              // 流式输出完成，更新为完整内容
              fullContent = parsed.reply
              messages.value[aiMsgIndex].content = fullContent
              displayContents.value[aiMsgIndex] = fullContent
              messages.value[aiMsgIndex].corrections = parsed.corrections || []
              
              // 停止打字机效果
              stopTypeWriter()
              
              // 标记流式输出完成，触发 Markdown 渲染
              messages.value[aiMsgIndex].isStreaming = false
              isStreaming.value = false
              
              scrollToBottom()
            }
          } catch (e) {
            // 忽略解析错误，继续处理下一行
          }
        }
      }
    }
  } catch (error: any) {
    ElMessage.error('发送失败: ' + (error.message || '请稍后重试'))
    messages.value[aiMsgIndex].content = '抱歉，发生了错误。请稍后重试。'
    messages.value[aiMsgIndex].isStreaming = false  // 错误时也标记为完成
    isStreaming.value = false
    stopTypeWriter()  // 停止打字机效果
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
  quickReplies.value = quickRepliesMap[scene] || []
}

// 跳转到电话模式（已整合到页面内，通过 Tab 切换）
const goToPhoneCall = () => {
  currentMode.value = 'phone'
}

// ===== 语音输入功能 =====
const startRecording = async () => {
  if (isLoading.value || isRecording.value) return
  
  try {
    // 先静默检查麦克风设备是否存在，避免直接弹出权限提示
    const devices = await navigator.mediaDevices.enumerateDevices()
    const hasMicrophone = devices.some(device => device.kind === 'audioinput')
    
    if (!hasMicrophone) {
      ElMessage.error('未找到麦克风设备，请确保已连接麦克风')
      return
    }
    
    // 请求麦克风权限
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    
    // 固定使用 WebM 格式（所有浏览器都支持）
    let mimeType = 'audio/webm'
    currentMimeType.value = mimeType  // 保存当前使用的格式
    
    mediaRecorder.value = new MediaRecorder(audioStream, { mimeType })
    
    // 验证 MediaRecorder 初始化是否成功
    if (!mediaRecorder.value || mediaRecorder.value.state === 'inactive') {
      throw new Error('MediaRecorder 初始化失败')
    }
    
    audioChunks.value = []
    
    mediaRecorder.value.ondataavailable = (e) => {
      if (e.data.size > 0) {
        audioChunks.value.push(e.data)
        
        // 实时模式：发送音频块
        if (isRealtimeMode.value && websocket && websocket.readyState === WebSocket.OPEN) {
          const reader = new FileReader()
          reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1]
            sendAudioStream(base64, false)
          }
          reader.readAsDataURL(e.data)
        }
      }
    }
    
    mediaRecorder.value.start(300) // 每300ms发送一次
    recordingStartTime.value = Date.now()
    isRecording.value = true
    interimText.value = ''
    ElMessage.info(isRealtimeMode.value ? '开始实时对话，请说话...' : '开始录音，请说话...')
  } catch (error: any) {
    isRecording.value = false
    console.error('录音失败:', error)
    // 区分不同错误类型
    if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
      ElMessage.error('麦克风权限被拒绝，请点击浏览器地址栏左侧的锁定图标允许访问')
    } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
      ElMessage.error('未找到麦克风设备，请确保已连接麦克风')
    } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
      ElMessage.error('麦克风已被其他应用占用，请关闭其他录音应用')
    } else {
      ElMessage.error('无法访问麦克风，请检查系统权限设置')
    }
  }
}

const stopRecording = () => {
  if (!isRecording.value || !mediaRecorder.value) return
  
  // 停止录音
  mediaRecorder.value.stop()
  isRecording.value = false
  
  // 停止音频流
  if (audioStream) {
    audioStream.getTracks().forEach(track => track.stop())
    audioStream = null
  }
  
  if (isRealtimeMode.value) {
    // 实时模式：发送结束标记
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'audio',
        data: '',
        is_final: true,
        scene: currentScene.value
      }))
    }
    return
  }
  
  // 非实时模式：等待录音数据完全收集
  mediaRecorder.value.onstop = async () => {
    // 检查录音时长
    const recordingDuration = Date.now() - recordingStartTime.value
    if (recordingDuration < 500) {
      isRecording.value = false
      ElMessage.warning('录音时间太短，请确保完整录音后重试')
      return
    }
    
    if (audioChunks.value.length === 0) {
      isRecording.value = false
      ElMessage.warning('录音为空，请重试')
      return
    }
    
    // 检测录音格式并设置对应的 Blob 类型
    const blobType = currentMimeType.value.includes('mp4') ? 'audio/mp4' : 'audio/webm'
    const audioBlob = new Blob(audioChunks.value, { type: blobType })
    
    // 发送语音对话请求
    await sendVoiceMessage(audioBlob, currentMimeType.value)
    
    // 清理录音数据
    audioChunks.value = []
  }
}

const cancelRecording = () => {
  if (!isRecording.value) return
  
  // 停止录音但不发送
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
  }
  isRecording.value = false
  
  // 停止音频流
  if (audioStream) {
    audioStream.getTracks().forEach(track => track.stop())
    audioStream = null
  }
  
  audioChunks.value = []
  ElMessage.info('已取消录音')
}

// 发送语音消息
const sendVoiceMessage = async (audioBlob: Blob, mimeType: string = 'audio/webm') => {
  if (isLoading.value) return
  
  isLoading.value = true
  scrollToBottom()
  
  try {
    const res = await chatApi.voiceChat(audioBlob, currentScene.value, mimeType)
    const data = res.data
    
    // 添加用户消息（显示识别的文字）
    messages.value.push({
      role: 'user',
      content: data.recognized_text || '[语音消息]',
      time: getCurrentTime(),
      recognizedText: data.recognized_text,
      corrections: []
    })
    
    // 添加AI回复（包含语音）
    messages.value.push({
      role: 'assistant',
      content: data.reply || '抱歉，我理解你的意思了。',
      time: getCurrentTime(),
      corrections: data.corrections || [],
      audio: data.audio  // 保存语音数据
    })
    
    // 如果有语音，自动播放
    if (data.audio) {
      const msgIndex = messages.value.length - 1
      playAudioByIndex(msgIndex, data.audio)
    }
  } catch (error: any) {
    console.error('语音对话失败:', error)
    isRecording.value = false
    
    // 提取错误信息，根据不同错误类型显示友好提示
    const errMsg = error.response?.data?.detail || error.message || ''
    let userHint = '请检查麦克风权限后重试'
    
    if (errMsg.includes('录音太短')) {
      userHint = '录音时间太短，请确保完整录音后松开麦克风'
    } else if (errMsg.includes('未能识别语音')) {
      userHint = '未检测到清晰语音，请再说一次'
    } else if (errMsg.includes('音频格式转换失败') || errMsg.includes('音频文件已损坏')) {
      userHint = '音频文件损坏，请重新录制'
    } else if (errMsg.includes('语音对话失败')) {
      userHint = '对话暂时失败，请稍后重试'
    }
    
    ElMessage.error('语音识别失败: ' + userHint)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，语音对话失败了。请稍后重试。',
      time: getCurrentTime()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// ===== 语音播放功能 =====
const playAudioByIndex = (index: number, audioBase64?: string) => {
  const msg = messages.value[index]
  const audioData = audioBase64 || msg.audio
  
  if (!audioData) return
  
  // 停止当前播放
  stopAudio()
  
  // 解码并播放
  const byteCharacters = atob(audioData)
  const byteNumbers = new Array(byteCharacters.length)
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  const byteArray = new Uint8Array(byteNumbers)
  const audioBlob = new Blob([byteArray], { type: 'audio/webm' })
  const audioUrl = URL.createObjectURL(audioBlob)
  
  currentAudio = new Audio(audioUrl)
  playingMsgIndex.value = index
  isPlayingAudio.value = true
  
  currentAudio.onended = () => {
    isPlayingAudio.value = false
    playingMsgIndex.value = null
    URL.revokeObjectURL(audioUrl)
  }
  
  currentAudio.onerror = () => {
    isPlayingAudio.value = false
    playingMsgIndex.value = null
    ElMessage.error('音频播放失败')
    URL.revokeObjectURL(audioUrl)
  }
  
  currentAudio.play().catch(err => {
    console.error('播放失败:', err)
    ElMessage.error('音频播放失败')
    isPlayingAudio.value = false
    playingMsgIndex.value = null
  })
}

const playAudio = (msg: any) => {
  // 找到消息的索引
  const index = messages.value.indexOf(msg)
  if (index !== -1) {
    playAudioByIndex(index)
  }
}

const stopAudio = () => {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }
  isPlayingAudio.value = false
  playingMsgIndex.value = null
}

// 组件卸载时停止播放和断开连接
onUnmounted(() => {
  stopAudio()
  disconnectWebSocket()
  stopTypeWriter()  // 停止打字机效果
})

// 根据场景获取快捷回复建议
const quickReplies = ref<string[]>([])
const quickRepliesMap: Record<string, string[]> = {
  daily: [
    "What's your hobby?",
    "How was your day?",
    "What do you usually do on weekends?",
    "Tell me about your favorite movie."
  ],
  travel: [
    "Can you recommend some tourist attractions?",
    "What's the best season to visit?",
    "How do I get to the airport?",
    "What should I pack for the trip?"
  ],
  business: [
    "Could we schedule a meeting?",
    "Please review the proposal.",
    "What's the project timeline?",
    "Let me explain the details."
  ],
  academic: [
    "What's your opinion on this theory?",
    "Could you explain this concept?",
    "What evidence supports this?",
    "How does this relate to previous studies?"
  ]
}

// 加载历史记录
onMounted(async () => {
  try {
    const res = await chatApi.getHistory()
    // 后端返回格式: { items: [...], total, page, limit }
    // 需要转换为前端格式，按时间顺序交错显示
    if (res.data && res.data.items) {
      // 按时间顺序排序
      const sortedItems = [...res.data.items].sort((a: any, b: any) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      )
      
      // 按时间顺序交错添加 user 和 assistant 消息
      const loadedMessages: typeof messages.value = []
      sortedItems.forEach((item: any) => {
        // 添加用户消息
        loadedMessages.push({
          role: 'user',
          content: item.user_message,
          time: item.created_at ? new Date(item.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : getCurrentTime()
        })
        // 添加 AI 回复
        if (item.ai_message) {
          loadedMessages.push({
            role: 'assistant',
            content: item.ai_message,
            time: item.created_at ? new Date(item.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : getCurrentTime(),
            corrections: item.corrections || []
          })
        }
      })
      messages.value = loadedMessages
      // 加载完成后滚动到底部（显示最新对话）
      nextTick(() => scrollToBottom())
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
  background: #0f0f23;
  border-radius: 16px;
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16162a 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title .el-icon {
  color: #667eea;
}

.mode-switch :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
}

.mode-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.chat-container {
  flex: 1;
  background: #0f0f23;
  overflow-y: auto;
  padding: 20px 24px;
}

.messages-wrapper {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 20px;
}

.welcome-message {
  position: relative;
  padding: 40px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.12) 0%, rgba(118, 75, 162, 0.12) 100%);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  overflow: hidden;
  margin-bottom: 20px;
}

.welcome-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
  background-size: 40px 40px;
}

.bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.35;
  animation: float 10s ease-in-out infinite;
}

.bg-glow-1 { width: 250px; height: 250px; background: #667eea; top: -80px; right: -40px; }
.bg-glow-2 { width: 180px; height: 180px; background: #764ba2; bottom: -40px; left: -20px; animation-delay: -4s; }
.bg-glow-3 { width: 120px; height: 120px; background: #409EFF; top: 45%; left: 55%; animation-delay: -6s; }

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(8px, -8px) scale(1.03); }
  66% { transform: translate(-4px, 4px) scale(0.97); }
}

.welcome-content {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 28px;
  align-items: flex-start;
}

.welcome-avatar {
  position: relative;
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.35);
}

.avatar-ring {
  position: absolute;
  top: -6px;
  left: -6px;
  right: -6px;
  bottom: -6px;
  border-radius: 50%;
  border: 2px solid rgba(102, 126, 234, 0.4);
  animation: ring-pulse 2.5s ease-in-out infinite;
}

.avatar-ring-2 {
  animation-delay: -1.2s;
  top: -12px;
  left: -12px;
  right: -12px;
  bottom: -12px;
  border-color: rgba(102, 126, 234, 0.15);
}

@keyframes ring-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.08); opacity: 0.4; }
}

.avatar-pulse {
  position: absolute;
  top: -18px;
  left: -18px;
  right: -18px;
  bottom: -18px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.25) 0%, transparent 70%);
  animation: avatar-glow 3.5s ease-in-out infinite;
}

@keyframes avatar-glow {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.12); }
}

.welcome-text { flex: 1; }

.welcome-text h3 {
  font-size: 24px;
  color: #fff;
  margin-bottom: 10px;
  font-weight: 700;
}

.title-highlight {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 14px;
  line-height: 1.6;
}

.feature-tags {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.feature-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 18px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.3s ease;
}

.feature-tag:hover {
  background: rgba(102, 126, 234, 0.15);
  border-color: rgba(102, 126, 234, 0.25);
}

.feature-tag .el-icon { color: #667eea; }

.welcome-tip {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.45);
}

.welcome-voice-tip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-top: 10px;
  font-size: 12px;
  color: #67C23A;
  padding: 7px 12px;
  background: rgba(103, 194, 58, 0.12);
  border-radius: 18px;
}

.welcome-voice-tip .el-icon {
  animation: mic-pulse 1.5s ease-in-out infinite;
}

@keyframes mic-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.scene-cards {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex-wrap: wrap;
}

.scene-card {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(255, 255, 255, 0.65);
}

.scene-card:hover {
  background: rgba(102, 126, 234, 0.12);
  border-color: rgba(102, 126, 234, 0.25);
  color: #fff;
  transform: translateY(-2px);
}

.scene-card.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
}

.scene-card .el-icon { color: #667eea; }
.scene-card.active .el-icon { color: #fff; }

.welcome-text p {
  font-size: 14px;
  color: #606266;
  margin-top: 6px;
  line-height: 1.6;
}

.message-item {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  animation: message-in 0.4s ease;
}

@keyframes message-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-item.is-user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-inner {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.is-user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.is-user .avatar-inner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.is-ai .message-avatar {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
}

.is-ai .avatar-inner {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
  color: #fff;
}

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}

.message-bubble {
  padding: 14px 18px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.6;
  color: #e2e8f0;
  word-wrap: break-word;
  white-space: pre-wrap;
  transition: all 0.2s ease;
  position: relative;
}

/* 流式输出时的纯文本样式 */
.message-bubble .streaming-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  animation: typeIn 0.3s ease-out;
}

/* 打字机光标动画 - 模拟真实打字效果 */
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background: #667eea;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursor-blink 0.65s infinite;
  border-radius: 1px;
}

@keyframes cursor-blink {
  0%, 45% { opacity: 1; }
  50%, 100% { opacity: 0; }
}

/* 打字机淡入效果 */
@keyframes typeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

.is-user .message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-bottom-right-radius: 6px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.is-ai .message-bubble {
  background: linear-gradient(135deg, rgba(74, 85, 104, 0.8) 0%, rgba(45, 55, 72, 0.8) 100%);
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-bottom-left-radius: 6px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.message-bubble.loading {
  padding: 18px 24px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.loading-text {
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  animation: textPulse 1.5s infinite;
}

@keyframes textPulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.loading-dots {
  display: flex;
  gap: 5px;
  align-items: center;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.message-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 8px;
  padding: 0 4px;
}

.is-user .message-time {
  text-align: right;
}

/* 纠错卡片样式 */
.corrections {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed #e4e7ed;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  padding: 12px;
}

.correction-title {
  font-size: 12px;
  font-weight: 600;
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

/* 消息操作按钮 */
.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-item:hover .message-actions {
  opacity: 1;
}

/* 消息气泡内嵌代码样式 */
:deep(.message-bubble code.inline-code) {
  background: #e8e8e8;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  color: #e6a23c;
}

:deep(.message-bubble blockquote) {
  border-left: 3px solid #909399;
  padding-left: 12px;
  margin: 8px 0;
  color: #606266;
}

:deep(.message-bubble ul) {
  margin: 8px 0;
  padding-left: 20px;
}

:deep(.message-bubble li) {
  margin: 4px 0;
}

:deep(.message-bubble li.numbered) {
  list-style: decimal;
}

/* 快捷回复建议 */
.quick-replies {
  margin-top: 12px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 12px;
  border: 1px solid #ebeef5;
}

.quick-replies-label {
  font-size: 12px;
  color: #909399;
  margin-right: 8px;
}

.quick-replies-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.quick-replies-list .el-button {
  font-size: 12px;
  background: #fff;
  border: 1px solid #dcdfe6;
  color: #606266;
}

.quick-replies-list .el-button:hover {
  background: #409EFF;
  border-color: #409EFF;
  color: #fff;
}

/* ===== 底部输入区域 ===== */
.input-area {
  flex: 1;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.3s ease;
}

.input-area:focus-within {
  border-color: rgba(102, 126, 234, 0.5);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-wrapper {
  display: flex;
  gap: 14px;
  align-items: flex-end;
  padding: 16px 20px;
  background: rgba(26, 26, 46, 0.8);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
}

.input-wrapper .el-textarea {
  flex: 1;
}

.input-wrapper :deep(.el-textarea__inner) {
  background: transparent !important;
  border: none !important;
  color: #e2e8f0 !important;
  resize: none;
  padding: 8px 0;
  font-size: 14px;
  line-height: 1.6;
}

.input-wrapper :deep(.el-textarea__inner)::placeholder {
  color: rgba(255, 255, 255, 0.4) !important;
}

.input-wrapper :deep(.el-textarea__inner):focus {
  box-shadow: none !important;
}

/* 发送按钮 */
.send-btn {
  height: 44px;
  padding: 0 20px;
  border-radius: 22px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.send-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.send-btn .el-icon {
  margin-right: 4px;
}

/* 语音输入按钮 - 胶囊形状与发送按钮一致 */
.voice-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 44px;
  height: 44px;
  padding: 0 12px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 22px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.voice-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: #fff;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.voice-btn:active {
  transform: scale(0.95);
}

.voice-btn.recording {
  background: #F56C6C;
  border-color: #F56C6C;
  color: #fff;
  transform: scale(0.95);
}

.voice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.voice-btn-text {
  display: none;
}

.voice-btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

/* 输入提示 */
.input-tips {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  text-align: right;
}

/* 实时语音模式切换 */
.mode-toggle {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.mode-toggle :deep(.el-switch__label) {
  color: rgba(255, 255, 255, 0.7);
}

.realtime-hint {
  font-size: 12px;
  color: #67C23A;
}



.recording-indicator {
  position: absolute;
  bottom: 8px;
  display: flex;
  gap: 3px;
}

.recording-indicator span {
  width: 6px;
  height: 6px;
  background: #fff;
  border-radius: 50%;
  animation: recording-pulse 1s infinite;
}

.recording-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.recording-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes recording-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

/* 语音识别文字样式 */
.recognized-text {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  padding: 6px 10px;
  background: #f5f7fa;
  border-radius: 6px;
}

.recognized-text .el-icon {
  color: #67C23A;
}

/* 欢迎页面的语音提示 */
.welcome-voice-tip {
  margin-top: 12px;
  font-size: 13px;
  color: #67C23A;
  padding: 8px 12px;
  background: rgba(103, 194, 58, 0.1);
  border-radius: 8px;
  display: inline-block;
}
</style>