# 更新说明 · Changelog

> 本文件记录「中国术数平台」各版本的主要变更。
> All notable changes to the **Chinese Metaphysics Platform** are documented here.

---

## v6.0.0 — 中国术数平台（2026）

> 本次发布将项目正式更名为 **中国术数平台 / Chinese Metaphysics Platform**，
> 并完成七大术数系统全覆盖、多模型 AI 升级与完整工程化改造。

### 项目更名 · Rename

| 项 | 旧 | 新 |
|---|---|---|
| 中文名 | 八卦推演系统 | **中国术数平台** |
| 英文名 | BaGua Divination System | **Chinese Metaphysics Platform** |
| 前端包名 | bagua-frontend | chinese-metaphysics-frontend |
| API 标题 | 八卦推演 API | 中国术数平台 API |

> 注：代码中作为术数概念的「八卦」（如 `knowledge/bagua_system.py`、`/api/v1/knowledge/bagua/*`）
> 以及内部技术标识（`.bagua` 虚拟环境目录、日志/PID 文件、localStorage key 等）予以保留，以保证既有安装环境与用户存档的向后兼容。

### 新增功能 · New Features

- **易经板块（YiJing）**：太极 → 两仪 → 四象 → 八卦 → 六十四卦的可视化知识图谱与卦爻辞。
- **仪表盘（Dashboard）**：平台首页总览与全局入口。
- **每日守护（Daily Guardian）**：每日方位、宜忌等守护信息。
- **叙事系统（Narration）**：有界行文与审定层，支持导出「# 中国术数平台 · 行文存档」。
- **用户体系（Auth）**：注册 / 登录与命盘本地存档（SQLite）。

### AI 能力升级 · AI Upgrade

- 由单一 Claude 接口升级为**多模型 LLM**：Anthropic Claude / OpenAI / DeepSeek / Moonshot / Gemini，
  以及任意 OpenAI 兼容接口（GLM、Qwen、Yi、Baichuan、MiniMax、Hunyuan、iFlytek Spark、Ollama 等）。
- 新增 **BM25 RAG 检索引擎**：古籍知识库按相关度检索后注入提示词，生成有据可查的解读。

### 知识库扩充 · Knowledge Base

- 知识模块扩充至 **24 个**，覆盖八字、紫微、六爻、奇门、风水、择日、易经等经典古籍
  （《穷通宝鉴》《滴天髓》《三命通会》《子平真诠》《增删卜易》《卜筮正宗》《奇门遁甲统宗》《阳宅三要》等）。

### 工程化 · Engineering

- 新增 **123 个测试文件**（pytest 后端测试 + 前端测试）。
- 新增文档：`docs/PROJECT_PORTRAIT.md`、`docs/WORK_TODO.md`、`docs/COMPETITIVE_ANALYSIS.md`、`docs/MODULE_REVIEW_STANDARD.md`。
- 新增云端部署脚本 `start_cloud.sh` / `start_cloud.bat`，以及安装验证脚本 `verify_installation.sh`。
- 新增 `INSTALL.md` 安装指南、`Makefile`、`pytest.ini` 与 `scripts/` 工具脚本。

### 规模变化 · Scale

| 维度 | 旧版本 | v6.0.0 |
|---|---|---|
| 源文件 | 约 108 | 450+ |
| 前端页面 | 9 | 12 |
| 后端 API 路由 | 10 | 12（新增 `auth`、`narration`） |
| 测试文件 | 0 | 123 |

---

## 历史版本 · History

### v1（update_v1）

- 初始发布：八字、六爻、奇门、风水、择日、知识库、AI 命理顾问等基础能力。
