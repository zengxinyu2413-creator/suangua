<div align="center">

# ☯ Chinese Metaphysics Platform
# 中国术数平台

**A Full-Stack Platform Where Traditional Chinese Metaphysics Meets Modern AI**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React_19-Vite-61DAFB?style=flat-square&logo=react&logoColor=black)](https://vitejs.dev/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Multi-LLM](https://img.shields.io/badge/Multi-LLM-AI%20Powered-7C3AED?style=flat-square)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

<br/>

> Grounded in classical texts such as *Qiong Tong Bao Jian*, *Di Tian Sui*, *Zeng Shan Bu Yi* and *Qi Men Dun Jia Tong Zong*, this platform combines a pure-Python calculation engine with multi-LLM streaming interpretation to deliver authentic Chinese metaphysics analysis.

</div>

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Key Features](#2-key-features)
3. [Architecture](#3-architecture)
4. [The Seven Systems](#4-the-seven-systems)
5. [Quick Start](#5-quick-start)
6. [Configuration](#6-configuration)
7. [Dependencies](#7-dependencies)
8. [API Reference](#8-api-reference)
9. [Project Structure](#9-project-structure)
10. [Development Guide](#10-development-guide)
11. [Troubleshooting](#11-troubleshooting)
12. [Roadmap](#12-roadmap)
13. [Contributing](#13-contributing)
14. [License](#14-license)

---

## 1. Introduction

**Chinese Metaphysics Platform** (中国术数平台) is an open-source, full-stack application that bridges traditional Chinese metaphysical arts with modern software engineering. At its core lies a **pure Python calculation engine** that implements **seven major systems** — BaZi Four Pillars, ZiWei DouShu, LiuYao Six Lines, QiMen DunJia, XuanKong FengShui, Date Selection and YiJing — following classical textbook algorithms precisely. A **multi-LLM layer** then provides streaming interpretation grounded in a BM25-retrieved classical knowledge base.

Core design principles:

- **Classical fidelity** — Year pillars use LiChun as the boundary; month pillars use the *Wu Hu Dun Nian Qi Yue* method; day pillars reference the canonical 1900-01-01 甲戌 epoch; hour pillars use the *Wu Shu Dun Ri Qi Shi* method.
- **Engineering rigour** — Full Pydantic v2 validation, strict separation between the calculation layer and the API layer.
- **AI empowerment** — A multi-text classical knowledge base with BM25 retrieval serves as the LLM context, producing citation-backed interpretation rather than generic output.
- **One-click launch** — Native launchers for Windows (PowerShell + cmd), macOS and Linux; no manual environment setup required.

---

## 2. Key Features

### Calculation Engines

| Feature | Description |
|---|---|
| **BaZi Four Pillars** | Full four-pillar chart with NaYin and hidden stems |
| **Ten Gods** | Complete Ten Gods matrix across all pillars |
| **Chart Patterns** | Auto-detection of major and special patterns (e.g. Cong Ge) |
| **ShenSha** | Complete ShenSha table including LuShen and YangRen |
| **DaYun & LiuNian** | DaYun start age exact to the day (3-day conversion) |
| **ZiWei DouShu** | 12-palace chart, SiHua, FeiXing schools, pattern detection |
| **LiuYao** | Three-coin / yarrow / time-based / manual divination |
| **NaJia** | Full NaJia with world line, six relatives and six spirits |
| **QiMen DunJia** | Sanyuan Jiuju: Nine Stars, Eight Doors, Eight Deities |
| **XuanKong FengShui** | Flying stars, double-star judgments, annual remedies |
| **YangZhai** | Ming Gua, East/West Four Life, Eight Mansion sectors |
| **Date Selection** | Twelve Officers, purpose-specific auspicious day selection |
| **YiJing** | TaiJi → LiangYi → SiXiang → BaGua → 64 hexagrams graph |

### AI Interpretation

- **Classical knowledge base** — 24 knowledge modules covering *Qiong Tong Bao Jian*, *Di Tian Sui*, *San Ming Tong Hui*, *Zi Ping Zhen Quan*, *Zeng Shan Bu Yi*, *Bu Shi Zheng Zong*, *Qi Men Dun Jia Tong Zong*, *Yang Zhai San Yao* and more.
- **Multi-LLM** — Anthropic Claude, OpenAI, DeepSeek, Moonshot, Gemini, plus any OpenAI-compatible endpoint (GLM, Qwen, Yi, Baichuan, MiniMax, Hunyuan, iFlytek Spark, Ollama, …).
- **BM25 RAG** — retrieves the most relevant classical passages before generating, instead of dumping the whole corpus.
- **Streaming output** — Server-Sent Events (SSE) for real-time, token-by-token responses.

---

## 3. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Browser / Client                         │
│                      React + Vite  (Port 5173)                   │
│  Dashboard | BaZi | ZiWei | LiuYao | QiMen | FengShui | YiJing   │
└────────────────────────┬─────────────────────────────────────────┘
                         │  HTTP / SSE (Server-Sent Events)
┌────────────────────────▼─────────────────────────────────────────┐
│                  FastAPI Application  (Port 8888)                 │
│  /agent (SSE)  /bazi  /liuyao  /qimen  /fengshui  /date-sel      │
│  /ziwei  /yijing  /narration  /auth  /models                     │
│                                                                   │
│          Pydantic v2 Schemas  (models/)                          │
│                                                                   │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐   │
│  │  bazi/   │ liuyao/  │  qimen/  │fengshui/ │date_select.. │   │
│  │  ziwei/  │narration │ calendar │constants │              │   │
│  └──────────┴──────────┴──────────┴──────────┴──────────────┘   │
│                                                                   │
│         knowledge/  (Classical Text Library + BM25 RAG)          │
└──────────────────────────────┬───────────────────────────────────┘
                               │  HTTPS  (httpx async)
                   ┌────────────▼──────────────┐
                   │      Multi-LLM Providers   │
                   │   Streaming SSE response   │
                   └───────────────────────────┘
```

### Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| **API framework** | FastAPI 0.115 | Native async SSE, auto Swagger docs, deep Pydantic integration |
| **Validation** | Pydantic v2 | Strict type safety, 5–50× faster than v1 |
| **ASGI server** | Uvicorn | Production-grade, `--reload` for development |
| **Calendar** | ephem 4.1.5 | High-precision astronomy for solar terms |
| **Lunar conversion** | lunarcalendar 0.0.9 | Gregorian ↔ lunar (1900–2100) |
| **HTTP client** | httpx 0.27.2 | Native async, calls multi-LLM streaming APIs |
| **Frontend** | React 19 + Vite | Fast HMR, component-based UI |

---

## 4. The Seven Systems

| System | Chinese | Classical Basis |
|---|---|---|
| BaZi Four Pillars | 八字四柱 | *Di Tian Sui*, *Qiong Tong Bao Jian*, *San Ming Tong Hui* |
| ZiWei DouShu | 紫微斗数 | *Zi Wei Dou Shu Quan Shu* |
| LiuYao Six Lines | 六爻 | *Zeng Shan Bu Yi*, *Bu Shi Zheng Zong* |
| QiMen DunJia | 奇门遁甲 | *Qi Men Dun Jia Tong Zong* |
| FengShui | 风水 | *Shen Shi Xuan Kong Xue*, *Yang Zhai San Yao* |
| Date Selection | 择日 | *Xie Ji Bian Fang Shu* |
| YiJing | 易经 | *Zhou Yi*, *Yi Zhuan* |

Each system exposes a **chart / analysis / synthesis / perspectives / consistency-audit** pipeline, so the calculation output is always cross-checked for internal consistency before it is narrated.

---

## 5. Quick Start

### Windows

```bat
start.bat          # cmd.exe
# or
.\start.ps1        # PowerShell
```

### macOS / Linux

```bash
chmod +x start.sh
./start.sh
```

The launcher creates a virtual environment, installs dependencies, builds the frontend and starts:

- **Backend** — http://localhost:8888 (interactive docs at `/docs`)
- **Frontend** — http://localhost:5173 (dev) or served by FastAPI (production)

### Cloud Deployment

```bash
chmod +x start_cloud.sh
./start_cloud.sh              # default port 9000
PORT=8080 ./start_cloud.sh    # custom port
SKIP_BUILD=1 ./start_cloud.sh # skip frontend rebuild
```

The cloud script builds the frontend and serves it from FastAPI on a single port (Railway / Render / Zeabur friendly).

### Verify Installation

```bash
chmod +x verify_installation.sh
./verify_installation.sh
```

---

## 6. Configuration

Copy `.env.example` to `.env` and fill in your keys:

```dotenv
APP_HOST=0.0.0.0
APP_PORT=8888
DEBUG=false

# Any of the supported LLM providers (see /api/v1/models/providers)
DEEPSEEK_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
```

The platform supports multiple LLM providers simultaneously; the frontend lets you select the provider and model at runtime.

---

## 7. Dependencies

- **Python** ≥ 3.10
- **Node.js** ≥ 18
- Backend packages are listed in `requirements.txt`
- Frontend packages are listed in `frontend/package.json`

---

## 8. API Reference

Interactive OpenAPI documentation is served at `/docs` (Swagger) and `/redoc`.

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `POST /api/v1/bazi/*` | BaZi chart, analysis, synthesis, perspectives |
| `POST /api/v1/ziwei/*` | ZiWei chart, palaces, patterns, fortune |
| `POST /api/v1/liuyao/*` | LiuYao divination, NaJia, full reading |
| `POST /api/v1/qimen/*` | QiMen layout, purpose analysis, synthesis |
| `POST /api/v1/fengshui/*` | XuanKong flying stars, YangZhai |
| `POST /api/v1/date-selection/*` | Auspicious day selection |
| `GET /api/v1/knowledge/*` | Classical knowledge base (incl. BaGua/YiJing) |
| `POST /api/v1/agent/*` | Multi-LLM streaming interpretation (SSE) |
| `POST /api/v1/narration/*` | Bounded narration / archival export |
| `POST /api/v1/auth/*` | Register / login / saved charts |
| `GET /api/v1/models/*` | Model listing and providers |

---

## 9. Project Structure

```
.
├── main.py                 # FastAPI entry point
├── config.py               # Pydantic settings
├── api/                    # API routers (thin layer)
├── core/                   # Calculation engines (pure Python)
│   ├── bazi/               #   Four Pillars
│   ├── ziwei/              #   ZiWei DouShu
│   ├── liuyao/             #   Six Lines
│   ├── qimen/              #   QiMen DunJia
│   ├── fengshui/           #   XuanKong + YangZhai
│   ├── date_selection/     #   Date Selection
│   ├── calendar/           #   GanZhi + solar terms
│   ├── narration/          #   Bounded narration
│   └── constants.py        #   Single source of truth
├── knowledge/              # Classical text library + RAG
├── models/                 # Pydantic schemas
├── frontend/               # React + Vite application
│   └── src/pages/          #   Dashboard, BaZi, ZiWei, LiuYao, QiMen,
│                           #   FengShui, DateSelection, YiJing, …
├── tests/                  # 123 pytest + frontend tests
├── docs/                   # Project portrait, TODO, competitive analysis
├── scripts/                # Utility scripts
├── start.sh / start.ps1 / start.bat      # Local launchers
├── start_cloud.sh / start_cloud.bat      # Cloud launchers
├── verify_installation.sh                # Installation verifier
└── Makefile / pytest.ini
```

---

## 10. Development Guide

```bash
# Backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8888

# Frontend (separate terminal)
cd frontend
npm install
npm run dev        # http://localhost:5173

# Tests
pytest             # backend
cd frontend && npm run build   # build check
```

---

## 11. Troubleshooting

| Symptom | Fix |
|---|---|
| `Python version too old` | Install Python ≥ 3.10 |
| Frontend fails to build | `node --version` — need ≥ 18, then `npm install` |
| No AI output | Set an LLM API key in `.env` and pick a provider in Settings |
| Port already in use | Change `APP_PORT` / `PORT` and restart |

---

## 12. Roadmap

- Deeper classical-text coverage per module (classical-text completeness)
- Multi-provider model routing and fallback
- Export / sharing of chart images and narration archives
- Expanded test coverage and CI pipeline

---

## 13. Contributing

Contributions are welcome. Please keep the calculation layer and the API layer decoupled, follow the existing module structure, and add tests for new logic. See `docs/MODULE_REVIEW_STANDARD.md` for the quality bar.

---

## 14. License

This project is released under the **MIT License**. See [LICENSE](LICENSE).

```
MIT License — Copyright (c) 2024-2026 Chinese Metaphysics Platform Contributors
```
