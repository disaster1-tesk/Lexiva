/*
 * API Service
 * Axios API calls to backend
 */
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Chat API
export const chatApi = {
  send: (message: string, scene: string = 'daily') =>
    api.post('/api/chat/send', { message, scene }),
  
  getHistory: (page = 1, limit = 20) =>
    api.get('/api/chat/history', { params: { page, limit } }),
  
  clearHistory: () =>
    api.post('/api/chat/clear')
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
  
  review: (wordId: number, result: string) =>
    api.post('/api/vocabulary/review', { word_id: wordId, result }),
  
  toReview: () => api.get('/api/vocabulary/to-review')
}

// Pronunciation API
export const pronunciationApi = {
  record: (audio: Blob, sentenceId: number) => {
    const formData = new FormData()
    formData.append('audio', audio)
    formData.append('sentence_id', String(sentenceId))
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
    api.get('/api/statistics/trend', { params: { days } })
}

export default api