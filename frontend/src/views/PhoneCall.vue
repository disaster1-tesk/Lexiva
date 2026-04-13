<template>
  <div class="phone-call-page">
    <!-- 背景动画 -->
    <div class="phone-bg">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
      <div class="bg-orb bg-orb-3"></div>
    </div>

    <!-- 顶部状态栏 -->
    <div class="call-header">
      <div class="header-left">
        <el-button link @click="goBack" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
      </div>
      <div class="header-center">
        <div class="call-status" :class="{ active: callStatus === 'connected' }">
          <span class="status-dot"></span>
          {{ statusText }}
        </div>
      </div>
      <div class="header-right">
        <el-select v-model="currentScene" @change="handleSceneChange" class="scene-select">
          <el-option label="日常对话" value="daily" />
          <el-option label="旅行英语" value="travel" />
          <el-option label="商务英语" value="business" />
          <el-option label="学术讨论" value="academic" />
        </el-select>
      </div>
    </div>

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
        <button class="control-btn end-call-btn" @click="endCall">
          <el-icon :size="28"><PhoneFilled /></el-icon>
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
        <span v-if="!isRecording">点击麦克风开始说话</span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { chatApi } from '../api'
import { ArrowLeft, PhoneFilled, Microphone, MuteNotification, Service } from '@element-plus/icons-vue'

// 将 WebM Blob 转换为 WAV Blob (16bit PCM mono)
const convertWebMToWav = async (webmBlob: Blob): Promise<Blob> => {
  return new Promise(async (resolve, reject) => {
    try {
      // 检查 Blob 是否为空
      if (webmBlob.size === 0) {
        reject(new Error("Empty audio blob"))
        return
      }
      
      const arrayBuffer = await webmBlob.arrayBuffer()
      
      // 检查 ArrayBuffer 是否为空
      if (arrayBuffer.byteLength === 0) {
        reject(new Error("Empty audio data"))
        return
      }
      
      const audioContext = new AudioContext()
      
      try {
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer.slice(0))
        
        const numChannels = 1
        const sampleRate = audioBuffer.sampleRate
        const length = audioBuffer.length
        const wavBuffer = new ArrayBuffer(44 + length * numChannels * 2)
        const view = new DataView(wavBuffer)
        
        const writeString = (offset: number, str: string) => {
          for (let i = 0; i < str.length; i++) {
            view.setUint8(offset + i, str.charCodeAt(i))
          }
        }
        
        writeString(0, 'RIFF')
        view.setUint32(4, 36 + length * 2, true)
        writeString(8, 'WAVE')
        writeString(12, 'fmt ')
        view.setUint32(16, 16, true)
        view.setUint16(20, 1, true)
        view.setUint16(22, numChannels, true)
        view.setUint32(24, sampleRate, true)
        view.setUint32(28, sampleRate * numChannels * 2, true)
        view.setUint16(32, numChannels * 2, true)
        view.setUint16(34, 16, true)
        writeString(36, 'data')
        view.setUint32(40, length * 2, true)
        
        const channelData = audioBuffer.getChannelData(0)
        let offset = 44
        for (let i = 0; i < length; i++) {
          const sample = Math.max(-1, Math.min(1, channelData[i]))
          view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true)
          offset += 2
        }
        
        await audioContext.close()
        resolve(new Blob([wavBuffer], { type: 'audio/wav' }))
      } catch (decodeErr: any) {
        await audioContext.close()
        // 如果 decodeAudioData 失败，尝试使用 Web Audio API 的 AudioWorklet 或其他方法
        console.warn('decodeAudioData failed, trying alternative approach:', decodeErr.message)
        
        // 尝试创建空的 WAV 文件（作为最后的回退）
        const emptyWav = createEmptyWav()
        resolve(emptyWav)
      }
    } catch (err: any) {
      console.error('Audio conversion error:', err.message)
      reject(err)
    }
  })
}

// 创建空的 WAV 文件作为回退
const createEmptyWav = (): Blob => {
  const sampleRate = 16000
  const numChannels = 1
  const bitsPerSample = 16
  const duration = 0.1 // 100ms 静音
  const numSamples = Math.floor(sampleRate * duration)
  const dataSize = numSamples * numChannels * (bitsPerSample / 8)
  const bufferSize = 44 + dataSize
  
  const wavBuffer = new ArrayBuffer(bufferSize)
  const view = new DataView(wavBuffer)
  
  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i))
    }
  }
  
  writeString(0, 'RIFF')
  view.setUint32(4, 36 + dataSize, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, numChannels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * numChannels * 2, true)
  view.setUint16(32, numChannels * 2, true)
  view.setUint16(34, bitsPerSample, true)
  writeString(36, 'data')
  view.setUint32(40, dataSize, true)
  
  return new Blob([wavBuffer], { type: 'audio/wav' })
}

const router = useRouter()

// 通话状态
const callStatus = ref<'idle' | 'connecting' | 'connected' | 'ended'>('idle')
const aiStatus = ref<'idle' | 'speaking' | 'thinking' | 'interrupted' | 'waiting'>('idle')
const currentScene = ref('daily')
const callDuration = ref(0)
const aiText = ref('')
const messageCount = ref(0)

// 音频相关
const isRecording = ref(false)
const isUserSpeaking = ref(false)
const isMuted = ref(false)
const currentMimeType = ref('audio/webm')  // 当前录音格式

// 流式音频相关
const isStreamingAudio = ref(false)  // 是否正在接收流式音频
const audioChunksQueue: Uint8Array[] = []  // 音频块队列
let streamingAudioContext: AudioContext | null = null
let streamingSourceNode: AudioBufferSourceNode | null = null
let audioBuffer: AudioBuffer | null = null
let currentPlayingChunk: number = 0  // 当前播放到的块索引
let websocket: WebSocket | null = null
let audioContext: AudioContext | null = null
let mediaRecorder: MediaRecorder | null = null
let audioStream: MediaStream | null = null
let durationTimer: number | null = null
let currentAudio: HTMLAudioElement | null = null
let recordingStartTime = 0  // 录音开始时间

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

// 返回
const goBack = () => {
  if (callStatus.value === 'connected') {
    endCall()
  } else {
    router.push('/chat')
  }
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
      // 发送初始化消息
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
      // 语音识别结果
      if (!data.interim) {
        isUserSpeaking.value = false
      }
      break
    case 'ai_response':
      handleAIResponse(data)
      break
    case 'audio_chunk':
      // 流式音频块
      handleAudioChunk(data)
      break
    case 'error':
      ElMessage.error(data.message)
      break
  }
}

// 处理通话状态
const handleCallStatus = (data: any) => {
  const status = data.status
  const message = data.message || ''
  
  switch (status) {
    case 'connected':
      callStatus.value = 'connected'
      startDurationTimer()
      startRecording()
      break
    case 'thinking':
      aiStatus.value = 'thinking'
      aiText.value = ''
      break
    case 'interrupted':
      aiStatus.value = 'interrupted'
      // 停止当前播放的音频
      stopAudio()
      setTimeout(() => {
        if (aiStatus.value === 'interrupted') {
          aiStatus.value = 'waiting'
        }
      }, 1500)
      break
    case 'scene_changed':
      ElMessage.success(message)
      break
  }
}

// 处理 AI 回复
const handleAIResponse = (data: any) => {
  messageCount.value++
  
  if (data.status === 'ended') {
    // 通话结束
    callStatus.value = 'ended'
    showEndDialog.value = true
    return
  }
  
  // 显示 AI 说的话
  aiText.value = data.text
  aiStatus.value = 'speaking'
  
  // 播放 AI 语音
  if (data.audio) {
    playAudio(data.audio)
  }
  
  // 说话结束后回到等待状态
  if (currentAudio) {
    currentAudio.onended = () => {
      setTimeout(() => {
        if (aiStatus.value === 'speaking') {
          aiStatus.value = 'waiting'
          aiText.value = ''
        }
      }, 1000)
    }
  }
}

// 处理流式音频块
const handleAudioChunk = (data: any) => {
  const audioBase64 = data.audio
  const isFinal = data.is_final
  
  if (!audioBase64) return
  
  // 解码 base64 音频数据
  const byteCharacters = atob(audioBase64)
  const byteNumbers = new Array(byteCharacters.length)
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  const byteArray = new Uint8Array(byteNumbers)
  
  // 追加到队列
  audioChunksQueue.push(byteArray)
  
  // 设置状态
  if (!isStreamingAudio.value) {
    isStreamingAudio.value = true
    aiStatus.value = 'speaking'
    // 立即开始播放
    playNextStreamChunk()
  }
  
  // 如果文本已准备好，更新显示
  if (data.text && !aiText.value) {
    aiText.value = data.text
  } else if (data.text) {
    // 追加新文本
    aiText.value = data.text
  }
  
  // 如果是最后一个块，设置结束回调
  if (isFinal) {
    // 延迟清理状态，让音频播放完毕
    setTimeout(() => {
      isStreamingAudio.value = false
      audioChunksQueue.length = 0  // 清空队列
      if (aiStatus.value === 'speaking') {
        aiStatus.value = 'waiting'
        aiText.value = ''
      }
    }, 1500)
  }
}

// 播放下一个流式音频块
const playNextStreamChunk = async () => {
  if (audioChunksQueue.length === 0) {
    isStreamingAudio.value = false
    return
  }
  
  try {
    // 创建或复用 AudioContext
    if (!streamingAudioContext) {
      streamingAudioContext = new AudioContext()
    }
    
    // 获取当前音频块
    const chunkData = audioChunksQueue.shift()
    if (!chunkData) return
    
    // 将 PCM 数据转换为 AudioBuffer
    // 假设是 16kHz, 16-bit, mono
    const sampleRate = 16000
    const numChannels = 1
    const bitsPerSample = 16
    const bytesPerSample = bitsPerSample / 8
    const length = chunkData.length / bytesPerSample
    
    const audioBuffer = streamingAudioContext.createBuffer(
      numChannels,
      length,
      sampleRate
    )
    
    // 写入数据到 AudioBuffer
    const channelData = audioBuffer.getChannelData(0)
    const int16Array = new Int16Array(chunkData.buffer, chunkData.byteOffset, length)
    
    for (let i = 0; i < length; i++) {
      // 将 int16 转换为 float32
      channelData[i] = int16Array[i] / 32768.0
    }
    
    // 创建播放源
    const source = streamingAudioContext.createBufferSource()
    source.buffer = audioBuffer
    
    // 连接到输出
    source.connect(streamingAudioContext.destination)
    
    // 播放
    source.start()
    
    // 设置播放完成回调
    source.onended = () => {
      // 播放下一个块
      if (audioChunksQueue.length > 0 && isStreamingAudio.value) {
        playNextStreamChunk()
      }
    }
    
  } catch (error) {
    console.error('Stream audio play error:', error)
    // 出错时尝试使用传统方式
    isStreamingAudio.value = false
  }
}

// 播放音频
const playAudio = (audioBase64: string) => {
  stopAudio()
  
  const byteCharacters = atob(audioBase64)
  const byteNumbers = new Array(byteCharacters.length)
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  const byteArray = new Uint8Array(byteNumbers)
  const audioBlob = new Blob([byteArray], { type: 'audio/mp4' })
  const audioUrl = URL.createObjectURL(audioBlob)
  
  currentAudio = new Audio(audioUrl)
  currentAudio.play().catch(console.error)
  
  currentAudio.onended = () => {
    URL.revokeObjectURL(audioUrl)
  }
}

// 停止音频
const stopAudio = () => {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }
}

// 开始录音
const startRecording = async () => {
  try {
    audioStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    })
    
    // 优先使用 MP4 格式（兼容性更好），其次 WebM
    let mimeType = 'audio/webm'
    if (MediaRecorder.isTypeSupported('audio/mp4;codecs=mp4a.40.2')) {
      mimeType = 'audio/mp4;codecs=mp4a.40.2'
    } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
      mimeType = 'audio/webm;codecs=opus'
    }
    
    mediaRecorder = new MediaRecorder(audioStream, { mimeType })
    
    // 验证 MediaRecorder 初始化是否成功
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
      audioStream.getTracks().forEach(track => track.stop())
      throw new Error('MediaRecorder 初始化失败')
    }
    
    const audioChunks: Blob[] = []
    
    mediaRecorder.ondataavailable = async (e) => {
      if (e.data.size > 0) {
        audioChunks.push(e.data)
        
        // 将 WebM 转换为 WAV 后发送
        try {
          const wavBlob = await convertWebMToWav(e.data)
          const reader = new FileReader()
          reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1]
            sendAudioData(base64, false, 'audio/wav')
          }
          reader.readAsDataURL(wavBlob)
        } catch (err) {
          console.error('Audio conversion error:', err)
          // 回退：发送原始 WebM 数据
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
      // 检查录音时长
      const recordingDuration = Date.now() - recordingStartTime
      if (recordingDuration < 500) {
        isRecording.value = false
        ElMessage.warning('录音时间太短，请确保完整录音后重试')
        return
      }
      
      if (audioChunks.length > 0) {
        try {
          const wavBlob = await convertWebMToWav(new Blob(audioChunks))
          const reader = new FileReader()
          reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1]
            sendAudioData(base64, true, 'audio/wav')
          }
          reader.readAsDataURL(wavBlob)
        } catch (err) {
          console.error('Audio conversion error:', err)
          // 回退：发送原始数据
          const reader = new FileReader()
          reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1]
            sendAudioData(base64, true, currentMimeType.value)
          }
          reader.readAsDataURL(new Blob(audioChunks))
        }
      }
    }
    
    mediaRecorder.start(300) // 每300ms发送一次
    recordingStartTime = Date.now()
    isRecording.value = true
    
  } catch (error: any) {
    isRecording.value = false  // 确保异常时重置状态
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
      mime_type: mimeType  // 添加格式信息
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
const endCall = () => {
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
}

// 确认结束
const handleEndConfirm = () => {
  showEndDialog.value = false
  router.push('/chat')
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
  startCall()
})

onUnmounted(() => {
  endCall()
})
</script>

<style scoped>
.phone-call-page {
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
  z-index: 10;
}

.back-btn {
  color: #fff;
  font-size: 24px;
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
  padding: 30px 20px 40px;
  position: relative;
  z-index: 10;
}

.main-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 30px;
  margin-bottom: 20px;
}

.control-btn {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #fff;
}

.end-call-btn {
  background: linear-gradient(135deg, #F56C6C 0%, #f78989 100%);
  box-shadow: 0 4px 20px rgba(245, 108, 108, 0.4);
}

.end-call-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 30px rgba(245, 108, 108, 0.6);
}

.mute-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.mute-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.mute-btn.muted {
  background: #E6A23C;
  border-color: #E6A23C;
}

.control-hints {
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.recording-hint {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #67C23A;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #67C23A;
  border-radius: 50%;
  animation: pulse-dot 1s infinite;
}

/* 结束弹窗 */
.end-dialog :deep(.el-dialog) {
  background: #1a1a2e;
  border-radius: 16px;
}

.end-dialog :deep(.el-dialog__title) {
  color: #fff;
}

.end-dialog-content {
  text-align: center;
}

.end-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #409EFF;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.end-message {
  color: #909399;
  font-size: 14px;
  line-height: 1.6;
}
</style>
