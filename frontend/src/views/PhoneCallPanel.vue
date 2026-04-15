<template>
  <div class="phone-call-panel">
    <!-- 背景动画 -->
    <div class="phone-bg">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
      <div class="bg-orb bg-orb-3"></div>
    </div>

    <!-- 顶部状态栏 -->
    <div class="call-header">
      <div class="header-left">
        <el-button link @click="handleExit" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
      </div>
      <div class="header-center">
        <div class="call-status" :class="{ active: callStatus === 'connected' }">
          <span class="status-dot"></span>
          {{ statusText }}
        </div>
      </div>
      <!-- 右上角下拉框已移除，通话模式中完全隐藏 -->
    </div>

    <!-- 未开始通话时的开始按钮 -->
    <div v-if="!hasStartedCall || callStatus === 'idle' || callStatus === 'ended'" class="start-call-overlay">
      <div class="start-call-content">
        <div class="start-avatar">
          <el-icon :size="80"><Service /></el-icon>
        </div>
        <h2 class="start-title">AI 口语陪练</h2>
        <p class="start-desc">选择一个场景，开始电话式英语练习</p>
        
        <div class="current-scene-display" v-if="currentScene">
          <span class="scene-label">当前场景：</span>
          <span class="scene-value">{{ currentSceneLabel }}</span>
        </div>
        
        <div class="start-scene-select">
          <el-select v-model="currentScene" placeholder="选择练习场景">
            <el-option label="日常对话" value="daily" />
            <el-option label="旅行英语" value="travel" />
            <el-option label="商务英语" value="business" />
            <el-option label="学术讨论" value="academic" />
          </el-select>
        </div>
        
        <button class="start-btn" @click="handleStartCallClick">
          <el-icon :size="24"><PhoneFilled /></el-icon>
          开始通话
        </button>
      </div>
    </div>

    <!-- 通话界面（已开始通话后显示） -->
    <template v-else>
    <!-- 主通话区域 -->
    <div class="call-main">
      <!-- AI Tutor 头像区域 -->
      <div class="tutor-avatar-area">
        <div class="tutor-avatar" :class="aiStatus">
          <!-- 头像光晕 -->
          <div class="avatar-glow"></div>
          <!-- 头像图片/动画 -->
          <div class="avatar-visual">
            <div v-if="aiStatus === 'speaking'" class="speaking-animation">
              <div class="wave w1"></div>
              <div class="wave w2"></div>
              <div class="wave w3"></div>
            </div>
            <div v-else-if="aiStatus === 'thinking'" class="thinking-animation">
              <div class="pulse-ring"></div>
            </div>
            <div v-else-if="aiStatus === 'interrupted'" class="interrupted-animation">
              <div class="shake"></div>
            </div>
            <el-icon :size="80" class="avatar-icon"><Service /></el-icon>
          </div>
          <!-- 状态标签 -->
          <div class="status-label">{{ statusLabel }}</div>
        </div>
      </div>

      <!-- 通话时长 -->
      <div class="call-duration">
        {{ formatDuration(callDuration) }}
      </div>

      <!-- AI 说的内容显示 -->
      <div v-if="aiText" class="ai-speech-bubble">
        {{ aiText }}
      </div>
    </div>

    <!-- 用户音频可视化 -->
    <div class="user-waveform" :class="{ active: isUserSpeaking }">
      <div class="wave-bar" v-for="i in 15" :key="i"></div>
    </div>

    <!-- 底部控制区 -->
    <div class="call-controls">
      <!-- 主控制按钮 -->
      <div class="main-controls">
        <!-- 结束通话按钮 -->
        <button class="control-btn end-call-btn" @click="handleEndCall">
          <el-icon :size="28"><PhoneFilled /></el-icon>
        </button>
        
        <!-- 主麦克风按钮 - 开始/停止录音 -->
        <button 
          class="control-btn record-btn" 
          :class="{ recording: isRecording }"
          @click="toggleRecording"
        >
          <el-icon :size="32">
            <Microphone />
          </el-icon>
        </button>
        
        <!-- 静音按钮 -->
        <button 
          class="control-btn mute-btn" 
          :class="{ muted: isMuted }"
          @click="toggleMute"
        >
          <el-icon :size="24">
            <MuteNotification v-if="isMuted" />
            <Microphone v-else />
          </el-icon>
        </button>
      </div>

      <!-- 提示文字 -->
      <div class="control-hints">
        <span v-if="aiStatus === 'waiting'">请点击麦克风开始说话</span>
        <span v-else-if="!isRecording">点击麦克风开始说话</span>
        <span v-else class="recording-hint">
          <span class="pulse-dot"></span>
          正在录音...
        </span>
      </div>
    </div>

    <!-- 通话结束弹窗 -->
    <el-dialog
      v-model="showEndDialog"
      title="通话结束"
      width="360px"
      :close-on-click-modal="false"
      class="end-dialog"
    >
      <div class="end-dialog-content">
        <div class="end-stats">
          <div class="stat-item">
            <span class="stat-value">{{ formatDuration(callDuration) }}</span>
            <span class="stat-label">通话时长</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ messageCount }}</span>
            <span class="stat-label">对话轮次</span>
          </div>
        </div>
        <p class="end-message">感谢您的练习！继续保持口语练习会进步更快哦～</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="handleEndConfirm">确定</el-button>
      </template>
    </el-dialog>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { chatApi } from '../api'
import { ArrowLeft, PhoneFilled, Microphone, MuteNotification, Service } from '@element-plus/icons-vue'

// 直接返回原始音频Blob（后端可通过mime_type处理WebM/MP4）
const convertWebMToWav = async (webmBlob: Blob): Promise<Blob> => {
  // 直接返回原始blob，不进行解码转换
  // 后端 whisper 服务支持通过 mime_type 参数处理 WebM/MP4/AAC 等格式
  return webmBlob
}


const emit = defineEmits(['exit', 'end'])

// 退出处理
const handleExit = () => {
  if (callStatus.value === 'connected' || callStatus.value === 'connecting') {
    // 如果正在通话，询问是否结束
    handleEndCall()
  } else {
    // 未开始通话，直接退出
    emit('exit')
  }
}

// 通话状态
const callStatus = ref<'idle' | 'connecting' | 'connected' | 'ended'>('idle')
const aiStatus = ref<'idle' | 'speaking' | 'thinking' | 'interrupted' | 'waiting'>('idle')
const currentScene = ref('daily')

// 场景标签映射
const sceneLabels: Record<string, string> = {
  daily: '日常对话',
  travel: '旅行英语',
  business: '商务英语',
  academic: '学术讨论'
}

const currentSceneLabel = computed(() => sceneLabels[currentScene.value] || '日常对话')
const callDuration = ref(0)
const aiText = ref('')
const messageCount = ref(0)

// 新增：是否已点击开始通话
const hasStartedCall = ref(false)

// 音频相关
const isRecording = ref(false)
const isUserSpeaking = ref(false)
const isMuted = ref(false)
const currentMimeType = ref('audio/webm')  // 当前录音格式
let websocket: WebSocket | null = null
let mediaRecorder: MediaRecorder | null = null
let audioStream: MediaStream | null = null
let durationTimer: number | null = null
let currentAudio: HTMLAudioElement | null = null
let currentAudioSource: AudioBufferSourceNode | null = null  // AudioContext 音频源节点
let recordingStartTime = 0  // 录音开始时间
let audioContext: AudioContext | null = null  // 音频上下文（用于音量检测）
let analyser: AnalyserNode | null = null  // 分析节点（用于音量检测）
let audioLevelCheckInterval: number | null = null  // 音量检测定时器
let hasAudioInput = false  // 是否有声音输入

// ===== 音频预加载机制 =====
let preloadedAudioBuffer: AudioBuffer | null = null  // 预加载的音频Buffer
let preloadedAudioContext: AudioContext | null = null  // 预加载用的 AudioContext
let preloadPromise: Promise<void> | null = null  // 预加载 Promise，用于等待预加载完成
let currentAudioText = ''  // 当前音频对应的文本

// 预加载音频 - 在收到 AI 响应时提前解码
const preloadAudio = (audioBase64: string) => {
  // 清除之前的预加载
  preloadedAudioBuffer = null
  preloadPromise = null
  
  // 创建预加载 Promise
  preloadPromise = (async () => {
    try {
      // 创建专用的 AudioContext 用于预加载
      if (!preloadedAudioContext) {
        preloadedAudioContext = new AudioContext()
      }
      if (preloadedAudioContext.state === 'suspended') {
        await preloadedAudioContext.resume()
      }
      
      // 解码 base64
      const byteCharacters = atob(audioBase64)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      
      // 预解码音频
      preloadedAudioBuffer = await preloadedAudioContext.decodeAudioData(byteArray.buffer)
      console.log('音频预加载完成，预解码时长:', preloadedAudioBuffer.duration, '秒')
    } catch (error) {
      console.error('音频预加载失败:', error)
      preloadedAudioBuffer = null
    }
  })()
}

// 播放预加载的音频 - 等待预加载完成后播放
const playPreloadedAudio = async (): Promise<boolean> => {
  // 等待预加载完成
  if (preloadPromise) {
    await preloadPromise
  }
  
  if (!preloadedAudioBuffer || !preloadedAudioContext) {
    console.warn('没有预加载的音频')
    return false
  }
  
  // 确保 AudioContext 处于 running 状态
  if (preloadedAudioContext.state === 'suspended') {
    await preloadedAudioContext.resume()
  }
  
  // 创建音频源节点
  const source = preloadedAudioContext.createBufferSource()
  source.buffer = preloadedAudioBuffer
  source.connect(preloadedAudioContext.destination)
  
  // 播放完成回调
  source.onended = () => {
    aiStatus.value = 'waiting'
    aiText.value = ''
  }
  
  // 立即播放（无延迟，因为已预解码）
  source.start(0)
  currentAudioSource = source
  aiStatus.value = 'speaking'
  
  // 清除预加载，为下一次准备
  preloadedAudioBuffer = null
  preloadPromise = null
  
  return true
}

// 弹窗
const showEndDialog = ref(false)

// 计算属性
const statusText = computed(() => {
  switch (callStatus.value) {
    case 'connecting': return '正在连接...'
    case 'connected': return '通话中'
    case 'ended': return '通话已结束'
    default: return '等待开始'
  }
})

const statusLabel = computed(() => {
  switch (aiStatus.value) {
    case 'speaking': return 'AI 说话中'
    case 'thinking': return 'AI 思考中'
    case 'interrupted': return '我听到你了'
    case 'waiting': return '等待你说话'
    default: return '准备好了'
  }
})

// 格式化时长
const formatDuration = (seconds: number) => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// 开始通话
const startCall = async () => {
  try {
    callStatus.value = 'connecting'
    aiStatus.value = 'waiting'
    
    // 创建 WebSocket 连接
    websocket = chatApi.createPhoneCall()
    
    websocket.onopen = () => {
      console.log('Phone WebSocket connected')
      websocket?.send(JSON.stringify({
        type: 'start_call',
        client_id: `user_${Date.now()}`,
        scene: currentScene.value
      }))
    }
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleMessage(data)
    }
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      ElMessage.error('连接失败，请重试')
      callStatus.value = 'idle'
    }
    
    websocket.onclose = () => {
      console.log('WebSocket closed')
      if (callStatus.value === 'connected') {
        callStatus.value = 'ended'
        showEndDialog.value = true
      }
    }
    
  } catch (error: any) {
    console.error('Start call error:', error)
    ElMessage.error('无法建立通话连接')
    callStatus.value = 'idle'
  }
}

// 处理 WebSocket 消息
const handleMessage = (data: any) => {
  switch (data.type) {
    case 'call_status':
      handleCallStatus(data)
      break
    case 'recognition':
      if (!data.interim) {
        isUserSpeaking.value = false
      }
      break
    case 'ai_response':
      // 提前开始预加载音频（如果有音频数据）
      if (data.audio) {
        preloadAudio(data.audio)
      }
      // 异步处理 AI 响应，等待预加载完成后再播放
      handleAIResponse(data)
      break
    case 'error':
      ElMessage.error(data.message)
      break
  }
}

// 处理通话状态
const handleCallStatus = (data: any) => {
  const status = data.status
  
  switch (status) {
    case 'connected':
    case 'waiting':
      callStatus.value = 'connected'
      // waiting 状态表示等待用户说话（AI 不主动说话）
      if (status === 'waiting') {
        aiStatus.value = 'waiting'
      }
      startDurationTimer()
      // 不再自动开始录音，等待用户主动点击麦克风
      break
    case 'thinking':
      aiStatus.value = 'thinking'
      aiText.value = ''
      break
    case 'interrupted':
      aiStatus.value = 'interrupted'
      stopAudio()
      setTimeout(() => {
        if (aiStatus.value === 'interrupted') {
          aiStatus.value = 'waiting'
        }
      }, 1500)
      break
    case 'scene_changed':
      ElMessage.success(data.message)
      break
  }
}

// 处理 AI 回复
const handleAIResponse = async (data: any) => {
  messageCount.value++

  if (data.status === 'ended') {
    callStatus.value = 'ended'
    showEndDialog.value = true
    return
  }

  aiText.value = data.text

  // 播放音频 - 优先使用预加载的音频，否则实时解码
  if (data.audio) {
    // 尝试播放预加载的音频（异步等待预加载完成）
    const played = await playPreloadedAudio()
    if (!played) {
      // 预加载失败，实时解码播放
      playAudio(data.audio)
    }
  }
  // 如果没有音频，手动设置状态
  else {
    aiStatus.value = 'speaking'
    setTimeout(() => {
      if (aiStatus.value === 'speaking') {
        aiStatus.value = 'waiting'
        aiText.value = ''
      }
    }, 3000)
  }
}

// 播放音频 - 使用 AudioContext 预解码，解决开头单词丢失问题
const playAudio = (audioBase64: string) => {
  stopAudio()  // 先停止之前的播放

  // 创建或恢复 AudioContext
  const initAudioContext = async (): Promise<AudioContext> => {
    if (!audioContext) {
      audioContext = new AudioContext()
    }
    // 确保 AudioContext 处于 running 状态（解决浏览器自动暂停问题）
    if (audioContext.state === 'suspended') {
      await audioContext.resume()
    }
    return audioContext
  }

  // 解码 base64 为 ArrayBuffer
  const byteCharacters = atob(audioBase64)
  const byteNumbers = new Array(byteCharacters.length)
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  const byteArray = new Uint8Array(byteNumbers)

  // 使用 AudioContext 预解码音频
  initAudioContext().then(async context => {
    try {
      // 同步解码
      const audioBuffer = await context.decodeAudioData(byteArray.buffer.slice(0))
      
      // 创建音频源节点
      const source = context.createBufferSource()
      source.buffer = audioBuffer
      source.connect(context.destination)

      // 播放完成回调
      source.onended = () => {
        aiStatus.value = 'waiting'
        aiText.value = ''
      }

      // 确保 AudioContext 状态正确后立即播放
      if (context.state === 'suspended') {
        await context.resume()
      }
      source.start(0)
      currentAudioSource = source
      aiStatus.value = 'speaking'
    } catch (error) {
      console.error('音频解码失败:', error)
      // 回退到旧的 Audio 方式
      fallbackPlayAudio(audioBase64)
    }
  }).catch(error => {
    console.error('AudioContext 初始化失败:', error)
    fallbackPlayAudio(audioBase64)
  })
}

// 回退方案：使用传统 Audio 播放
const fallbackPlayAudio = (audioBase64: string) => {
  const byteCharacters = atob(audioBase64)
  const byteNumbers = new Array(byteCharacters.length)
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  const byteArray = new Uint8Array(byteNumbers)
  const audioBlob = new Blob([byteArray], { type: 'audio/webm' })
  const audioUrl = URL.createObjectURL(audioBlob)

  currentAudio = new Audio(audioUrl)
  currentAudio.play().catch(console.error)

  currentAudio.onended = () => {
    URL.revokeObjectURL(audioUrl)
    aiStatus.value = 'waiting'
    aiText.value = ''
  }
}

// 停止音频
const stopAudio = () => {
  // 停止 AudioBufferSourceNode（如果使用 AudioContext 播放）
  if (currentAudioSource) {
    try {
      currentAudioSource.stop()
    } catch (e) {
      // 忽略已停止的错误
    }
    currentAudioSource = null
  }
  // 停止 HTMLAudioElement（回退方案）
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }
}

// 初始化音量检测
const initAudioLevelDetection = (stream: MediaStream) => {
  audioContext = new AudioContext()
  analyser = audioContext.createAnalyser()
  analyser.fftSize = 256

  const source = audioContext.createMediaStreamSource(stream)
  source.connect(analyser)

  hasAudioInput = false

  // 定期检测音量
  audioLevelCheckInterval = window.setInterval(() => {
    if (!analyser) return

    const dataArray = new Uint8Array(analyser.frequencyBinCount)
    analyser.getByteFrequencyData(dataArray)

    // 计算平均音量
    const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length
    const volume = Math.round(average)

    // 如果音量超过阈值，认为有声音输入
    if (volume > 10) {
      hasAudioInput = true
    }
  }, 100)
}

// 停止音量检测
const stopAudioLevelDetection = () => {
  if (audioLevelCheckInterval) {
    clearInterval(audioLevelCheckInterval)
    audioLevelCheckInterval = null
  }
  if (audioContext) {
    audioContext.close()
    audioContext = null
  }
  analyser = null
}

// 检测麦克风是否有声音输入（改为只验证权限和设备可用性，不强制要求有声音输入）
const checkMicrophoneHasAudio = async (): Promise<boolean> => {
  try {
    // 请求麦克风权限
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    })

    // 验证麦克风轨道是否可用（有音频轨道且未结束）
    const audioTrack = stream.getAudioTracks()[0]
    if (!audioTrack) {
      console.warn('没有找到音频轨道')
      stream.getTracks().forEach(track => track.stop())
      return false
    }

    // 检查麦克风是否被禁用
    if (!audioTrack.enabled) {
      console.warn('麦克风被禁用')
      stream.getTracks().forEach(track => track.stop())
      return false
    }

    // 检查麦克风设置（获取设备信息用于调试）
    const settings = audioTrack.getSettings()
    console.log('麦克风设置:', settings)

    // 只要麦克风权限正常且设备可用就返回 true
    // 不再强制要求有声音输入，让用户自行判断
    stream.getTracks().forEach(track => track.stop())
    return true
  } catch (error: any) {
    console.error('麦克风检测失败:', error)
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
    return false
  }
}

// 开始录音
const startRecording = async () => {
  try {
    // 先检测麦克风权限
    const hasAudio = await checkMicrophoneHasAudio()
    if (!hasAudio) {
      ElMessage.warning('请确保麦克风已开启并有声音输入后再试')
      return
    }

    // 获取麦克风权限
    audioStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    })

    // 初始化音量检测
    initAudioLevelDetection(audioStream)
    
    // 优先使用 MP4 格式（兼容性更好），其次 WebM
    let mimeType = 'audio/webm'
    if (MediaRecorder.isTypeSupported('audio/mp4;codecs=mp4a.40.2')) {
      mimeType = 'audio/mp4;codecs=mp4a.40.2'
      currentMimeType.value = 'audio/mp4'
    } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
      mimeType = 'audio/webm;codecs=opus'
      currentMimeType.value = 'audio/webm'
    } else {
      currentMimeType.value = 'audio/webm'
    }
    
    mediaRecorder = new MediaRecorder(audioStream, { mimeType })

    const audioChunks: Blob[] = []
    
    mediaRecorder.ondataavailable = async (e) => {
      if (e.data.size > 0) {
        audioChunks.push(e.data)
        
        // 直接发送 WebM 数据，后端可处理 WebM 格式
        try {
          const webmBlob = await convertWebMToWav(e.data)
          const reader = new FileReader()
          reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1]
            // 发送正确的 mime_type (WebM 而不是 WAV)
            sendAudioData(base64, false, currentMimeType.value || 'audio/webm')
          }
          reader.readAsDataURL(webmBlob)
        } catch (err) {
          console.error('Audio conversion error:', err)
          // 如果转换失败，回退到原始数据
          const reader = new FileReader()
          reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1]
            sendAudioData(base64, false, currentMimeType.value)
          }
          reader.readAsDataURL(e.data)
        }
      }
    }
    
    mediaRecorder.onstop = async () => {
      // 停止音量检测
      stopAudioLevelDetection()

      // 检查录音时长
      const recordingDuration = Date.now() - recordingStartTime
      if (recordingDuration < 500) {
        isRecording.value = false
        ElMessage.warning('录音时间太短，请确保完整录音后重试')
        return
      }
      
      if (audioChunks.length > 0) {
        try {
          // 直接发送 WebM 数据
          const webmBlob = await convertWebMToWav(new Blob(audioChunks))
          const reader = new FileReader()
          reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1]
            // 发送正确的 mime_type
            sendAudioData(base64, true, currentMimeType.value || 'audio/webm')
          }
          reader.readAsDataURL(webmBlob)
        } catch (err) {
          console.error('Audio conversion error:', err)
          // 回退到原始数据
          const reader = new FileReader()
          reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1]
            sendAudioData(base64, true, currentMimeType.value)
          }
          reader.readAsDataURL(new Blob(audioChunks))
        }
      }
    }
    
    mediaRecorder.start(300)
    recordingStartTime = Date.now()
    isRecording.value = true
    
  } catch (error: any) {
    isRecording.value = false  // 确保异常时重置状态
    stopAudioLevelDetection()  // 停止音量检测
    console.error('Recording error:', error)
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

// 发送音频数据
const sendAudioData = (base64Data: string, isFinal: boolean, mimeType: string = 'audio/wav') => {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({
      type: 'audio',
      data: base64Data,
      is_final: isFinal,
      mime_type: mimeType
    }))
    
    if (!isFinal) {
      isUserSpeaking.value = true
    }
  }
}

// 停止录音
const stopRecording = () => {
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop()
    isRecording.value = false
  }
  
  if (audioStream) {
    audioStream.getTracks().forEach(track => track.stop())
    audioStream = null
  }
}

// 结束通话
const handleEndCall = () => {
  stopRecording()
  stopAudio()
  
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({
      type: 'end_call'
    }))
    websocket.close()
    websocket = null
  }
  
  if (durationTimer) {
    clearInterval(durationTimer)
    durationTimer = null
  }
  
  callStatus.value = 'ended'
  showEndDialog.value = true
  emit('end', { duration: callDuration.value, messages: messageCount.value })
}

// 确认结束
const handleEndConfirm = () => {
  showEndDialog.value = false
  callStatus.value = 'idle'
  hasStartedCall.value = false
  emit('exit')
}

// 切换录音状态
const toggleRecording = async () => {
  if (isRecording.value) {
    // 停止录音
    stopRecording()
  } else {
    // 开始录音
    await startRecording()
  }
}

// 切换静音
const toggleMute = () => {
  isMuted.value = !isMuted.value
  
  if (audioStream) {
    audioStream.getTracks().forEach(track => {
      track.enabled = !isMuted.value
    })
  }
}

// 切换场景
const handleSceneChange = (scene: string) => {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({
      type: 'text',
      content: `/scene ${scene}`
    }))
  }
}

// 计时器
const startDurationTimer = () => {
  callDuration.value = 0
  durationTimer = window.setInterval(() => {
    callDuration.value++
  }, 1000)
}

// 生命周期
onMounted(() => {
  // 不自动开始，等待用户点击开始按钮
})

// 点击开始通话按钮
const handleStartCallClick = () => {
  hasStartedCall.value = true
  startCall()
}

onUnmounted(() => {
  handleEndCall()
})
</script>

<style scoped>
.phone-call-panel {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  overflow: hidden;
}

/* 背景动画 */
.phone-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  pointer-events: none;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
  animation: float 20s ease-in-out infinite;
}

.bg-orb-1 {
  width: 400px;
  height: 400px;
  background: #667eea;
  top: -100px;
  right: -100px;
  animation-delay: 0s;
}

.bg-orb-2 {
  width: 300px;
  height: 300px;
  background: #764ba2;
  bottom: -50px;
  left: -50px;
  animation-delay: -5s;
}

.bg-orb-3 {
  width: 250px;
  height: 250px;
  background: #409EFF;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -10s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(20px, -20px) scale(1.1); }
  50% { transform: translate(-10px, 10px) scale(0.9); }
  75% { transform: translate(-20px, -10px) scale(1.05); }
}

/* 顶部状态栏 */
.call-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  position: relative;
  z-index: 30;
}

.back-btn {
  color: #fff;
  font-size: 24px;
  cursor: pointer;
  pointer-events: auto;
  padding: 8px;
}

.header-center {
  flex: 1;
  text-align: center;
}

.call-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 14px;
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.call-status.active {
  color: #67C23A;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #909399;
}

.call-status.active .status-dot {
  background: #67C23A;
  animation: pulse-dot 1.5s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.scene-select {
  width: 140px;
}

.scene-select :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.1);
  box-shadow: none;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.scene-select :deep(.el-input__inner) {
  color: #fff;
}

/* 主通话区域 */
.call-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  z-index: 10;
}

/* AI Tutor 头像 */
.tutor-avatar-area {
  margin-bottom: 30px;
}

.tutor-avatar {
  position: relative;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 60px rgba(102, 126, 234, 0.5);
  transition: all 0.3s ease;
}

.tutor-avatar.speaking {
  box-shadow: 0 0 80px rgba(102, 126, 234, 0.8);
  animation: speak-pulse 1s infinite;
}

.tutor-avatar.thinking {
  box-shadow: 0 0 40px rgba(230, 162, 60, 0.5);
}

.tutor-avatar.interrupted {
  animation: shake 0.5s ease-in-out;
}

@keyframes speak-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-10px); }
  75% { transform: translateX(10px); }
}

.avatar-glow {
  position: absolute;
  top: -20px;
  left: -20px;
  right: -20px;
  bottom: -20px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.3) 0%, transparent 70%);
  animation: glow-pulse 2s infinite;
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.1); }
}

.avatar-visual {
  position: relative;
  z-index: 1;
}

.avatar-icon {
  color: #fff;
  filter: drop-shadow(0 2px 10px rgba(0, 0, 0, 0.3));
}

/* 说话动画 */
.speaking-animation {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  gap: 4px;
}

.wave {
  width: 4px;
  height: 20px;
  background: #fff;
  border-radius: 2px;
  animation: wave 0.5s infinite ease-in-out;
}

.w1 { animation-delay: 0s; }
.w2 { animation-delay: 0.1s; }
.w3 { animation-delay: 0.2s; }

@keyframes wave {
  0%, 100% { height: 20px; }
  50% { height: 40px; }
}

/* 思考动画 */
.thinking-animation {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.pulse-ring {
  width: 60px;
  height: 60px;
  border: 3px solid #E6A23C;
  border-radius: 50%;
  animation: pulse-ring 1.5s infinite;
}

@keyframes pulse-ring {
  0% { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(1.5); opacity: 0; }
}

/* 打断动画 */
.interrupted-animation {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.shake {
  width: 40px;
  height: 40px;
  background: #E6A23C;
  border-radius: 50%;
  animation: shake 0.5s ease-in-out;
}

.status-label {
  position: absolute;
  bottom: -30px;
  left: 50%;
  transform: translateX(-50%);
  color: #fff;
  font-size: 14px;
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  white-space: nowrap;
}

/* 通话时长 */
.call-duration {
  color: rgba(255, 255, 255, 0.6);
  font-size: 16px;
  font-family: 'Monaco', monospace;
  margin-bottom: 20px;
}

/* AI 说话气泡 */
.ai-speech-bubble {
  max-width: 80%;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  border-bottom-left-radius: 4px;
  color: #fff;
  font-size: 16px;
  line-height: 1.6;
  text-align: center;
  backdrop-filter: blur(10px);
  animation: fade-in 0.3s ease;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 用户波形 */
.user-waveform {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 3px;
  height: 40px;
  margin-bottom: 20px;
  opacity: 0;
  transition: opacity 0.3s;
  position: relative;
  z-index: 10;
}

.user-waveform.active {
  opacity: 1;
}

.user-waveform .wave-bar {
  width: 3px;
  height: 10px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 2px;
  transition: all 0.3s;
}

.user-waveform.active .wave-bar {
  background: #67C23A;
  animation: user-wave 0.5s infinite ease-in-out;
}

.user-waveform.active .wave-bar:nth-child(2n) { animation-delay: 0.1s; }
.user-waveform.active .wave-bar:nth-child(3n) { animation-delay: 0.2s; }
.user-waveform.active .wave-bar:nth-child(4n) { animation-delay: 0.3s; }

@keyframes user-wave {
  0%, 100% { height: 10px; }
  50% { height: 30px; }
}

/* 底部控制区 */
.call-controls {
  padding: 30px 20px 50px;
  position: relative;
  z-index: 10;
}

.main-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 40px;
  margin-bottom: 24px;
}

.control-btn {
  width: 68px;
  height: 68px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #fff;
  position: relative;
  overflow: visible;
}

.control-btn::before {
  content: '';
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.end-call-btn {
  background: linear-gradient(135deg, #F56C6C 0%, #f78989 100%);
  box-shadow: 0 6px 25px rgba(245, 108, 108, 0.45);
}

.end-call-btn::before {
  background: linear-gradient(135deg, #F56C6C 0%, #f78989 100%);
}

.end-call-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 8px 35px rgba(245, 108, 108, 0.65);
}

.end-call-btn:hover::before {
  opacity: 0.3;
  animation: btn-pulse 1.5s infinite;
}

.mute-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 2px solid rgba(255, 255, 255, 0.25);
}

.mute-btn::before {
  background: rgba(255, 255, 255, 0.2);
}

.mute-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.05);
}

.mute-btn.muted {
  background: linear-gradient(135deg, #E6A23C 0%, #f0c78a 100%);
  border-color: #E6A23C;
  box-shadow: 0 4px 15px rgba(230, 162, 60, 0.4);
}

.record-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: 3px solid rgba(255, 255, 255, 0.5);
  width: 80px;
  height: 80px;
  transition: all 0.3s ease;
  box-shadow: 0 6px 25px rgba(102, 126, 234, 0.5);
}

.record-btn::before {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.record-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 0 30px rgba(102, 126, 234, 0.7);
}

.record-btn.recording {
  background: linear-gradient(135deg, #f5365c 0%, #f56075 100%);
  box-shadow: 0 0 30px rgba(245, 54, 92, 0.6);
  animation: pulse-recording 1.5s infinite;
}

@keyframes pulse-recording {
  0% { box-shadow: 0 0 0 0 rgba(245, 54, 92, 0.7); }
  70% { box-shadow: 0 0 0 20px rgba(245, 54, 92, 0); }
  100% { box-shadow: 0 0 0 0 rgba(245, 54, 92, 0); }
}

@keyframes btn-pulse {
  0% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.3); opacity: 0.1; }
  100% { transform: scale(1); opacity: 0.3; }
}

.control-hints {
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  display: inline-block;
}

.recording-hint {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #67C23A;
  font-weight: 500;
}

.pulse-dot {
  width: 10px;
  height: 10px;
  background: #67C23A;
  border-radius: 50%;
  animation: pulse-dot 1s infinite;
  box-shadow: 0 0 10px rgba(103, 194, 58, 0.5);
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

/* 结束弹窗 */
.end-dialog :deep(.el-dialog) {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.end-dialog :deep(.el-dialog__header) {
  padding: 24px 24px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.end-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-size: 20px;
  font-weight: 600;
}

.end-dialog :deep(.el-dialog__body) {
  padding: 28px 24px;
}

.end-dialog-content {
  text-align: center;
}

.end-stats {
  display: flex;
  justify-content: center;
  gap: 50px;
  margin-bottom: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 30px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 8px;
}

.end-message {
  color: rgba(255, 255, 255, 0.65);
  font-size: 14px;
  line-height: 1.7;
  padding: 16px 20px;
  background: rgba(103, 194, 58, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(103, 194, 58, 0.2);
}

.end-dialog :deep(.el-dialog__footer) {
  padding: 16px 24px 24px;
}

.end-dialog :deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  padding: 12px 36px;
  border-radius: 25px;
  font-weight: 500;
  transition: all 0.3s ease;
}


.start-call-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
  background: radial-gradient(ellipse at center, transparent 0%, rgba(0, 0, 0, 0.4) 100%);
}

.start-call-content {
  text-align: center;
  padding: 50px 60px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-radius: 32px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: content-fade-in 0.5s ease;
}

@keyframes content-fade-in {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.start-avatar {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin: 0 auto 28px;
  box-shadow: 0 12px 50px rgba(102, 126, 234, 0.5);
  position: relative;
  animation: avatar-float 3s ease-in-out infinite;
}

@keyframes avatar-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.start-avatar::before {
  content: '';
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  border-radius: 50%;
  border: 2px solid rgba(102, 126, 234, 0.4);
  animation: ring-expand 2s ease-in-out infinite;
}

@keyframes ring-expand {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.15); opacity: 0.3; }
}

.start-title {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 14px;
  background: linear-gradient(135deg, #fff 0%, rgba(255, 255, 255, 0.8) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.start-desc {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 24px;
  line-height: 1.6;
}

.current-scene-display {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  gap: 8px;
}

.scene-label {
  color: #909399;
  font-size: 14px;
}

.scene-value {
  color: #667eea;
  font-size: 16px;
  font-weight: 600;
}

.start-scene-select {
  margin-bottom: 36px;
}

.start-scene-select :deep(.el-select) {
  width: 260px;
}

.start-scene-select :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: none;
  border-radius: 12px;
  padding: 4px 12px;
}

.start-scene-select :deep(.el-input__wrapper:hover) {
  border-color: rgba(102, 126, 234, 0.5);
}

.start-scene-select :deep(.el-input__inner) {
  color: #fff;
  font-size: 14px;
}

.start-scene-select :deep(.el-select__placeholder) {
  color: rgba(255, 255, 255, 0.5) !important;
}

.start-btn {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  padding: 18px 48px;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #67C23A 0%, #85CE61 100%);
  border: none;
  border-radius: 50px;
  cursor: pointer;
  box-shadow: 0 8px 30px rgba(103, 194, 58, 0.45);
  transition: all 0.3s ease;
}

.start-btn:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 12px 40px rgba(103, 194, 58, 0.6);
}

.start-btn:active {
  transform: translateY(0) scale(0.98);
}
</style>
