#!/usr/bin/env bash
# Z-5 / Z-6 / Z-7 / Z-8 / Z-9 polish 测试一键跑

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 1. 准备依赖
cd /tmp
if [ ! -d "/tmp/node_modules/jsdom" ] || [ ! -d "/tmp/node_modules/@babel/cli" ]; then
  echo "[setup] installing test deps..."
  npm install --silent --no-progress --save-dev \
    jsdom react react-dom \
    @babel/core @babel/cli @babel/preset-env @babel/preset-react
fi

# 2. 转译 JSX
mkdir -p /tmp/test_build
echo "[step 1/7] transpiling JSX..."
for f in ZiweiInsightsBar.jsx ZiweiPalaceDetailPanel.jsx ; do
  npx --no-install babel \
    "$PROJECT_ROOT/frontend/src/pages/ZiWei/$f" \
    --presets=@babel/preset-env,@babel/preset-react \
    --out-file "/tmp/test_build/${f%.jsx}.js"
done
# Visualizations.jsx
npx --no-install babel \
  "$PROJECT_ROOT/frontend/src/components/particles/Visualizations.jsx" \
  --presets=@babel/preset-env,@babel/preset-react \
  --out-file /tmp/test_build/Visualizations.js
# StructuredAiOutput.jsx — Z-9
npx --no-install babel \
  "$PROJECT_ROOT/frontend/src/components/UI/StructuredAiOutput.jsx" \
  --presets=@babel/preset-env,@babel/preset-react \
  --out-file /tmp/test_build/StructuredAiOutput.js

# 3. 跑 InsightsBar 测试
echo "[step 2/7] InsightsBar component tests..."
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_ziwei_polish_frontend.js"

# 4. 跑 PalaceDetailPanel 测试
echo
echo "[step 3/7] PalaceDetailPanel component tests..."
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_ziwei_palace_panel_frontend.js"

# 5. 跑 layer-aware overlay panel 测试
echo
echo "[step 4/7] PalaceDetailPanel overlay (decade/triple) tests..."
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_ziwei_overlay_panel_frontend.js"

# 6. 跑 ZiweiVis 飞化箭头测试
echo
echo "[step 5/7] ZiweiVis (particle visualization with fh_type) tests..."
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_ziwei_vis_frontend.js"

# 7. 跑 ChongChainsCard 测试（Z-8）
echo
echo "[step 6/7] ChongChainsCard (chong chains visualization) tests..."
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_ziwei_chong_chains_frontend.js"

# 8. 跑 StructuredAiOutput 测试（Z-9）
echo
echo "[step 7/8] StructuredAiOutput (structured AI output renderer) tests..."
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_ziwei_structured_ai_frontend.js"

# 9. 跑 BaziInsightsBar 测试（B-3）
echo
echo "[step 8/10] BaziInsightsBar (bazi insights bar) tests..."
# 转译 BaziInsightsBar
npx --no-install babel \
  "$PROJECT_ROOT/frontend/src/pages/Bazi/BaziInsightsBar.jsx" \
  --presets=@babel/preset-env,@babel/preset-react \
  --out-file /tmp/test_build/BaziInsightsBar.js
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_bazi_insights_frontend.js"

# 10. 跑 LiuyaoDeepRelations 测试（L-1）
echo
echo "[step 9/10] LiuyaoDeepRelations (六爻深度关系) tests..."
npx --no-install babel \
  "$PROJECT_ROOT/frontend/src/pages/LiuYao/LiuyaoDeepRelations.jsx" \
  --presets=@babel/preset-env,@babel/preset-react \
  --out-file /tmp/test_build/LiuyaoDeepRelations.js
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_liuyao_deep_relations_frontend.js"

# 11. 紫微真实命盘端到端字段验证
echo
echo "[step 10/12] 紫微真实命盘端到端字段..."
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_ziwei_real_chart_frontend.js"

# 12. 紫微高密度宫位测试（文墨天机风格）
echo
echo "[step 11/13] 紫微高密度宫位（文墨天机风格）..."
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_ziwei_high_density_frontend.js"

# 13. 紫微专业布局测试（超越文墨）
echo
echo "[step 12/14] 紫微专业布局（5 行时间盘 + 8 方位 + 中宫八字大运）..."
# 转译 3 个新组件
for f in ZiweiCenterPanel ZiweiTimePanel ZiweiDirections; do
  npx --no-install babel "$PROJECT_ROOT/frontend/src/pages/ZiWei/$f.jsx" \
    --presets=@babel/preset-env,@babel/preset-react \
    --out-file "/tmp/test_build/$f.js"
done
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_ziwei_pro_layout_frontend.js"

# 15. 紫微 4 大新功能（日时切换/派别/命例库/PNG 导出）
echo
echo "[step 13/15] 紫微 4 大新功能（日时切换 / 派别 / 命例库 / PNG 导出）..."
# 转译 ZiweiFamousCases + 拷贝 famousCases.js
npx --no-install babel "$PROJECT_ROOT/frontend/src/pages/ZiWei/ZiweiFamousCases.jsx" \
  --presets=@babel/preset-env,@babel/preset-react \
  --out-file "/tmp/test_build/ZiweiFamousCases.js"
cp "$PROJECT_ROOT/frontend/src/pages/ZiWei/famousCases.js" /tmp/test_build/famousCases.js
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_ziwei_new_features_frontend.js"

# 16. 紫微布局修复（导出按钮位置 / 方位标注 padding / 警示展开）
echo
echo "[step 14/16] 紫微布局修复（用户反馈：字叠加 / 警示截断）..."
node "$SCRIPT_DIR/test_ziwei_layout_fixes_frontend.js"

# 17. 紫微派别真实呈现差异
echo
echo "[step 15/16] 紫微派别真实呈现差异（飞星/三合/四化 各派专属解读面板）..."
# 转译派别面板组件
npx --no-install babel "$PROJECT_ROOT/frontend/src/pages/ZiWei/ZiweiSchoolPanel.jsx" \
  --presets=@babel/preset-env,@babel/preset-react \
  --out-file "/tmp/test_build/ZiweiSchoolPanel.js"
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_ziwei_school_diff_frontend.js"

# 18. React hooks import 完整性检查（防白屏 bug 回归）
echo
echo "[step 16/18] React hooks import 完整性检查（防白屏 bug 回归）..."
node "$SCRIPT_DIR/test_react_hooks_imports.js"

# 19. XuankongPanel (玄空飞星专业版)
echo
echo "[step 17/18] XuankongPanel (玄空飞星专业排盘面板)..."
for f in XuankongCellDetail XuankongAdvanced XuankongPanel; do
  npx --no-install babel "$PROJECT_ROOT/frontend/src/pages/FengShui/$f.jsx" \
    --presets=@babel/preset-env,@babel/preset-react \
    --out-file "/tmp/test_build/$f.js"
done
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_xuankong_panel.js"

# 20. ClassicalCompendiumPanel (典籍精读)
echo
echo "[step 18/18] ClassicalCompendiumPanel (10 大典籍精读专题)..."
npx --no-install babel "$PROJECT_ROOT/frontend/src/pages/Knowledge/ClassicalCompendiumPanel.jsx" \
  --presets=@babel/preset-env,@babel/preset-react \
  --out-file "/tmp/test_build/ClassicalCompendiumPanel.js"
NODE_PATH=/tmp/node_modules node "$SCRIPT_DIR/test_compendium_panel.js"
