#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# start_cloud.sh — 云端一键启动脚本（中国术数平台）
#
# 特点：
#   · 监听 0.0.0.0，可被云平台 / 反向代理 / 公网访问
#   · 端口默认 9000（避开常被占用 / 被限制的 8000），
#     也可通过环境变量 PORT 覆盖（Railway / Render / Zeabur 等
#     平台会自动注入 $PORT，脚本会优先使用它）
#   · 前端会被 `npm run build` 打包，并由 FastAPI 在同一个端口
#     直接托管（main.py 已加入 StaticFiles 挂载 + SPA fallback），
#     因此云端只需要暴露一个端口，无需额外起 nginx / 静态服务器
#
# 用法：
#   chmod +x start_cloud.sh
#   ./start_cloud.sh                # 使用默认端口 9000
#   PORT=8080 ./start_cloud.sh      # 自定义端口
#   SKIP_BUILD=1 ./start_cloud.sh   # 跳过前端重新构建（dist 已存在时加速重启）
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

# ─── 基础配置 ───────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

HOST="0.0.0.0"
# 云平台常见会注入 $PORT；本地/自建服务器则用默认 9000（明确避开 8000）
PORT="${PORT:-9000}"
if [ "$PORT" = "8000" ]; then
  echo "⚠️  检测到 PORT=8000，按要求自动改用 9000。"
  PORT=9000
fi

WORKERS="${WORKERS:-1}"
SKIP_BUILD="${SKIP_BUILD:-0}"

echo "════════════════════════════════════════════"
echo "  中国术数平台 · 云端启动"
echo "  Host: ${HOST}   Port: ${PORT}"
echo "════════════════════════════════════════════"

# ─── 1. Python 依赖 ─────────────────────────────────────────────
echo "▶ [1/4] 检查后端依赖 ..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "✗ 未找到 python3，请先安装 Python 3.10+"
  exit 1
fi
python3 -m pip install --quiet --break-system-packages -r requirements.txt \
  || python3 -m pip install --quiet -r requirements.txt

# ─── 2. .env 检查 ───────────────────────────────────────────────
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  echo "▶ 未找到 .env，已从 .env.example 复制一份，请按需填写 DEEPSEEK_API_KEY 等变量"
  cp .env.example .env
fi

# ─── 3. 构建前端 ────────────────────────────────────────────────
if [ "$SKIP_BUILD" != "1" ]; then
  echo "▶ [2/4] 构建前端 (frontend/) ..."
  if ! command -v npm >/dev/null 2>&1; then
    echo "✗ 未找到 npm，请先安装 Node.js 18+"
    exit 1
  fi
  (
    cd frontend
    if [ -f "package-lock.json" ]; then
      npm ci --silent
    else
      npm install --silent
    fi
    npm run build
  )
else
  echo "▶ [2/4] SKIP_BUILD=1，跳过前端构建（沿用现有 frontend/dist）"
fi

if [ ! -f "frontend/dist/index.html" ]; then
  echo "✗ 前端构建产物不存在（frontend/dist/index.html 缺失），无法完成单端口托管。"
  exit 1
fi
echo "  ✓ 前端已就绪：frontend/dist/"

# ─── 4. 启动服务（前后端同进程、同端口） ──────────────────────
echo "▶ [3/4] 启动 FastAPI（同时托管 API + 前端静态页面）..."
echo "▶ [4/4] 访问地址： http://<你的服务器IP或域名>:${PORT}/"
echo "         API 文档： http://<你的服务器IP或域名>:${PORT}/docs"
echo "────────────────────────────────────────────"

exec python3 -m uvicorn main:app \
  --host "${HOST}" \
  --port "${PORT}" \
  --workers "${WORKERS}"
