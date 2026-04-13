<template>
  <div class="settings-page">
    <!-- 当前配置概览 -->
    <el-card class="config-overview" v-if="currentConfig">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Monitor /></el-icon>
            当前配置
          </span>
          <el-tag :type="connectionStatus === 'connected' ? 'success' : 'info'">
            {{ connectionStatus === 'connected' ? '已连接' : '未测试' }}
          </el-tag>
        </div>
      </template>
      <div class="config-info">
        <div class="config-item">
          <span class="config-label">服务厂商</span>
          <span class="config-value">{{ getProviderName(currentConfig.provider) }}</span>
        </div>
        <div class="config-item">
          <span class="config-label">模型</span>
          <span class="config-value">{{ currentConfig.model }}</span>
        </div>
        <div class="config-item">
          <span class="config-label">Temperature</span>
          <span class="config-value">{{ currentConfig.temperature }}</span>
        </div>
        <div class="config-item">
          <span class="config-label">Max Tokens</span>
          <span class="config-value">{{ currentConfig.max_tokens }}</span>
        </div>
      </div>
      <!-- 可用厂商列表 -->
      <div class="available-providers">
        <span class="label">可用厂商：</span>
        <el-tag v-for="p in providers" :key="p.id" :type="p.id === currentConfig.provider ? 'primary' : 'info'" size="small" class="provider-tag">
          {{ p.name }}
        </el-tag>
      </div>
    </el-card>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><ChatLineRound /></el-icon>
            AI 模型配置
          </span>
        </div>
      </template>
      
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <!-- Provider Selection -->
        <el-form-item label="服务提供商" prop="provider">
          <el-select v-model="form.provider" placeholder="选择 AI 服务提供商" @change="onProviderChange">
            <el-option v-for="p in providers" :key="p.id" :label="p.name" :value="p.id">
              <span>{{ p.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 12px">{{ p.description }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        
        <!-- API Key -->
        <el-form-item label="API Key" prop="api_key">
          <el-input 
            v-model="form.api_key" 
            type="password" 
            show-password
            placeholder="请输入 API Key"
          ></el-input>
          <div class="form-tip">
            <span v-if="form.provider === 'deepseek'">DeepSeek: 在 deepseek.com 获取</span>
            <span v-else-if="form.provider === 'openai'">OpenAI: 在 platform.openai.com 获取</span>
            <span v-else-if="form.provider === 'ollama'">Ollama: 本地部署，无需 API Key</span>
          </div>
        </el-form-item>
        
        <!-- Model Selection -->
        <el-form-item label="模型选择" prop="model">
          <el-select 
            v-model="form.model" 
            placeholder="选择或输入模型名称"
            filterable
            allow-create
            default-first-option
            :reserve-keyword="false"
          >
            <el-option v-for="m in availableModels" :key="m" :label="m" :value="m" />
          </el-select>
          <div class="form-tip">可从列表选择或自定义输入模型名称</div>
        </el-form-item>
        
        <!-- Advanced Parameters -->
        <el-divider>高级参数</el-divider>
        
        <!-- Temperature -->
        <el-form-item label="Temperature">
          <div class="slider-wrapper">
            <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-stops />
            <span class="slider-value">{{ form.temperature }}</span>
          </div>
          <div class="form-tip">控制输出的随机性，值越高越有创意</div>
        </el-form-item>
        
        <!-- Max Tokens -->
        <el-form-item label="Max Tokens">
          <el-input-number v-model="form.max_tokens" :min="100" :max="4000" :step="100" />
          <div class="form-tip">单次回复的最大 token 数</div>
        </el-form-item>
        
        <!-- Top P -->
        <el-form-item label="Top P">
          <div class="slider-wrapper">
            <el-slider v-model="form.top_p" :min="0" :max="1" :step="0.1" show-stops />
            <span class="slider-value">{{ form.top_p }}</span>
          </div>
          <div class="form-tip">核采样参数</div>
        </el-form-item>
        
        <!-- Base URL (for Ollama) -->
        <el-form-item label="API 地址" v-if="form.provider === 'ollama'">
          <el-input v-model="form.base_url" placeholder="http://localhost:11434" />
          <div class="form-tip">Ollama 本地服务地址</div>
        </el-form-item>
        
        <!-- Save Button -->
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">保存配置</el-button>
          <el-button @click="testConnection" :loading="testing">测试连接</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- TTS 配置 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Microphone /></el-icon>
            语音合成 (TTS) 配置
          </span>
        </div>
      </template>
      
      <el-form label-width="120px">
        <el-form-item label="服务提供商">
          <el-select v-model="form.tts_provider" placeholder="选择 TTS 服务" @change="onTTSProviderChange">
            <el-option v-for="p in ttsProviders" :key="p.id" :label="p.name" :value="p.id">
              <span>{{ p.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 12px">{{ p.description }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        
        <!-- 腾讯云 TTS 密钥配置 -->
        <template v-if="form.tts_provider === 'tencent'">
          <el-form-item label="Secret ID">
            <el-input 
              v-model="form.tencent_secret_id" 
              type="password" 
              show-password
              placeholder="腾讯云 SecretId"
            ></el-input>
          </el-form-item>
          <el-form-item label="Secret Key">
            <el-input 
              v-model="form.tencent_secret_key" 
              type="password" 
              show-password
              placeholder="腾讯云 SecretKey"
            ></el-input>
          </el-form-item>
          <el-form-item label="App ID">
            <el-input 
              v-model="form.tencent_app_id" 
              placeholder="腾讯云 AppId (可选)"
            ></el-input>
          </el-form-item>
        </template>
        
        <el-form-item label="语音选择">
          <el-select v-model="form.tts_model" placeholder="选择语音">
            <el-option v-for="v in ttsVoices" :key="v.id" :label="v.name" :value="v.id">
              <span>{{ v.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 12px">{{ v.gender }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 发音评测配置 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Setting /></el-icon>
            发音评测 (Whisper) 配置
          </span>
        </div>
      </template>
      
      <el-form label-width="120px">
        <el-form-item label="服务提供商">
          <el-select v-model="form.whisper_provider" placeholder="选择语音识别服务" @change="onWhisperProviderChange">
            <el-option v-for="p in whisperProviders" :key="p.id" :label="p.name" :value="p.id">
              <span>{{ p.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 12px">{{ p.description }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型选择">
          <el-select v-model="form.whisper_model" placeholder="选择模型">
            <el-option v-for="m in whisperModels" :key="m.id" :label="m.name" :value="m.id">
              <span>{{ m.name }}</span>
              <span v-if="m.size" style="float: right; color: #8492a6; font-size: 12px">{{ m.size }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getAISettings,
  updateAISettings,
  getProviders,
  getModels,
  getTTSProviders,
  getTTSVoices,
  getWhisperProviders,
  getWhisperModels
} from '@/api/settings'
import { Monitor, Setting, Microphone, ChatLineRound } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

const formRef = ref<FormInstance>()
const saving = ref(false)
const testing = ref(false)
const connectionStatus = ref<'connected' | 'disconnected' | 'untested'>('untested')
const currentConfig = ref<{
  provider: string
  model: string
  temperature: number
  max_tokens: number
  top_p: number
  base_url: string
} | null>(null)

const providers = ref<{ id: string; name: string; description: string }[]>([])
const availableModels = ref<string[]>([])

// TTS 相关
const ttsProviders = ref<{ id: string; name: string; description: string }[]>([])
const ttsVoices = ref<{ id: string; name: string; gender: string }[]>([])

// Whisper 相关
const whisperProviders = ref<{ id: string; name: string; description: string }[]>([])
const whisperModels = ref<{ id: string; name: string; size?: string }[]>([])

// 厂商名称映射
function getProviderName(providerId: string): string {
  const map: Record<string, string> = {
    deepseek: 'DeepSeek',
    openai: 'OpenAI',
    ollama: 'Ollama (本地)'
  }
  return map[providerId] || providerId
}

const form = reactive({
  provider: 'deepseek',
  api_key: '',
  model: 'deepseek-chat',
  temperature: 0.7,
  max_tokens: 1000,
  top_p: 1.0,
  base_url: '',
  // TTS 配置
  tts_provider: 'edge',
  tts_model: 'en-US-AriaNeural',
  // 腾讯云 TTS 配置
  tencent_secret_id: '',
  tencent_secret_key: '',
  tencent_app_id: '',
  // Whisper 配置
  whisper_provider: 'faster-whisper',
  whisper_model: 'base'
})

const rules: FormRules = {
  provider: [{ required: true, message: '请选择服务提供商', trigger: 'change' }],
  model: [{ required: true, message: '请选择模型', trigger: 'change' }]
}

// Load providers
async function loadProviders() {
  try {
    const res = await getProviders()
    providers.value = res.providers
  } catch (e) {
    console.error('Failed to load providers:', e)
  }
}

// Load available models for provider
async function loadModels(provider: string) {
  try {
    const res = await getModels(provider)
    availableModels.value = res.models
  } catch (e) {
    console.error('Failed to load models:', e)
  }
}

// 加载 TTS 配置
async function loadTTSConfig() {
  try {
    const res = await getTTSProviders()
    ttsProviders.value = res.providers
    await onTTSProviderChange(form.tts_provider)
  } catch (e) {
    console.error('Failed to load TTS providers:', e)
  }
}

async function onTTSProviderChange(provider: string) {
  try {
    const res = await getTTSVoices(provider)
    ttsVoices.value = res.voices
  } catch (e) {
    console.error('Failed to load TTS voices:', e)
  }
}

// 加载 Whisper 配置
async function loadWhisperConfig() {
  try {
    const res = await getWhisperProviders()
    whisperProviders.value = res.providers
    await onWhisperProviderChange(form.whisper_provider)
  } catch (e) {
    console.error('Failed to load Whisper providers:', e)
  }
}

async function onWhisperProviderChange(provider: string) {
  try {
    const res = await getWhisperModels(provider)
    whisperModels.value = res.models as { id: string; name: string; size?: string }[]
  } catch (e) {
    console.error('Failed to load Whisper models:', e)
  }
}

// Load settings
async function loadSettings() {
  try {
    const res = await getAISettings()
    form.provider = res.provider
    form.model = res.model
    form.temperature = res.temperature
    form.max_tokens = res.max_tokens
    form.top_p = res.top_p
    form.base_url = res.base_url
    
    // TTS 配置
    form.tts_provider = res.tts_provider || 'edge'
    form.tts_model = res.tts_model || 'en-US-AriaNeural'
    // 腾讯云 TTS 配置
    form.tencent_secret_id = res.tencent_secret_id || ''
    form.tencent_secret_key = res.tencent_secret_key || ''
    form.tencent_app_id = res.tencent_app_id || ''
    
    // Whisper 配置
    form.whisper_provider = res.whisper_provider || 'faster-whisper'
    form.whisper_model = res.whisper_model || 'base'
    
    // 保存当前配置用于展示
    currentConfig.value = {
      provider: res.provider,
      model: res.model,
      temperature: res.temperature,
      max_tokens: res.max_tokens,
      top_p: res.top_p,
      base_url: res.base_url
    }
    
    await loadModels(res.provider)
  } catch (e) {
    console.error('Failed to load settings:', e)
  }
}

// Provider change handler
async function onProviderChange(provider: string) {
  await loadModels(provider)
  // Set default model
  if (provider === 'deepseek') {
    form.model = 'deepseek-chat'
  } else if (provider === 'openai') {
    form.model = 'gpt-4o-mini'
  } else if (provider === 'ollama') {
    form.model = 'llama3'
  }
}

// Save settings
async function saveSettings() {
  if (!formRef.value) return
  
  saving.value = true
  try {
    await updateAISettings({
      provider: form.provider,
      api_key: form.api_key,
      model: form.model,
      temperature: form.temperature,
      max_tokens: form.max_tokens,
      top_p: form.top_p,
      base_url: form.base_url,
      tts_provider: form.tts_provider,
      tts_model: form.tts_model,
      // 腾讯云 TTS 配置
      tencent_secret_id: form.tencent_secret_id,
      tencent_secret_key: form.tencent_secret_key,
      tencent_app_id: form.tencent_app_id,
      whisper_provider: form.whisper_provider,
      whisper_model: form.whisper_model
    })
    ElMessage.success('配置保存成功')
  } catch (e: any) {
    if (e?.response?.data?.detail) {
      ElMessage.error(e.response.data.detail)
    } else if (e !== 'cancel') {
      ElMessage.error('保存失败')
    }
  } finally {
    saving.value = false
  }
}

// Test connection
async function testConnection() {
  testing.value = true
  try {
    // Just try to save, the backend will validate
    await updateAISettings({
      provider: form.provider,
      api_key: form.api_key,
      model: form.model,
      temperature: form.temperature,
      max_tokens: form.max_tokens,
      top_p: form.top_p,
      base_url: form.base_url
    })
    ElMessage.success('配置有效')
  } catch (e: any) {
    if (e?.response?.data?.detail) {
      ElMessage.warning(e.response.data.detail)
    } else {
      ElMessage.warning('连接测试暂不可用，请在聊天界面测试')
    }
  } finally {
    testing.value = false
  }
}

onMounted(async () => {
  await loadProviders()
  await loadTTSConfig()
  await loadWhisperConfig()
  await loadSettings()
})
</script>

<style scoped>
.settings-page {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.config-overview {
  margin-bottom: 20px;
}

.config-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.config-item {
  display: flex;
  flex-direction: column;
}

.config-label {
  font-size: 12px;
  color: #8492a6;
  margin-bottom: 4px;
}

.config-value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.available-providers {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #ebeef5;
}

.available-providers .label {
  font-size: 12px;
  color: #8492a6;
  margin-right: 8px;
}

.provider-tag {
  margin-right: 8px;
}

.settings-card {
  margin-bottom: 32px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-tip {
  font-size: 12px;
  color: #8492a6;
  margin-top: 4px;
}

.slider-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
}

.slider-wrapper .el-slider {
  flex: 1;
}

.slider-value {
  width: 40px;
  text-align: right;
  margin-left: 12px;
  font-weight: 500;
}
</style>