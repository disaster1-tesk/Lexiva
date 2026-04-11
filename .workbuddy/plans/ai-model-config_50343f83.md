---
name: ai-model-config
overview: 创建 AI 模型配置功能，支持 DeepSeek/OpenAI/Ollama 三种服务，可配置 API Key、模型、温度等参数，界面包含设置页面和右上角下拉菜单
design:
  architecture:
    framework: react
  styleKeywords:
    - Element Plus
    - 卡片式布局
    - 下拉菜单
  fontSystem:
    fontFamily: system-ui
    heading:
      size: 20px
      weight: 600
    subheading:
      size: 16px
      weight: 500
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#409EFF"
    background:
      - "#FFFFFF"
      - "#F5F7FA"
    text:
      - "#303133"
      - "#606266"
    functional:
      - "#67C23A"
      - "#F56C6C"
todos:
  - id: create-ai-settings-table
    content: 创建ai_settings数据库表模型
    status: completed
  - id: create-settings-api
    content: 新建backend/api/settings.py设置API路由
    status: completed
    dependencies:
      - create-ai-settings-table
  - id: refactor-ai-chat-service
    content: 重构backend/services/ai_chat.py支持多提供商
    status: completed
    dependencies:
      - create-ai-settings-table
  - id: create-settings-api-client
    content: 新建frontend/src/api/settings.ts前端API调用
    status: completed
  - id: create-settings-page
    content: 新建frontend/src/views/Settings.vue设置页面
    status: completed
    dependencies:
      - create-settings-api-client
  - id: add-settings-router
    content: 修改router/index.ts添加Settings路由
    status: completed
    dependencies:
      - create-settings-page
  - id: add-header-dropdown
    content: 修改App.vue添加右上角下拉菜单入口
    status: completed
    dependencies:
      - create-settings-api-client
---

## 用户需求

- 需要一个地方可以配置AI模型
- 支持多种AI服务提供商：DeepSeek API、OpenAI API、Ollama本地部署
- 可配置参数：API Key、模型选择、温度(top_p)、最大token数等
- 配置界面：设置页面 + 右上角下拉菜单

## 产品概述

AI英语学习系统的AI模型配置功能，允许用户在界面上切换不同的AI服务提供商并调整模型参数

## 核心功能

- AI服务提供商切换（DeepSeek/OpenAI/Ollama）
- API Key配置和安全管理
- 模型选择（根据提供商动态加载可选模型）
- 高级参数调整（temperature、max_tokens、top_p等）
- 设置页面完整表单
- 右上角快速访问下拉菜单

## 技术栈

- 后端：FastAPI + SQLite
- 前端：Vue3 + TypeScript + Element Plus
- 存储：SQLite数据库 + localStorage

## 技术架构

### 后端架构

1. **数据库层**：新建 `ai_settings` 表存储AI配置
2. **服务层**：重构 `backend/services/ai_chat.py` 支持多提供商动态切换
3. **API层**：新增 `/api/settings/ai` 路由（GET/POST）

### 前端架构

1. **路由**：新增 `/settings` 页面
2. **状态管理**：使用 localStorage 存储当前AI配置
3. **组件**：

- 新增 `views/Settings.vue` 设置页面
- 修改 `App.vue` 添加右上角下拉菜单

### 数据流

```
用户选择配置 → 前端localStorage保存 → 后端API接收 → 数据库存储 → AI服务调用时读取
```

### 模块划分

- `backend/api/settings.py` - [NEW] 设置API
- `backend/services/ai_chat.py` - [MODIFY] 支持多提供商
- `backend/db/models.py` - [MODIFY] 新增AI配置模型
- `frontend/src/views/Settings.vue` - [NEW] 设置页面
- `frontend/src/App.vue` - [MODIFY] 添加右上角菜单
- `frontend/src/router/index.ts` - [MODIFY] 添加Settings路由
- `frontend/src/api/settings.ts` - [NEW] 设置API调用

## 设计风格

采用与现有项目一致的Element Plus组件风格，保持深色侧边栏+浅色内容区的布局。设置页面使用卡片式布局，右上角使用下拉菜单。

## UI设计

### 设置页面

- 使用 el-card 卡片组件布局
- 分区展示：提供商选择、API配置、高级参数
- 使用 el-select 下拉选择提供商
- 使用 el-input 配置API Key（密码模式）
- 使用 el-slider 调节温度参数

### 右上角菜单

- 在现有学习天数标签旁添加下拉菜单
- 显示当前使用的AI提供商和模型
- 快速跳转到设置页面