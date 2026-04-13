# Lexiva - AI 英语学习系统

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Vue](https://img.shields.io/badge/Vue-3+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

> 现代化技术栈 | 极致用户体验 | 开源免费 | 零门槛部署

Lexiva 是一款面向学生的 AI 英语学习 Web 系统，核心定位是「体验优先」——追求媲美商业产品的流畅交互体验，同时保持开源免费、极易部署的特性。

## 🌟 核心特性

### 五个零体验

- **零成本运行**：使用免费开源 AI 模型，不产生任何费用
- **零门槛部署**：Python + SQLite，Windows/Mac/Linux 一键启动
- **零等待响应**：WebSocket 实时通信，对话秒回无刷新
- **零插件体验**：浏览器原生 Web Audio API，语音对话一键搞定
- **零隐私泄露**：所有数据本地存储，不上传云端

### 完整学习闭环

| 模块 | 功能描述 |
|------|----------|
| 🎙️ AI 口语对话 | 流式语音交互 + 自动打断 + 多场景话题 |
| 🗣️ 智能发音评测 | 实时评分 + 详细音素分析 + 对比示范音 |
| ✍️ 写作辅助批改 | AI 批改 + 错误标注 + 写作建议 |
| 🎧 听力材料练习 | 听写练习 + 音频控制 + 即时反馈 |
| 📚 词汇本管理 | 生词添加 + 复习计划 + 记忆曲线 |
| 📊 学习数据统计 | 学习时长 + 正确率趋势 + AI 使用分析 |

### 核心 AI 能力

| 能力 | 技术实现 |
|------|----------|
| 智能对话 | DeepSeek / Qwen 大模型，流式响应 |
| 语音识别 | Whisper (faster-whisper)，支持实时转写 |
| 语音合成 | Edge TTS，多音色选择 |
| 发音评测 | AI 音素打分，细节到每个音节 |
| 写作批改 | AI 自动纠错，语法建议 |

## 🛠️ 技术架构

### 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端框架 | Vue 3 + TypeScript |
| 前端构建 | Vite |
| UI 组件库 | Element Plus |
| 状态管理 | Pinia |
| 后端框架 | FastAPI |
| 数据库 | SQLite + SQLAlchemy |
| 大语言模型 | DeepSeek API / Qwen |
| 语音识别 | Whisper (faster-whisper) |
| 语音合成 | Edge TTS |

### 系统架构

```
┌─────────────────────────────────────────────────┐
│                    前端 (Vue3)                    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │
│  │ 口语对话 │ │ 发音评测 │ │ 写作批改 │ │ 听力练习 │  │
│  └────────┘ └────────┘ └────────┘ └────────┘  │
│  ┌────────┐ ┌────────┐                        │
│  │ 词汇本  │ │ 学习统计 │                        │
│  └────────┘ └────────┘                        │
└─────────────────────────────────────────────────┘
                         │ RESTful / WebSocket
┌─────────────────────────────────────────────────┐
│                   后端 (FastAPI)                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │
│  │ Chat API│ │语音识别 │ │语音合成 │ │发音评测 │  │
│  └────────┘ └────────┘ └────────┘ └────────┘  │
└─────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────┐
│                  数据层 (SQLite)                  │
│  ┌──────────────────────────────────────────┐ │
│  │ users │ conversations │ vocabularies │ ... │ │
│  └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- npm 或 yarn

### 安装部署

#### 1. 克隆项目

```bash
git clone https://github.com/your-repo/lexiva.git
cd lexiva
```

#### 2. 后端启动

```bash
cd backend

# 创建虚拟环境 (可选)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端服务启动后访问：http://localhost:8000/docs 查看 API 文档

#### 3. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动后访问：http://localhost:5173

#### 4. 生产构建

```bash
cd frontend
npm run build
```

构建产物位于 `frontend/dist` 目录

## 📁 项目结构

```
lexiva/
├── .gitignore                 # Git 忽略配置
├── pyproject.toml            # Python 项目配置
├── README.md                  # 本文件
│
├── backend/                   # FastAPI 后端
│   ├── api/                   # API 路由
│   │   ├── chat.py            # AI 对话
│   │   ├── vocabulary.py      # 词汇管理
│   │   ├── writing.py         # 写作批改
│   │   ├── pronunciation.py   # 发音评测
│   │   ├── listening.py       # 听力练习
│   │   ├── statistics.py      # 学习统计
│   │   ├── settings.py        # 系统设置
│   │   └── __init__.py
│   ├── models/                # 数据模型
│   │   └── __init__.py
│   ├── services/              # 业务逻辑
│   │   ├── ai_chat.py         # AI 对话服务
│   │   ├── ai_whisper.py      # 语音识别服务
│   │   ├── ai_tts.py          # 语音合成服务
│   │   ├── writing.py         # 写作批改服务
│   │   └── __init__.py
│   ├── db/                    # 数据库操作
│   │   └── connection.py
│   ├── websocket/             # WebSocket 处理
│   │   └── manager.py
│   ├── main.py                # 应用入口
│   └── requirements.txt       # Python 依赖
│
├── frontend/                  # Vue3 前端
│   ├── src/
│   │   ├── api/              # API 调用 (index.ts)
│   │   ├── components/       # 公共组件
│   │   ├── stores/           # Pinia 状态
│   │   ├── views/            # 页面视图
│   │   │   ├── Home.vue       # 首页
│   │   │   ├── Chat.vue       # AI 对话
│   │   │   ├── Vocabulary.vue # 词汇本
│   │   │   ├── Writing.vue    # 写作
│   │   │   ├── Listening.vue  # 听力
│   │   │   ├── Pronunciation.vue # 发音
│   │   │   └── Statistics.vue # 统计
│   │   ├── App.vue           # 根组件
│   │   └── main.ts           # 入口文件
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
└── docs/                      # 项目文档
    ├── AI英语学习系统体验优先版技术方案.md
    ├── AI英语学习系统学生版技术方案.md
    └── 本地AI语音通话（流式+自动打断+高颜值+轻量高音质）.md
```

## ⚙️ 配置说明

### 环境变量

在 `backend/` 目录下创建 `.env` 文件：

```bash
# ========== AI 模型配置 ==========
# DeepSeek API (对话模型)
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# OpenAI 兼容 API (可选，如使用 Qwen 等)
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# ========== Whisper 语音识别 ==========
# 模型大小: base / small / medium / large-v3
WHISPER_MODEL=base

# ========== Edge TTS 语音合成 ==========
# 默认音色: zh-CN-XiaoxiaoNeural
TTS_VOICE=zh-CN-XiaoxiaoNeural

# ========== 服务器配置 ==========
# API 端口 (默认 8000)
PORT=8000
# 允许的跨域来源
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 配置优先级

1. **环境变量** (`.env` 文件) - 推荐用于生产环境
2. **代码默认值** - 开发环境开箱即用

### AI 模型配置

- **对话模型**：默认使用 DeepSeek API，可配置为 Qwen 本地模型
- **语音识别**：使用 faster-whisper，默认 `base` 模型，可选 `small`/`medium`/`large-v3`
- **语音合成**：使用 Edge TTS，支持多种音色

## 📝 功能文档

详细技术方案请参考 [docs/](docs/) 目录下的文档：

| 文档 | 说明 |
|------|------|
| [体验优先版技术方案](docs/AI英语学习系统体验优先版技术方案.md) | 完整技术架构与实现细节 |
| [学生版技术方案](docs/AI英语学习系统学生版技术方案.md) | 功能需求与产品设计 |
| [本地AI语音通话](docs/本地AI语音通话（流式+自动打断+高颜值+轻量高音质）.md) | 实时语音对话技术实现 |

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'Add xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

## 📄 开源协议

本项目基于 MIT 协议开源。

---

<p align="center">Made with ❤️ for English Learners</p>
