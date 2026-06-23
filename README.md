# PubMed-Research-Agent 🔬

> 基于 AI 的 PubMed 科研文献检索、分析与 RAG 问答系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 项目简介

输入一个科研问题（如 *"SEC61G in Lung Cancer"*），系统自动完成：

1. **PubMed 检索** —— 调用 Entrez API 获取文献
2. **结果展示** —— 标题、摘要、PMID、DOI、作者、期刊
3. **LLM 分析** —— 综述总结 + 研究热点 + 未来方向
4. **RAG 追问** —— 基于向量检索的深度问答

---

## 🏗️ 系统架构

```
┌──────────────┐     HTTP/REST     ┌──────────────┐
│   Streamlit  │ ◄───────────────► │   FastAPI    │
│   Frontend   │                   │   Backend    │
└──────────────┘                   └──────┬───────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
              ┌─────▼─────┐        ┌──────▼──────┐      ┌──────▼──────┐
              │  PubMed   │        │    LLM      │      │  ChromaDB   │
              │  Entrez   │        │  (OpenAI/   │      │  (Vector    │
              │   API     │        │ Compatible) │      │   Store)    │
              └───────────┘        └─────────────┘      └─────────────┘
```

---

## 📁 项目结构

```
PubMed-Research-Agent/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/          # REST API 路由
│   │   ├── core/            # 核心配置、依赖注入
│   │   ├── models/          # SQLAlchemy ORM 模型
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   └── utils/           # 工具函数
│   └── alembic/             # 数据库迁移
├── frontend/                # Streamlit 前端
│   ├── pages/               # 多页面
│   └── components/          # 可复用组件
├── database/                # 数据库文件存放
├── tools/                   # 外部工具集成
├── agents/                  # AI Agent 定义
├── services/                # 核心业务服务
├── config/                  # 全局配置文件
├── tests/                   # 测试
│   ├── unit/
│   └── integration/
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量模板
└── README.md
```

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- pip

### 1. 克隆项目

```bash
git clone <repo-url>
cd PubMed-Research-Agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 PubMed 邮箱和 LLM API Key
```

### 4. 启动后端

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 启动前端

```bash
cd frontend
streamlit run app.py --server.port 8501
```

### 6. 使用 Docker 一键启动

```bash
docker-compose up -d
```

访问：
- 前端界面：http://localhost:8501
- API 文档：http://localhost:8000/docs

---

## 🔧 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| 前端 | Streamlit |
| ORM | SQLAlchemy + Alembic |
| LLM | LangChain (OpenAI 兼容接口) |
| 向量数据库 | ChromaDB |
| 文献检索 | PubMed Entrez API (Biopython) |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |

---

## 🌐 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/search` | 发起文献检索 |
| `GET` | `/api/v1/search/{id}` | 查询检索结果 |
| `GET` | `/api/v1/search/history` | 检索历史 |
| `POST` | `/api/v1/search/{id}/analyze` | 触发 LLM 分析 |
| `GET` | `/api/v1/search/{id}/analysis` | 获取分析报告 |
| `GET` | `/api/v1/search/{id}/export` | 导出报告 |
| `POST` | `/api/v1/rag/query` | RAG 自然语言查询 |
| `GET` | `/api/v1/health` | 健康检查 |

---

## 📝 License

MIT © 2026
