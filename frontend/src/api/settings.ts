// Settings API
import { api } from './index'

export interface AISettings {
  id: number
  provider: string
  model: string
  temperature: number
  max_tokens: number
  top_p: number
  base_url: string
  // TTS 配置
  tts_provider: string
  tts_model: string
  // 腾讯云 TTS 配置
  tencent_secret_id?: string
  tencent_secret_key?: string
  tencent_app_id?: string
  // 发音评测配置
  whisper_provider: string
  whisper_model: string
  created_at: string
  updated_at: string
}

export interface Provider {
  id: string
  name: string
  description: string
}

export interface ProvidersResponse {
  providers: Provider[]
}

export interface ModelsResponse {
  provider: string
  models: string[] | { id: string; name: string; size?: string; description?: string }[]
}

// TTS 接口
export interface TTSVoice {
  id: string
  name: string
  gender: string
}

export interface TTSVoicesResponse {
  provider: string
  voices: TTSVoice[]
}

// Get AI settings
export async function getAISettings(): Promise<AISettings> {
  const response = await api.get('/api/settings/ai')
  return response.data
}

// Update AI settings
export async function updateAISettings(data: Partial<AISettings>): Promise<AISettings> {
  const response = await api.post('/api/settings/ai', data)
  return response.data
}

// Get available providers (LLM)
export async function getProviders(): Promise<ProvidersResponse> {
  const response = await api.get('/api/settings/ai/providers')
  return response.data
}

// Get available models for a provider (LLM)
export async function getModels(provider: string): Promise<ModelsResponse> {
  const response = await api.get('/api/settings/ai/models', {
    params: { provider }
  })
  return response.data
}

// TTS: Get available providers
export async function getTTSProviders(): Promise<ProvidersResponse> {
  const response = await api.get('/api/settings/ai/tts/providers')
  return response.data
}

// TTS: Get available voices for a provider
export async function getTTSVoices(provider: string = "edge"): Promise<TTSVoicesResponse> {
  const response = await api.get('/api/settings/ai/tts/voices', {
    params: { provider }
  })
  return response.data
}

// Whisper: Get available providers
export async function getWhisperProviders(): Promise<ProvidersResponse> {
  const response = await api.get('/api/settings/ai/whisper/providers')
  return response.data
}

// Whisper: Get available models for a provider
export async function getWhisperModels(provider: string = "faster-whisper"): Promise<ModelsResponse> {
  const response = await api.get('/api/settings/ai/whisper/models', {
    params: { provider }
  })
  return response.data
}