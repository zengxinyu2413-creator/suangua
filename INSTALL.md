# 中国术数平台 v6 — 安装与运行指南

> 含紫微斗数 Z-1 → Z-5 全部优化（飞星派飞化、命格评级、经典格局检测、前端洞察栏）

---

## 一、环境要求

| 项目 | 最低版本 | 推荐 |
|---|---|---|
| Python | 3.10 | 3.12 |
| Node.js | 18 | 20 LTS |
| 操作系统 | Linux / macOS / Windows | — |

---

## 二、后端安装

### 方式 A：用 venv（推荐生产部署）

```bash
# 1. 创建虚拟环境
python3 -m venv venv

# 2. 激活
source venv/bin/activate            # Linux / macOS
# 或
venv\Scripts\activate.bat           # Windows

# 3. 装依赖
pip install -r requirements.txt

# 4. 启动后端
python3 main.py
# 或
uvicorn main:app --reload --port 8000
```

### 方式 B：全局安装（Ubuntu 24+/Debian 12+ 需加 PEP 668 标志）

```bash
pip install --break-system-packages -r requirements.txt
python3 main.py
```

### 方式 C：用验证脚本（自动处理 PEP 668）

```bash
chmod +x verify_installation.sh
./verify_installation.sh
```

---

## 三、前端安装

```bash
cd frontend
npm install
npm run dev
```

默认前端 http://localhost:5173，后端 http://localhost:8000。
前端 vite 已配置代理把 `/api/*` 转发到后端。

---

## 四、验证安装

### 4.1 跑全套测试

```bash
# Z-1 → Z-5 + E2E 共 7 套测试，123 项断言
python3 tests/test_ziwei_context.py        # Z-1（19 项）
python3 tests/test_ziwei_feihua.py         # Z-2（10 项）
python3 tests/test_ziwei_overlay.py        # Task 3（9 项）
python3 tests/test_ziwei_brightness.py     # Z-3（7 项）
python3 tests/test_ziwei_patterns.py       # Z-4（13 项）
python3 tests/test_ziwei_polish_backend.py # Z-5 backend（4 项）
python3 tests/test_ziwei_e2e.py            # E2E（36 项）
```

### 4.2 跑前端组件测试（可选）

```bash
bash tests/run_polish_frontend_tests.sh    # Z-5 frontend（25 项）
```

### 4.3 一键完整验证

```bash
./verify_installation.sh
```

期望输出：
```
[1/6] 检查 Python 版本... ✓
[2/6] 检查 pip... ✓
[3/6] 安装 requirements.txt... ✓
[4/6] 验证模块加载... ✓
[5/6] 跑紫微优化测试套件（7 套）...
  ✓ Z-1 context (19 项)
  ✓ Z-2 feihua (10 项)
  ✓ Task 3 overlay (9 项)
  ✓ Z-3 brightness (7 项)
  ✓ Z-4 patterns (13 项)
  ✓ Z-5 polish backend (4 项)
  ✓ E2E (36 项)
[6/6] 真实排盘验证... ✓
全部验证通过！
```

---

## 五、紫微斗数模块说明（新增）

```
core/ziwei/
├── chart.py                  # iztro-py 包装 + 三方四正（既有，含 Z-1 修复）
├── context_builder.py        # AI prompt 上下文生成（Z-1 新建 + Z-2~Z-4 集成）
├── feihua_advanced.py        # Z-2 飞星派飞化引擎（788 行）
├── brightness.py             # Z-3 主星亮度评级 + 命格评分（514 行）
└── pattern_detector.py       # Z-4 23 个经典格局自动检测（1294 行）

api/ziwei.py                  # /chart 端点增强返回 insights（Z-5）

frontend/src/pages/ZiWei/
├── ZiWeiPage.jsx             # 主页面（Z-5 集成 InsightsBar）
└── ZiweiInsightsBar.jsx      # Z-5 洞察栏组件（330 行）
```

### 5.1 API 返回示例（POST /ziwei/chart）

```json
{
  "success": true,
  "data": {
    "palaces": [ ... ],
    "metadata": { ... },
    "feihua": [ ... ],
    "insights": {
      "rating": {
        "overall": "上格",
        "score": 2.14,
        "summary": "命宫与三方四正主星普遍庙旺，先天命格优异",
        "soul_stars": ["紫微"],
        "soul_rating": "上格",
        "sfsz_brief": [
          { "palace": "命宫", "branch": "午", "stars": ["紫微"], "rating": "上格", "score": 3.0 },
          ...
        ],
        "star_notes": ["紫微午宫入庙：帝座之地，权威最盛", ...]
      },
      "patterns": {
        "good": [
          { "name": "君臣庆会格", "evidence": [...], "meaning": "...", "break_conditions": [...] },
          ...
        ],
        "bad": [],
        "total": 3
      },
      "feihua_summary": {
        "double_ji": [ { "from": "夫妻宫", "star": "天同", "to": "疾厄宫" } ],
        "lu_jie_ji": [ { "from": "官禄宫", "star": "天同", "to": "疾厄宫" } ],
        "lu_ji_war": [],
        "soul_incoming": [ { "from": "田宅宫", "hua": "化科", "star": "紫微" } ],
        "soul_chong": [ { "from": "父母宫", "star": "贪狼" } ],
        "quality_changes": [],
        "self_out_palaces": [...],
        "self_in_palaces": [...],
        "concentration": {}
      }
    }
  }
}
```

---

## 六、常见问题

### Q1: `pip install` 报 "externally-managed-environment"
你的系统是 Ubuntu 24+/Debian 12+/Fedora 38+，启用了 PEP 668。
**推荐解决**：用 venv（方式 A）。
**临时解决**：加 `--break-system-packages` 标志（方式 B）。

### Q2: 安装时是否需要 C/C++ 编译器？

**95% 情况下不需要**。所有依赖都有预编译 wheel，pip 会自动下载二进制版本。

**含 C/C++/Rust 扩展的包**（PyPI 上都有预编译 wheel）：

| 包 | 扩展语言 | 用途 | 是否直接依赖 |
|---|---|---|---|
| ephem | C | 天文历法计算 | ✅ 是 |
| pydantic_core | Rust | pydantic 2.x 核心 | ❌ 间接（pydantic 带入） |
| numpy | C/Fortran | 数值计算 | ❌ 间接（rank-bm25 带入） |
| uvloop | C | 高性能事件循环 | ❌ 间接（uvicorn[standard] 带入） |
| httptools | C | HTTP 解析加速 | ❌ 间接（uvicorn[standard] 带入） |
| watchfiles | Rust | 文件监听（--reload） | ❌ 间接（uvicorn[standard] 带入） |
| websockets | C | WebSocket 加速 | ❌ 间接（uvicorn[standard] 带入） |
| PyYAML | C (libyaml) | YAML 解析 | ❌ 间接（uvicorn[standard] 带入） |

**支持的平台（预编译 wheel 直接可用，零编译）**：
- Linux x86_64 (manylinux2014+)
- Linux ARM64 (manylinux_2_28_aarch64)
- macOS Intel + Apple Silicon
- Windows x64

**需要本地编译的情况（罕见）**：
- Alpine Linux（musl libc 而非 glibc）
- ARM 32 位 / RISC-V 等小众架构
- Python 3.13+ 刚发布、wheel 还没出齐
- pip 太旧（< 21.0，不支持 manylinux2014）

**如果某包必须本地编译，需要的工具链**：

```bash
# Ubuntu / Debian
sudo apt install build-essential python3-dev libffi-dev libyaml-dev gfortran

# CentOS / RHEL / Fedora
sudo dnf install gcc gcc-c++ python3-devel libffi-devel libyaml-devel gcc-gfortran

# macOS
xcode-select --install

# Windows (用 venv 走 wheel 永远不需要本地编译；
# 如果非要从源码装，需要 Visual Studio Build Tools 含 C++)

# Rust（pydantic_core / watchfiles 编译时需要）
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Q3: `iztro-py` 装不上
此包是紫微斗数排盘核心。如装失败：
```bash
# 升级 pip 后重装
pip install --upgrade pip
pip install iztro-py
```
若仍失败，检查 https://pypi.org/project/iztro-py/ 是否可访问。
中国大陆用户可加镜像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple iztro-py`

### Q4: 前端 `npm install` 慢
中国大陆建议用淘宝镜像：
```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### Q5: 命盘没出来 insights 字段
检查后端日志，确认 Z-* 模块加载成功；旧版本前端代码请更新到 Z-6。

---

## 七、Z-1 → Z-5 主要改动一览

| 版本 | 关键能力 | 新增代码 |
|---|---|---|
| Z-1 | 修 4 个严重 bug，prompt 基础上下文完整 | context_builder.py (693行) |
| Z-2 | 飞星派飞化引擎（离心/向心/普通飞宫、5 大语象） | feihua_advanced.py (788行) |
| Task 3 | 大限/流年应期判断 + 三盘叠合忌汇聚 | feihua_advanced.py 扩展 (+330行) |
| Z-3 | 主星亮度评级 + 命格自动评分（上/中/下格） | brightness.py (514行) |
| Z-4 | 23 个经典格局自动检测（15 吉 + 8 凶） | pattern_detector.py (1294行) |
| Z-5 | 前端洞察栏 + 后端 insights API | ZiweiInsightsBar.jsx (330行) |

总代码新增 ~3700 行，测试 123 项全部通过。
prompt 信息密度从原始坏 bug 的 ~700 字提升到 ~6941 字（结构化、可验证、命理师级别）。
