---
name: week4-listening-stats
overview: 完善听力训练工具和学习中心：实现Listening.vue页面功能，创建Stats.vue学习统计页面
design:
  styleKeywords:
    - Element Plus
    - Modern Dashboard
    - Responsive Layout
    - ECharts Visualization
  fontSystem:
    fontFamily: system-ui
    heading:
      size: 24px
      weight: 600
    subheading:
      size: 18px
      weight: 500
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#409EFF"
      - "#337ECC"
    background:
      - "#FAFAFA"
      - "#FFFFFF"
    text:
      - "#303133"
      - "#606266"
    functional:
      - "#67C23A"
      - "#F56C6C"
      - "#E6A23C"
todos:
  - id: week4-router-setup
    content: 配置前端路由系统 router/index.ts
    status: completed
  - id: week4-app-layout
    content: 实现App.vue导航布局
    status: completed
    dependencies:
      - week4-router-setup
  - id: week4-home-page
    content: 实现Home.vue首页统计面板
    status: completed
    dependencies:
      - week4-app-layout
  - id: week4-chat-page
    content: 实现Chat.vue AI对话页面
    status: completed
    dependencies:
      - week4-app-layout
  - id: week4-listening-page
    content: 实现Listening.vue听力训练页面
    status: completed
    dependencies:
      - week4-app-layout
  - id: week4-pronunciation-page
    content: 实现Pronunciation.vue发音评测页面
    status: completed
    dependencies:
      - week4-app-layout
  - id: week4-vocabulary-page
    content: 实现Vocabulary.vue单词本页面
    status: completed
    dependencies:
      - week4-app-layout
---

## 项目背景

AI英语学习系统 Web版 Week4 任务：完善前端界面和学习统计功能。

## 当前状态

**后端 (已就绪)**：

- FastAPI 已注册所有路由
- listening.py - TTS和听写API已实现
- statistics.py - 统计API框架已实现（返回mock数据）
- services/ai_tts.py - Edge TTS语音合成
- services/ai_whisper.py - Whisper语音识别

**前端 (待开发)**：

- 框架：Vue 3.4 + Vite 5.0 + Element Plus
- 所有Vue文件为空：Chat.vue, Home.vue, Listening.vue, Pronunciation.vue, Vocabulary.vue, Writing.vue
- 缺少：路由配置、App.vue导航布局、Stats.vue统计页面

## Week4任务目标

1. 完善前端路由和导航系统
2. 实现6个核心页面的完整UI
3. 新增学习统计页面（Stats.vue）
4. 后端统计功能与数据库集成

## 技术栈

### 后端

- **框架**: FastAPI 0.109.0
- **ORM**: SQLAlchemy（已有模型）
- **统计图表**: ECharts 数据格式

### 前端

- **框架**: Vue 3.4 + Vite 5.0
- **路由**: Vue Router 4.2（已安装未配置）
- **状态**: Pinia 2.1（已安装未配置）
- **UI**: Element Plus 2.5
- **图表**: ECharts 5.4 + vue-echarts

## 架构设计

### 前端架构

- **布局**: 左侧导航栏 + 右侧内容区
- **路由配置**: /home, /chat, /pronunciation, /listening, /vocabulary, /writing, /stats
- **API调用**: 通过 api/index.ts 统一调用后端

### 目录结构

```
frontend/src/
├── App.vue           # [MODIFY] 导航布局
├── main.ts           # [MODIFY] 挂载router
├── router/index.ts   # [NEW] 路由配置
├── views/
│   ├── Home.vue      # [NEW] 首页统计面板
│   ├── Chat.vue      # [NEW] AI对话页面
│   ├── Listening.vue # [NEW] 听力训练页面
│   ├── Pronunciation.vue # [NEW] 发音评测页面
│   ├── Vocabulary.vue    # [NEW] 单词本页面
│   ├── Writing.vue       # [NEW] 写作批改页面
│   └── Stats.vue        # [NEW] 学习统计页面
```

## 页面设计

采用 Element Plus 组件库，构建现代化英语学习平台界面。

### 公共布局

- 左侧固定导航栏（el-menu），宽度220px
- 右侧内容区（el-main），白色背景
- 顶部带面包屑导航

### 页面设计

- **Home**: 统计卡片 + 快捷入口
- **Chat**: 聊天气泡 + 实时对话
- **Listening**: TTS播放器 + 听写输入框
- **Pronunciation**: 音频波形 + 评测结果
- **Vocabulary**: 单词卡片表格 + 复习进度
- **Writing**: 富文本编辑器 + AI批改结果
- **Stats**: ECharts 折线图 + 饼图

### 配色

- 主色: #409EFF (Element Blue)
- 背景: #FAFAFA
- 文字: #303133

## 可用扩展

无额外扩展，需手动实现所有功能。