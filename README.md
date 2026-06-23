# PubMed Research Agent 🔬

> 🧠 AI 驱动的医学文献智能分析系统 &mdash; &mdash; 输入一个研究问题，30秒内获得结构化文献综述报告。

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-61%20passed-brightgreen)]()
[![Model](https://img.shields.io/badge/Supports-GPT%7CDeepSeek%7CQwen-purple)]()

---

## 📖 目录

- [项目简介](#项目简介)
- [效果预览](#效果预览)
- [环境准备](#环境准备)
- [5步部署](#5步部署)
- [使用教程](#使用教程)
- [常见问题](#常见问题)
- [模型选择](#模型选择)
- [项目结构](#项目结构)

---

## 项目简介

你只需要输入一个研究问题，比如：

> **"SEC61G in Lung Cancer"**

系统会自动完成以下全部工作：

| 步骤 | 做了什么 | 你看到的 |
|------|----------|------------|
| 🔍 检索 | 自动调用 PubMed API，搜索全球生物医学文献 | 文献列表（标题、摘要、PMID、DOI、作者） |
| 🧠 分析 | LLM 大模型智能读懂所有摘要 | 5维结构化分析报告 |
| 📊 输出 | 自动提炼研究热点、未来方向 | 可复制、可导出 JSON/Markdown |

---

## 效果预览

输入关键词 **SEC61G**，系统输出：

```
✅ 状态：COMPLETED  |  文献：10篇  |  耗时：1.62秒  |  模型：gpt-4o

📄 文献列表（可展开摘要，一键跳转 PubMed）
📚 研究背景（3段综述）
🔥 研究热点（双栏卡片，带 PMID 证据）
💡 主要发现（要点列表）
🧪 实验方法（使用频次统计）
🚀 未来方向（方向 + 理由 + 挑战）
```

---

## 环境准备

### 你需要安装以下软件

| 软件 | 下载地址 | 安装说明 |
|------|----------|----------|
| **Python 3.11+** | [python.org/downloads](https://www.python.org/downloads/) |  安装时**勾选** "Add Python to PATH"  |
| **Git** | [git-scm.com/downloads](https://git-scm.com/downloads) | 一路默认即可 |
| **VS Code**（推荐） | [code.visualstudio.com](https://code.visualstudio.com/) | 可选，方便编辑配置文件 |

### 你需要以下账号（全部免费）

| 服务 | 注册地址 | 用途 |
|------|----------|------|
| **OpenAI**（或其他模型） | [platform.openai.com](https://platform.openai.com/) | LLM 分析文献 |
| **NCBI**（可选） | [account.ncbi.nlm.nih.gov](https://account.ncbi.nlm.nih.gov/) | PubMed API Key（提升速度） |

> **没有 OpenAI 账号也能用！** 支持 DeepSeek、Qwen、本地 Ollama 等任何 OpenAI 兼容接口，详见 [模型选择](#模型选择)。

---

## 5步部署

### 第 1 步：下载项目

打开终端（命令提示符或 PowerShell），输入：

```bash
git clone https://github.com/0609x/PubMed-Research-Agent.git
cd PubMed-Research-Agent
```

> 👉 不会用 git？直接点 GitHub 页面的绿色 **Code** 按钮 → **Download ZIP** → 解压到任意文件夹。

### 第 2 步：安装依赖

在项目目录内执行：

```bash
pip install -r requirements.txt
```

> ❓ 如果报错 `pip: command not found`，说明你安装 Python 时没有勾选 "Add Python to PATH"。解决办法看 [常见问题](#常见问题)。

### 第 3 步：配置环境变量

复制配置文件模板：

```bash
# Windows PowerShell
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

用 VS Code 或记事本打开 `.env` 文件，修改以下两项：

```ini
# 你的邮箱（NCBI 要求，任意真实邮箱即可）
PUBMED_EMAIL=your_email@example.com

# 你的 LLM API Key（去对应平台获取）
LLM_API_KEY=sk-your-api-key-here
```

> **重要：** `.env` 文件包含密钥，不要上传到 GitHub！已经在 `.gitignore` 中排除。

### 第 4 步：启动系统

```bash
cd frontend
streamlit run app.py
```

### 第 5 步：打开浏览器

终端会显示：

```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

在浏览器中打开 **http://localhost:8501**

🎉 部署完成！接下来看怎么用。

---

## 使用教程

### 1. 填写左侧配置

打开页面后，看到左侧 **Settings** 面板：

| 区域 | 填什么 | 示例 |
|------|----------|------|
| **Email** | 你的邮箱 | `myname@qq.com` |
| **Base URL** | LLM API 地址 | `https://api.openai.com/v1` |
| **API Key** | LLM 密钥 | `sk-proj-xxxxxxxx` |
| **Model** | 下拉选择模型 | `gpt-4o-mini`（便宜） |
| **Language** | 输出语言 | `zh`（中文） |
| **Verify SSL** | 取消勾选 | （大多数用户） |

### 2. 搜索

在页面顶部输入任意研究问题：

```
SEC61G in Lung Cancer
PD-L1 immunotherapy NSCLC
CRISPR cancer therapy review
……
```

点击 **🔍 Search** 按钮，等待 10-30 秒。

### 3. 查看结果

搜索完成后，页面会展示：

- **顶部状态栏**：完成状态、文献数量、耗时、使用模型
- **📄 文献列表**：点击 "Show Abstract" 展开摘要，点 PMID 直达 PubMed 原文
- **📚 研究背景**：2-3 段综合综述
- **🔥 研究热点**：双栏卡片，附 PMID 证据
- **💡 主要发现**：要点列表
- **🧪 实验方法**：使用频次统计
- **🚀 未来方向**：方向 + 理由 + 挑战

### 4. 导出报告

页面底部三个按钮：

| 按钮 | 功能 |
|------|------|
| **📥 JSON** | 下载 `.json` 文件（完整数据） |
| **📄 Markdown** | 下载 `.md` 文件（可直接粘贴到论文/笔记） |
| **📋 Copy JSON** | 复制到剪贴板 |

---

## 常见问题

### Q1：`pip: command not found`

**原因：** Python 没有加入系统 PATH。

**解决：**
1. 搜索打开 "Python" ⇒ 点击 **Modify**（修改）
2. 勾选 **"Add Python to PATH"** ⇒ Install
3. **重启终端**，再试一次

### Q2：启动报错 `ModuleNotFoundError: No module named 'xxx'`

```bash
# 缺什么就安装什么
pip install httpx pydantic biopython
```

### Q3：搜索报错 `SSL: CERTIFICATE_VERIFY_FAILED`

**原因：** 公司网络或代理环境。

**解决：** 左侧面板取消勾选 **Verify SSL**。

### Q4：搜索报错 `LLM API returned 401`

**原因：** API Key 填错了或没有余额。

**解决：**
- 检查 API Key 是否复制完整（没有多余空格）
- 登录对应平台查看余额

### Q5：搜索报错 `LLM API returned 404`

**原因：** Base URL 填错了。

**解决：** 确认 Base URL 以 `/v1` 结尾：

| 模型 | Base URL |
|------|----------|
| OpenAI | `https://api.openai.com/v1` |
| DeepSeek | `https://api.deepseek.com/v1` |
| Qwen（阿里） | `https://dashscope.aliyuncs.com/compatible-mode/v1` |

### Q6：搜索结果为 0

**原因：** PubMed API 限流或网络不可达。

**解决：**
1. 等待 30 秒后重试（NCBI 没有 API Key 时限速 3次/秒）
2. 申请免费 NCBI API Key：[account.ncbi.nlm.nih.gov](https://account.ncbi.nlm.nih.gov/) → API Key Management

### Q7：分析结果为空

**原因：** LLM 模型不支持 `response_format: json_object`。

**解决：**
- 部分旧版模型和本地 Ollama 模型可能不支持 JSON mode
- 建议换用 `gpt-4o-mini`（最便宜）或 `deepseek-chat`

---

## 模型选择

页面左侧 **Model** 下拉框支持以下模型，切换即用：

| 模型 | 价格 | 速度 | 质量 | 适合场景 |
|------|------|------|------|----------|
| `gpt-4o-mini` | ★ 便宜 | 快 | 优秀 | ★★★ 日常使用，推荐 |
| `gpt-4o` | ★★★ 贵 | 中 | 最佳 | 重要分析 |
| `deepseek-chat` | ★ 便宜 | 快 | 优秀 | 国内用户首选 |
| `qwen-plus` | ★ 便宜 | 快 | 良好 | 阿里云用户 |

> **本地模型？** Base URL 填 `http://localhost:11434/v1`（Ollama），Model 手动输入 `llama3` 或 `qwen2.5`。

---

## 项目结构

```
PubMed-Research-Agent/
├── agents/                  # AI Agent 定义
│   ├── research_agent.py    # 主 Agent——检索→总结→报告全流程编排
│   └── query_rewrite.py      # 查询改写——自然语言→PubMed检索式
├── services/                # 核心业务服务
│   ├── literature_summary.py # LLM 文献总结（5维分析）
│   ├── hybrid_search.py      # 混合检索（关键词+语义）
│   ├── reranker.py           # 精排重排序（Pointwise/Listwise）
│   ├── context_compressor.py # 上下文压缩（降低Token消耗）
│   ├── prompt_cache.py       # 提示缓存（重复查询免费）
│   └── memory.py             # 对话记忆（多轮追问）
├── tools/                   # 工具层
│   └── pubmed_tool.py         # PubMed API 封装
├── frontend/                # Streamlit 前端
│   ├── app.py                 # 主页面（深色主题UI）
│   └── api_client.py          # Agent 调用封装
├── tests/                   # 单元测试（61个）
├── requirements.txt         # Python 依赖清单
├── .env.example             # 环境变量模板
└── README.md                # 本文档
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Streamlit |
| 检索 | PubMed Entrez API + Biopython |
| LLM | OpenAI 兼容接口（GPT / DeepSeek / Qwen / Ollama） |
| 向量数据库 | ChromaDB（可选） |
| 数据库 | SQLite（开箱即用） |
| HTTP 客户端 | httpx |
| 数据验证 | Pydantic v2 |
| 测试 | pytest（61 个测试，100% 通过） |

---

## 📝 License

MIT © 2026

---

开始你的第一次 AI 文献分析吧 🚀
