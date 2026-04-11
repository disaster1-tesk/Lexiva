// Settings API
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

export interface AISettings {
  id: number
  provider: string
  model: string
  temperature: number
  max_tokens: number
  top_p: number
  base_url: string
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
  models: string[]
}

// Get AI settings
export async function getAISettings(): Promise<AISettings> {
  const response = await axios.get(`${API_BASE}/api/settings/ai`)
  return response.data
}

// Update AI settings
export async function updateAISettings(data: Partial<AISettings>): Promise<AISettings> {
  const response = await axios.post(`${API_BASE}/api/settings/ai`, data)
  return response.data
}

// Get available providers
export async function getProviders(): Promise<ProvidersResponse> {
  const response = await axios.get(`${API_BASE}/api/settings/ai/providers`)
  return response.data
}

// Get available models for a provider
export async function getModels(provider: string): Promise<ModelsResponse> {
  const response = await axios.get(`${API_BASE}/api/settings/ai/models`, {
    params: { provider }
  })
  return response.data
}