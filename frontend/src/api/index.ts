/*
 * API Service
 * Axios API calls to backend
 */
import axios from 'axios'

// 支持环境变量配置，默认使用相对路径（通过代理）
const API_BASE = import.meta.env.VITE_API_BASE || ''

/**
 * 从 API 响应中提取数据
 * 兼容多种响应格式:
 * - { code: 0, data: {...} }
 * - { data: {...} }
 * - {...} (直接返回)
 */
const getResponseData = <T = any>(res: any, defaultValue: T | null = null): T => {
  if (!res) return defaultValue
  // 尝试多种路径: res.data.data > res.data > res
  return res?.data?.data ?? res?.data ?? res ?? defaultValue
}

/**
 * 检查 API 响应是否成功
 */
const isResponseSuccess = (res: any): boolean => {
  if (!res) return false
  // 检查 code 字段（可能不存在）
  return res.code === 0 || res.code === undefined
}

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 导出工具函数供其他模块使用
export { getResponseData, isResponseSuccess, api }

// Chat API
export const chatApi = {
  send: (message: string, scene: string = 'daily') =>
    api.post('/api/chat/send', { message, scene }),

  // 流式对话
  streamSend: (message: string, scene: string = 'daily') => {
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
    const baseUrl = API_BASE || `${protocol}//${window.location.host}`
    const url = `${baseUrl}/api/chat/stream`

    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message, scene })
    })
  },

  getHistory: (page = 1, limit = 20) =>
    api.get('/api/chat/history', { params: { page, limit } }),
  
  clearHistory: () =>
    api.post('/api/chat/clear'),

  // 语音对话：发送音频，获取文字回复+语音
  voiceChat: (audio: Blob, scene: string = 'daily', mimeType: string = 'audio/webm') => {
    const formData = new FormData()
    // 根据 Blob 类型动态设置文件名后缀
    const filename = audio.type.includes('mp4') ? 'recording.m4a' : 'recording.webm'
    formData.append('audio', audio, filename)
    formData.append('scene', scene)
    formData.append('mime_type', mimeType)  // 传递录音格式
    return api.post('/api/chat/voice', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000  // 语音对话需要更长的超时时间
    })
  },

  // WebSocket 实时语音对话
  createRealtimeChat: () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`
    return new WebSocket(wsUrl)
  },

  // WebSocket 全双工电话通话
  createPhoneCall: () => {
    // 使用与 API 相同的后端地址
    const wsHost = API_BASE ? new URL(API_BASE).host : window.location.host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${wsHost}/ws/phone`
    console.log('[PhoneCall] Connecting to:', wsUrl)
    return new WebSocket(wsUrl)
  }
}

// Writing API
export const writingApi = {
  correct: (text: string, examType = 'general') =>
    api.post('/api/writing/correct', { text, exam_type: examType }),
  
  getHistory: (page = 1, limit = 20) =>
    api.get('/api/writing/history', { params: { page, limit } })
}

// Vocabulary API
export const vocabApi = {
  getList: () => api.get('/api/vocabulary/list'),

  add: (word: string) => api.post('/api/vocabulary/add', { word }),

  delete: (id: number) => api.delete(`/api/vocabulary/${id}`),

  // 批量添加单词到单词本
  batchAdd: (words: any[]) => api.post('/api/vocabulary/batch-add', { words }),

  review: (wordId: number, result: string) =>
    api.post('/api/vocabulary/review', { word_id: wordId, result }),

  toReview: () => api.get('/api/vocabulary/to-review'),

  // AI生成单词（支持排除已默写的单词）
  generate: (params: { topic: string; count: number; exclude_words?: string[] }) =>
    api.post('/api/vocabulary/generate', params),

  // 拼写检查
  spellCheck: (params: { word: string; answer: string }) =>
    api.post('/api/vocabulary/spell-check', params),

  // 音标评测
  phoneticCheck: (params: { word: string; phonetic: string; audio: string }) =>
    api.post('/api/vocabulary/phonetic-check', params, {
      headers: { 'Content-Type': 'application/json' }
    })
}

// Pronunciation API
export const pronunciationApi = {
  record: (audio: Blob, sentenceId: number, sentenceText?: string, mimeType: string = 'audio/webm') => {
    const formData = new FormData()
    formData.append('audio', audio)
    formData.append('sentence_id', String(sentenceId))
    if (sentenceText) {
      formData.append('sentence_text', sentenceText)
    }
    formData.append('mime_type', mimeType)  // 传递录音格式
    return api.post('/api/pronunciation/record', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  getSentences: (difficulty?: string) =>
    api.get('/api/pronunciation/sentences', { params: { difficulty } }),
  
  getSentenceAudio: (id: number) =>
    api.get(`/api/pronunciation/sentence/${id}/audio`)  // 移除responseType: 'blob'
}

// Listening API
export const listeningApi = {
  tts: (text: string, speed = 1.0, voice = 'en-US-AriaNeural') =>
    api.post('/api/listening/tts', { text, speed, voice }),
  
  dictation: (text: string, reference: string) =>
    api.post('/api/listening/dictation', { text, reference }),
  
  getMaterials: () => api.get('/api/listening/materials')
}

// Statistics API
export const statisticsApi = {
  getSummary: () => api.get('/api/statistics/summary'),
  
  getTrend: (days = 7) =>
    api.get('/api/statistics/trend', { params: { days } }),
  
  getActivities: (days = 7) =>
    api.get('/api/statistics/activities', { params: { days } })
}

// Dictation API
export const dictationApi = {
  generate: (params: { theme: string; word_count: number; modes: string[] }) =>
    api.post('/api/dictation/generate', params),
  
  submit: (params: { question_id: string; answer: string; mode: string }) =>
    api.post('/api/dictation/submit', params),
  
  getThemes: () => api.get('/api/dictation/themes')
}

// Grammar API
export const grammarApi = {
  getTopics: () => api.get('/api/grammar/topics'),

  getTopicsByCategory: (categoryId: string) =>
    api.get(`/api/grammar/topics/${categoryId}`),

  learn: (topicId: string) =>
    api.post('/api/grammar/learn', { topic_id: topicId }),

  submitExercise: (params: { topic_id: string; exercise_id: number; answer: string }) =>
    api.post('/api/grammar/exercise', params),

  recommend: () => api.get('/api/grammar/recommend'),

  // AI生成语法
  generate: (params: { category: string; count: number }) =>
    api.post('/api/grammar/generate', params)
}

export default api