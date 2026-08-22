# 中国术数平台 v6 —— 开发/CI 任务入口
#
# 用法：
#   make test         全量 pytest（含护栏量化回归）
#   make test-fast    跳过较慢的 regression（本地快速迭代）
#   make regression   仅跑护栏量化回归（pytest -m regression）
#   make metrics      跑独立量化脚本（打印指标 + 阈值断言，退出码即 CI 信号）
#   make guards       前端守护（空值安全 + Hooks 导入）
#   make ci           完整 CI 闸门：guards + 全量 test（含 regression）
#   make package      打包发布 zip（需 VERSION，如 make package VERSION=139）

PYTHON ?= python
NODE   ?= node
PYTEST  = $(PYTHON) -m pytest

.PHONY: test test-fast regression metrics guards ci package help

help:
	@grep -E '^#   make' Makefile | sed 's/^#   /  /'

test:
	$(PYTEST) tests/ -q

test-fast:
	$(PYTEST) tests/ -q -m "not regression"

regression:
	$(PYTEST) tests/ -q -m regression

metrics:
	$(PYTHON) scripts/narration_metrics.py --min-interception 0.98

guards:
	$(NODE) tests/test_react_null_safety.js
	$(NODE) tests/test_react_hooks_imports.js
	$(NODE) tests/test_app_routing.js

ci: guards test
	@echo ""
	@echo "✓ CI 闸门全通过：前端守护 + 全量测试（含护栏量化回归）"

package:
ifndef VERSION
	$(error 需指定版本号：make package VERSION=139)
endif
	cd .. && \
	  find bagua_v6_pack -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null; \
	  find bagua_v6_pack -type d -name ".pytest_cache" -prune -exec rm -rf {} + 2>/dev/null; \
	  zip -rq bagua_v6_complete_$(VERSION).zip bagua_v6_pack \
	    -x "*/node_modules/*" -x "*/__pycache__/*" -x "*/.pytest_cache/*" -x "*/.git/*" -x "*/dist/*"
	@echo "✓ 已打包 ../bagua_v6_complete_$(VERSION).zip"
