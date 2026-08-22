# 中国术数平台 v6 — 全项目画像与描述

> 本文档按「整体项目 → 功能模块 → 具体功能 → 细节函数 → 最底层数据」五层逻辑，
> 对整个项目的所有内容进行画像。所有数据均基于代码实测，非估算。
> 生成基准：后端 472 测试全过、前端 78 JSX 全转译通过。

---

## 目录

1. [第一层 · 整体项目画像](#第一层--整体项目画像)
2. [第二层 · 功能模块画像](#第二层--功能模块画像)
3. [第三层 · 具体功能画像](#第三层--具体功能画像)
4. [第四层 · 细节函数画像](#第四层--细节函数画像)
5. [第五层 · 最底层数据画像](#第五层--最底层数据画像)
6. [横切关注点](#横切关注点跨层)

---

# 第一层 · 整体项目画像

## 1.1 项目定位

**中国术数平台**是一套生产级深度的中国传统术数推演平台，覆盖**七大术数系统**，
以「classical-text completeness（古籍级完整度）」为质量铁律——拒绝皮毛逻辑，
每模块须达到对应古籍的完整解释范围。

七大系统：
| 系统 | 中文名 | 核心古籍 | 性质 |
|------|--------|----------|------|
| 六爻 | 纳甲筮法 | 《增删卜易》 | 占断（卦象） |
| 八字 | 四柱命理 | 《子平真诠》《穷通宝鉴》 | 命理（生辰） |
| 紫微 | 紫微斗数 | 《紫微斗数全书》 | 命理（星盘） |
| 奇门 | 奇门遁甲 | 《烟波钓叟赋》《奇门旨归》 | 占断（时局） |
| 玄空 | 玄空飞星风水 | 《沈氏玄空学》《玄空秘旨》 | 风水（理气） |
| 阳宅 | 阳宅三要 | 《阳宅十书》《八宅明镜》 | 风水（形法） |
| 择日 | 选择学 | 《协纪辨方书》老黄历 | 择吉（日课） |

## 1.2 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI (Python) |
| 历法计算 | `lunar_python`（节气/干支历）、`ephem`（天文节气）、`lunarcalendar` |
| 中文分词 | `jieba`（RAG 检索用） |
| 检索 | BM25（`rank_bm25`）+ jieba 的古籍 RAG |
| 用户存储 | SQLite（`users.db`，仅用户账户） |
| 术数数据 | Python 原生数据结构（常量表/数据模块，非 SQL） |
| AI 解读 | Anthropic API（有界叙事/审定层） |
| 前端框架 | React + Vite |
| 前端转译 | Babel（JSX） |

## 1.3 代码规模（实测）

| 部分 | 文件数 | 行数 |
|------|--------|------|
| `core/`（术数引擎） | 102 | 32,316 |
| `api/`（路由层） | 12 | 5,065 |
| `knowledge/`（古籍知识库） | 24 | 12,255 |
| `models/`（请求响应模型） | 6 | — |
| `tests/`（测试） | 58 文件 | 472 用例全过 |
| `frontend/src/`（前端） | 78 jsx + 7 js | — |
| **合计** | **约 250 源文件** | **约 5 万行后端 + 前端** |

## 1.4 顶层目录结构

```
bagua_v6_pack/
├── main.py                  # FastAPI 入口，注册 7 路由（prefix=/api/v1）
├── api/                     # 路由层：每系统一个 router + agent + auth + knowledge
├── core/                    # 术数引擎核心（7 子模块 + calendar 历法底座）
│   ├── constants.py         # 659 行基础常量（34 张数据表：干支/五行/六十甲子…）
│   ├── user_db.py           # SQLite 用户账户库（users.db）
│   ├── calendar/            # 历法底座（节气、干支、真太阳时）
│   ├── bazi/  liuyao/  ziwei/  qimen/  fengshui/  date_selection/
├── knowledge/               # 古籍知识库（24 模块）+ BM25/RAG 检索引擎
├── models/                  # Pydantic 请求/响应模型
├── docs/                    # 文档（含本画像 + 六件套标准）
├── tests/                   # 58 测试文件
└── frontend/src/            # React 前端（12 页面 + 13 组件 + store/api）
```

## 1.5 请求生命周期（数据流）

```
前端页面 (React)
   │  fetch JSON
   ▼
api/{module}.py  路由 handler
   │  ① 调用 core 引擎排盘/起卦/排局
   ▼
core/{module}/   确定性术数计算（历法→排盘→分析）
   │  ② 装配六件套（总论/推理链/视角/审核）
   ▼
core/{module}/overview·synthesis·perspectives·consistency_audit
   │  ③ 可选：跨模块协同（命卦匹配/大运流年/理气形法/八字个性化）
   ▼
返回 ApiResponse(success, data)
   │
   ▼
前端渲染 hero → 推理链 → 多视角 → 审核 → （可选）AI 解读
                                              │
                                              ▼ api/agent.py → Anthropic API
```

## 1.6 入口与路由注册（main.py）

```python
app = FastAPI(title="中国术数平台 API", version="2.0.0")
app.include_router(bazi_router,     prefix="/api/v1")   # 八字
app.include_router(liuyao_router,   prefix="/api/v1")   # 六爻
app.include_router(qimen_router,    prefix="/api/v1")   # 奇门
app.include_router(fengshui_router, prefix="/api/v1")   # 玄空+阳宅
app.include_router(date_router,     prefix="/api/v1")   # 择日
app.include_router(knowledge_router,prefix="/api/v1")   # 古籍知识库
app.include_router(agent_router,    prefix="/api/v1")   # AI 解读/统一咨询
# （auth 路由按部署可选挂载）
```

---

# 第二层 · 功能模块画像

> 每模块均遵循统一的「六件套」深度架构（见 [横切关注点](#横切关注点跨层)）。

## 2.1 六爻模块（`core/liuyao/`，17 文件）

**职能**：纳甲筮法占断。给定问题 + 起卦法 → 本卦/变卦 → 装卦纳甲 → 世应用神 → 应期。

| 文件 | 行 | 职能 |
|------|----|------|
| `interpreter.py` | 1119 | 总解释引擎（最大，L-1 关系深度分析） |
| `hexagram_data.py` | 932 | **64 卦数据库**（卦辞/爻辞/卦象） |
| `najia.py` | 686 | 装卦纳甲（世应/六亲/六神/旬空/爻强弱） |
| `yingqi_calculator.py` | 577 | 应期推算（17 函数：日辰/月建/旺衰/滚动未来） |
| `advanced_features.py` | 448 | 进阶（伏神/飞神/六合六冲卦等） |
| `relations.py` | 449 | 爻位关系（生克冲合刑害） |
| `zhuang_gua.py` | 308 | 装卦（卦宫/世应定位） |
| `zonghe_duan.py` | 290 | 综合断 |
| `full_reading.py` | 267 | **① 综合总论合成**（用神 yong_liuqin） |
| `divination.py` | 253 | 起卦法（coin/yarrow/time/manual 四法） |
| `yongshen_synthesis.py` | 189 | **② 用神力量推理链** |
| `perspectives.py` | 191 | **③ 多视角** |
| `hua_bian.py` | 217 | 化进退神/化空化墓 |
| `consistency_audit.py` | 206 | **④ 一致性审核** |
| `topic_templates.py` | 173 | 占问主题模板（求财/婚姻/疾病…） |
| `duan_overview.py` | 113 | 断语总览 |

## 2.2 八字模块（`core/bazi/`，18 文件）

**职能**：四柱命理。生辰 → 四柱八字 → 十神/格局/强弱/用神/神煞 → 大运流年。

| 文件 | 行 | 职能 |
|------|----|------|
| `forecaster.py` | 572 | **大运流年预测**（13 函数：起运/方向/流年/岁运） |
| `day_master_profiles.py` | 550 | 日主画像 + **用神分析** `analyze_yong_shen` |
| `special_patterns.py` | 540 | 特殊格局识别（19 函数：从格/化格/专旺…） |
| `combos.py` | 507 | 组合断（神煞组合 + 格局成破 + 岁运组合） |
| `relations.py` | 588 | 刑冲合害（11 函数）+ 大运流年触发 |
| `tiaohou_yongshen.py` | 458 | 调候用神（《穷通宝鉴》） |
| `analyzer.py` | 446 | 命盘分析总成 |
| `chart.py` | 300 | **排盘底座**（真太阳时/节气月柱/胎元命宫） |
| `applications.py` | 264 | 专项应用（事业/财/婚/健康…） |
| `consistency_audit.py` | 219 | **④ 一致性审核**（含命运背驰） |
| `synthesis.py` | 162 | **② 命局力量推理链**（先天+后天分层） |
| `perspectives.py` | 185 | **③ 多视角**（含运程时序） |
| `overview.py` | 149 | **① 命局总论**（含当前运程） |
| `chenggu.py` | 147 | 称骨算命 |
| `classical.py` | 137 | 古籍断语 |
| `current_fortune.py` | 106 | **大运流年并入主读盘**（跨模块协同 #1） |
| `reverse_lookup.py` | 104 | 反推（已知特征推命） |

## 2.3 紫微模块（`core/ziwei/`，16 文件）

**职能**：紫微斗数。生辰 → 十二宫 + 主星辅星 → 庙旺/四化/格局 → 大限流年。

| 文件 | 行 | 职能 |
|------|----|------|
| `pattern_detector.py` | 1628 | **格局识别**（47 函数，最大） |
| `feihua_advanced.py` | 1147 | 飞星四化进阶（14 函数） |
| `chart.py` | 1176 | **排盘底座**（17 函数：安星/大限/流年/叠盘） |
| `context_builder.py` | 1012 | 上下文构建（18 函数） |
| `star_palace.py` | 574 | 星曜入宫断 |
| `brightness.py` | 529 | 庙旺利陷（星曜亮度） |
| `chong_analysis.py` | 402 | 冲照分析 |
| `feihua_chain.py` | 307 | 飞化冲链 |
| `perspectives.py` | 194 | **③ 多视角**（含行运运限） |
| `consistency_audit.py` | 169 | **④ 一致性审核** |
| `synthesis.py` | 161 | **② 命格力量推理链**（先天+后天） |
| `birth_sihua.py` | 151 | 生年四化 |
| `overview.py` | 140 | **① 命盘总论**（含当前运限） |
| `current_fortune.py` | 100 | **大限流年并入主读盘**（跨模块协同 #1） |
| `classical.py` | 52 | 古籍 |

## 2.4 奇门模块（`core/qimen/`，14 文件）

**职能**：奇门遁甲。时刻 + 用途 → 三元局数 → 九宫飞布（天地人神四盘）→ 用神落宫。

| 文件 | 行 | 职能 |
|------|----|------|
| `algorithm.py` | 723 | **排局引擎**（局数/节气元/九宫飞布/值符值使） |
| `patterns_complete.py` | 657 | 格局全集（吉格凶格） |
| `analyzer.py` | 625 | 分析总成（含 purpose 驱动用神） |
| `purpose_analysis.py` | 488 | **用途用神逻辑**（求财/事业/婚姻…各取用神） |
| `palace_layers.py` | 261 | 宫位多层（旬空/马星/击刑/入墓） |
| `synthesis.py` | 171 | **② 用神力量推理链** |
| `yongshen.py` | 167 | 用神选取 |
| `zeji.py` | 154 | **奇门择吉**（×择日跨模块） |
| `perspectives.py` | 141 | **③ 多视角** |
| `geju_layers.py` | 128 | 格局分层 |
| `yingqi.py` | 125 | 应期 |
| `consistency_audit.py` | 124 | **④ 一致性审核** |
| `overview.py` | 115 | **① 局势总论** |

## 2.5 风水模块（`core/fengshui/`，22 文件 — 玄空 + 阳宅）

**玄空（理气）**：坐山 + 年运 → 运山向三盘飞星 → 山向格局 → 各宫吉凶 → 旺衰方。
**阳宅（形法）**：门主灶 + 命卦 → 八宅游年 → 门主局/灶局 → 人宅相配 → 六事。

| 文件 | 行 | 职能 |
|------|----|------|
| `xuankong_advanced.py` | 814 | 玄空进阶（19 函数：城门/反伏吟/七星打劫…） |
| `xuankong.py` | 760 | **玄空排盘**（运/飞星/山向格局/特殊格局/化解） |
| `yangzhai_data.py` | 729 | **阳宅数据库**（512 门主灶局 + 64 断语…） |
| `double_star_judgments.py` | 523 | 双星组合断（玄空山向星组合） |
| `flying_stars.py` | 561 | 紫白飞星 |
| `yangzhai_sanyao.py` | 468 | **阳宅三要排断**（八宅游年/门主局/灶局） |
| `yangzhai_liushi.py` | 365 | **阳宅六事**（路井灶厕碓磨畜栏） |
| `calculator.py` | 262 | 命卦计算（东四命/西四命/人宅相配） |
| `xuankong_luantou.py` | 170 | 峦头形理（砂水宜忌/旺衰方） |
| `house_report.py` | 162 | **理气×形法统一宅报告**（跨模块协同 #2） |
| `yangzhai_floors.py` | 133 | 楼层五行 + 穿宫九星 |
| 玄空六件套 | — | overview/synthesis/perspectives/audit + **mingua（纳命卦 #4）** |
| 阳宅六件套 | — | overview/synthesis/perspectives/audit + **mingua（人宅相配）** |

## 2.6 择日模块（`core/date_selection/`，8 文件）

**职能**：选择学。用途 + 年月 → 逐日建除/黄道/神煞/宜忌 → 吉日排序 → 八字个性化。

| 文件 | 行 | 职能 |
|------|----|------|
| `selector.py` | 399 | **择日主引擎**（逐日建除/黄道/神煞/岁破/生辰冲合） |
| `twelve_officers.py` | 338 | 建除十二神(12) + 二十八宿(28) + 三煞(4) |
| `perspectives.py` | 144 | **③ 多视角**（含个人配合真计算） |
| `synthesis.py` | 139 | **② 吉日力量推理链** |
| `personalize.py` | 119 | **八字个性化**（用神/冲克过滤，跨模块协同 #3） |
| `overview.py` | 115 | **① 选期总论** |
| `consistency_audit.py` | 115 | **④ 一致性审核** |

## 2.7 历法底座（`core/calendar/`，3 文件）— 所有模块的共同地基

| 文件 | 行 | 职能 |
|------|----|------|
| `solar_terms.py` | 199 | **节气计算**（ephem 天文 + 节气日 + 月支 + 立春） |
| `ganzhi.py` | 55 | 六十甲子（干支序号互转） |

> 历法底座是**严谨性的根**：节气定月柱（八字）、月建（六爻）、局数元（奇门）、
> 运（玄空）。审计中发现的六爻月令 bug 即源于绕过此底座、自造转换。

## 2.8 知识库模块（`knowledge/`，24 文件，12,255 行）+ AI（`api/agent.py`）

古籍知识库 + BM25/RAG 检索 + Anthropic AI 解读层（详见第五层）。

---

# 第三层 · 具体功能画像

> 以 API 端点为单位。全部端点前缀 `/api/v1`。下表「输出字段」为实测顶层字段数。

## 3.1 八字（`api/bazi.py`，9 端点）

| 端点 | 方法 | 功能 | 输出 |
|------|------|------|------|
| `/bazi/chart` | POST | 排盘（四柱+十神+格局+强弱+用神+神煞+刑冲合害+特殊格局+组合断+**当前运程**+六件套） | 35 字段 |
| `/bazi/fortune` | POST | **运势全推**（大运10+流年21+流月日时+岁运组合断） | — |
| `/bazi/career` | POST | 事业专断（事业方向/十神建议/性格优劣） | — |
| `/bazi/marriage` | POST | 婚姻专断（配偶宫/配偶星/刑冲/质量） | — |
| `/bazi/wealth` | POST | 财运专断（财星/财格等第） | — |
| `/bazi/health` | POST | 健康专断（日主脏腑/弱五行/分布） | — |
| `/bazi/compatibility` | POST | 合婚（双盘相合） | — |
| `/bazi/chenggu` | POST | 称骨算命 | — |
| `/bazi/reverse` | POST | 反推（特征推命） | — |

请求体：`{year, month, day, hour, gender, is_lunar, is_leap_month?, use_true_solar_time?, city?, province?}`；
`/fortune` 用 `{birth:{...}, query_year?}` 嵌套体。

## 3.2 六爻（`api/liuyao.py`，5 端点）

| 端点 | 方法 | 功能 | 输出 |
|------|------|------|------|
| `/liuyao/divine` | POST | **起卦占断**（本卦/变卦/装卦纳甲/世应/用神/六亲/六神/旬空/伏神/应期+六件套） | 43 字段 |
| `/liuyao/hexagram/{n}` | GET | 单卦详情 | — |
| `/liuyao/hexagrams` | GET | 64 卦目录 | — |
| `/liuyao/gua_static/{n}` | GET | 静态卦象 | — |
| `/liuyao/gua_catalog` | GET | 卦象总目 | — |

起卦法（`method`）：`coin`（铜钱，需 `yao_values`）｜`yarrow`（蓍草）｜`time`（时间，可 `query_time`）｜`manual`（手输 6 爻值 6/7/8/9）。
关键字段：`full_reading.yong_liuqin`（用神六亲）、`world_line/application_line`（世应）、`month_zhi/day_zhi/day_gan`（**节气月令+日干支**）、`yingqi`（应期）。

## 3.3 紫微（`api/ziwei.py`，4 端点）

| 端点 | 方法 | 功能 | 输出 |
|------|------|------|------|
| `/ziwei/chart` | POST | 排盘（十二宫+主辅星+庙旺+四化+格局+三方四正+**当前运限**+bazi_overlay+六件套） | 20 字段 |
| `/ziwei/triple` | POST | 三盘叠合（本命+大限+流年） | — |
| `/ziwei/decade` | POST | 大限四化 | — |
| `/ziwei/hours` | GET | 时辰对照 | — |

关键字段：`palaces[12]`（各宫含 `decadal_range` 大限/`ages` 流年虚岁/`major_stars`/`palace_full`）、`metadata.five_elements`（**五行局**，如火六局）、`bazi_overlay`（八字↔紫微叠盘）、`current_fortune`（当前大限宫+流年宫）。

## 3.4 奇门（`api/qimen.py`，5 端点）

| 端点 | 方法 | 功能 | 输出 |
|------|------|------|------|
| `/qimen/layout` | POST | **排局**（三元局数+**节气元**+九宫天地人神四盘+用神落宫+格局+六件套） | 33 字段 |
| `/qimen/now` | GET | 当前时刻局 | — |
| `/qimen/hour-layout` | POST | 时家奇门 | — |
| `/qimen/hour-now` | GET | 当前时家局 | — |
| `/qimen/zeji` | POST | **奇门择吉**（×择日：扫日×时辰选最佳） | — |

关键字段：`ju_type`（阳遁/阴遁）、`ju_number`（局数）、`jieqi`（**节气名**）、`yuan`（**上/中/下元，由日位定**）、`palaces`（九宫 star/door/deity/stem）。`purpose` 驱动用神选取。

## 3.5 风水（`api/fengshui.py`，8 端点 — 玄空+阳宅）

| 端点 | 方法 | 功能 | 输出 |
|------|------|------|------|
| `/fengshui/xuankong` | POST | **玄空排盘**（运/山向飞星三盘/格局/正零城门/峦头旺衰/**命卦人盘**+六件套） | 41 字段 |
| `/fengshui/yangzhai_sanyao` | POST | **阳宅三要**（门主灶游年/门主局/灶局/命卦相配/六事+六件套） | — |
| `/fengshui/house_report` | POST | **统一宅报告**（理气×形法合断同房） | — |
| `/fengshui/analysis` | POST | 命卦宅卦分析 | — |
| `/fengshui/yangzhai_liushi` | POST | 阳宅六事 | — |
| `/fengshui/twenty_four_mountains` | GET | 二十四山 | — |
| `/fengshui/monthly_flying` | GET | 月飞星 | — |
| `/fengshui/yangzhai_layout` | GET | 最佳布局 | — |

请求：玄空 `{sitting_mountain:'子', year, birth_year?, gender?}`（向自动对宫推；带生年出命卦人盘）；
阳宅 `{men:'坎', zhu:'巽', zao:'震', birth_year?, gender?}`；统一 `{sitting_mountain, year, men, zhu, zao, birth_year?, gender?}`。

## 3.6 择日（`api/date_selection.py`，1 端点）

| 端点 | 方法 | 功能 | 输出 |
|------|------|------|------|
| `/date-selection/select` | POST | **择吉**（逐日建除/黄道/二十八宿/神煞/岁破/三煞/宜忌 → 吉日排序 → **八字个性化**+六件套） | 14 字段 |

请求：`{purpose, year, month, birth_year?, birth_month?, birth_day?}`（带生辰则按本命用神/冲克个性化重排）。
关键字段：`all_days`（逐日含 score/officer/宿/神煞）、`best_days`（首选）、`personalization`（个人首选/个人不宜）、`three_killings`（三煞方）。

## 3.7 知识库（`api/knowledge.py`，约 90 端点）

巨型 GET 树，覆盖 `/classical/*`（古籍：十神/六爻/奇门/八字/风水/择日各专题）、`/foundations/*`（阴阳/五行/干支/纳音/藏干）、`/advanced/*`（紫微/梅花/大六壬/各系统深层）、`/practical/*`（财运/感情/事业/疾病/应期/择日/口诀/名家）、`/bagua/*`（太极/先后天/64卦/京房/易传）、`/xingxiu/*`（四象/28宿/七政/分野）、`/compendium/*`（古籍全集）。
检索端点：`/knowledge/search`、`/smart-search`（BM25+jieba RAG）。

## 3.8 AI 解读（`api/agent.py`，7 端点）

| 端点 | 功能 |
|------|------|
| `/agent/consult` | **统一咨询**（路由多模块综合） |
| `/agent/interpret` | 通用解读 |
| `/agent/bazi` `/liuyao` `/qimen` `/fengshui` | 各系统 AI 解读 |

AI 解读系统（`INTERPRET_SYSTEMS`）：`bazi/ziwei/qimen/liuyao/fengshui` 各有「解读」与「审定」(`*_audit`) 双角色，
共 12 键：`bazi, bazi_audit, ziwei, ziwei_audit, qimen, qimen_audit, liuyao, liuyao_audit, fengshui, xuankong_audit, yangzhai_audit, zeri_audit`。
AI 仅作**有界叙事与审定**，所有术数推算由确定性引擎完成。

---

# 第四层 · 细节函数画像

> 列各引擎之核心函数。`_` 前缀为内部辅助函数。

## 4.1 历法底座（最底层，所有模块依赖）

**`core/calendar/solar_terms.py`**
- `_ephem_solarterm(year, term)` — ephem 天文计算节气精确时刻
- `_get_solarterm_dt(year, name)` — 取某年某节气 datetime（奇门局数/八字月柱共用）
- `get_jie_dates(year)` — 一年十二「节」日期
- `get_month_dizhi_at(dt)` — 某时刻的节气月支（月建）
- `nearest_jie(dt)` / `lichun_of_year(year)` — 最近节 / 立春

**`core/calendar/ganzhi.py`**
- `ganzhi_from_index(idx)` — 六十甲子序号 → (天干, 地支)
- `index_from_ganzhi(gz)` — 干支 → 序号；`_REF_DATE/_REF_DAY_IDX` — 日干支推算基准

## 4.2 八字引擎

**`core/bazi/chart.py`**（排盘底座）
- `_year_ganzhi / _month_ganzhi / _day_ganzhi / _hour_ganzhi` — 四柱干支（月柱按节气、日柱连续推、时柱五鼠遁）
- `apply_true_solar_time(dt, longitude)` — 真太阳时校正（均时差 `_equation_of_time` + 经度差）
- `longitude_from_city(city)` — 城市经度查询
- `_get_renyuan_siling(month_zhi, day)` — 人元司令（月令藏干分日用事）

**`core/bazi/forecaster.py`**（大运流年）
- `_dayun_start_age(birth_dt, gender, ...)` — 起运年龄（节气距离 ÷ 3）
- `_dayun_direction(gender, year_gan)` — **起运方向（阳男阴女顺、阴男阳女逆）**
- `calculate_dayun(chart, gender, birth_year, num=10)` — 排大运
- `calculate_liunian(...)` / `calculate_liuyue(...)` — 流年 / 流月
- `_analyze_dayun_interactions / _analyze_liunian_taisu` — 大运/流年与命局交互

**`core/bazi/day_master_profiles.py`**
- `analyze_yong_shen(chart)` — **用神分析**（返回 yong/xi/ji/chou 五行 + 调候 + 格局）
- `get_day_master_profile(dm)` — 日主十干画像

## 4.3 六爻引擎

**`core/liuyao/najia.py`**（装卦纳甲）
- `annotate_with_najia(result, hex_num, lower, upper, day_gan, day_idx, day_zhi)` — 总装卦
- `_get_world_line(...)` — 世应定位（八宫卦序）
- `get_liu_qin(palace_wx, yao_wx)` — 六亲（生克定父子兄财官）
- `assign_liu_shen(day_gan)` — 六神（日干起青龙）
- `get_kong_wang(day_idx)` — 旬空；`get_line_strength(...)` — 爻强弱（月日生克）

**`core/liuyao/yingqi_calculator.py`**（应期，17 函数）
- `_roll_future_dates / _roll_future_months` — 滚动未来日/月找应期
- `_sheng_me / _branches_of_wuxing` — 生克关系 / 某五行之地支
- 旺相休囚死、合冲值日、墓库等应期法

## 4.4 紫微引擎

**`core/ziwei/chart.py`**（17 函数）
- `build_ziwei_chart(...)` — 排盘总成（定五行局→安紫微→安诸星→十二宫）
- `calculate_feihua(palaces)` — 飞星四化（化禄权科忌）
- `get_decade_palace(solar_date, hour_idx, gender, age)` — 大限宫定位
- `compute_decade_palaces_layout / compute_annual_palaces_layout` — 大限盘/流年盘
- `get_palace_three_directions(...)` — 三方四正
- `calculate_decade_feihua(stem, palaces)` — 大限四化叠盘

## 4.5 奇门引擎

**`core/qimen/algorithm.py`**
- `_is_yang_dun(dt)` — 阴阳遁判定（冬至后阳遁、夏至后阴遁）
- `_estimate_ju_number(dt, yang_dun)` — 局数（三元局数表 × 节气元）
- `_get_ju_context(dt, yang_dun)` — **返回真实节气+元+局数**（元由日在节气内位序定）
- `_fly_layout(ju, yang_dun)` — 九宫飞布（星门神洛书序）
- `_get_palace_stem(pos, ju, yang_dun)` — 地盘六仪三奇
- `calculate_heavenly_plate(...)` — 天盘；`detect_qimen_patterns(...)` — 格局
- `calculate_qimen(...)` — 总排局入口

## 4.6 风水引擎

**`core/fengshui/xuankong.py`**
- `get_yun(year)` — 三元九运（2024-2043 九运）
- `get_mountain_by_degree / get_mountain_by_name` — 二十四山定位
- `fly_stars(...)` — 飞星（运盘+山盘+向盘三盘）
- `calculate_xuankong_chart(year, sitting_mountain)` — 玄空总排盘
- `detect_special_patterns(...)` — 旺山旺向/上山下水/反伏吟/七星打劫
- `_get_remedies(...)` — 化解法

**`core/fengshui/yangzhai_sanyao.py`**
- `_younian_between(gua1, gua2)` — 两卦间游年星（生气/天医/延年/伏位/绝命/五鬼/六煞/祸害）
- `analyze_yangzhai_sanyao(men, zhu, zao)` — 门主灶三要排断
- `parse_door / _to_gua_name` — 门向解析

## 4.7 择日引擎

**`core/date_selection/selector.py`**
- `select_dates(purpose, year, month, ...)` — 主引擎（逐日评分排序）
- `_build_day(...)` — 单日构建（建除/黄道/宿/神煞/岁破/三煞/生辰冲合）
- `_get_officer(...)` — 建除十二神；`_get_year_zhi(...)` — 年支（定三煞/岁破）

**`core/date_selection/personalize.py`**
- `personalize_days(days, birth_year, ...)` — 八字个性化（用神扶/忌克 + 命支冲合 → 个人契合分）
- `_person_profile(...)` — 复用 build_chart+analyze_yong_shen 取本命用神/命支

---
# 第五层 · 最底层数据画像

> **关键架构决策**：术数推算数据（卦象、星曜、断语、格局）全部以 **Python 原生数据
> 结构**（常量表、数据模块）存储，**不入 SQL**——便于版本控制、原子加载、与引擎同源。
> SQL（SQLite）仅用于**用户账户与收藏**。

## 5.1 基础常量层 — `core/constants.py`（659 行，34 张数据表）

全平台共享的最底层常量，含（部分）：
- `JIUGONG_POSITIONS` — 九宫方位（洛书）
- `JIUXING` — 九星（天蓬天任…奇门/玄空共用）
- `BAMEN` — 八门（休生伤杜景死惊开）
- `BASHEN` — 八神（值符螣蛇太阴…）
- `BAMEN_AUSPICIOUS` — 八门吉凶
- `SANHE_GROUPS` — 三合局（申子辰水…）
- 另含：天干地支、五行生克、六十甲子、藏干、纳音、十神、地支六冲六合三刑、
  二十四山、生肖、时辰对照等共 34 表。
- 历史 bug 教训：`hour_to_dizhi` 等映射须用于其本职（时辰），误用于月支致六爻月令错。

## 5.2 各系统数据库（Python 数据模块）

| 数据文件 | 行 | 内容 |
|----------|----|------|
| `core/liuyao/hexagram_data.py` | 932 | **64 卦完整数据库**（卦名/卦辞/爻辞/卦象/上下卦） |
| `core/fengshui/yangzhai_data.py` | 729 | **512 门主灶局** + 64 门主断语 + 灶向原则（ZAO_PRINCIPLE 等 5 表） |
| `core/bazi/day_master_profiles.py` | 550 | 十干日主画像 + 用神逻辑 |
| `core/fengshui/double_star_judgments.py` | 523 | 玄空双星组合断（81 组山向星组合） |
| `core/ziwei/pattern_detector.py` | 1628 | 紫微格局库（47 检测函数 + 格局数据） |
| `core/qimen/patterns_complete.py` | 657 | 奇门格局全集 |

> 紫微 360 条结构化解释（168 主星×宫 + 24 双星 + 168 辅煞星×宫）、阳宅 512 门主灶配置，
> 均为这一层的结构化数据，由引擎合成（`palace_full`/`synthesize_full_judgment`）为连贯读盘。

## 5.3 古籍知识库 — `knowledge/`（24 模块，12,255 行）

独立于排盘引擎的古籍原文知识库，供 RAG 检索与 AI 解读引用：

| 模块 | 行 | 内容 |
|------|----|------|
| `classical_compendium.py` | 1683 | 古籍全集（最大） |
| `liuyao_classical.py` | 1043 | 六爻古籍（《增删卜易》等） |
| `classical_knowledge.py` | 912 | 综合古籍知识 |
| `qimen_classical.py` | 768 | 奇门古籍（《烟波钓叟赋》等） |
| `classical_texts.py` | 637 | 古籍原文 |
| `knowledge_deep.py` | 608 | 深层知识 |
| `foundations.py` | 572 | 基础理论（阴阳五行干支纳音藏干） |
| `bazi_classical_deep.py` | 527 | 八字深层（《子平真诠》《穷通宝鉴》） |
| `yijing_graph.py` | 501 | 易经卦序图谱 |
| `xingxiu_system.py` | 492 | 星宿系统（28 宿/七政/分野） |
| `ziwei_deep.py` `ziwei_classical*.py` | 230-483 | 紫微古籍 |
| `advanced_systems.py` | 474 | 进阶系统（梅花/大六壬） |
| `shishen_shensha.py` | 445 | 十神神煞 |
| `bazi_classical.py` | 443 | 八字古籍 |
| `date_classical.py` | 432 | 择日古籍 |
| `bagua_system.py` | 411 | 八卦系统（先后天/京房/易传） |
| `fengshui_classical.py` | 378 | 风水古籍 |
| `najia_complete.py` | 317 | 纳甲全表 |
| `practical_divination.py` | 294 | 实务断例 |

## 5.4 检索引擎 — `knowledge/rag.py`（214 行，BM25 + jieba）

`ClassicalRAG` 类：
- `build()` — 遍历（harvest）所有知识模块，jieba 中文分词，建 BM25 索引
- `search(query, top_k)` — BM25 检索最相关古籍段落
- `search_and_format(...)` — 检索 + 格式化（供 AI 解读引用古籍佐证）

技术：`rank_bm25` 的 BM25 算法 + `jieba` 中文分词，轻量、无需向量数据库。

## 5.5 用户数据库 — `core/user_db.py` + `users.db`（SQLite）

唯一的真 SQL 数据库，仅存账户与收藏：

**表 `users`**：用户账户（用户名/密码哈希/显示名/token）
**表 `saved_charts`**：收藏命盘（user_id/module/title/summary/birth_info/chart_data/notes/tags）

核心函数：
- `register(username, password, display_name)` — 注册（hashlib 哈希 + secrets token）
- `login(username, password)` — 登录
- `get_user_by_token(token)` — token 鉴权
- `save_chart / get_chart` — 命盘收藏/读取
- `get_birth_info / save_birth_info` — 生辰信息存取

---

# 横切关注点（跨层）

## A. 六件套深度架构（每模块统一）

所有 7 模块均实现统一的六层深度（标准见 `docs/MODULE_REVIEW_STANDARD.md`）：

| 件 | 文件 | 职能 |
|----|------|------|
| ① 综合总论合成 | `overview.py` | hero 级总论，返回 quality(吉/中/凶)/headline/verdict_line/段落 |
| ② 推理链 | `synthesis.py` | factors[] / composite_score / composite_label / chain_text |
| ③ 多视角 | `perspectives.py` | 6+ 视角，无孤儿，coverage 映射核查 |
| ④ 一致性审核 | `consistency_audit.py` | 确定性 findings{id,severity,title,modules,detail,suggestion}，按矛盾/注意/提示排序 |
| ⑤ AI 审定 | `api/agent.py` | `{module}_audit` 角色，有界叙事 |
| ⑥ 古籍典籍 | `knowledge/` | RAG 检索佐证 |

## B. 历法底座（严谨性的根）

`core/calendar/` 为所有模块的共同地基：节气定**月柱**（八字）、**月建**（六爻）、
**局数元**（奇门）、**运**（玄空）。任何绕过底座的自造转换都是 bug 温床
（审计中六爻月令、奇门元两 bug 皆此类）。

## C. 跨模块协同（四项）

| # | 协同 | 引擎 | 揭示 |
|---|------|------|------|
| 1 | 命理时间维度 | `{bazi,ziwei}/current_fortune.py` | 大运/大限/流年并入六件套，先天+后天分层 |
| 2 | 玄空↔阳宅 | `fengshui/house_report.py` | 理气×形法合断同房，门主灶×飞星旺衰 |
| 3 | 择日↔八字 | `date_selection/personalize.py` | 吉日按本命用神/冲克过滤重排 |
| 4 | 玄空纳命卦 | `fengshui/xuankong_mingua.py` | 旺方×命卦吉凶定宜居方 |

设计共性：**先天/理气（固定）与后天/人盘（随人变）分层**。

## D. AI 层边界

AI（Anthropic API）**仅作有界叙事与审定**，绝不参与术数推算——所有排盘、起卦、
排局、定局由确定性引擎完成，确保可复现、可验证、可回归测试。

## E. 质量保障

- **472 后端测试**全过（含严谨性回归守护：六爻月令、奇门节气元）
- **78 前端 JSX** 全 Babel 转译 + hooks 完整性通过
- **差异测试**：变输入验输出变，排除硬编码
- **真实校验**：对照古籍案例、专业软件、历史人物，非仅功能跑通

---

*本画像基于代码实测生成。后端 472 测试全过为生成基准。*
