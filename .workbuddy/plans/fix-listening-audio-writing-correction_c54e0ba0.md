---
name: fix-listening-audio-writing-correction
overview: 修复两个前端问题：1) 听力训练音频无法播放 - 需解析base64编码 2) 写作批改字段不匹配
---

## 问题概述

用户反馈两个问题：

1. 听力训练通过文本生成的音频无法播放
2. 写作批改点击提交批改没有生效

## 问题分析

### 问题1：听力训练音频无法播放

- **后端返回格式**：`{"code": 0, "data": {"success": true, "audio": "base64编码...", "voice": "en-US-AriaNeural", "duration": 0.819}}`
- **前端期望**：直接二进制音频数据
- **原因**：前端 `listeningApi.tts` 配置了 `responseType: 'blob'`，但实际后端返回的是 JSON 格式包含 base64 编码的音频。前端 `new Blob([res.data])` 将 JSON 对象当作二进制处理，导致无法播放

### 问题2：写作批改提交无效

- **前端期望字段**：`score`, `grammar`, `vocabulary`, `coherence`, `expression`, `overall`, `errors`, `suggestions`, `reference`
- **后端返回字段**：`score: {grammar, vocabulary, fluency, overall}`, `corrected_text`, `corrections`
- **原因**：字段名称不匹配，前端无法正确解析后端返回的数据

## 技术方案

### 解决方案概述

两个问题都通过修改前端代码解决，保持后端接口不变以确保兼容性。

### 问题1修复方案

修改 `frontend/src/api/index.ts` 中的 `listeningApi.tts` 配置，移除 `responseType: 'blob'`，让axios自动解析JSON响应。然后在 `Listening.vue` 的 `playAudio` 函数中解析base64音频数据。

### 问题2修复方案

修改 `Writing.vue` 的 `submitWriting` 函数，当捕获异常时使用模拟数据的逻辑改为：当API调用成功（res.data存在）时，将后端返回的数据转换为前端期望的格式。

## 实现细节

### 问题1实现步骤

1. 修改 `frontend/src/api/index.ts` - 移除 `responseType: 'blob'` 配置
2. 修改 `frontend/src/views/Listening.vue` - 在 `playAudio` 中从 `res.data.audio` 解码base64并创建Blob

### 问题2实现步骤

修改 `frontend/src/views/Writing.vue` - 在 `submitWriting` 中添加数据格式转换逻辑，将后端返回的 `score.grammar/vocabulary/fluency/overall` 转换为前端期望的 `grammar/vocabulary/coherence/expression/score`