/*
 * Chat Store
 * Manages chat conversation state across components
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  time: string
  corrections?: Array<{ original: string; corrected: string }>
  recognizedText?: string
  audio?: string
}

export const useChatStore = defineStore('chat', () => {
  // 消息列表
  const messages = ref<ChatMessage[]>([])

  // 当前场景
  const currentScene = ref('daily')

  // 是否正在加载
  const isLoading = ref(false)

  // 添加消息
  const addMessage = (msg: ChatMessage) => {
    messages.value.push(msg)
    // 持久化到 sessionStorage
    saveToStorage()
  }

  // 更新最后一条AI消息（用于流式输出）
  const updateLastAssistantMessage = (content: string, corrections?: Array<{ original: string; corrected: string }>) => {
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg.role === 'assistant') {
        lastMsg.content = content
        if (corrections) {
          lastMsg.corrections = corrections
        }
      }
    }
    saveToStorage()
  }

  // 获取当前时间
  const getCurrentTime = () => {
    const now = new Date()
    return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
  }

  // 持久化到 sessionStorage
  const saveToStorage = () => {
    try {
      sessionStorage.setItem('chat_messages', JSON.stringify({
        messages: messages.value,
        scene: currentScene.value
      }))
    } catch (e) {
      console.error('Failed to save chat to storage:', e)
    }
  }

  // 从 sessionStorage 加载
  const loadFromStorage = () => {
    try {
      const stored = sessionStorage.getItem('chat_messages')
      if (stored) {
        const data = JSON.parse(stored)
        messages.value = data.messages || []
        currentScene.value = data.scene || 'daily'
        return true
      }
    } catch (e) {
      console.error('Failed to load chat from storage:', e)
    }
    return false
  }

  // 清除消息
  const clearMessages = () => {
    messages.value = []
    currentScene.value = 'daily'
    sessionStorage.removeItem('chat_messages')
  }

  // 检查是否有保存的消息
  const hasStoredMessages = () => {
    const stored = sessionStorage.getItem('chat_messages')
    return !!stored
  }

  return {
    messages,
    currentScene,
    isLoading,
    addMessage,
    updateLastAssistantMessage,
    clearMessages,
    loadFromStorage,
    hasStoredMessages,
    getCurrentTime
  }
})