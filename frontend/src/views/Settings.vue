<template>
  <div class="settings-page">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span class="title">AI 模型配置</span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAISettings, updateAISettings, getProviders, getModels } from '@/api/settings'
import type { FormInstance, FormRules } from 'element-plus'

const formRef = ref<FormInstance>()
const saving = ref(false)
const testing = ref(false)

const providers = ref<{ id: string; name: string; description: string }[]>([])
const availableModels = ref<string[]>([])

const form = reactive({
  provider: 'deepseek',
  api_key: '',
  model: 'deepseek-chat',
  temperature: 0.7,
  max_tokens: 1000,
  top_p: 1.0,
  base_url: ''
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
    await formRef.value.validate()
    await updateAISettings({
      provider: form.provider,
      api_key: form.api_key,
      model: form.model,
      temperature: form.temperature,
      max_tokens: form.max_tokens,
      top_p: form.top_p,
      base_url: form.base_url
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
  await loadSettings()
})
</script>

<style scoped>
.settings-page {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.settings-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: 600;
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