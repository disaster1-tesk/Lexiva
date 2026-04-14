<!-- PROJECT LOGO -->
<br/>
<div align=center>

![Lexiva Logo](frontend/public/logo.png)

# Lexiva

_AI 英语学习系统 | 体验优先 | 开源免费_

[![Version](https://img.shields.io/badge/version-0.1.0-blue)]()
[![Python](https://img.shields.io/badge/python-3.10+-green)]()
[![Vue](https://img.shields.io/badge/Vue-3+-green)]()
[![License](https://img.shields.io/badge/license-MIT-orange)]()
[![Platform](https://img.shields.io/badge/platform-Windows|Mac|Linux-blue)]()

</div>

---

## ⭐ 项目简介

Lexiva 是一款面向学生的 **AI 英语学习 Web 系统**，核心定位是「体验优先」——追求媲美商业产品的流畅交互体验，同时保持开源免费、极易部署的特性。

**五大核心优势：**

| ⚡ 零成本 | 🚀 零门槛 | 💨 零等待 | 🔊 零插件 | 🔒 零泄露 |
|:---:|:---:|:---:|:---:|:---:|
| 免费开源 AI 模型 | Python + SQLite | WebSocket 实时通信 | 浏览器原生 Web Audio | 数据本地存储 |

---

## ✨ 功能特性

### 📖 学习模块

| 模块 | 功能描述 |
|:---:|:---|
| 🎙️ AI 口语对话 | 流式语音交互 + 自动打断 + 多场景话题 |
| 🗣️ 智能发音评测 | 实时评分 + 详细音素分析 + 对比示范音 |
| ✍️ 写作辅助批改 | AI 批改 + 错误标注 + 写作建议 |
| 🎧 听力材料练习 | 听写练习 + 音频控制 + 即时反馈 |
| 📚 词汇本管理 | 生词添加 + 复习计划 + 记忆曲线 |
| 📊 学习数据统计 | 学习时长 + 正确率趋势 + AI 使用分析 |

### 🤖 AI 能力

| 能力 | 技术实现 |
|:---:|:---|
| 智能对话 | DeepSeek / Qwen 大模型，流式响应 |
| 语音识别 | Whisper (faster-whisper)，支持实时转写 |
| 语音合成 | Edge TTS，多音色选择 |
| 发音评测 | AI 音素打分，细节到每个音节 |
| 写作批改 | AI 自动纠错，语法建议 |

---

## 🛠️ 技术栈

<div align=center>

| 分类 | 技术 |
|:---:|:---|
| **前端** | Vue 3 + TypeScript + Vite + Element Plus + Pinia |
| **后端** | FastAPI + SQLAlchemy + SQLite |
| **AI** | DeepSeek API / Qwen + faster-whisper + Edge TTS |
| **通信** | RESTful API + WebSocket |

</div>

### 🗺️ 系统架构

```
┌─────────────────────────────────────────────────┐
│                   前端 (Vue3)                     │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │
│  │ 口语对话 │ │ 发音评测 │ │ 写作批改 │ │ 听力练习 │  │
│  └────────┘ └────────┘ └────────┘ └────────┘  │
│  ┌────────┐ ┌────────┐                        │
│  │ 词汇本  │ │ 学习统计 │                        │
│  └────────┘ └────────┘                        │
└─────────────────────────────────────────────────┘
                         │ RESTful / WebSocket
┌─────────────────────────────────────────────────┐
│                  后端 (FastAPI)                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │
│  │ Chat API│ │语音识别 │ │语音合成 │ │发音评测 │  │
│  └────────┘ └────────┘ └────────┘ └────────┘  │
└─────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────┐
│                  数据层 (SQLite)                 │
└─────────────────────────────────────────────────┘
```

---

## 🐳 Docker 部署（推荐）

### 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/lexiva.git
cd lexiva

# 2. 复制环境变量配置
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入您的 API Keys

# 3. 使用启动脚本
./run.sh docker
```

### 手动启动

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

> ✅ 后端: http://localhost:8000 | 前端: http://localhost:5173 | API 文档: http://localhost:8000/docs

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 安装部署

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/lexiva.git
cd lexiva

# 2. 后端启动
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\/scripts\banActivate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. 前端启动
cd frontend
npm install
npm run dev
```

> ✅ 后端地址: http://localhost:8000/docs | 前端地址: http://localhost:5173

---

## 📁 项目结构

```
lexiva/
├── Dockerfile                  # Docker 镜像配置
├── docker-compose.yml          # Docker Compose 配置
├── run.sh                      # 项目启动脚本
├── pyproject.toml              # Python 项目配置
├── README.md                   # 本文件
│
├── backend/                    # FastAPI 后端
│   ├── .env.example           # 环境变量模板
│   ├── api/                   # API 路由
│   ├── api/                   # API 路由
│   │   ├── chat.py            # AI 对话
│   │   ├── vocabulary.py      # 词汇管理
│   │   ├── writing.py        # 写作批改
│   │   ├── pronunciation.py   # 发音评测
│   │   ├── listening.py      # 听力练习
│   │   ├── statistics.py     # 学习统计
│   │   └── settings.py       # 系统设置
│   ├── services/             # 业务逻辑
│   │   ├── ai_chat.py        # AI 对话服务
│   │   ├── ai_whisper.py     # 语音识别服务
│   │   ├── ai_tts.py         # 语音合成服务
│   │   └── writing.py        # 写作批改服务
│   ├── db/                   # 数据库操作
│   ├── websocket/           # WebSocket 处理
│   └── main.py              # 应用入口
│
├── frontend/                 # Vue3 前端
│   ├── src/
│   │   ├── api/             # API 调用
│   │   ├── components/     # 公共组件
│   │   ├── stores/         # Pinia 状态
│   │   └── views/          # 页面视图
│   └── package.json
│
└── docs/                     # 项目文档
    ├── AI英语学习系统体验优先版技术方案.md
    ├── AI英语学习系统学生版技术方案.md
    └── 本地AI语音通话技术实现.md
```

---

## ⚙️ 配置说明

### 环境变量

在 `backend/` 目录下创建 `.env` 文件：

```bash
# AI 模型配置
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Whisper 语音识别 (base/small/medium/large-v3)
WHISPER_MODEL=base

# Edge TTS 语音合成
TTS_VOICE=zh-CN-XiaoxiaoNeural
```

---

## 📖 文档

| 文档 | 说明 |
|:---:|:---|
| [体验优先版技术方案](docs/AI英语学习系统体验优先版技术方案.md) | 完整技术架构与实现细节 |
| [学生版技术方案](docs/AI英语学习系统学生版技术方案.md) | 功能需求与产品设计 |
| [本地AI语音通话](docs/本地AI语音通话（流式+自动打断+高颜值+轻量高音质）.md) | 实时语音对话技术实现 |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'Add xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

---

## 📄 许可证

本项目基于 [MIT](LICENSE) 协议开源。

---

<div align=center>

_Made with ❤️ for English Learners_

</div>