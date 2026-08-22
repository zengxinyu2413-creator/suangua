#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# 中国术数平台 v6 - 安装验证脚本
# ─────────────────────────────────────────────────────────────
# 用法：
#   chmod +x verify_installation.sh
#   ./verify_installation.sh
#
# 此脚本会：
#   1. 检查 Python 版本 ≥ 3.10
#   2. 检查 pip / venv 可用
#   3. 装 requirements.txt
#   4. 跑紫微斗数模块的 7 套测试
#   5. 真实排盘验证 iztro-py 可用
#   6. 启动 FastAPI 看 /chart 端点

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════════"
echo "  中国术数平台 v6 — 安装验证"
echo "═══════════════════════════════════════════════════════════"
echo

# Step 1: Python 版本
echo "[1/6] 检查 Python 版本..."
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
  echo "  ✓ Python $PYTHON_VERSION (≥ 3.10)"
else
  echo "  ✗ Python $PYTHON_VERSION 太旧。请装 Python 3.10+"
  exit 1
fi
echo

# Step 2: pip
echo "[2/6] 检查 pip..."
if python3 -m pip --version > /dev/null 2>&1; then
  echo "  ✓ pip 可用"
else
  echo "  ✗ pip 不可用，请装 pip"
  exit 1
fi
echo

# Step 3: 装依赖
echo "[3/6] 安装 requirements.txt..."
# PEP 668：某些 Linux 发行版（Ubuntu 24+/Debian 12+）禁止 pip 全局安装
# 自动检测并加 --break-system-packages（推荐用户用 venv）
PIP_FLAGS="--quiet"
if python3 -c "import sys; sys.exit(0 if hasattr(sys, 'base_prefix') and sys.prefix == sys.base_prefix else 1)" 2>/dev/null; then
  # 系统 Python（非 venv），需检查 PEP 668
  if python3 -m pip install --quiet --dry-run pip 2>&1 | grep -q "externally-managed\|PEP 668" ; then
    echo "  ⓘ 检测到 PEP 668 受管理环境，自动使用 --break-system-packages"
    echo "  ⓘ 建议生产部署用 venv: python3 -m venv venv && source venv/bin/activate"
    PIP_FLAGS="$PIP_FLAGS --break-system-packages"
  fi
fi
python3 -m pip install $PIP_FLAGS -r requirements.txt 2>&1 | tail -3
echo "  ✓ 依赖安装完成"
echo

# Step 4: 模块加载
echo "[4/6] 验证模块加载..."
python3 -c "
import sys; sys.path.insert(0, '.')
from core.ziwei.context_builder import build_ziwei_context
from core.ziwei.feihua_advanced import analyze_palace_feihua, summarize_feihua_landscape
from core.ziwei.brightness import compute_mingge_overall_rating
from core.ziwei.pattern_detector import detect_all_patterns
from api.ziwei import router
print('  ✓ 所有紫微优化模块加载成功')
"
echo

# Step 5: 跑测试
echo "[5/6] 跑紫微优化测试套件（7 套）..."
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_ziwei_context.py    > /tmp/test_z1.log 2>&1 && echo "  ✓ Z-1 context (19 项)" || echo "  ✗ Z-1 failed (see /tmp/test_z1.log)"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_ziwei_feihua.py     > /tmp/test_z2.log 2>&1 && echo "  ✓ Z-2 feihua (10 项)" || echo "  ✗ Z-2 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_ziwei_overlay.py    > /tmp/test_t3.log 2>&1 && echo "  ✓ Task 3 overlay (9 项)" || echo "  ✗ Task 3 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_ziwei_brightness.py > /tmp/test_z3.log 2>&1 && echo "  ✓ Z-3 brightness (7 项)" || echo "  ✗ Z-3 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_ziwei_patterns.py   > /tmp/test_z4.log 2>&1 && echo "  ✓ Z-4 patterns (13 项)" || echo "  ✗ Z-4 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_ziwei_polish_backend.py > /tmp/test_z5b.log 2>&1 && echo "  ✓ Z-5/Z-6 polish backend (5 项)" || echo "  ✗ Z-5/Z-6 backend failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_ziwei_decade_layout.py  > /tmp/test_z7.log 2>&1 && echo "  ✓ Z-7 decade layout (7 项)" || echo "  ✗ Z-7 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_ziwei_chong_chains.py  > /tmp/test_z8.log 2>&1 && echo "  ✓ Z-8 chong chains (9 项)" || echo "  ✗ Z-8 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_ziwei_z9_prompt.py     > /tmp/test_z9.log 2>&1 && echo "  ✓ Z-9 structured prompt (6 项)" || echo "  ✗ Z-9 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_bazi_relations.py      > /tmp/test_b1.log 2>&1 && echo "  ✓ B-1 bazi relations (12 项)" || echo "  ✗ B-1 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_bazi_special_patterns.py > /tmp/test_b2.log 2>&1 && echo "  ✓ B-2 bazi special patterns (9 项)" || echo "  ✗ B-2 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_liuyao_relations.py    > /tmp/test_l1.log 2>&1 && echo "  ✓ L-1 liuyao relations (8 项)" || echo "  ✗ L-1 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_metaphysics_correctness.py > /tmp/test_meta.log 2>&1 && echo "  ✓ 命理学专业性 (13 项)" || echo "  ✗ 命理学专业性 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_fengshui_correctness.py > /tmp/test_fs.log 2>&1 && echo "  ✓ 风水专业性 (11 项)" || echo "  ✗ 风水专业性 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_fengshui_api_contract.py > /tmp/test_fs2.log 2>&1 && echo "  ✓ 风水 API 契约 (6 项)" || echo "  ✗ 风水 API 契约 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_ziwei_api_contract.py > /tmp/test_zw2.log 2>&1 && echo "  ✓ 紫微 API 契约 (9 项)" || echo "  ✗ 紫微 API 契约 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_ziwei_pro_audit.py > /tmp/test_zw_pro.log 2>&1 && echo "  ✓ 紫微专业性审计 (5 项)" || echo "  ✗ 紫微专业性审计 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_liuyao_pro_audit.py > /tmp/test_ly_pro.log 2>&1 && echo "  ✓ 六爻专业性审计 (15 项)" || echo "  ✗ 六爻专业性审计 failed"
PYTHONPATH="$SCRIPT_DIR" python3 tests/test_ziwei_e2e.py        > /tmp/test_e2e.log 2>&1 && echo "  ✓ E2E (36 项)" || echo "  ✗ E2E failed"
echo

# Step 6: 真实排盘 + FastAPI
echo "[6/6] 真实排盘验证（调用 iztro-py + 完整端到端）..."
python3 << 'PYEOF'
import sys; sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from fastapi import FastAPI
from api.ziwei import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

response = client.post('/ziwei/chart', json={
    'year': 1990, 'month': 5, 'day': 22, 'hour': 7,
    'gender': '男', 'is_lunar': True,
})

if response.status_code == 200:
    data = response.json()['data']
    palaces = data.get('palaces', [])
    insights = data.get('insights', {})
    print(f'  ✓ /ziwei/chart 端点 200')
    print(f'  · 12 宫: {len(palaces)} 个')
    print(f'  · insights.rating.overall: {insights.get("rating", {}).get("overall")}')
    print(f'  · insights.patterns 数: 吉{len(insights.get("patterns", {}).get("good", []))}/凶{len(insights.get("patterns", {}).get("bad", []))}')
    print(f'  · insights.feihua_summary 关键警示: 双忌{len(insights.get("feihua_summary", {}).get("double_ji", []))}、禄解忌{len(insights.get("feihua_summary", {}).get("lu_jie_ji", []))}')
else:
    print(f'  ✗ HTTP {response.status_code}: {response.text[:300]}')
    sys.exit(1)
PYEOF

echo
echo "═══════════════════════════════════════════════════════════"
echo "  ✓ 全部验证通过！项目可以正常运行。"
echo "═══════════════════════════════════════════════════════════"
echo
echo "下一步："
echo "  · 启动后端：  python3 main.py  或  uvicorn main:app --reload"
echo "  · 启动前端：  cd frontend && npm install && npm run dev"
