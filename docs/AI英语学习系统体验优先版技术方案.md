# AI 英语学习系统（体验优先版）技术方案

> 现代化技术栈 | 极致用户体验 | 开源免费 | GitHub友好

## 一、项目概述

### 1.1 项目定位

本项目是一款面向学生的**AI英语学习Web系统**，核心定位是「**体验优先**」——追求媲美商业产品的流畅交互体验，同时保持开源免费、极易部署的特性。技术栈全面升级为现代化方案：后端使用FastAPI实现高性能异步处理，前端使用Vue3打造丝滑流畅的界面，AI能力采用开源方案实现零成本运行。

项目目标用户为初高中学生、大学生、英语自学者。系统设计遵循「**用户体验 > 技术复杂度**」原则，所有选型都为了实现「好用、流畅、自然」的使用体验。学生无需注册、无需付费、无需配置复杂环境，一键启动即可使用。

本系统适合作为计算机专业的课程设计、毕业设计选题，或开源项目学习/团队开发的参考模板。GitHub开源采用MIT协议，代码规范、注释完整，学生可以轻松部署和二次开发。

### 1.2 核心特性

本系统的核心特性可以概括为「**五个零**」：**零成本**运行，使用免费开源AI模型，不产生任何费用；**零门槛**部署，Python + SQLite，Windows/Mac/Linux一键启动；**零等待**响应，WebSocket实时通信，对话秒回无刷新；**零插件**体验，浏览器原生Web Audio API，语音对话一键搞定；**零隐私泄露**，所有数据本地存储，不上传云端。

对比上一代「极简基础版」，本系统在以下方面进行了体验升级：后端从Flask升级为FastAPI，获得异步非阻塞能力，支持WebSocket实时通信；前端从Bootstrap升级为Vue3 + Element Plus，实现 SPA 流畅体验；语音从gTTS升级为Edge TTS，发音更自然；新增发音评测功能，实现完整的口语练习闭环。

---

## 二、技术架构设计

### 2.1 系统架构概述

本系统采用现代化的「**Vue3 + FastAPI + SQLite**」前后端分离架构。FastAPI后端提供RESTful API和WebSocket两套接口，满足不同场景需求；Vue3前端单页应用实现丝滑流畅的交互体验；SQLite本地数据库实现零配置数据存储。

整体架构分为四层：**接入层**（Vue3前端 + WebSocket）、**网关层**（FastAPI路由）、**业务层**（AI处理 + 业务逻辑）、**数据层**（SQLite + 文件系统）。这种分层架构清晰规范，便于理解、学习和二次开发。

### 2.2 技术栈详解

#### 后端框架：FastAPI

FastAPI是新一代Python Web框架，采用异步非阻塞设计，性能远超传统同步框架。选择FastAPI的核心原因是**完美支持实时语音和对话场景**：WebSocket接口天然支持长连接，对话可以「秒回复」无需等待页面刷新；异步处理让语音识别和AI响应并行执行，减少等待时间。

FastAPI的另一大优势是**自动生成API文档**，访问/docs即可查看交互式API文档，开发调试极为方便。配合Pydantic进行数据校验，API输入输出类型安全，减少运行时错误。

代码组织建议：将路由（api/）、业务逻辑（services/）、数据模型（models/）分离。WebSocket处理单独模块（websockets/），避免阻塞主线程。

#### 前端框架：Vue3 + Vite

Vue3是当前最流行的前端框架之一，Composition API让代码逻辑清晰复用方便。Vite是其官方构建工具，启动速度极快（毫秒级），热更新体验丝滑。配合Element Plus组件库，开箱即用的精美界面，媲美商业产品。

选择这套技术栈的原因是「**开箱即用的精美**」：Element Plus提供完整的UI组件，Navigation导航、Form表单、Table表格、Dialog对话框等无需自己样式，直接使用即可。响应式设计天然支持移动端和桌面端。

前端采用TypeScript进行类型约束，配合VS Code的智能提示，开发效率大幅提升。项目结构遵循Vue官方规范：views/页面、components/组件、api/接口、stores/状态管理。

#### UI组件库：Element Plus

Element Plus是Vue3生态最成熟的UI组件库，由饿了么团队维护。组件设计现代美观，符合主流审美，学生直接使用即可获得商业级界面效果。

本系统使用的核心组件包括：ElMenu导航栏、ElButton按钮、ElInput输入框、ElDialog对话框、ElCard卡片、ElTable表格、ElTabs标签页、ElProgress进度条、ElStatistic统计卡片。所有组件支持主题定制，可以修改CSS变量实现暗黑模式。

#### 数据可视化：ECharts

ECharts是百度开源的可视化图表库，功能强大、配置灵活。本系统用它绘制学习统计图表，包括：学习时长折线图、各项功能使用次数饼图、词汇量增长曲线、发音评分趋势图。图表交互流畅，点击可查看详情数据。

#### AI能力选型

AI能力是本系统用户体验的核心，全部选用「效果接近商业产品、100%免费开源」的方案：

**大语言模型**首选DeepSeek免费API（国内可直接访问），英语能力极强，支持上下文记忆，免费额度充足学生足够使用。备选Qwen开源大模型（本地部署），适合有GPU的学生。

**语音识别**使用Whisper Large V3，这是目前开源效果最好的语音识别模型，英语识别准确率行业顶尖。推荐使用faster-whisper加速推理，CPU也能流畅运行。

**语音合成**使用Edge TTS（微软开源免费），发音比gTTS更自然、更像真人，支持美式/英式多种音色可选。edge-tts库直接调用，无需API密钥。

**发音评测**采用自研算法：Whisper识别结果与参考句子对比，通过音素级别对齐计算相似度，配合AI分析给出错误原因和改进建议。

#### 数据库：SQLite

SQLite是本系统数据存储的最佳选择。文件型数据库，零安装零配置，学生电脑直接运行。所有数据存在本地文件中，隐私安全，不上传云端。

使用SQLAlchemy ORM进行操作，兼容性好，后期可以轻松迁移到MySQL/PostgreSQL（如果需要多用户部署）。

### 2.3 项目目录结构

```
ai-english-vue-fastapi/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 项目入口
│   ├── api/                    # API路由
│   │   ├── __init__.py
│   │   ├── chat.py             # 对话路由
│   │   ├── pronunciation.py      # 发音评测路由
│   │   ├── writing.py          # 写作批改路由
│   │   ├── vocabulary.py        # 单词本路由
│   │   ├── listening.py        # 听力路由
│   │   └── statistics.py       # 统计路由
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── ai_chat.py          # 对话服务
│   │   ├── ai_asr.py           # 语音识别
│   │   ├── ai_tts.py           # 语音合成
│   │   ├── pronunciation.py     # 发音评测
│   │   └── writing.py           # 写作批改
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── vocabulary.py
│   │   └── statistics.py
│   ├── db/                    # 数据库
│   │   ├── __init__.py
│   │   └── connection.py
│   ├── websocket/             # WebSocket处理
│   │   ├── __init__.py
│   │   └── manager.py
│   └── utils/                 # 工具函数
│       ├── __init__.py
│       └── audio.py
├── frontend/                   # Vue3 前端
│   ├── src/
│   │   ├── api/               # 前端API封装
│   │   ├── assets/            # 静态资源
│   │   ├── components/        # 通用组件
│   │   │   ├── VoiceRecorder.vue
│   │   │   ├── AudioPlayer.vue
│   │   │   └── StatChart.vue
│   │   ├── composables/       # 组合式函数
│   │   │   ├── useWebSocket.js
│   │   │   └── useAudio.js
│   │   ├── layouts/           # 布局组件
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # 状态管理(Pinia)
│   │   ├── styles/           # 全局样式
│   │   ├── types/              # TypeScript类型
│   │   ├── views/             # 页面
│   │   │   ├── Home.vue
│   │   │   ├── Chat.vue
│   │   │   ├── Pronunciation.vue
│   │   │   ├── Writing.vue
│   │   │   ├── Vocabulary.vue
│   │   │   ├── Listening.vue
│   │   │   └── Statistics.vue
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── .env
├── data/                      # 数据目录
│   └── database.db             # SQLite数据库
├── requirements.txt           # Python依赖
├── package.json               # 前端依赖
├── README.md                  # 项目说明
└── LICENSE                   # MIT协议
```

---

## 三、核心功能模块设计

### 3.1 AI 实时口语陪练

#### 3.1.1 功能定位

口语陪练是本系统的**核心功能**，提供文字对话和语音对话两种模式。AI扮演英语陪练角色，通过日常对话帮助学生练习英语表达，同时实时纠正语法错误。学生可以选择不同场景进行对话，如日常生活、校园生活、考试备考、职场英语等，AI会根据场景调整对话难度和话题范围。

文字对话支持流式输出，学生发送消息后AI逐字显示回复，模拟真实对话体验。对话历史自动保存，学生可以回顾和复习之前的重要内容。语音对话支持实时识别，学生按住语音按钮说话，松开后自动识别发送，AI回复后播放语音。

#### 3.1.2 技术实现

语音对话的技术流程包括：前端使用Web Audio API录制音频，录制完成后将音频Blob发送到WebSocket端点；后端接收音频流，使用faster-whisper进行语音识别（ASR）；识别结果作为prompt发送给DeepSeek免费API；AI回复的文本调用Edge TTS转换为语音；语音流式返回给前端播放。

WebSocket是关键：建立长连接后，客户端可以持续发送音频，后端实时处理返回。区别于传统HTTP的「请求-响应」模式，WebSocket实现真正的实时对话。对于语音对话场景，延迟��以��制在2秒以内。

语音识别推荐使用faster-whisper的base型号，兼顾速度和准确率。首次运行自动下载模型（约140MB），后续本地运行不依赖网络。如果学生电脑性能较好，可以使用large-v3型号获得更好效果。

#### 3.1.3 交互设计

对话页面采用聊天气泡样式，左侧显示学生消息（蓝色渐变），右侧显示AI消息（灰色背景）。页面顶部提供场景选择器，下拉菜单可选：Daily Life、Exam Prep、Campus、Business等。切换场景后清空对话历史，重新开始。

每个对话轮次后，AI会自动标注学生句子中的语法错误。错误以红色高亮显示，点击可查看详细解释。对话支持收藏重点句子，收藏的句子会自动加入单词本。页面侧边栏显示对话历史列表，点击可回顾之前对话。

### 3.2 AI 发音智能评测

#### 3.2.1 功能定位

发音评测功能帮助学生纠正英语发音。学生点击「开始录音」后朗读系统给出的句子，录音完成后AI立即给出评测分数并标注问题最为严重的音素，学生可以针对性练习。评测维度包括：发音准确度（单词是否读对）、流利度（是否连贯）、语调（升降调是否正确）。

系统内置评测句子库，按照难度分类：入门（简单句子）、基础（日常对话）、中级（复合句）、高级（学术文章）。每个难度提供50句左右的评测材料，涵盖音标分类、连读技巧、语调练习等不同维度。所有评测句子配有标准发音音频，学生可以先听标准发音再跟读练习。

#### 3.2.2 技术实现

发音评测的技术流程：学生录音上传后端 → faster-whisper识别文本 → 对比参考句子计算相似度 → AI分析具体发音问题 → 返回结构化评测结果。

评分算法采用多维度评估：音素准确度（识别结果与参考句子的编辑距离）、完整度（是否漏读或多读）、流利度（录音时长与参考时长的比例）。综合给出0-100分的评分。

错误定位使用phoneme对齐：将识别结果的每个词与参考句子的音素逐个对比，标记出发错的位置。AI进一步分析错误原因，给出口型提示和练习建议。

#### 3.2.3 交互设计

发音评测页面主要区域显示待朗读的句子，字号放大加粗以便阅读。句子下方是大型圆形录音按钮，按住说话，松开结束录音。录音按钮旁边显示实时波形动画，直观展示录音状态。

评测结果显示在句子下方：评分用大号数字显示，同时用进度条展示（绿色>85分，黄色70-85分，红色<70分）。问题发音用红色高亮标注，下方显示AI给出的纠正建议。页面侧边栏显示评测历史，每次评测都有记录可回顾。

### 3.3 AI 写作全能助手

#### 3.3.1 功能定位

写作批改功能帮助学生提升写作能力。学生粘贴英语作文或句子后，系统一键进行纠错、润色和评分。批改结果标注每处错误的类型（语��错误、拼写错误、用词不当）和原因，同时提供润色后的版本供参考。对话式批改功能允许学生针对具体问题追问AI，获得更详细的解释和练习建议。

批改维度包括：语法正确性（时态、主谓一致）、词汇使用（同义词替换、高级词汇）、句子流畅度（连词使用、逻辑衔接）、逻辑结构（段落组织、论证完整）、表达地道性（符合英语表达习惯）。系统会根据学生选择的考试类型调整评分标准。

#### 3.3.2 技术实现

写作批改的技术流程：学生输入文本 → 发送给DeepSeek API → 按照批改prompt进行评测 → 返回结构化结果。prompt设计是关键，需要明确批改维度和输出格式。

返回结果的结构化设计：original_text（原文本）、corrected_text（批改后文本）、corrections（错误列表，每项包含位置、错误类型、错误内容、纠正内容）、score（各维度评分）、suggestions（改进建议）。前端根据这个结构渲染批改界面。

追问功能采用增量调用：首次批改返回完整结果，后续学生针对某个错误追问时，只发送错误句子的上下文（而非全文），减少API调用量和响应时间。

### 3.4 智能单词本

#### 3.4.1 功能定位

单词本是学生学习英语的基础工具，功能设计智能化：手动添加单词或从文章中收藏，系统自动补全音标、例句、同义词，发音采用Edge TTS合成更自然。艾宾浩斯遗忘曲线算法自动安排复习计划，到期提醒学生复习。

单词本支持导入和导出，可以从CSV文件批量导入单词，也可以导出备份。复习模式采用看英文说中文或看中文说英文的方式，检验学生记忆效果。记忆效果曲线帮助学生了解自己的记忆特征。

#### 3.4.2 技术实现

单词数据模型：id、word（单词）、phonetic（音标）、meaning（中文释义）、example_sentences（例句列表）、synonyms（同义词列表）、audio_path（发音文件路径）、added_at（添加时间）、reviewed_count（复习次数）、correct_count（正确次数）、memory_strength（记忆强度）、next_review（下次复习时间）。

遗忘曲线采用简化SM-2算法：新单词初始记忆强度为1.0，复习正确则强度×1.5，复习错误则强度×0.5。复习间隔根据强度动态调整：强度1.0间隔1天，2.0间隔3天，3.0间隔7天，4.0间隔15天，以此类推。每晚检查待复习单词，顶部显示提醒徽章。

### 3.5 听力训练工具

#### 3.5.1 功能定位

听力练习功能帮助学生提升听力理解能力。系统将英文文本转换为语音（TTS），学生可以调整语速（0.5x、0.75x、1x、1.25x、1.5x、2x）和音色（美式男声、美式女声、英式男声、英式女声）。听写模式下，系统播放语音，学生输入听到的内容，系统对比给出准确率。

听力材料支持三种来源：学生粘贴文本直接转语音、使用系统内置听力库、导入外部音频文件。内置听力库按难度分类（入门、基础、中级、高级），每个难度提供30篇左右的材料，涵盖日常对话、短文朗读、新闻摘要等类型。

#### 3.5.2 技术实现

TTS使用Edge TTS生成音频，首次生成时调用API并缓存到本地文件。文件名按文本内容Hash命名，相同文本不会重复生成。音频缓存避免每次都调用API，既节省时间又节省API调用量。

听写对比采用词级别细粒度：用户输入与参考文本分词后逐词对比，正确显示绿色、错误显示红色并在下方给出正确答案。系统计算正确率并记录到统计数据库。

### 3.6 学习中心

#### 3.6.1 功能定位

学习中心帮助学生了解自己的学习情况。系统自动记录学习行为数据：对话次数和时长、发音评测次数和平均分、写作批改篇数、单词复习个数和记忆率、���力���习时长。学习数据以本地方式存储，不上传云端。

统计面板以卡片+图表形式呈现，展示本周学习数据概览和历史趋势。数据包括：学习总时长、各功能使用次数、学习进步曲线。图表使用ECharts绘制，支持交互查看详情。

#### 3.6.2 数据模型

学习记录按天存储，statistics表结构：date（日期唯一键）、chat_count（对话次数）、chat_minutes（对话分钟）、pronunciation_count（发音评测次数）、pronunciation_avg_score（发音平均分）、writing_count（写作批改次数）、wordlearned（新增单词）、word_reviewed（复习单词）、listening_minutes（听力分钟）。

每日数据在用户使用各功能时自动累加，后台定时统计生成。如果某天没有使用记录，则不添加条目。查询统计时按日期范围聚合。

---

## 四、接口设计

### 4.1 RESTful API

本系统采用RESTful风格的API设计，URL语义清晰，HTTP方法使用正确。所有API返回统一的JSON格式：成功时返回 {"code": 0, "data": {...}}，失败时返回 {"code": 1, "message": "错误信息"}。

#### 4.1.1 对话接口

POST /api/chat/send - 发送文字对话
请求参数：{"message": "用户消息", "scene": "场景类型"}
返回：{"reply": "AI回复", "corrections": [...]}

POST /api/chat/voice - 语音对话（WebSocket优先）
返回WebSocket连接信息，前端通过WebSocket发送音频

GET /api/chat/history - 获取对话历史
参数：page, limit

#### 4.1.2 发音接口

POST /api/pronunciation/record - 提交发音评测
参数：formData(audio, sentence_id)

GET /api/pronunciation/sentences - 获取评测句子列表
参数：difficulty(可选)

GET /api/pronunciation/sentence/{id}/audio - 获取句子示范发音

#### 4.1.3 写作接口

POST /api/writing/correct - 提交写作批改
参数：{"text": "待批改文本", "exam_type": "CET-4"}

GET /api/writing/history - 获取批改历史

#### 4.1.4 单词接口

POST /api/vocabulary/add - 添加单词
参数：{"word": "单词"}

GET /api/vocabulary/list - 获取单词列表

POST /api/vocabulary/review - 复习结果上报
参数：{"word_id": 1, "result": "correct|incorrect"}

GET /api/vocabulary/to-review - 获取今日待复习单词

DELETE /api/vocabulary/{id} - 删除单词

#### 4.1.5 听力接口

POST /api/listening/tts - 文本转语音
参数：{"text": "文本", "speed": 1.0, "voice": "en-US-AriaNeural"}

POST /api/listening/dictation - 提交听写
参数：{"text": "用户输入", "reference": "参考文本"}

GET /api/listening/materials - 获取听力材料

#### 4.1.6 统计接口

GET /api/statistics/summary - 获取统计概览

GET /api/statistics/trend - 获取历史趋势

### 4.2 WebSocket接口

WebSocket用于实时语音对话，建立连接后双方可以持续发送消息。

客户端发送（text）：{"type": "text", "content": "消息内容", "scene": "场景"}
客户端发送（audio）：{"type": "audio", "data": "base64编码的音频"}

服务端发送（text）：{"type": "text", "reply": "AI回复", "corrections": [...]}
服务端发送（audio）：{"type": "audio", "data": "base64编码的语音"}
服务端发送（done）：{"type": "done"} 表示本次对话结束

---

## 五、数据库设计

### 5.1 数据模型

#### 5.1.1 用户表（users）

id - 主键、自增
username - 用户名
created_at - 创建时间
settings - JSON格式的设置项

#### 5.1.2 对话历史表（conversations）

id - 主键
scene - 场景类型
user_message - 用户消息
ai_message - AI回复
corrections - JSON格式的错误标注
created_at - 时间戳

#### 5.1.3 单词表（words）

id - 主键
word - 单词
phonetic - 音标
meaning - 释义
example_sentences - 例句列表JSON
audio_path - 发音文件路径
added_at - 添加时间
reviewed_count - 复习次数
correct_count - 正确次数
memory_strength - 记忆强度
next_review - 下次复习时间

#### 5.1.4 发音评测表（pronunciations）

id - 主键
sentence_id - 句子ID
score - 评分
details - 详细分析JSON
recorded_at - 时间戳

#### 5.1.5 写作批改表（writings）

id - 主键
original_text - 原文本
corrected_text - 批改后文本
corrections - 错误列表JSON
score - 评分
created_at - 时间戳

#### 5.1.6 学习统计表（statistics）

id - 主键
date - 日期（唯一）
chat_count - 对话次数
chat_minutes - 对话分钟
pronunciation_count - 发音评测次数
pronunciation_avg_score - 发音平均分
writing_count - 写作批改次数
word_learned - 新学单词
word_reviewed - 复习单词
listening_minutes - 听力分钟

### 5.2 索引

在常用查询字段上建立索引：
conversations.created_at
words.word（唯一索引）
words.next_review
statistics.date（唯一索引）

---

## 六、前端页面设计

### 6.1 页面结构

前端采用Vue3 Router单页应用架构，URL变化不刷新页面。整体布局为左侧导航栏加右侧内容区，各功能模块通过路由切换。Element Plus组件保证界面美观一致。

#### 6.1.1 导航栏

使用ElMenu组件实现垂直导航，包含：首页（统计概览）、口语陪练、发音评测、写作批改、单词本、听力练习、设置。导航栏支持折叠，节省空间。移动端自动折叠为汉堡菜单。

页面顶部可以显示学习提醒徽章：有待复习单词时显示红色徽章。点击徽章直接进入复习页面。

### 6.2 核心页面

#### 6.2.1 首页（统计面板）

首页展示学习统计概览，使用ElRow + ElCol网格系统。每个功能模块一张统计卡片，显示今日数据。卡片下方用ECharts绘制本周学习时长折线图。底部是快捷入口按钮，点击直接进入对应功能。

页面加载时调用/api/statistics/summary获取数据，用Pinia状态管理存储。前端使用watch监听数据变化，实时更新界面。

#### 6.2.2 口语对话页面

页面分为上下两部分：上方是ElScrollbar包裹的聊天记录区域，消息用div实现气泡样式；下方是输入区域，包含ElInput输入框和语音按钮。

语音对话使用WebSocket，useWebSocket composable封装连接逻辑。录音使用navigator.mediaDevices.getUserMedia获取音频流。实时波形用analysernode获取频谱数据绘制Canvas。

#### 6.2.3 发音评测页面

显示当前待朗读句子，用大号字体。下方是录音按钮，按住说话松开结束。评测结果显示在句子下方：ElProgress进度条显示分数，红色标注问题发音。

侧边栏显示历史评测记录，用ElTable表格展示。点击一行可以查看详情。

#### 6.2.4 写作批改页面

左右分栏布局：左侧ElInput输入作文，右侧显示批改结果。错误以红色高亮显示，点击弹出ElDialog显示详细解释。

批改完成后底部显示追问入口，点击可以追问具体错误。

#### 6.2.5 单词本页面

顶部搜索和添加区域：ElInput搜索框，添加按钮弹出ElDialog。单词以ElCard卡片展示，每张卡片显示单词、音标、释义。右上角显示记忆强度标签。

点击卡片进入复习模式：用ElDialog显示单词，隐藏释义，点击按钮显示。底部两个按钮：「认识」「不认识」。

#### 6.2.6 听力练习页面

顶部材料选择器：ElSelect选择内置材料或粘贴文本。选择后进入听写模式。

页面中央大播放按钮，点击播放语��。��方ElInput输入听到的内容。提交后显示对比结果：正确绿色，错误红色。

#### 6.2.7 学习中心页面

数据可视化页面，用ECharts绘制多个图表：学习时长趋势（折线图）、功能使用分布（饼图）、词汇量增长（面积图）。

ElDatePicker选择日期范围，获取数据后更新图表。

---

## 七、开发阶段规划

### 7.1 第一阶段：MVP体验版（2周）

Week 1：项目初始化
- 搭建FastAPI + Vue3项目结构
- 配置Element Plus和路由
- 实现SQLite数据模型
- 完成首页和导航

Week 2：核心功能
- AI文字对话（REST API）
- 写作批改基础功能
- 单词本CRUD
- 精美UI界面

### 7.2 第二阶段：完整版（3周）

Week 3：语音能力
- WebSocket实时对话
- Whisper语音识别
- Edge TTS语音合成

Week 4：评测功能
- 发音评测
- 听力生成
- 听写功能

Week 5：完善发布
- 学习统计
- 移动端适配
- 文档完善
- GitHub发布

---

## 八、部署指南

### 8.1 本地部署

```bash
# 克隆项目
git clone https://github.com/xxx/ai-english-vue-fastapi.git
cd ai-english-vue-fastapi

# 安装后端依赖
pip install -r requirements.txt

# 启动后端
python backend/main.py

# 安装前端依赖（新终端）
cd frontend
npm install

# 启动前端
npm run dev
```

访问 http://localhost:5173 即可使用。

### 8.2 云平台部署

推荐免费平台：Railway、Render、Fly.io。需配置Procfile和build配置。

---

## 九、技术风险与应对

### 9.1 AI API稳定性

免费API存在配额限制或服务不稳定风险。应对：准备多个AI方案，主方案DeepSeek，备选Qwen本地部署。

### 9.2 中文编码

Windows环境可能出现中文编码问题。应对：所有文件声明UTF-8编码，字符串使用Unicode。

### 9.3 语音延迟

网络状况影响语音识别速度。应对：前端显示加载状态，预处理音频减少传输量。

---

## 十、总结

本技术方案详细阐述了「体验优先版」AI英语学习系统的完整设计。六个核心功能模块覆盖学生英语学习的主要场景。技术栈全面升级为现代化方案：FastAPI + Vue3 + Element Plus + Edge TTS + Whisper，实现媲美商业产品的用户体验。项目代码结构清晰规范，适合学生作为课程设计、毕业设计或开源项目学习的参考模板。