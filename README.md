# Weiss Schwarz Agent (WS Agent)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.42.0-red)](https://streamlit.io/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-green)](https://github.com/langchain-ai/langgraph)

**Weiss Schwarz Agent** 是一个专为集换式卡牌游戏 **Weiss Schwarz (黑白双翼，WS)** 设计的垂直领域 AI 智能助手。

本项目旨在解决非日语/英语母语玩家在查阅英文卡牌数据、理解复杂游戏规则以及获取即时赛事上位卡组信息时的痛点。通过集成大语言模型（LLM）、检索增强生成（RAG）技术以及实时联网能力，Agent 能够提供精准的卡牌查询、规则裁定解释、卡组构筑建议以及数据库更新服务。

![图片描述](./pic.jpg)

---

## ✨ 核心特性

- 🧠 **智能问答**: 基于 LangGraph 的 ReAct 架构，能够理解复杂的自然语言查询意图。
- 📚 **精准检索 (RAG)**: 内置 ChromaDB 向量数据库，支持对数万张 WS 卡牌和官方规则书进行语义检索。
- 🌐 **联网能力**: 集成百度千帆 AI Search 和 数眼智能 AI Reader（可自由替换其他联网搜索和网页抓取API），支持实时联网搜索卡牌有关信息和抓取官网卡组。
- 💬 **现代化 UI**: 基于 Streamlit 深度定制的前端 Chat 界面，支持流式输出、思维链、工具链展示（Thought/Action）、打字机效果和多轮对话记忆。
- 🛠 **技能扩展**: 插件化的 Skills 系统，支持动态加载新能力（如查卡、查规则、获取上位卡组）。
- 🔄 **自主运维**: 具备检查数据源更新并自动同步本地数据库的能力。

---

## 🚀 快速开始

### 1. 环境准备

确保您的系统已安装 **Python 3.10** 或更高版本。

```bash
# 克隆项目
git clone https://github.com/modernnice/ws-agent.git
cd ws-agent

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

本项目依赖多个大模型服务，在第一次对话开始前，请取消 `config/agent.yml.example` 的`.example` 后缀，将文件名改为 `config/agent.yml` 并填写配置，或在启动后的 Web 界面侧边栏设置界面中填写或修改您的模型 URL 和各项 API Key（推荐）。

- **Chat Model**: 默认使用 DeepSeek-Chat (OpenAI 兼容接口)
- **Embedding Model**: 默认使用 text-embedding-v4 (Aliyun DashScope兼容接口)
- **Search Tools**: 默认使用Baidu AI Search (百度搜索API，用于联网搜索), ShuyanAI (数眼智能国际版API，用于网页抓取)，可自行替换其他联网搜索和网页抓取API

### 3. 启动应用

```bash
streamlit run app.py
```

如果启动界面报错，请尝试手动指定虚拟环境启动：

```bash
./venv/bin/streamlit run app.py
```

启动后，浏览器将自动打开 `http://localhost:8501`。

### 4. 初始化RAG向量知识库

在首次进行卡牌或规则查询前，还需要将本地的卡牌 JSON 数据和规则文档写入向量数据库。英文卡牌数据库来源：https://github.com/CCondeluci/WeissSchwarz-ENG-DB 

本仓库英文数据当前更新版本为 2026-03-11T05:44:42+00:00

也可选择自行将英文数据库替换为日文数据库并重新向量化入库：https://github.com/CCondeluci/WeissSchwarz-JP-DB

如果您选择日文数据库，请一并修改 `skills/card-upgrade` 中的各项有关英文数据库的配置为日文数据库。

> **注意**: 请确保 `data/Card_DB` 目录下有卡牌 JSON 数据，`data/Rule_DB` 下有规则文件。

```bash
# 初始化向量数据库 (ChromaDB)
python3 rag/vector_store.py
```

执行上述命令后，会自动在项目目录下创建向量数据库 `WeissSchwarz_db`和`md5`文件。

#### 现在您可以自由与Weiss Schwarz Agent进行对话了！

---

## 📂 项目结构

```
.
├── app.py                  # Streamlit 应用入口
├── agent/                  # Agent 核心逻辑 (LangGraph)
│   └── react_agent.py      # ReAct Agent 实现
├── rag/                    # RAG 检索增强生成模块
│   ├── vector_store.py     # 向量库管理 (ChromaDB)
│   └── rag_service.py      # 检索服务封装
├── skills/                 # 技能插件目录
│   ├── card-search/        # 查卡/查规则技能
│   ├── card-upgrade/       # 数据库自动更新技能
│   └── get-deckrecipe/     # 官网卡组爬取技能
├── tools/                  # 通用工具 (Search, WebReader)
├── frontend/               # 前端 UI 组件与样式
│   ├── style.css           # 自定义 CSS 样式
│   └── ui/                 # UI 渲染逻辑
├── config/                 # 配置文件
└── data/                   # 本地数据源 (JSON/PDF)
```

## 🛠️ 技能使用指南

Agent 支持自然语言交互，您也可以通过特定指令触发技能：

- **查卡牌**: "查一下卡名中包含高松灯的卡牌"
- **查规则**: "Encore 阶段的详细流程是什么？"
- **找卡组**: "帮我找一下最近的上位卡组"
- **更新数据**: "检查一下有没有新的卡牌数据更新"

## 📄 许可证

MIT License
