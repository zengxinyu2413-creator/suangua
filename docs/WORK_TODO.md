# 中国术数平台 v6 · 工作清单（TODO）

> 汇总所有待办工作。来源：架构审查发现 + 全功能激活要求 + 数据深度审计。
> 状态标记：⬜ 待做　🔧 进行中　✅ 完成

---

## A. 全功能激活 + 总汇合参（架构要求）

> 要求：任何模块、每个问题 → 启动该模块全部功能 → 单点 + 跨模块组合 + 最终汇总，皆必经。

- ✅ **八字**（模板）：/chart 全激活（核心+六件套+当前运程+事业/婚姻/财运/健康专域）
  + `master_synthesis.py` 总汇合参（单点速览→组合段落→总评总建议）+ 前端置顶卡片。
- ✅ **紫微**：master_synthesis（官禄→事业/财帛→财运/夫妻→婚姻/疾厄→健康/福德→福分/田宅→家宅 + 行运，四化factored）+ 前端置顶卡片。
- ✅ **六爻**：master_synthesis（五维：用神/世应/动爻/卦型/应期 → 成败+应期+提示）+ 前端置顶卡片。
- ✅ **奇门**：master_synthesis（用神落宫×格局×值符×吉凶方×应期，purpose-sensitive）+ 前端卡片。
- ✅ **玄空**：master_synthesis（山向格局×特殊格局×旺衰方×命卦宜居×化解）+ 前端卡片。
- ✅ **阳宅**：master_synthesis（宅型纯净×门主局×灶局×命卦相配×六事，捕捉宅吉人不宜）+ 前端卡片。
- ✅ **择日**：master_synthesis（月令/通用首选/个人首选/忌避）+ 前端卡片。同修两历法 bug。

## B. 数据丰富度审计 — 已审计（关键发现：富数据存在但未接通）
审计法：逐模块在端点层实测解释覆盖度与文本深度，对标阳宅基准。

**重大发现并修复（数据库本就古籍级，键不匹配致其失效）：**
- ✅ 紫微 星曜入宫断语：STAR_PALACE/AUX_STAR_PALACE 各 168 条，但宫名后缀不一
  （表中除命宫外不带「宫」，传入带「宫」）致 **仅 1/12 宫能用**。修 get_star_palace/
  get_aux_star 兼容带/不带后缀 + 别名 → **12/12 宫全激活**（168+168 条古籍解释接通）。
- ✅ 八字 格局描述：pattern_desc 一直为空——十神名（正财）不匹配表键（正财格），
  且未接《子平真诠》库。修 _cg_to_pattern + 接 ZIPING_GE_FULL 章旨 → 各格 90~110 字古籍描述。

**审计确认已达古籍级（数据接通良好）：**
- 玄空：DOUBLE_STAR_81 满 81 组，每宫 nature/short/detailed/health/wealth/source。
- 奇门：14 格局全有详描 + 用神落宫断。
- 六爻：64卦 + 爻辞6/6 + 六亲含义6/6 + 应期。
- 择日：每日 35 字段（建除/黄道/彭祖百忌/天德月德/太神/喜财福神方位/旬空/年月破…）。
- 八字其余：日主画像 1058字、调候 342字、神煞、组合断 908字 — 丰富。
- 守护：tests/test_data_depth.py + test_ziwei_palace_coverage.py。

## C. 架构审查发现的工程问题

- ✅ **【高】基础常量归一** — 确立 core/constants.py 为单一真源；current_moment/ziwei master 已改为导入；
  新增 tests/test_constants_consistency.py 守护：AST 扫描全 core 的 12地支/10天干 本地 dict，
  逐一比对权威表，任何分叉即失败（当前 33 处重复全部锁定一致）。增量物理迁移可在守护下安全进行。
- ✅ **【高】静默失败可见化** — 新增 core/log.py（项目级 logger + attach_safe）；
  6 个 api 文件 54 处 assembly 吞错改为带日志（失败记 WARNING、available=False 记 DEBUG）；
  成功无噪、坏件暴露。环境变量 BAGUA_LOG_LEVEL 可调。
- ✅ **【中】六件套共享契约** — core/contracts.py（validate_master_synthesis 校验器）+
  tests/test_master_contract.py（七模块总汇合规 + 当下维度必在）。以测试强制契约，零重构得构造级一致。
- ✅ **【中】深化 /consult 跨盘合参** — consult 上下文现注入：当下时空（此刻四柱）+ 此刻时令对本命用神扶抑 +
  当前大运流年 + 紫微命宫（跨盘印证）。命理双盘 + 当下 + 流年 一并供 AI 合参。

## D. 前后端对齐（用户已预约的下一大项）

- ⬜ 逐端点比对后端输出字段 vs 前端实际读取/渲染字段，找出：
  - 后端有数据但前端没显示（数据浪费）
  - 前端读了但后端没有的字段（潜在报错/空白）
  - 按模块逐一对齐。

## 已完成（近期里程碑）

- ✅ 命理时间维度并入主读盘（八字/紫微 大运大限流年）
- ✅ 玄空↔阳宅 统一宅报告（理气×形法）
- ✅ 择日↔八字 真个性化（用神/冲克过滤）
- ✅ 玄空纳命卦（人盘维度）
- ✅ 后端严谨性审计（修复六爻月令、query_time、奇门元/节气 共4 bug）
- ✅ 全项目画像文档（PROJECT_PORTRAIT.md）
- ✅ 八字 全功能激活 + 总汇合参（模板）

## E. 审计中新发现（待修）
- ✅ **六爻 用神判定三路统一**：full_reading 原从 zonghe_duan 取类神，与 topic_analysis.timing/yingqi 分叉
  （自占类疾病/官司/出行：timing 取世爻、full 取官鬼）。修：full_reading 以 topic_analysis.timing.yong_shen_name
  为准（自占以世为用），新增 yong_shen_name/yong_position 字段；master 按爻位/六亲正确定位用神并显示
  「世爻（临官鬼）」。8+ 主题三路全一致。守护 test_liuyao_yongshen_consistency.py。顺修 strength 字典显示 bug。
- ✅ 紫微 master_synthesis（已完成）
- ✅ 六爻 master_synthesis（已完成，五维：用神/世应/动爻/卦型/应期）

## F. 历法底座 bug（同根·已积累，待系统根治）
已修复但同根反复出现的「绕过历法底座、自造月支/节气」类 bug：
- ✅ 六爻月令（hour_to_dizhi(month*2+1) 误用时辰函数）
- ✅ 奇门元（从局数反推，应由日在节气内位序定）
- ✅ 择日月支（_MONTH_TO_DIZHI[(month-1)%12] 日历月当农历月，7月得申应未）→ 改逐日节气月建
- ✅ 择日 month_jieqi 节气名错位（硬编码索引对齐 getJieQiJulianDays 失准）→ 改库直接取名
- ⬜ **根治**：归一历法底座（core/calendar），凡月支/节气一律走底座；禁止各模块自造（见 C 项）。

## F 节根治 — 已完成（历法底座归一）
- ✅ 历法底座补齐权威 helper：day_ganzhi_at / month_ganzhi_at / month_dizhi_at /
     solar_term_on / current_solar_term（core/calendar/solar_terms.py，全基于节气历）
- ✅ 迁移自造处到底座：api/liuyao.py、core/date_selection/selector.py、
     core/liuyao/yingqi_calculator.py（_day_ganzhi/_month_ganzhi）
- ✅ 回归守护：tests/test_calendar_canonical.py（7 用例锁定月支/节气/日干支）
- 规则确立：凡月支/节气/日月柱，一律走 core/calendar，禁止各模块自造。

## G. 当下时辰维度（新增需求）
- ✅ 当下时空层 core/calendar/current_moment.py（current_sizhu 当前四柱 + moment_vs_yongshen 扶抑 + moment_dimension）
- ✅ 七模块 master_synthesis 全部织入「当下」维度 + 汇总段落：
     八字（时令五行×用神扶抑）、紫微（流时×命宫冲合）、六爻/奇门（占时/局时即基准，奇门用局时非now）、
     玄空/阳宅（宅静时动·流时辅参）、择日（当下为择吉基准）。三才合参：先天为体、行运为势、当下为机。

## D. 前后端对齐 — 进行中
方法：逐端点比对后端输出字段 vs 前端引用，找「后端有前端没读」「前端读后端没有」。
- ✅ 验证刚接通的富数据前端已读：紫微 star_interpretations/palace_full（ZiweiPalaceDetailPanel 已接入，12/12宫可达）、
  八字 pattern_desc（BaziPage line 395 已读）。
- ✅ 补 **八字 life_aspects 详断卡片**：事业/财运/婚姻/健康四域专断（career_fields/analysis/advice/配偶星/脏腑）
  原仅总汇一句速览，现加「人生四域详断」卡片显示全部详情。
- 甄别为非缺口：current_fortune（经总汇运程/行运维度已现）、择日 all_days（经吉/凶日子集建日历）、
  奇门吉凶宫（经总汇趋避维度已现）、各 *_raw 原始中间字段（无需显示）。
- ✅ 反方向核查：择日 0 缺口；其余「前端读后端没有」均为误报——页面调多端点（/fortune、/career 等）
  + 子对象嵌套访问（data.analysis 实为 life_aspects 子属性），非顶层缺字段。无真实空白 bug。
- D 节核心达成：新接通富数据前端可达 + 八字四域详断补全。

## 紧急修复 — 紫微界面打不开（null 崩溃）
- ✅ 根因：紫微/阳宅/奇门 总汇卡片用 `result.master_synthesis?.available`，`?.` 只护 master_synthesis，
  未护 result 本身；result 初值 null（未排盘），始终渲染区内 `null.master_synthesis` 抛 TypeError，整页崩。
- ✅ 修复：三处改为 `result?.master_synthesis?.available`（与择日一致）。八字用 data.（已安全）。
- ✅ 回归：tests 中可加 null-result 渲染守护（前端）。三文件转译 + hooks 78 通过。

## 前端空值渲染守护（已完成）
- ✅ tests/test_react_null_safety.js：Babel AST 静态分析，防紫微那类 null 崩溃复发。
  对 useState(null) 可空变量，检测「守护外」直接成员访问。准确识别守护：
  {v && …}/{v ? …}/v?./if(!v)return（仅函数直接体）/if(v){…}正向块/二元逻辑测试；
  处理参数与局部 const 解构遮蔽；不下钻子函数误判。
- 自查纠错：检查初版自身有两个 bug——① Babel8 须 parseSync（误用 parse 致解析失败被吞、
  检查永远空过）；② _hasEarlyGuard 用 traverse 下钻子函数，在无关回调里见 if(!v)return 误判全safe。
  均已修，并用「注入 bug→应报、还原→0」双向验证检查确实有效。
- 运行：node tests/test_react_null_safety.js（自动定位 @babel/core）。

## 各模块真实命例/古籍参验（已完成 — 全部对独立权威基准核验）
- ✅ 八字：日柱 vs 1900-01-01甲戌锚点独立六十甲子推算 40/40；毛泽东命例年癸巳·月甲子·日丁酉全中；
     年柱立春换年正确。顺修 solar_terms 误导死注释。
- ✅ 紫微：命宫定位（寅起正月·子时逆数）5例全对；紫微星定位（起紫微诀）5例全对；
     十四主星紫微系/天府系排布 14/14；五行局（命宫纳音）核对一致。
- ✅ 六爻：纳甲地支（乾子寅辰午申戌/坤未巳卯丑亥酉）全合京房；六亲、世应（含姤一世/剥五世变宫）全对。
     小发现：天干未暴露（六爻以地支为主可接受）。
- ✅ 奇门：局数 vs《烟波钓叟赋》局数表（冬至1·7·4 / 小暑 / 夏至9 / 春分3）全对；
     三元转换、阴阳遁、地盘三奇六仪（阳遁一局戊1己2庚3辛4壬5癸6丁7丙8乙9）9/9。
- ✅ 玄空：运盘洛书顺飞（八运8/九运9，非硬编码）；山星/向星入中=运盘坐山/向首宫运星，规则正确。
- ✅ 择日：建日=日支==当日节气月建；并验证「建除遇节重复」古法正确实现（小暑处双建）。
- 守护：tests/test_{bazi,ziwei,liuyao,qimen,fengshui,dateselection}_classical_validation.py（16 用例）。

## 六爻纳甲天干 + 「所问×占卦时刻」组合分析（已完成）
- ✅ 纳甲天干暴露：core/liuyao/najia.py 增 NAJIA_STEMS（乾甲壬/坤乙癸/震庚/巽辛/坎戊/离己/艮丙/兑丁），
     每爻补 stem/ganzhi/changed_stem/changed_ganzhi；前端 LiuYaoPage 显示完整纳甲（天干弱化·地支主显）。
     验证：乾甲子…壬戌、坤乙未…癸酉、既济离己坎戊，全合京房。
- ✅ 组合分析检验中发现并修复三个真 bug：
  · 用神旺衰按「日支」算（应按月令）——annotate_with_najia 第7参误传 day_zhi，应 month_zhi。
    修后寅木妻财 春旺/夏休/秋死/冬相 全对（秋季原误为「相」）。
  · 用神三处不一致（topic_analysis 顶层取「首个非世应类神」≠ timing 的 get_yong_shen[0]）——
    顶层改与 timing 同源；自占类（求医/官司/出行）顶层=timing=full_reading=世爻。
  · 当下维度用 now()（应=占卦时刻）——master_synthesis 传 divine_date 入 moment_dimension。
- ✅ 所有起卦方法（含手动/铜钱）均尊重 query_time 为占卦时刻（原仅 time 法）。
- ✅ 有效时间段明示：总汇增「自占卦时刻起算→应期止」之时间窗口（应期相对占时推、随占时平移）。
- 守护：test_liuyao_time_combination.py（旺衰月令/用神一致/当下锚定/应期平移/有效期，5 用例）
       + test_liuyao_classical_validation.py 增纳甲天干校验。

## 奇门「起局时刻 × 求测目的」组合分析（已完成 — 同六爻方法论推广）
- ✅ 当下维度锚定起局时刻（实测确认，非凭记忆）：当下显示起局之刻与节气，非 now()。
- ✅ 用神归并 bug 修复：purpose 非规范键（求职求官/诉讼/考试/求医）曾静默回退「求财（生门）」，
     标签都串成"求财谋利用神"。修 analyzer._analyze_yong_shen：
     ① _Q2P 同义词映射对 purpose 亦生效（诉讼→官司、求官→事业、考试→学业、求医→疾病）；
     ② 默认回退由「求财」改「谋事」（通用），杜绝误默认。
- ✅ 有效时间段明示：奇门 master_synthesis 增「时家一局只管一时辰」之时辰窗口
     （午时11-13、子时跨日23-1次日等），逾时换局；随起局时刻变。
- ✅ 用神随目的变（实测）：同局 求财艮宫/婚姻坎宫凶/疾病乾宫，断语随之异。
- 注（待精化）：官司/学业/疾病显示用神门为吉门（开门），古法此类用神实为类神星
     （学业天辅文昌、疾病天芮病符/天心医）；principle 正文已正确，门-用神为简化。
- 守护：test_qimen_time_combination.py（当下锚定/用神归并/问句归并/目的敏感/有效时段，5 用例）。

## 奇门用神取法精化（已完成 — 类神分门/星/神 + 逆向用神五行受制）
- ✅ 用神类神分型：PURPOSE_LOGIC 增 yong_shen{type,marker,label[,polarity]}。
     学业=天辅星(文昌)、疾病=天芮星(病符)、失物=玄武(盗神)——按星/神定位落宫，
     非一律取门；求财/事业/婚姻/出行等门类用神不受影响。
- ✅ 逆向用神(病符天芮/盗神玄武，polarity=adverse)五行受制反判：
     宫克用神(木克土)、用神生宫泄气(土生金) → 受制/泄 → 吉(病退/物可寻)；
     宫生用神(火生土)、比和 → 得生/得地 → 凶(病重/难寻)；用神克宫 → 平。
- ✅ 健康安全考量：初版"宫评反转"致病符恒判吉(对疾病占即"恒报病退"之有害虚假宽慰)，
     改为五行受制判定后跨日期吉/凶/平真正区分（病符艮土比和→凶病重、巽木克制→吉病退）。
- 守护：test_qimen_yongshen_refinement.py（星/神定位、门类不受影响、逆向五行受制，3 用例）。

## 玄空「建宅年 × 流年」分离（已完成 — 静态盘类时间逻辑修正）
- ✅ 核心 bug：xuankong 流年紫白叠加与太岁刑冲皆误用「建宅年 year」（定运的那个），
     致分析2010建之宅时叠加的是2010流年/太岁，而非当前流年。宅静时动，二者本须分。
- ✅ 修复：calculate_xuankong_chart 增 analysis_year 参（流年/分析年，缺省当前年）；
     流年紫白(overlay_annual_on_base/detect_annual_warnings)与太岁(detect_taisui_conflict)改用 analysis_year；
     输出增 analysis_year 字段；API 接受 analysis_year（缺省 now）。
     运盘/山向盘（本盘静态）不随分析年变；流年叠加随之变（2024三碧/2025二黑/2026一白入中，合年紫白逆飞）。
- ✅ 流年辅参维度：xuankong_master 增「流年」维度，明示建宅年定运为体（一运约廿年不易）+
     分析流年年紫白入中为用（一年一应）；与既有「当下（流时辅参）」维度并列，宅静时动两级时间。
- ✅ 前端：XuankongPanel 增「分析流年」输入（默认当前年），与「建宅/入伙年」并列。
- 静态盘核对：阳宅三要为门主灶静态关系无流年叠加；/analysis 八宅命卦已用 now() 取流年，均无此 bug。
- 守护：test_xuankong_time_separation.py（运盘不变/流年随分析年/缺省当前年/流年维度，4 用例）。

## 奇门官司用神(日干vs时干) + 阳宅三要流年方位辅参（已完成）
### 奇门官司用神精化
- ✅ 官司另法：日干为我、时干为彼，比二宫旺衰吉凶 + 干五行生克定胜负（《奇门法穷·词讼章》），
     不再简化为门。calculate_qimen 输出增 day_gan/day_zhi/hour_gan；
     _analyze_guansi 定位我宫(日干)/彼宫(时干)，综合宫位 score 差 + 生克(我克彼利我/彼克我不利)，
     edge≥1.5吉、≤-1.5凶、否则平。甲遁以戊旬首代。诉讼/纠纷同义词归并亦走此法。
- 守护：test_qimen_guansi.py（日干vs时干结构、胜负与score+生克一致、跨日期有别，3 用例）。
### 阳宅三要流年方位辅参（两级时间推广到静态盘）
- ✅ get_annual_directions(year)：由年紫白飞星定文昌(四绿)/财位(八白)/喜庆(九紫)/病符(二黑)/
     五黄/是非(三碧)位 + 年支定太岁/岁破/三煞。2026文昌东北·财位正东·五黄正南·太岁正南·三煞正北（核验无误）。
- ✅ yangzhai_master 增「流年方位」维度（门主灶静态·终身不易 + 流年九星加临·一年一换）；
     API 接受 analysis_year（缺省当前年）；前端 YangzhaiSanyaoPanel 增「分析流年」输入。
     门主灶 grade 不随流年变（静），流年方位逐年变（动）。
- 守护：test_yangzhai_annual_directions.py（方位算法、门主灶静态、维度动态、缺省当前年，4 用例）。

## 流年方位细化到流月（已完成 — 静态盘时间三级：运/年/月 + 时辰）
- ✅ get_monthly_directions(year,month)：流月紫白飞星定某月文昌/财位/喜庆/病符/五黄/是非方；
     并检测流月凶星叠流年凶星之方（双五黄/双病符/双三碧 = 该月该方大凶，万勿动土）。
     2026-8月（流月一白入中==流年一白入中，全盘叠合）双五黄叠临正南——核验无误。
- ✅ 玄空 xuankong_master 增「流月」维度、阳宅 yangzhai_master 增「流月方位」维度，
     列于「流年」之后、「当下」之前，构成 运→年→月→时辰 多级时间链。
- ✅ API（xuankong/yangzhai_sanyao）接受 analysis_month（缺省当前月）；
     前端 XuankongPanel/YangzhaiSanyaoPanel 增「分析流月」输入。
- 守护：test_monthly_directions.py（流月方位逐月异/叠加检测/玄空阳宅维度，4 用例）。

## 奇门胜负/比赛用神（已完成 — 复用官司「日干vs时干」较量）
- ✅ 胜负/比赛/竞争原简化为开门，现同官司法：日干为我、时干为彼，比二宫强弱+干生克定胜负。
     _analyze_guansi 增 topic 参，胜负措辞为竞斗（我占优→主动进取；彼优→避其锋另择吉时；
     势均→抢占吉方吉时），区别于官司之词讼措辞。比赛/竞争同义词归并亦走此法。
- 守护：test_qimen_guansi.py 增胜负用例（日干vs时干结构 + 竞斗措辞）。

## 奇门用神取法精化（续·已完成 — 剩余类神归位）
- ✅ 感情/婚姻 → 六合（神，和合之神，临门姻缘可成），原简化休门。
- ✅ 健康/求医 → 天心（星，医药之神，主良医得治），原简化休门。
- ✅ 寻人 → 时干（所寻之人），新增 _analyze_xunren：观落宫门星断远近归否——
     临生门/休门/开门→近易归(吉)、临死门→凶(险厄/音讯绝)、临伤惊门→阻滞、逢驿马→远走、杜门→自隐。
- 保留门类用神（principle 自身即用门，正确）：求财生门、事业开门、出行生门、谋事开门。
- 守护：test_qimen_yongshen_refinement.py 增类神(六合/天心)定位 + 寻人时干用例；
     更新 test_qimen_overview/test_door_yongshen（婚姻改判六合）。

## 流月再深一层到流时方位（已完成 — 时白诀；流日暂缓）
- ✅ 时家紫白（时白诀）：_is_yang_dun_zibai(冬至后阳遁/夏至后阴遁)、get_hourly_zibai_center、
     calculate_hourly_flying、get_hourly_directions。阳遁子午卯酉日子时一白/辰戌丑未日四绿/
     寅申巳亥日七赤(阴遁九紫/六白/三碧)，逐时顺/逆推。独立核对《沈氏玄空学·时白诀》起例无误
     （巳日子时七赤逐时+1、卯日子时一白丑时二黑）。
- ✅ 玄空/阳宅 master 增「流时方位/流时」维度，构成 运→年→月→时辰 四级方位时间链。
- ⚠ 流日（日家紫白）暂缓：日紫白起例多家分歧（三元日白法 vs 节气连续法），
     无单一权威基准可独立核验，依「不放未经核验数据」原则暂不实现，待权威古例核校后再补。
- 守护：test_hourly_directions.py（时白起例阳遁/9→1循环/方位结构/四级维度链，4 用例）。

## 奇门用神落宫断语深化（已完成 — 最薄主占模块补到阳宅级多维断）
- ✅ 新建 yongshen_judgment.synthesize_yongshen_judgment：将用神落宫之
     「门×星×神×旺衰×神煞」断料合成多维具体断语（得地旺衰/门户对口/星辰助应/
     八神临应/奇仪神煞 + 综合断），不另造数据、只组合排盘已富集之宫层断料。
     门户对口按用事(topic)判正应/忌门；得地旺衰按用神五行vs宫五行生克。
- ✅ 接入 analyzer：用神算出后挂 judgment_dimensions + judgment；
     官司/胜负/寻人自有专断故跳过。前端 QiMenPage 用神卡展示多维断 + 胜负/寻人判词。
- ✅ 又一键格式不匹配 bug：analyzer 内 _GONG_WX 键为「艮八宫」、palace_name 为「艮宫」，
     致 enriched 宫 gong_wx 取空、得地维度缺失。合成器侧改由 position 序稳健推宫五行绕过。
- 守护：test_qimen_yongshen_judgment.py（多维含得地/门户对口/得地五行正确/官司不挂落宫断，4 用例）。

## 六爻用神落爻多维断（已完成 — 推广奇门多维断思路到六爻，严格验证）
- ✅ 新建 yongshen_judgment.synthesize_yongshen_judgment：七维断——
     现伏/旺衰得令/动静化象/空破墓绝/元神生扶/忌神克制/世应关系 + 综合成败断。
     处理用神现卦/伏藏两态：伏时从 fu_shen 取用神、给出出伏条件。
- ✅ 真 bug 修复：用神伏藏时 zonghe_duan.roles 全空（present=None），致原神/忌神误判"不上卦"。
     加 _locate_role_from_yaos：roles 空时从 yaos 按预期六亲(生克环)自定位原神/忌神并评旺衰。
     求财(妻财伏)忌神兄弟现正确识别在卦(酉/申)而非误判不上卦。
- ✅ 独立差分验证（非样本）：
     ① 元神/忌神六亲——五种用神全核合古法生克环（财→原子孙忌兄弟…官→原财忌子孙…）；
     ② 判语随月令真实变——同卦(用神兄弟酉金)酉月旺净分2.0→午月囚-3.0→卯月囚-3.5，证非硬编码；
     ③ role_check 内嵌独立校验 roles 之原神忌神方向。
- ✅ 接入 API(yongshen_judgment) + 前端新组件 LiuyaoYongShenJudgment（综合成败条 + 七维）。
- 守护：test_liuyao_yongshen_judgment.py（六亲生克/现伏两态/伏时定位/随月令变/七维完整，5 用例）。

## 流日方位（日家紫白·三元日白·已完成 — 权威起例核校）
- ✅ 三元日白（《协纪辨方书·卷十一》）：六锚点冬至一白/雨水七赤/谷雨四绿（阳）、
     夏至九紫/处暑三碧/霜降六白（阴），各以离锚点节气最近之甲子日（符头）起，阳遁顺/阴遁逆。
     get_daily_zibai_center/calculate_daily_flying/get_daily_directions + _nearest_jiazi 符头定位。
- ✅ 独立核校（非样本，对古法起例）：
     ① 六锚点符头甲子日入中=锚星（冬至甲子2025-12-21→一白等全核）；
     ② 阳遁顺+1/阴遁逆-1/9↔1循环；
     ③ 三元连续性——锚星间隔60日(60%9=6)恰衔接，阳1→7→4、阴9→3→6 全验证，印证起例自洽。
- ✅ 玄空/阳宅 master 增「流日方位/流日」维度，时间链补全为 运→年→月→日→时辰 五级。
- 守护：test_daily_directions.py（六锚点起例/阳顺阴逆/三元连续/方位逐日变+维度，4 用例）。

## 择日深化：神煞释义库 + 择事专属断（已完成 — 最薄模块补释义层）
- 背景核验：先独立核校择日引擎正确性——建除十二神（卯月卯日建、惊蛰双建、酉日破且月破）、
     黄道黑道（卯月青龙起寅→明堂→天刑…玉堂，黄黑判定全对）、三合/六合/月德/天德/往亡 全正确。
     模块神煞引擎扎实（59吉神+82凶煞=141种），唯只列名无释义——此为真薄处。
- ✅ 新建 shensha_meanings.py：145条神煞释义库（《协纪辨方书·义例》），每条含
     类型(吉/凶)/等级(上吉…大凶)/含义/宜/忌。实占神煞 100% 覆盖（140/140）。
- ✅ synthesize_shensha_for_purpose：据所择之事(PURPOSE_KEYWORDS 18类)判该日神煞
     利此事之吉神、忌此事之凶煞 → 宜/忌/参半/平 专断。
- ✅ 独立差分验证（非样本）：
     ① 释义方向合古法（天德上吉诸事宜/月破大凶/往亡忌嫁娶出行/天医利求医/血忌忌针灸）；
     ② 实占覆盖率 100%；
     ③ 择事专属断真实区分——结婚逢往亡/月破判忌、得三合天喜不将判宜、三合遇重日判参半；
     ④ 同日异事神煞相关集不同（结婚 vs 纳财），证非硬编码。
- ✅ 接入 API（每日 shensha_purpose + shensha_annotated）+ 前端 DateSelectPage
     选中日详情展示择事专断 + 吉神/凶煞逐条释义。
- 守护：test_shensha_meanings.py（释义方向/覆盖率/择事区分/同日异事/API附注，5 用例）。

## 择日总论汇入神煞择事专属断（已完成 — 每日层→月度合参）
- ✅ build_date_master_synthesis 加「神煞总论」维度：跨候选日聚合逐日 shensha_purpose——
     本月正利/正忌/参半日数、常助此事之吉神(频次)、常忌之凶煞、神煞最宜之日、正忌当避之日。
     并汇入 integrated_paragraphs 总论正文。
- ✅ 独立差分验证：
     ① 一致性——总论所列最宜/正忌日，必在每日 shensha_purpose 宜/忌集内；
     ② 异事差分——结婚助"不将"忌"月厌"、开业助"五富"忌"五虚天贼"、安葬助"鸣吠"忌"土符重日"，
        各取择事专神，证非硬编码。
- 守护：test_date_shensha_summary.py（总论存在/最宜日一致/正忌日一致/异事不同/入正文，5 用例）。

## 紫微格局深化（已完成 — 补10经典高价值吉格，30→40格）
- ✅ pattern_detector 增 G21–G30：三奇加会（禄权科会命·大贵）、双禄朝垣（禄存+化禄）、
     禄马交驰（天马+禄）、财荫夹印（天相被化禄+天梁夹）、日月夹命、文桂文华（昌曲夹/会）、
     坐贵向贵（魁钺坐对）、极向离明（紫微午宫）、金灿光辉（太阳午宫）、月生沧海（太阴子宫）。
     每格含 evidence/meaning/break_conditions，结构同原格、前端 PatternsCard 自动渲染。
- ✅ 真实差分验证（3456 盘扫描，非样本）：
     ① 0 崩溃、10 格全触发，频次合理（位置格罕见26/19/27、会照格常见746/598/403）；
     ② 位置格证据独立核验 2301 正确 / 0 错误（极向离明=紫微午、金灿=太阳午、月生=太阴子、财荫夹印=命坐天相）；
     ③ 化曜格抽验——三奇加会盘三方四正确含巨门化禄+太阳化权+文曲化科。
- 守护：test_ziwei_new_patterns.py（无崩溃/全触发/位置格证据/三奇实有四化，4 用例）。
- 注：八字格局已深（pattern_desc引《子平真诠》+geju_cheng_bai成败救应+special_patterns证据），本轮聚焦紫微补遗。

## 六爻总断接入用神七维断（已完成 — 总断=用神断，二者一致）
- ✅ build_liuyao_master_synthesis 接入 yongshen_judgment：以七维断（现伏×旺衰×动静化象×
     空破墓×元神×忌神×世应→综合成败）为成败主依据——overall_quality 取 verdict_level 映射
     （auspicious吉/inauspicious凶/neutral中）、headline 取七维断 verdict，并单列「用神七维断」维度（含净分）。
- ✅ 真实一致性验证（跨8卦/多月令，非样本）：
     ① 总断 overall_quality == 七维 verdict_level 映射 8/8 一致；
     ② headline 即七维 verdict（同一断语不相违）；
     ③ 同卦异月令——七维随旺衰变、总断同步联动变化（酉月vs午月总断不同）。
- 守护：test_liuyao_master_yongshen_consistency.py（总断映射/headline同源/七维维度/月令联动，4 用例）。

## 紫微落宫释义·杂曜补全（已完成 — 诚实甄别后做的真改进，纯查表零净分零矛盾）
- 甄别先行：先查证「落宫释义缺失」前提是否成立——结论是主星×宫(168) + 辅煞星(六吉六煞禄存天马)×宫
     断语库**早已存在且端到端接入**（chart→palace_full.aux→API→前端 ZiweiPalaceDetailPanel 全渲染），
     故主星/六吉六煞落宫层不重做（重做=冗余、零提升）。
- 真缺口（差分扫盘发现）：盘中 52 辅/杂曜，仅 14 个有落宫断，**其余 38 杂曜出现却无释义**——
     含红鸾天喜天姚咸池（桃花喜庆）、天刑孤辰寡宿华盖（刑孤）、龙池凤阁三台八座台辅封诰恩光天贵（科甲贵显）、
     天官天福天巫天厨天才天寿（贵福）、天哭天虚破碎蜚廉阴煞天月（忧耗病）、天德月德解神年解（解厄）、
     天空截路旬空空亡天伤天使（空亡灾耗）——皆「落宫最改断语」之星。
- ✅ 扩 AUX_STAR_INFO 14→52、AUX_STAR_PALACE 168→624（52×12），补 38 杂曜各 12 宫落宫断（出《全书》义例）。
- ✅ 修一接入 bug：杂曜在 adj_stars，而 interpret_palace_full 只收 minor_stars→杂曜被漏；
     改为 minor_stars+adj_stars 合并传入，杂曜落宫断方 surface 至 palace_full.aux。
- ✅ 真实差分验证（非样本）：① 实占杂曜 100% 覆盖（0 漏）；② 落宫真随宫变——红鸾/天刑/孤辰/华盖/天姚
     各 5 宫≥4 种不同断（非通用占位，红鸾命宫"貌美早婚"vs疾厄"血光妇科"）；③ surface 核验——
     杂曜落宫断已入命盘 palace_full.aux（天刑·命"利军警法医"、天官·父母"父母有官望"）。
- 守护：test_ziwei_star_palace.py 更新（≥48星/624条/核心14+杂曜齐 + 落宫差分 + 入盘 surface，3 用例）。
- 注：此步只做「事实查表」层，不碰成败净分；AI 行文层留待地基验毕后再叠（受约束转述、不新增判断）。

## 先验·六爻动爻/化合冲键错配修复（已完成 — 高发"键格式错配"类，两处）
- 审计法：孤儿合成器扫描（多为列表注册之假阳性；真孤儿 analyze_hua_qi/analyze_dayun_liunian_trigger
     皆有等效实现在跑，属冗余旧版，非缺口）+ 恒空字段扫描（命中真 bug）。
- ✅ bug1 化合冲恒空：analyze_hua_he_chong 读 dong/zhi/changed_zhi，而 interpreter 转换时
     dong 取 is_moving/type=="moving"（爻实为 is_changing）→ dong 恒 False → 化合/化冲/化进/化退全不触发。
     修 interpreter.py:1074 转换为 is_changing。化合(子丑六合)/化冲(巳亥六冲) 现古法正确触发。
- ✅ bug2 独发独静恒判全静：interpreter.py:1067 同一错配喂 analyze_dong_jing → 永远「全静」、
     从不识独发（独发"断事关键"乃六爻要法）。同修。现独发卦/全静卦/多发卦三态正确区分。
- 二者皆经 perspectives.py 与前端 LiuyaoAdvancedPanel 消费（前端早已 render，惟数据一直为空/错）。
- 守护：test_liuyao_dong_hua_wiring.py（化合冲触发+六合六冲核对/独发全静多发三态区分/有动绝不恒静，3 用例）。
- 误报甄别（非 bug）：玄空 chart_type（冗余，盘型在 verdict）、阳宅 mouth_star（传 zao_facing 即populate）、
     奇门 nianming_zhi（需生年）、玄空 fan_fu_yin/annual_note（无相应卦象/未触发）——均条件/入参依赖。

## 先验·紫微性别归一化 bug 修复（已完成 — 差分恒值扫描命中的真 bug）
- 审计法（新角度）：差分恒值扫描——给差异极大的输入，找「本应随输入变却恒定」的语义字段
     （恒定=硬编码/键值错配嫌疑）。逐模块跑八字/紫微/奇门/玄空。
- 多数恒定为合理（日柱十神恒=日主之定义、wuxing_colors为UI色、奇门法则/古籍引用固定、
     玄空洛书方位固定、我误传不存在的 calendar 字段致 _is_lunar 恒 True 等——皆甄别为非 bug）。
- ✅ 命中真 bug：紫微 `.metadata.gender` 跨 2男2女输入恒为「男」——根因 api/ziwei.py:92
     `gender if gender in ('男','女') else '男'`，**英文 'female' 不在中文集合→静默 fallback 成男**。
     后果：API 直连或英文流程下女命被当男命排——大限顺逆算反、命主/身主可能错。
- ✅ 修复：加 `_norm_gender()` 归一化（男/女 与 male/female/man/woman/m/f 皆识别，未知方默认男），
     并应用于 ziwei.py 全部 5 处 gender 处理点（chart / triple_chart / decade）。
- ✅ 验证：male→男、female→女；male≡男、female≡女（英中同盘）；男≠女（大限顺逆正确区分）。
     交叉验证八字 gender 本就正确（男顺行癸未→甲申、女逆行辛巳→庚辰），仅紫微有此 bug。
- 守护：test_ziwei_gender_norm.py（female不被吞/英中等价/男女有别/helper覆盖常见写法，4 用例）。

## 跨边界值错配·系统全审（已完成 — gender/历法/purpose 三类一次扫清）
审计范围：枚举全部端点，对三类高危跨边界值逐一差分验证。
### ① 性别 gender（男/女 ↔ male/female）
- ✅ 全端点 male≡男、female≡女 一致（bazi/ziwei/liuyao/fengshui 全绿）——除已修的 ziwei(128)外无他例。
- 甄别非 bug：fengshui 命卦男女不同（1988 为巧合同值，7/8 年不同，gender 生效）；
   calculate_ming_gua 用 `male = g in ("male","男")` 正确模式；bazi career/health/wealth 男女无别属合理
   （静态四柱分析，gender-neutral；marriage 因男看财妻/女看官夫故有别——已验证）。
### ② 历法 is_lunar（农历/阳历）
- ✅ bazi 与 ziwei 统一用 `is_lunar`（默认True）+ to_solar_date()，农历vs阳历产不同盘，前端 BirthForm 用对字段。干净无 bug。
   （注：此前测试常传不存在的 calendar 字段是 no-op，属测试写法问题，非产品 bug。）
### ③ purpose/topic 路由（非规范串→错默认）——找到并修 2 个真 bug
- ✅ bug1 六爻 topic 别名：'婚姻'(非规范键'婚姻感情')→ explicit 不精确匹配 → 退回空 question → 默认世爻，
   **男占婚不取妻财、女占婚不取官鬼**（绕过性别专用神）。修 interpreter.py：explicit_topic 非精确键时
   先经 _match_topic 按关键词归一（'婚'→婚姻感情、'财运'→求财）。现婚姻/感情/结婚→男妻财女官鬼。
- ✅ bug2 择日 purpose 别名：'下葬/婚礼/开张/乔迁/远行/看病' 等同义词不在 PURPOSE_KEYWORDS →
   get(purpose,[purpose]) → 匹配不到 → 落通用默认、拿不到神煞择事专属断。加 PURPOSE_ALIASES 归一化（30+同义词）。
   现下葬≡安葬(鸣吠)、开张≡开业(五富)、乔迁≡搬家 等全部归位。
- 甄别非 bug：奇门 purpose 路由稳健——疾病(天芮·病所)vs健康(天心·医药)系有意区分非别名；
   婚姻/感情皆→六合；乱串/空→默认"谋事(开门)"兜底。analyzer 有完整 PURPOSE_LOGIC 关键词表。
- 守护：test_liuyao_topic_routing.py（4 用例）、test_date_purpose_alias.py（3 用例）。

## 深审·键错配静默错值 + 孤儿函数（已完成 — 用户重点关切两类）
### 审计法
- 全局键交叉引用：收集 core/+api/ 所有"被写入键"vs"被读取键"，找读取但全局从未写入的键（恒落默认=静默错值嫌疑）。
- 全函数孤儿扫描：所有 def 整词引用计数 ≤1（仅定义自身）即候选孤儿。
### 键错配静默错值——命中并修
- ✅ 奇门伏吟/反吟键错配：_detect_patterns 读 layout.get("fuyin")/("fanyin")，而实际键为 fuyin_fanyin(dict)
     → 恒 None → 伏吟/反吟【大凶格】从不进 patterns 格局列表（扫240局0次）。改为直接调 detect_fuyin_fanyin
     按局数/遁判定。现伏吟/反吟正确入 patterns，且与 fuyin_fanyin 字段一致（无矛盾）。
     注：该功能经 fuyin_fanyin 字段本已 surface 到前端，故非用户全失，但格局列表此前不完整。
### 孤儿函数——甄别与处置
- ✅ 复活 contracts.py 校验器（validate_master_synthesis / must_have_current_moment / normalize）：
     原意「逐模块校验真实 master_synthesis、漂移即失败」，但从未被调用。新建 conformance 测试接入，
     7 模块全部校验通过（字段形状/quality合法/非空维度/含当下），并自检校验器确能抓注入违规。
- ✅ 移除六爻死孤儿 _detect_fuyin_fanyin：以「全静」误判伏吟、读不存在的 yaos_raw、结果 fuyin_type 亦弃用，
     且被 hua_bian 爻级自化伏吟/反吟（动化同支/动化六冲）正确取代并已 surface。删除函数+无用调用。
- 甄别为非缺口/范畴外：number_divination（梅花数字起卦，属另一系统非纳甲六爻范畴，不强接）；
     get_zao_judgment（get_zao_full 的冗余别名）；analyze_dayun_liunian_trigger/analyze_hua_qi（均有等效实现在跑）；
     其余 _私有小helper 多为内部工具。
- 守护：test_master_synthesis_contracts.py（7模块契约+验证器自检，4用例）、
     test_qimen_fuyin_fanyin_patterns.py（伏吟反吟入格局+与字段一致，2用例）。

## 深审续·奇门值符星恒值 bug（已完成 — 本轮最重大修复）
### 审计法（深层差分恒值）
- depth-5 差分恒值扫描：给差异极大输入，找深层"应变却恒定"的语义字段。
- 多数恒定甄别为合理（success标志/scope=origin结构元/shishen.day=日主定义/固定法则引文）。
### 命中重大 bug：值符星恒为天蓬
- 现象：值符星(zhifu_analysis.zhifu.star)跨72个不同时辰**恒为天蓬**（应随旬首变、九星皆可为值符）。
- 根因：calculate_qimen 用简化错法（line 472"找天盘中天蓬所在宫当值符宫"）→ 值符星永远天蓬。
     值符统领整个天盘与八神，此恒值使约 8/9 命盘的值符分析全错——奇门最严重的静默错值之一。
- 修复：改用正法（《奇门遁甲秘笈》）——旬首六仪所在「地盘」宫之本位九星 = 值符星，
     天盘中该值符星所在宫 = 值符宫。在值符判定前先算 hour_ganzhi（时柱）→ XUNSHOU_LIUYI 得旬首六仪。
- 独立核验（非自证）：① 值符星现遍历全 9 种；② 60 例独立重算"旬首六仪→地盘宫→本位星"链 60/60 吻合；
     ③ 古法锚点——阳遁一/二/三局戊在 1/2/3 宫 → 值符天蓬/天芮/天冲，合《奇门》。
- 值使门：用简化地支-宫法，遍历 9 种（随时变非恒值），经典精确化（旬首数时辰）留作后续，非 bug。
- 守护：test_qimen_zhifu_star.py（值符变化/与旬首六仪吻合/阳遁一局甲子锚点，3 用例）。
### 其余健康确认
- 异常通道：happy-path + 边界输入(闰月/1900/2099/罕见山/代占/全老阴/闰日time)均 0 个被吞异常。
- 查表层：称骨 float 键用 min(abs差) 取最近键安全；DOUBLE_STAR_81 全81组合0缺且内容正确；
     HEXAGRAM_DATA/NAYIN/SHISHEN 等重复表均共享同一对象（零漂移）。

## 深审续2·值使结论 + 玄空七星打劫/六爻卦身恒值 bug（已完成）
### #1 值使门经典精确化——结论：保持现状（有意简化，非 bug）
- 验证发现：正法「值使门=值符宫本位门」会使符使五行关系 8/8 退化为恒「同气」
  （每宫本位星与门同五行：天蓬水·休门水…），毁去 analyzer 核心的符使生克判断。
- 且值使本就随时变化（非恒定 bug），全套八门重飞布在无参考盘下不可验证、风险高。
- 按「不发不可验证判断」原则，保留独立随时变化的值使取宫法，并加代码注说明此为有意简化。
### #2 续挖恒值 bug——又找到 2 个
- ✅ 玄空七星打劫恒报「艮坤假打劫·吉」：艮坤(2-5-8)向星恒成三般卦乃飞星「中宫线必差±3」
  之数学必然（96/96 命盘皆中），旧版 OTHER_TRIPLETS 把此平凡项误判为吉格，且每盘 +1 verdict 分。
  真打劫专论离-坎(南中北1-5-9)线，而该线数学上永不成三般（中5=V,顺飞离9=V+4坎1=V+5,永不差3）。
  修：移除虚假 OTHER_TRIPLETS 假打劫，无离宫/坎宫打劫即报「无」。现 144 盘皆「无」（真打劫罕见，符合）。
- ✅ 六爻卦身·世爻阴阳恒「阴」：interpreter:1015 读 world_y.get('type')/('yin_yang')（爻无此键）
  → world_yy 恒「阴」→ 所有阳世卦（世爻阳爻，约半数）误用「阴世从午起」、卦身全算错。
  修：改读爻性字段 line（"阳"/"阴"）。现 world_yy 随世爻阴阳变（阴31/阳49），
  乾(世阳)→阳世从子→卦身巳、坤(世阴)→阴世从午→卦身亥，独立核验合《增删卜易·安卦身诀》。
- 守护：test_xuankong_qixing_dajie.py（3用例）、test_liuyao_guashen_yinyang.py（3用例）。
- 改进扫描器：列表字段聚合全部元素（非仅前4），消除 o[:4] 假阳性；非列表深层恒值才是可靠信号。

## 端到端金标准验证 + AI 行文层（①② 完成）
### ① 公认命例 / 端到端整盘金标准（确定性根基已充分验证）
- 八字四柱：公认命例邓小平(1904-8-22辰时)=甲辰壬申戊子丙辰 ✓；
  独立交叉(独立于 lunar_python)：日干支(1900-01-01锚点连续)60/60、时干支(五鼠遁)60/60、
  月干(五虎遁)60/60、年干支(1984锚点)44/45（唯一miss为立春边界，乃引擎正确以上年干支处理）。
- 紫微整盘：命宫/身宫 49/50(1例闰月约定)、生年四化 10/10(对古法四化表)、
  14主星结构 80/80（紫微-天府寅申对称 + 紫微系逆行偏移 + 天府系顺行偏移）、紫微星位随农历日遍历全12宫。
- 期间两处「虚惊」诚实记录（均我查错字段名，非引擎 bug）：
  阳宅 master_synthesis（真实断语在 grade/overall_quality/headline/dimension_verdicts，非 verdict）；
  紫微四化（字段名 birth_sihua 非 sihua）。
### ② AI 行文层（下游转写，firm boundary 强制）
- core/narration/narrator.py：转写引擎 master_synthesis 事实为流畅古文，绝不新增判断。
- 【核心安全】verify_fidelity 忠实度护栏（不依赖 LLM、可独立测试）：
  · 用引擎自身权威术语表（14主星+辅曜+十神+六亲六神+奇门九星八门八神+207神煞，共310词）。
  · hallucinated_entity：AI 文中出现而引擎事实中没有的判断性实体 → 违规。
  · quality_flip：AI 把引擎判凶之域写成吉（仅当该搭配为AI新造、不见于事实时）→ 违规。
  · 自洽铁律：verify_fidelity(事实,事实) 对 5 模块全 clean（不冤枉忠实转写）。
- narrate 编排 fail-closed：AI 越界则丢弃其文本、退回确定性拼接（纯引擎事实），越界文留 rejected_prose 供审计。
- llm_anthropic 工厂：惰性载 anthropic SDK + ANTHROPIC_API_KEY，无则自动降级确定性。
- API：POST /api/v1/narration/synthesize（facts→prose）、/verify（独立校验一段行文是否忠实）。
- 守护：test_narration_fidelity.py（9用例：术语表/自洽/幻觉/翻转/fail-closed/降级/端点）。

## 行文层前端接入 + 风格分级 + 深挖续（①②③ 完成）
### ② 风格分级（白话/半文/文言）—— 仅改文采，护栏对三档一视同仁
- narrator.STYLES：白话（现代白话）/半文（雅俗共赏）/文言（古命书批语），各注入不同文风指令。
- build_narration_prompt(ms, style) / narrate(ms, llm, style)；非法 style 回落「半文」。
- 忠实度护栏不随 style 变：幻觉文在任一文风下都 fail-closed（test 已验三档）。
- API：GET /api/v1/narration/styles；synthesize 增 style 参数。
### ① 行文层前端接入 —— 各盘结果页「古文行文」按钮
- frontend/src/api/client.js：加 narrationApi（styles/synthesize/verify）。
- frontend/src/components/NarrationPanel.jsx：共享组件，「✶古文行文」按钮 + 三档风格切换 +
  正文展示 + 来源标识（AI行文已过护栏 / 越界已拦截 / 确定性行文）；各风格独立缓存。
- 插入全部 7 个结果页 master_synthesis 块（八字/紫微/六爻/奇门/玄空/阳宅/择日）。
- esbuild 解析校验 8 个 JSX 全通过；前端守护 hooks 80、null-safety 0。
### ③ 深挖剩余复杂计算元素 —— 全部健康（无新 bug）
- 八字大运顺逆排：阳男阴女顺/阴男阳女逆，4 组合全对（从月柱±1 连续）。
- 六爻六神起例：日干戊勾陈/己腾蛇/庚辛白虎起，3 日干 3 排列，合古法。
- 紫微大限：火六局起运 6 岁（=局数），顺行岁数递增。
- 奇门格局：56 种（三奇入墓/门迫/六仪击刑/真诈/玉女守门…），非恒非空。
- 紫微各宫飞化：192/192 合宫干四化表；大限四化 6/6 合表（随大限干变）。

## 整盘综合行文 + 护栏量化指标（① ② 完成）
### ① 整盘综合行文（汇聚多面板事实成一篇）
- narrator.collect_facts(chart_data, module)：把一个盘的多个事实面板（master_synthesis +
  格局成败/调候/命格/古籍引文/用神判断/收山出煞/宅相 等）汇聚成「增强版 ms」（同构），
  故 narrate/verify_fidelity 零改动即可转写并守护更丰富事实；汇聚内容全出引擎既有断语、不新增判断。
- 各模块汇聚面板键已逐一核验真实键名（_AGGREGATE_PANELS）：bazi 4→24、ziwei 4→23、
  liuyao 4→8、qimen 5→6、xuankong 8→11、yangzhai 8→9、date 4→5 段；7 模块汇聚后自洽全 clean。
- 古籍引文取前 6、总段封顶 24，保聚焦不冗长。
- API：POST /api/v1/narration/synthesize_full（chart_data+module → 整盘行文）。
- 前端：NarrationPanel 增 fullData+module 入参 → 「整盘综合 / 本论」切换；7 页全部传入。
### ② 护栏量化指标（回归监控）
- narrator.guard_metrics(ms_list)：对每盘造忠实样本（应 clean）+ 对抗样本（注入幻觉实体 / 翻转凶域，应被拦），
  报：忠实通过率(零误报)、拦截率(recall)、分类型拦截率、术语覆盖。
- 实测 17 盘语料：忠实通过率 1.0（0 误报）、拦截率 1.0（27 对抗全抓：17 幻觉实体 + 10 质性翻转），术语 310。
- 守护：test_narration_fidelity.py 增 4 用例（整盘汇聚自洽/汇聚后仍拦幻觉/synthesize_full端点/指标阈值），共 16 用例。

## 护栏干支/年份保真 + 多盘合参行文（① ② 完成）
### ① 护栏增干支/年份保真校验
- verify_fidelity 新增两类检查（AI 只拿到事实，其产出之干支/年份须出自事实）：
  · hallucinated_ganzhi：文中 60 甲子合法干支若不见于引擎事实 → 拦截（捏造/篡改干支）。
  · hallucinated_number：文中四位年份（1800–2099）若不见于事实 → 拦截。
- 自洽：事实对自身仍全 clean（不冤枉真干支/真年份）；多模块 22 盘（本论+整盘）0 误报。
- guard_metrics 对抗生成器增干支/年份两类样本；现 4 类对抗（实体/翻转/干支/年份）全 100% 拦截。
### ② 多盘合参行文（同人多盘并陈）
- collect_facts_multi(charts, labels)：汇聚同人多盘（如八字+紫微）事实，按盘标注（域名「八字·事业」等），
  仅并陈各盘既有断语、绝不生成「合参」新判断、各盘质性互不混算；返回同构 ms。
- _domain_quality 处理带标签域名（「八字·事业」→匹配「事业」），质性翻转检查在合参模式仍有效。
- 实测八字+紫微合参：14 维度 + 24 段，自洽 clean、幻觉 fail-closed。
- API：POST /api/v1/narration/synthesize_multi（多盘 → 合参行文）。
- 守护：test_narration_fidelity.py 增 5 用例（干支保真/年份保真/4类指标/合参汇聚/合参端点），共 21 用例。

## 合参前端 + 量化端点/CI + 深挖续（① ② ③ 完成）
### ② 护栏量化指标端点 + CI 回归脚本
- API：POST /api/v1/narration/metrics（传 ms_list → 忠实通过率/拦截率/分类型指标）。
- scripts/narration_metrics.py：CI 回归脚本，构建 38 盘跨模块语料（本论+整盘+合参），
  断言忠实通过率==1.0、拦截率>=0.98（4 类对抗），退出码非 0 即护栏退化。
  实测：38 盘、0 误报、拦截率 1.0（133 对抗）、退出 0。
### ① 多盘合参前端接入
- frontend/src/api/client.js：加 narrationApi.synthesizeMulti。
- NarrationPanel 增 companions 入参（[{module,label,fetch}]）→ 「合参」scope（懒取伙伴盘+缓存）。
- 八字页可合参紫微、紫微页可合参八字（共用生辰输入）；esbuild 解析 3 文件通过。
### ③ 深挖续 —— 修真 flaky 测试 + 厘清 mu_conflict（非 bug）
- 修复 test_liuyao_consistency_audit 真 flaky：divine 未传 query_time → 入墓检测依赖 wall-clock 日辰、
  随真实时间漂移；改用固定 query_time=2026-01-02T10:00（稳定触发 mu_conflict+yong_duplication）。
- 另 8 个 liuyao 测试 divine 无 query_time，但断结构非具体时变结论，未发作（test_current_moment 本应用当前时刻）。
- 厘清 mu_conflict：乃「综合断 vs 应期」跨模块入墓判断相左之一致性矛盾检测器，非裸日墓检测；
  按设计正确工作（我初以"日支==墓库"判据有误，已纠正）—— 无 bug。

## 测试加固 + 深挖续（① ③）
### ① wall-clock flaky 测试统一钉死
- 7 个 liuyao 测试（classical_validation/duan_overview/full_reading/master_synthesis/
  perspectives/yongshen_synthesis/master_contract）的 divine 调用统一加固定
  query_time=2026-01-02T10:00:00，消除入墓/旬空/六神随真实时间漂移的潜在 flaky。
- 连同上轮的 consistency_audit，8 个 wall-clock 依赖测试全部钉死；全量 644 通过无回归。
- test_current_moment 本应用当前时刻，正确保留不动。
### ③ 六爻旬空核验（40/40 正确，假警报纠正）
- 旬空 kong_wang_branches vs 独立旬首推算：40/40 全对，随日辰旬变 5 种组合；
  爻级 kong_wang 标记与旬空地支一致。
- 初见"全空"乃字段名读错（误用 xunkong/empty_branches，实为 kong_wang_branches）——
  非引擎 bug，已纠正。再次印证：先核字段名，"恒值"疑点多为读取错误。

## 量化 CI 脚本接入实际工作流（pytest marker + Makefile + GitHub Actions）
### pytest marker
- pytest.ini：注册 regression marker（testpaths=tests, addopts=-q）。
- tests/test_narration_metrics_regression.py：@pytest.mark.regression，复用 scripts/narration_metrics.py
  的 build_corpus，断言忠实通过率==1.0、拦截率>=0.98、四类对抗逐一达标。
- 选择性运行：`pytest -m regression`(1 passed/644 deselected) / `pytest -m "not regression"`(644/1 deselected)。
### Makefile
- 目标：test / test-fast(跳 regression) / regression / metrics(独立脚本) / guards(前端) / ci(闸门) / package / help。
- `make ci` = guards + 全量 test，端到端退出 0 即闸门通过。
### GitHub Actions
- .github/workflows/ci.yml：backend job(pip + make test + make metrics) + frontend-guards job(make guards)。
### 顺带修复（CI 接入暴露的两个真问题）
- 前端守护硬编码绝对路径 /home/claude/bagua_project_build → 改 __dirname 相对路径，去 symlink 依赖，可移植。
- **空值守护静默失效**：babel.parseSync 用 presets:['@babel/preset-react']，环境缺该 preset →
  每文件解析失败(setExitCode 2 返回空)→ 假"0 违规 ✓"却退出 2，实则一个文件都没真解析。
  修：去 presets、加 configFile:false+babelrc:false，仅用 parser 的 jsx 插件 → 真正解析全部 66 文件、退出 0。
  此前只看 总计行未查退出码故未察觉；make 检查退出码方暴露 —— CI 接入的直接价值。

## 空值守护复核 + 自检加固（防再次静默失效）
### 真阳性/精确性复核（注入探针）
- 注入 5 个探针：违规 data.value / items.map（可空 useState 未守护成员访问）→ 均被抓、给修复建议、退出 1；
  安全 data?.value / data && data.value / if(!data)return（早返）→ 全部正确放行，不冤枉。
- 结论：守护真有真阳性能力 + 精确性（抓真违规、放行三类安全写法）。
### 守护自检（每次运行先自验，杜绝静默失效）
- 重构 analyzeFile → analyzeCode(code,label)；解析失败返回 null（区别于「0 违规」的 []）。
- 扫描真实文件前先自检：以已知违规(d.x)+已知安全(d?.x)样本验证守护本身——
  · 解析失效（babel 不可用）→ exit 2；
  · 抓不到已知违规（判别逻辑回归）→ exit 2；
  · 误报已知安全（精确性退化）→ exit 2。
- 验证：正常运行「✓ 守护自检通过」+ 退出 0；模拟 babel 失效 → 自检 exit 2 大声失败。
- 守护从此「不能假装通过」——若失效必红灯，根除本周期那种静默失效的复发。

## hooks 守护自检 + 行文层批量导出（① ②）
### ① hooks 导入守护自检（对称加固）
- 重构 checkFile → checkContent(content,rel) 返回失败列表（不再改全局），供自检调用。
- 守护自检：以已知违规（用 useEffect 未 import）+ 已知合法（import+use useState）样本自验——
  抓不到违规 → exit 2；误报合法 → exit 2。另加空文件保护（扫到 0 个 jsx → exit 2，防路径错静默通过）。
- 验证：正常「✓ hooks 守护自检通过」+ 退出 0；注入 useEffect 未 import → 抓住退出 1。
- 至此空值守护 + hooks 守护对称加固，二者都无法再静默失效。
### ② 行文层批量导出（存档/分享）
- narrator.build_export_document(ms, narrations, scope_label, fidelity_note)：组装 markdown 存档，
  三段结构——「一、引擎判断（权威结论）」「二、行文（多风格）」「三、凭据」，
  明确区分「判断属引擎、文辞属 AI」之边界，自带护栏凭据声明。
- API：POST /api/v1/narration/export（master_synthesis 或 chart_data+module；styles 默认全三档；
  整盘自动 collect_facts；返回 document(markdown)+各风格 source/fidelity+filename）。
- 前端：narrationApi.exportDoc；NarrationPanel 加「⤓ 导出存档」按钮 → Blob 下载 .md。
- 守护：test 增 2 用例（导出文档结构 + 导出端点），全量 647 通过。

## 量化回归元测试 + 神煞深挖（① ②）
### ① 自检的自检：CI 阈值能拦退化护栏
- guard_metrics 增可注入 verify_fn（默认 verify_fidelity），供元测试以伪护栏验证指标体系本身。
- test_metrics_catch_degraded_guard：① 真护栏 → CI 通过；② 伪护栏「永远放行」→ 拦截率 0 → CI 拦下；
  ③ 退化护栏「只抓判断实体、丢干支/年份」→ 干支/年份拦截率 0 → CI 拦下。
- 证明回归阈值（忠实通过率==1.0 且 拦截率>=0.98）真有牙齿，能区分真护栏与退化护栏，
  本身不是「静默通过」—— 与守护自检同源的「验证器须可信」原则。
### ② 八字神煞深挖 —— 健康（无新 bug）
- 天乙贵人 vs 独立贵人表（甲戊庚丑未/乙己子申/丙丁亥酉/辛午寅/壬癸卯巳）：24/24 全对。
- 驿马（三合长生之冲）：年支基 8/8；桃花（咸池）：年支基 8/8。皆按正统年支基计算、随输入变。
- 神煞体系健康，无恒值/无静默失效。

## 深挖续：紫微流月 + 奇门用神（健康，无新 bug）
- 紫微流月（time_panel.months）：流年 2026 丙午，正月庚寅（五虎遁「丙辛寻庚起」），
  12 月连续干支 vs 五虎遁独立推算 3/3 全对；time_panel.year 正确取当前年。
- 奇门用神（按事由选取）：用神宫随事由变（6/8：求财坤/婚姻乾/疾病中/诉讼震/考试兑…），
  用神门按正统选取（求财→生门、疾病→死门、诉讼→景门），factors（module/factor/polarity/note）丰富且全变。
- 方法论记录：本轮两处初见「恒值」（奇门 factors 全 None、流月"1 种"）均为读取字段名错误
  （factors 实键 module/factor/polarity/note 而非 name/symbol/type）—— 审计中第 4 次同类。
  差分扫描器价值取决于读对字段；读错即误报恒值。先核数据结构、再下结论，是排除假警报的关键纪律。

## 深挖最后角落：玄空正零神/城门 + 择日28宿（全部健康，无新 bug）
- 玄空正零神：三元九运运2–运9，正神=当运星、零神=合十对宫（运8正神8艮东北/零神2坤西南，
  运9正神9离/零神1坎）；卦位方位 vs 独立洛书推算 8/8。
- 玄空城门：8 山向各取「向之两侧山」（子山向午→左丙右丁，艮山向坤→左未右申），8/8 随向变。
- 择日二十八宿值日：连日按 28 宿顺序递进（星张翼轸角亢氐房…）30/30；28 宿全覆盖。
- 择日二十八宿吉凶：vs 古法吉凶表（角房尾箕斗室壁娄胃毕参井张轸吉，余凶）28/28 全合。
- 至此 7 系统深挖收官：四柱/十神/纳音/节气/大运/神煞、命宫身宫/四化/14主星/大限/飞化/流月、
  六爻六神/旬空/卦身、奇门值符星/格局/用神、玄空七星打劫/正零神/城门、阳宅断语、择日28宿——
  全独立核验健康；早期真 bug 已修净，近多轮持续确认 + 排除假警报（多为读取字段名错）。

## 前端审视 + URL 路由（前端改进 #1）
### 前端整体审视结论
- 覆盖度：核心占断 bazi9/9·ziwei4/4·liuyao5/5·qimen5/5·date1/1 全覆盖；行文层6/7（metrics为CI专用）；
  用户体系（注册/登录/命盘存档/生辰簿）、AI助手、知识库62/102、模型切换均接入。
  真实缺口小：fengshui monthly_flying（流月飞星）未做独立视图；twenty_four_mountains 冗余。
- 代码质量问题（按优先级）：① 无 URL 路由 ② 错误/加载处理不一致 ③ 单体大页面+内联样式过密
  ④ 无障碍薄弱 ⑤ 无代码分割。
### #1 URL 路由（History API，无新依赖）
- frontend/src/router.js：纯函数 parseRoute / routeToPath / ROUTE_SLUGS（active+showSettings ↔ URL）。
- App.jsx：三个 effect —— 挂载按 URL 还原（深链接/刷新）、popstate 听前进后退、状态变化 pushState。
  保留默认 guardian 行为；settings ↔ /settings；各模块 ↔ /<slug>。
- 价值：解锁深链接、浏览器前进后退、页面可收藏分享（呼应命盘存档/分享诉求）。
- tests/test_app_routing.js：往返/深链接/默认回落 25 项校验，纳入 make guards + Actions。

## 前端改进 #2：统一错误/加载反馈
- 问题：八字页有 error 态 + 内联 .error-box 持久显示；FengShui/DateSelect/QiMen 只 toast，
  错过即无反馈、页面空着 —— 错误处理不一致。
- frontend/src/hooks/useAsyncAction.js：抽取八字页成熟模式为共享 hook，封装
  loading + 持久 error 态 + 成功/失败 toast；run(asyncFn,{successMsg}) 失败返回 undefined 并置 error。
- 应用到三个薄弱页：DateSelectPage / FengShuiPage / QiMenPage（含 run + runZeji 两处），
  各自补上内联 .error-box 持久错误显示；移除分散的 setLoading/try-catch/notify 样板。
- 现一致：请求失败既弹 toast、又在页面内持久显示「⚠ 错误」，用户不会再面对空白页。
- esbuild 解析 4 文件通过；守护（含自检+路由 25 项）全绿。

## 前端改进 #4：无障碍补强
- frontend/src/utils/a11y.js：clickable(handler,{label}) helper —— 给「可点击 div」注入
  role="button" + tabIndex=0 + onClick + onKeyDown(Enter/Space) + 可选 aria-label，最小侵入式补强。
- 应用到 13 个内容选择器 div（键盘原本不可达）：App 模块导航×2、Primitives 选格、Shared 印章、
  AuthModal 登出、Dashboard 卡、Bazi 流年/月/日选择×3、Knowledge 卡、LiuYao 起卦法、
  Xuankong 宫格、DateSelect 日历格 —— 现均可键盘聚焦并以 Enter/Space 触发。
- 有意跳过 4 个遮罩/抽屉 div（Knowledge/DailyGuardian/Layout 的 overlay 背景与 stopPropagation）：
  非内容控件，正确做法是 Esc 关闭 + 焦点陷阱（另属一类），不应误标为 button。
- 图标按钮补 aria-label（设置齿轮、登录）；图片 alt 经查已全覆盖（无缺）。
- esbuild 全解析通过；守护（空值/hooks/路由）全绿。

## 前端改进 #5：路由懒加载（code-splitting）
- App.jsx：11 个页面 import 改为 React.lazy(() => import('./pages/...'))，
  各页成为独立 chunk，Vite 构建时按动态 import 自动切分。
- 两处渲染（SettingsPage / PageComp）用 <Suspense fallback={<PageFallback/>}> 包裹，
  PageFallback 为 spinner + 「加载中…」占位。
- 效果：首屏只加载外壳 + 当前页 chunk，不再一次性打包全部 22k 行页面 → 首屏更快。
- 与 #1 URL 路由天然配套：深链接进入某页时只拉该页 chunk。
- esbuild 解析通过（动态 import 合法）；守护（空值/hooks/路由）全绿。
### 前端审视清单进度
- ✓ #1 URL 路由  ✓ #2 统一错误/加载  ✓ #4 无障碍  ✓ #5 懒加载
- 待办 #3 大页面拆分 + 内联样式收敛（工作量大，建议渐进逐页进行）

## 前端改进 #3（示范）：LiuYaoPage 拆分
- 最大单体 LiuYaoPage（1524 行，含 876 行的 HexagramResult 顶层组件）做示范性拆分。
- 抽出 frontend/src/pages/LiuYao/LiuyaoHexagramResult.jsx（876 行 result 组件，export default）；
  其依赖（4 颜色/符号常量 + Primitives + Visualizations + 10 子面板 + NarrationPanel）逐字保留、原样 import。
- 抽出 liuyaoConstants.js（SYM/QIN_COLOR/SHEN_COLOR/STR_COLOR，供主页与 result 共享）。
- 主页：删 HexagramResult 体、改 import 二者、清理 13 行因抽走而未用的 import → 1524→633 行（减 58%）。
- 安全性：HexagramResult 为顶层函数、不闭包父 state，逐字迁移、行为不变；
  核查无未定义引用、无残留旧引用；esbuild 解析三文件通过；守护（空值68/hooks81/路由25）全绿，
  新拆出文件已纳入守护扫描。
- 这是 #3 的可复制范式：自包含顶层组件 → 独立文件 + 共享常量 + 清死 import。其余大页面可循此渐进。

## 拆分功能完整性核查（LiuYaoPage #3）—— 零丢失确认
- 方法：取拆分前 zip 148 的 LiuYaoPage.jsx（1523 行），与拆分后三文件逐行 diff。
- 结果（三处 diff 全为空，字节级一致）：
  · HexagramResult 体 876 行：零差异
  · 主组件 LiuYaoPage 289 行：零差异
  · 尾部 HexagramDetail + LiuYaoGuide 309 行：零差异
  · 4 常量 SYM/QIN_COLOR/SHEN_COLOR/STR_COLOR：值全部一致
- 账目：1523 → 632（主页）+ 892（HexagramResult）+ 5（常量）；多出几行仅为新文件 import 头，非新增逻辑。
- 原文件 4 个顶层组件一个不少，仅换文件：HexagramResult→LiuyaoHexagramResult.jsx；
  HexagramDetail/LiuYaoGuide/LiuYaoPage 仍在 LiuYaoPage.jsx。
- 结论：本次拆分为纯机械搬迁（搬组件 + 搬常量 + 清死 import），所有占断展示逻辑原样保留，功能零丢失。

## 设计系统统一（第一步：令牌 + 间距 + 语义色）
- 令牌卫生：① 删重复的 --text-2xl（曾 1.6/1.5 并存，1.6 为死令牌）② 头部注释字号表对齐实际值
  ③ 主色注释「朱砂红」→「青瓷绿」（历史遗留命名，值早已是 #6a9a80 青瓷绿）。
- 间距体系：新增 --space-1..8（4px 基准，4/8/12/16/24/32/48px），供各界面统一留白节奏。
- 语义色修复（真 bug）：错误/危险类原误用品牌绿（朱砂红切青瓷绿时遗留），改用 --red 砖红：
  · 新增 --red-bg / --red-dim 变体；
  · .error-box、.card-danger、.badge-red（名红实绿）、.btn-danger 全部改 --red。
  · 效果：请求失败的错误框不再与成功提示同绿，一眼可辨，仍是素雅砖红不刺眼。改共享类 → 全界面统一受益。
- 验证：大括号平衡(196/196)、--text-2xl 唯一、8 间距令牌、4 类用红；守护(空值/hooks/路由)全绿。
- 渲染了「调色板 + 错误色前后对比 + 组件示意」样例供设计评审。

---
## 盘式设计语言落地 (留白版) — 模块逐个改造

**设计语言定稿**：现代留白排版 + 印章 + 传统盘式骨架 + 五行配色。
- 白底近白 (#f8f7f3) · 细线收边 · 大留白分区 · 无背景色块
- 干支 40px 衬线大字 · 五行配色 (木青/火红/土金/金灰/水蓝)
- 印石章首 + 朱印定论
- HTML 定稿预览：outputs/盘式设计预览-现代版.html
- 共享样式：frontend/src/styles/plates.css (命名空间 .gv-plate，不污染全局主题)

**模块改造顺序**：① 八字四柱表 → ② 六爻竖梯 → ③ 紫微命盘 → ④ 奇门/玄空九宫 → ⑤ 择日/阳宅
**后续大改**：首页分享页 · 知识图谱 · AI（结构性重做，留到模块改造之后）

### ① 八字四柱表 — 完成 (zip 152)
- 新建 frontend/src/pages/Bazi/BaziSizhuPlate.jsx：左行标 + 四柱对齐列盘式
  - 行：主星(shishen_gan) / 天干(大字·五行色) / 地支(大字·五行色) / 五行标 / 藏干(canggan) / 副星(shishen_zhi) / 纳音 / 神煞(按柱归组)
  - 日柱列：表头朱线高亮 + 主星格显「日元」朱字
  - 综断区：格局+pattern_desc+调候verdict · 五行分布条(统计可见8字)
  - **严格用引擎真实字段，无「星运/十二长生」行（引擎不提供，不伪造）**
- BaziPage.jsx：四柱卡片内 PillarCard 行 → <BaziSizhuPlate chart={data}/>；移除死 import PillarCard
- 守护：esbuild 解析 OK · null-safety 69 文件 0 违规 · hooks 82 文件 · 路由 25 通过
- 纯展示层，未触碰引擎

### 全局换肤 — 完成 (zip 153)
**「按这个格调调整整个」—— 全局设计令牌层一次性换肤，所有页面/组件自动继承。**
- index.css :root 令牌：
  - --base #f3f0ea(暗米黄) → #f8f7f3(近白，去暗沉)
  - --surface #fffdf8 → #ffffff(纯白卡片)
  - --accent #6a9a80(青瓷绿) → #cf3b2c(朱砂红·印泥) ← 主色彻底换向，与印章语言统一
  - --accent-b/c/dark/light/bg/glow/dim 全部跟改为朱砂系
  - --border* 偏绿灰 → 暖中性墨灰(rgba(34,32,26,*))
  - 新增 --wx-mu/huo/tu/jin/shui 五行全局令牌(与 .gv-plate 一致)
- body 纸面氛围：冷蓝径向渐变 → 暖朱+琥珀极淡
- 滚动条/toggle阴影/border-active：跟随朱砂
- accent 变体(红/金/玉)与 dark theme 保持不变；error --red 保持砖红以区分 accent
- 纯 CSS 令牌改动，无类名/布局变更，零 JS 风险
- 守护：null-safety 69 文件 · 路由 25 · 无破坏
- 遗留：KnowledgePage.css 1 处标签分类内联色选择器(知识图谱大改时一并处理)

### ② 六爻装卦竖梯 — 完成 (zip 154)
- 新增 plates.css：.gv-ladder-* 系列（六爻竖梯专用，本卦｜变卦并列、无边框细线分行）
- 新建 frontend/src/pages/LiuYao/LiuyaoLadderPlate.jsx：
  - 本卦：上爻→初爻竖排，每行 六神(小字)｜六亲+纳甲干支(含空亡·旺衰标注)+伏神附注｜爻线(阳实/阴断)｜世应/动爻标记
  - 变卦：动爻行显化出六亲干支+变号；静爻行灰化重复本卦(古法：变卦仅动爻改变)
  - 用神行：左侧朱线高亮(box-shadow inset)
  - 中轴："N爻动 → 之卦"
  - 字段来源：data.yaos[].{line,is_changing,is_world,is_application,liu_qin,stem,branch,kong_wang,liu_shen,strength.label,changed_*}；data.fu_shen(伏神，position 1=初爻..6=上爻，与 yaos 索引一致，已核实后端 _find_fu_shen)
- LiuyaoHexagramResult.jsx：原"六爻纳甲详表"网格表（表头+140行内联样式）→ <LiuyaoLadderPlate data={data}/>；旬空提示、LiuyaoVis 可视化、伏神卡(独立卡，信息更细)、世应概况卡均保留
- 守护：esbuild 双文件解析 OK · null-safety 70 文件 0 违规 · hooks 83 文件 · 路由 25 通过
- 纯展示层，未触碰引擎；QIN_COLOR/SHEN_COLOR/STR_COLOR import 仍被其它 tab 使用，未删除（非死代码）

### ③ 紫微命盘 — 完成 (zip 155)
**十二宫方阵本身已是结构化传统盘式（非平铺），本次改造聚焦"洞察栏"中两个无状态展示组件：**
- 新增 plates.css：.gv-grade-seal / .gv-zw-hero / .gv-sfsz-grid / .gv-sfsz-cell
- ZiweiInsightsBar.jsx：
  - RatingBadge → 命格朱印 hero（64px 印章 + 亮度评分 + 综述 + 庙旺/失陷主星标签），数据源 rating.{overall,score,summary,soul_stars,soul_rating,bright_in_sfsz,fallen_in_sfsz} 完全不变
  - SfszRatingTable → 三方四正开放卡片网格（无边框、顶部色条标级），保留 showAllNotes 展开/收起状态与按钮逻辑不变
  - **保留不动**：PatternsCard / FeihuaWarningsCard / ChongChainsCard（均含展开/收起 useState + 与宫位点击联动的 HighlightWrapper 高亮，无法离线验证交互，判断为高风险，本轮不碰）
  - 保留 ZiWeiPage.jsx 既有架构决策注释："InsightsBar 移到十二宫盘之后，因为命盘本身是主体内容"——与本项目"盘为主·断为附"设计原则一致，无需改动位置
- 守护：esbuild 解析 OK · null-safety 70 文件 0 违规 · hooks 83 文件 · 路由 25 通过
- 纯展示层，未触碰引擎；未改动任何组件 props/state 行为

### ④ 奇门/玄空九宫 — 完成 (zip 156)
**两个九宫格本身已是结构化盘式（非平铺），本次做的是视觉重做：脏色块背景+彩色描边 → 白盘+顶部质量色条，与其它模块统一留白语言。**

- 新增 plates.css：.gv-jg-*（奇门九宫）/ .gv-xk-*（玄空九宫）
- **奇门 QiMenPage.jsx**（九宫排局·四盘叠合）：
  - 原：每格彩色背景色块(qs.bg) + 彩色描边(qs.border)，"死人的暗沉色"同款问题
  - 新：白格 + 顶部 2px 质量色条(仍用 qs.dot 语义色，信息不丢) + 细线分格
  - **完整保留**：onClick={() => setSelected(...)} 交互、isZhifu/isZhishi/isCenter 判断、天盘地盘干支条件渲染——逻辑代码零改动，仅 JSX 标签与样式来源从内联 style 换成 className
- **玄空 XuankongPanel.jsx**（ThreePalaceChart 组件，纯展示无状态，已确认无 onClick/useState）：
  - 原：坐向宫金色背景块 + 描边，五黄警示描边
  - 新：白格 + 坐向朱框(mark) + 五黄红点角标(warn5)，山星/向星/运星三层排布不变，"令"字当令标记保留
- 两文件均补 import '../../styles/plates.css'
- 守护：esbuild 双文件解析 OK · null-safety 70 文件 0 违规 · 路由 25 通过
- 纯展示层，未触碰引擎；奇门交互逻辑（点击选中宫位）完整保留未动

### 细节审查专项 — 完成 (zip 157)
**用户要求："检查之前的，一定要做到所有的细节都优化，而不是只是局部的布局更改"——系统回查①-④已完成模块 + 全局换肤，而非只做盘式骨架。**

发现并修复的真实问题（非泛泛而谈，逐条列出）：

1. **键盘可达性缺口**（2处）：
   - 奇门九宫格 `onClick` 裸 div → 补 `clickable()`（role/tabIndex/onKeyDown/aria-label），加 `:focus-visible` 描边
   - 紫微格局徽章 `<span onClick>` → 同样补 `clickable()`
   - 奇门九宫格补 `:hover` 反馈（原来鼠标悬停无任何视觉提示）

2. **响应式断点缺失**（3处，窄屏会挤爆）：
   - 八字四柱表 `.gv-sizhu`、奇门九宫 `.gv-jg-grid`、玄空九宫 `.gv-xk-grid` 原本零 `@media` 规则
   - 补齐 `max-width:480px` 断点：缩字号/缩间距，**列数不变**（四柱/九宫结构不能折叠成单列）

3. **印石色/图腾字与项目既有石章命名体系（Shared.jsx STONES/MODULES）不一致**（2处真实错误）：
   - 奇门章首：误用蓝色 + "局"字 → 修正为青田石绿 `#88b0a0` + 正确图腾字"门"
   - 玄空章首：误用灰色 → 修正为巴林石紫 `#a890c0`（与 fengshui 模块石色一致）
   - （八字田黄金、六爻芙蓉粉核对后确认已符合，未改）

4. **全局换肤引入的语义色冲突**（"大凶/凶/忌"误用新朱砂主色，7处）：
   - 换肤前 `--accent` 是青瓷绿，凶险语义误用它尚无大碍；换肤后 `--accent` = 朱砂品牌色，"大凶"等负面语义如果还用 accent，会和全站按钮/强调色混同
   - 逐一修复：DateSelectPage(5处：凶日图例/建除大凶/择日理由图标/神煞专断/凶煞释义标题) · KnowledgePage(1处：卦象大凶边框) · FengShuiPage(1处：九星大凶取色，此为第3处，与下条不同位置)
   - 统一改用独立的 `var(--red)` 危险色，不再复用品牌强调色

5. **硬编码旧青瓷绿 RGB 残留**（`rgba(106,154,128,*)`，13个文件，未随 CSS 变量换肤自动更新）：
   - 逐一分类：
     - **真负面语义**（"凶/inauspicious"，4处，DateSelectPage 择日日历热力图 + FengShuiPage 峦头砂水宜忌）→ 改红色系 `rgba(168,88,64,*)`，与"最佳/朱砂"区分，避免好坏撞色
     - **强调色晕染同步**（9处：Shared.jsx导航高亮、八字/紫微徽章背景、紫微大限流年高亮格、紫微真太阳时校正条、择日人元标注、六爻神煞徽章、Dashboard装饰山纹）→ 同步为新朱砂 RGB `rgba(207,59,44,*)`
   - Knowledge 页面（`精通`4级色阶）保留不动——该处是独立分级色而非品牌色克隆，且知识图谱本身已定为后续大改范围
   - **全站品牌 logo（App.jsx 顶部☯印章）**：渐变一端 `var(--accent)`、另一端硬编码旧深青瓷绿 `#3a6a50`，红绿撞色 → 改为 `var(--accent-dark)`，渐变自洽

6. **确认无误但特意排除的项**：dark theme 蓝色边框令牌（`[data-theme="dark"]` 独立配色，非本次换肤范围，正确保留）

- 守护：esbuild 对本轮涉及的全部 14 个文件逐一解析 OK · null-safety 70 文件 0 违规 · hooks 83 文件 · 路由 25 通过
- 纯前端视觉/可达性/一致性修复，零后端改动，零组件 props/state/交互逻辑改动

### ⑤ 择日/阳宅 + 延续细节审查 — 完成 (zip 158)
**这两个系统不是格子盘结构（择日=候选日历，阳宅=门主灶组合），按各自传统呈现设计，而非套用九宫/竖梯骨架。**

**继续细节审查（"继续"指令下先查漏，再做新结构）：**
- 发现并修复 3 处上轮遗漏的「凶=var(--accent)」语义冲突：DateSelectPage 日历格文字色(textColor)、凶煞释义列表项星煞名称；全项目做了最终穷举扫描（"凶"字前后2行内的 var(--accent)），确认无更多真实遗漏，其余均为已判断保留的系统性"中性档=品牌色"设计
- 补 2 处键盘可达性：择日日历列表视图卡片（`<div onClick>` → `clickable()`）

**⑤-A 择日 · 通书条目盘式**：
- 新增 plates.css `.gv-almanac-*`
- DateSelectPage.jsx「选中日期详解」面板 → 印石头部(历·田黄) + 建除值神/二十八宿/评分开放标签 + 宜忌列表(✓/✗对勾，非徽章) + 吉神/凶煞释义分组，替代原彩色徽章+色块背景写法
- 建除值神大吉/大凶取色统一改用 `var(--gv-mu)`/`var(--gv-vermilion)`（原硬编码 rgba 已在上轮同步）

**⑤-B 阳宅 · 门主灶生成链盘式**：
- 新增 plates.css `.gv-yz-*`
- 新建 `YangzhaiChainPlate.jsx`：合并原本分离的"三宫卦象"（3列网格卡）与"门主灶三要关系"（RelationRow色块列表）两张卡为**一张**——门→主→灶横向生成链（箭头连接，对应《阳宅三要》"门定卦、门→主→灶递推"的真实推算顺序），三条关系判断附于链下，纯杂判定作为底部印记
- YangzhaiSanyaoPanel.jsx：移除已死代码 `RelationRow` 函数；`STAR_COLOR`（8游星语义色，六事安置断仍用）保留不动
- 门主局详断/灶位详断/穿宫九星等64局断语库文本面板未改动（本身是丰富文字断语，非平铺列表问题）

- 守护：esbuild 3文件解析 OK · null-safety 71 文件 0 违规 · hooks 84 文件 · 路由 25 通过
- 纯展示层，未触碰引擎；零组件 props/state 行为改动

---
**至此：① 八字 ② 六爻 ③ 紫微 ④ 奇门/玄空 ⑤ 择日/阳宅，全部 7 系统的核心结果呈现均已按统一设计语言（留白 · 印章 · 五行/星煞语义色 · 传统盘式骨架）改造完毕，叠加两轮细节审查（可达性/响应式/色彩语义一致性）。**
**剩余未做（用户已知悉，明确排到后面）**：首页、分享页、知识图谱、AI 相关板块——结构性重做，不在本轮范围。

### 首页细节优化 — 完成 (zip 159)
**用户："首页已经很不错，但细节上可以更优化"——大方向不变，只做细节打磨。**

审查 App.jsx 首页区块（诗句题头/八模块卡/最近排盘记录/底部点题/顶部常驻石章导航），发现并修复：

1. **真实导航 bug**（非视觉问题）："最近排盘记录"点击后硬编码 `toggle('bazi')`，无视记录自带的 `module` 字段——查证 BaziPage/LiuYaoPage/QiMenPage 三处 `addRecord()` 调用均正确设置了 `module:'bazi'/'liuyao'/'qimen'`，首页却没用上。修复：改为 `toggle(r.module || 'bazi')`（含向后兼容旧记录的兜底）。**修复前：点击一条六爻或奇门的历史记录会被错误带到八字页。**

2. **显示 bug**：记录列表左侧 80px 定宽栏显示 `r.pillars`（八字专属字段），六爻/奇门记录无此字段，原渲染为空白。改为 `r.pillars ? 干支 : 模块名`兜底，非八字记录改显示"六爻"/"奇门"等模块名，不再留白。

3. **键盘可达性缺口**（3 处）：首页模块卡（八大模块网格）、最近排盘记录行、顶部常驻石章导航——原视觉反馈均只挂在 `onMouseEnter/onMouseLeave`（纯鼠标）。统一方案：新增共享 CSS 类 `.gv-focus-ring:focus-visible{outline:2px solid var(--accent);outline-offset:2px}`（追加进 App.jsx 底部已有的 `<style>` 标签），三处均加 `className="gv-focus-ring"`，与既有鼠标态内联样式互不冲突（outline 独立叠加，不覆盖 background/border 切换）。

4. 旧青瓷绿色残留最终核查：首页区块本身干净（此前已修复顶部☯品牌印章渐变，本轮为区块内其余部分复核，无新发现）。

- 守护：esbuild App.jsx 解析 OK · null-safety 71 文件 0 违规 · hooks 84 文件 · 路由 25 通过
- 纯前端修复（含 1 处真实功能 bug + 1 处显示兜底 + 3 处可达性），零后端改动

### 分享页 · 全七系统丰富化重做 — 完成 (zip 160)
**用户："分享页根据完善的这么多全新功能，进行丰富和优化，让layout更加合理和丰富"**

**问题诊断**：原分享功能极薄——`ShareImage.jsx`（156行手绘canvas）**只支持八字一个模块**，配色/布局与新盘式设计语言完全脱节（旧色板、无印章、无五行配色），且信息密度低（仅四柱干支+几行文字），完全没体现这几轮建立的深度内容体系。

**重做架构**：
1. **新建 `frontend/src/utils/shareCanvasKit.js`** — 共享 canvas 绘制工具库，与 `plates.css` 留白盘式设计语言对齐：
   - 色板与 `.gv-plate` 变量字面值一致（canvas 无法读取 CSS 变量，需硬编码同步）
   - `drawHeader`（印石章首+标题+平台印）· `drawGanZhiBig`（五行配色衬线大字干支）· `drawZhuSeal`（朱印定论，旋转双线印边）· `drawParagraph`（断语自动换行截断）· `drawFooter`（统一收尾诗句+模块名）
   - 印石配色对齐项目既有 STONES 命名体系（田黄/芙蓉/鸡血/青田/巴林）

2. **新建 `frontend/src/utils/shareRenderers.js`** — **七个模块**各自的分享图内容渲染（此前只有1个）：
   - 八字：四柱（大字+藏干+副星+纳音）+ 五行分布条 + 格局朱印定论
   - 六爻：本卦/变卦名 + 世应/用神/动爻数 + 断语
   - 紫微：命宫立命主星 + 命格评级朱印 + 格局标签
   - 奇门：局数(遁+局) + 值符值使 + 用神宫定位 + 断语
   - 玄空：坐向 + 当运 + 令星到位判定 + 断语
   - 阳宅：门→主→灶 三宫 + 纯杂判定 + 断语
   - 择日：最佳吉日 + 建除值神/评分 + 宜忌理由
   - **七模块统一复用 `master_synthesis.headline`（总汇合参）作为核心断语**——这是各模块引擎都提供的通用字段，此前分享图从未用上
   - 字段全部对齐真实后端返回（本轮逐一核实：紫微 `metadata.five_elements`、玄空 `data.verdict`、奇门 `yongshen_palaces.items[]`，均修正了最初的猜测性错误字段名）

3. **重写 `ShareImage.jsx`** — 从"仅渲染八字"改为按 `module` prop 分发到对应渲染器；每模块独立画布尺寸；`HAS_DATA` 逐模块判断最小可分享字段；渲染异常静默保护（某模块字段缺失不白屏崩溃）

4. **接入全部 7 个页面**（此前仅 BaziPage 一处）：BaziPage(显式传module) / LiuYaoPage / ZiWeiPage（与既有"导出高清PNG"并存，二者互补：一个是完整宫盘截图，一个是精炼摘要卡）/ QiMenPage / XuankongPanel / YangzhaiSanyaoPanel / DateSelectPage（补传 `form.year/month/purpose`，因 `result` 本身不含这三个字段，已实测核实）

- 守护：esbuild 10 个新建/改动文件逐一解析 OK · null-safety 71 文件（页面级）0 违规 · hooks 84 文件 · 路由 25 通过
- **诚实说明**：`utils/`、`components/UI/` 不在 null-safety 守护扫描范围内（项目既有限制，非本轮引入），已对 shareRenderers.js/ShareImage.jsx 逐行人工复核空值防护（全部使用 `?.` 或前置 if 守卫），并手工核算七个画布的高度预算确认内容不会溢出裁切；**canvas 实际渲染效果需用户本地验收**（环境无法执行真实 canvas 绘制）
- 纯前端新增/改动，未触碰引擎

### 每日守护 · 分享图重做 — 完成 (zip 161)
**用户提醒："最开始有个每天的分享页，那个有没有优化"——发现第三套独立分享实现，完全未被前两轮覆盖。**

**发现**：`DailyGuardianPage.jsx`（每日守护/DIZHI_IMG 瑞兽）自带一套内联 canvas 分享逻辑（约185行，`genShare` 回调），与本轮新建的 `shareCanvasKit`/`shareRenderers`（七大系统专用）完全独立、互不知情——是项目里第 3 套分享图实现。内容深度本身很好（农历大字/评分圈/瑞兽诗句/节气建除天神星宿冲煞/宜忌两栏/吉神凶煞/方位彭祖/十二时辰吉凶格/建除详解/星宿歌诀），**问题在视觉执行**：旧色板（`#f6f2ea`底/`#b5361e`强调/`#d8c8a0`分隔）、双线描边+四角圆点的"旧派"裱框、宜忌用色块底色（与此前"死人色"同类问题）、十二时辰格用边框+底色块、无印章语言、页脚样式独立于其余七个分享图。

**重做**（保留原有两遍测量换行的核心机制不变，仅替换视觉执行层）：
- `shareCanvasKit.js` 补充 `zhusha`（朱砂石）印色，对应 MODULES 中 `guardian` 模块的既定石材
- `drawFooter` 增加可选 `margin` 参数（默认24，本页传60与自身边距系统对齐）——避免直接复用导致页脚分隔线宽度与页面其余分隔线不一致
- 移除双线描边+四角圆点裱框（改无框留白）
- 顶部品牌文字条 → 复用 `drawHeader`（印石章首·守·朱砂，与七系统分享图同构）
- 全部硬编码旧色 → 统一替换为 `shareCanvasKit` 色板（INK/INK_2/INK_3/INK_4/VERMILION/PAPER + GREEN`#2f8f63`/AMBER`#c1953a`语义色，与七系统一致）
- 宜/忌：色块底 → 左侧2px细线标记（不再是大片色块底）
- 十二时辰格：边框+底色块 → 顶部2px细色条标吉，无边框无底色
- 页脚 → 复用 `drawFooter`，与其余七个分享图完全同构收尾

- 守护：esbuild 2 文件解析 OK · **null-safety 71 文件 0 违规（本文件在 pages/ 目录内，属守护扫描范围，非人工复核）** · hooks · 路由 25 通过
- 纯前端视觉重做，两遍测量换行的高度计算逻辑与字号完全不变（避免打乱高度预算数学），未触碰引擎

---
**至此：全站 8 处分享图（七大系统 + 每日守护）均已统一为同一套"留白盘式"视觉语言，共享同一 `shareCanvasKit` 绘制工具库。**

### 知识图谱 · 内容完整性与排布重做 — 完成 (zip 162)
**用户："展示架构还凑活，但内容排布不好，而且不能完整显示"——用真实后端数据逐一核实（in-process TestClient 调用全部67个 CATALOG 端点），找到具体 bug 而非猜测式改版。**

**诊断（数据驱动，非目测）**：
- 67 个知识目录端点全部请求成功（0 失败），"架构凑活"评价准确——问题不在整体骨架，在渲染细节
- **3 个真实内容显示 bug**（逐一用真实响应体核实字段名与长度）：
  1. `liuyao_rules`（16条断卦规则，字段 `rule/source/desc/detail`）与 `qm_yanbo`（12条《烟波钓叟赋》口诀，字段 `口诀/解析`）—— 命中通用 `ArrayRenderer` 的**旧版写死字段白名单**（只认 名/title/宿/符/吉凶/卦辞/核心/歌诀/禽星/desc），这两个端点的字段名都不在名单里，导致内容**几乎完全不显示**（不是截断，是根本没渲染）
  2. `yanbo_full.原文分段解析`（16段古籍原文+解析）—— 嵌套数组套对象，命中 `ObjectValue` 的 `JSON.stringify(item)` 兜底分支，原始 JSON 字符串糊在页面上
  3. 28宿卡片：`歌诀`/`出生命运` 硬截断 `.slice(0,50)`/`.slice(0,30)`（实测"箕"宿歌诀54字，被砍掉4字）；且**宜/忌/天文/说卦对应四个字段完整存在于数据里，但渲染代码完全没有显示它们**——比截断更严重的遗漏

**重做**：
- 新建通用 `SmartItemCard` 组件：不再靠写死字段名白名单，改为智能挑标题字段（名/title/宿/符/rule/口诀/原文等候选）+ 吉凶徽章（如有）+ **其余全部字段完整展示**（label:字段名，value:完整原文，不截断）
- `ArrayRenderer` 重写：用中位数启发式（每条目最长字段长度的中位数 <22 字）区分"密集网格"（如64卦，短字段适合浏览）vs"竖向列表"（如断卦规则/古籍解析，长文本适合阅读）——避免单条较长文本（如"泽天夬"卦辞恰好24字）误判拖累整批布局
- `ObjectValue` 数组分支改用 `SmartItemCard`，替换原 `JSON.stringify` 兜底
- 28宿卡片重写：网格加宽 155px→230px，补全全部12个字段（含此前完全未显示的 宜/忌/天文/说卦对应），宜忌数组用逗号分隔清晰展示，移除截断
- 移除死代码 `XiuCard`/`GuaCard`（从未被调用，94行）
- CSS：新增 `.kp-item-row/.kp-item-list/.kp-item-fields` 等类（复用既有 `.kp-val-obj` key-value 视觉语言）；合并此前散落三处的 `.kp-modal-body`/`.kp-modal-header` 重复声明为单一权威规则（增量打补丁遗留的碎片化清理）

**验证（非目测，数据驱动）**：
- 用 in-process TestClient 抽取全部67个端点真实数据，模拟新渲染逻辑，**穷举检查全部771个数组条目**（覆盖顶层数组+全部嵌套数组），确认 0 个会渲染成空卡片
- 逐一验证64卦(isCompact应为密集网格)、六爻规则(应为列表)、奇门烟波(应为列表)三种真实场景的布局分类结果符合预期

**已知遗留（如实告知，未处理）**：67个目录卡片中15个的图标渐变色（`iconBg`）及2个分类色仍硬编码旧青瓷绿 `#6a9a80`（换肤时特意跳过，因判断为"独立分类色而非品牌色克隆"）。这是一次独立的视觉身份设计任务（需要为15+卡片重新构思有意义的分类配色），和本轮"内容显示完整性"是不同性质的工作，仓促处理容易做得潦草，故未在本轮动手，如需要可另行安排。

- 守护：esbuild 解析 OK · null-safety 71 文件 0 违规 · hooks 84 文件 · 路由 25 通过 · CSS 大括号平衡
- 纯前端修复，未触碰引擎（问题本就出在前端渲染器，后端数据完整无误）

### 知识图谱 · 配色体系收尾 — 完成 (zip 163)
**延续上轮标记的遗留项：15+张卡片图标渐变色与分类色仍用旧青瓷绿 `#6a9a80`，这次认真做而非仓促找替换。**

**先厘清设计意图，再动手**（避免瞎改）：抽查发现"卡片图标渐变色"和"分类"其实**没有对应关系**——同一分类"基础理论"下3张卡分别用绿/蓝/褐三种颜色，是在一个5色小色池（绿/蓝/褐/紫/近黑）里轮换取视觉丰富感，并非"颜色=分类身份"。真正需要12色互不相同的，是 `CAT_META`（分类筛选按钮的颜色）——而这里发现了一个更严重的问题：**12个分类实际只用了6种颜色**，"星宿天文/高级系统/深度专题"三个不相关分类共享同一个紫色，筛选按钮形同虚设。

**修复**：
1. `CAT_META` 重新设计：12 个分类各自独立配色，色相均匀展开（木绿/土金/水蓝/紫罗兰/绯红/赭石/芙蓉粉/青田绿/巴林紫/玄青/赤橙/玄紫），其中六爻/奇门/风水三类特意与 app 内既有印石色呼应（芙蓉石·青田石·巴林石）保持全站视觉一致
2. `LEVEL_META['精通']` 换成独立紫色，不再与其它等级或新分类色冲突
3. **发现并清理一处脆弱的死代码**：`.kp-tag-cat[style*="#颜色值"]` 这类靠匹配内联style十六进制子串来强制覆盖背景色的规则（6条，全部因配色改版而失效）——查证后发现基础规则本就用 `color-mix(in srgb, var(--c) 8%, transparent)` 动态计算背景，这6条硬编码覆盖纯属多余（大概率是 color-mix 引入前的旧写法遗留），直接删除，新配色自动通过基础规则正确显示，无需为每个色值单独维护规则
4. 16 张卡片图标渐变里的 `#6a9a80` → 替换为色池内既有色，同分类内多张卡刻意错开避免撞色（如 深度专题 3 张卡此前全部同色，现分别为蓝/褐红/紫褐红）

- 全项目 `#6a9a80` 残留：0（此前刻意保留、如今彻底清除）
- 守护：esbuild 解析 OK · null-safety 71 文件 0 违规 · 路由 25 通过 · CSS 大括号平衡 · CATALOG 67 条目完整性核对无损
- 纯前端配色与死代码清理，未触碰内容渲染逻辑（上一版本已修复）、未触碰引擎

---
**至此，中国术数平台 v6 的全局设计语言统一工作（八字/六爻/紫微/奇门/玄空/阳宅/择日 七大盘式 + 全局换肤 + 首页 + 分享图×8 + 知识图谱内容与配色）已全部完成。**

### 修复真实布局架构 bug：解释性内容错放左侧窄栏 — 完成 (zip 164)
**用户上传择日页截图：左侧280px窄栏挤满长文本解释（综合总论等），右侧1fr宽栏几乎空白（仅AI面板+装饰太极水印）。用户明确："每个模块都要查，发现运程和紫微也有这问题"。**

**系统排查（而非只修用户指出的那一个）**：全项目 6 个使用 `.page-cols`（280px + 1fr 双栏）布局的页面逐一核对左右栏内容分布：
- ✅ 八字 / 六爻 / 奇门 / 风水（峦头形势 tab）—— 左栏干净，只有输入表单，无需改动
- ❌ **择日**（用户截图指出）—— 左栏混入"综合总论·总汇合参"+ DateOverview/DateSynthesis/DatePerspectives/DateConsistencyAudit + 本月概览统计，共 6 大块本该是主体内容的解释性面板
- ❌ **紫微**（用户口述"运程"，即代码中"运程层"—— 紫微大限流年概念，指的就是紫微整个模块）—— 左栏混入"综合论断·总汇合参"+ ZiweiOverview/MinggeSynthesis/Perspectives/ConsistencyAudit/Classical，共 6 大块；且其中"命宫三方四正"简化卡片与右栏 `ZiweiInsightsBar`（已改造过的三方四正评级卡）内容重复

**根因**：这些板块均带 `card-glow` 强调样式（说明设计意图本就是突出显示的主体内容），大概率是历次增量加功能时随手接在最近打开的 div（左栏）末尾，未按"盘为主·断为附"的既定顺序摆放到右侧主内容区。

**修复**（参照八字页——本项目中结构正确的范式模板，其右栏顺序为 盘→综合论断总汇合参→细项分析）：
- **择日**：6 大块从左栏移至右栏，插入顺序为：综合总论 → 本月概览统计 → 日历/列表视图切换 → 详情 → Overview/Synthesis/Perspectives/ConsistencyAudit
- **紫微**：6 大块从左栏移至右栏，插入点为十二宫盘可视化之后、图层选择器之前（利用既有注释"移到12宫盘之后，因为命盘本身是主体内容"作为定位锚点）；"命宫三方四正"简化卡片因与右栏已有更完整版本重复，直接删除而非移动
- 左栏最终只保留：占问事项/查询月份/个人生辰/择日理论精要（择日）；出生信息/命盘基本信息（紫微）——均为紧凑输入控件或摘要，符合 280px 窄栏定位

**验证**：两文件 esbuild 解析 OK；核对 `master_synthesis?.available` / "综合论断·总汇合参"标题在各自文件中仅有一处真实渲染（无重复）；守护 null-safety 71 文件 0 违规、路由 25 通过
- 纯前端结构调整（剪切+粘贴，未改动任何组件内部逻辑/样式），未触碰引擎

### 引擎完整性现场核查 + 择日推荐排序精度修复 — 完成 (zip 165)
**用户："能确定所有的都是根据时间、问题、演算规则、古籍理论来推演的吧，不要任何预设死的！"——现场跑差分测试验证，而非凭记忆背书。**

**现场验证（in-process TestClient，非文档回顾）**：
- 八字：同日不同时辰(3/9/15/21时) → 时柱/十神/格局(七杀格↔偏印格)/身强弱全部真实变化
- 紫微：同日不同时辰 → 命宫/主星/五行局完全不同
- 奇门：跨节气查询 → 阳遁/阴遁在夏至前后正确切换，局数随三元局数表变化
- 六爻：同卦不同"问题"(求财/求官仕途/婚姻) → 用神正确切换(妻财/官鬼)，应期规则给出具体爻位干支非空话；读 `master_synthesis.py` 源码确认 headline/段落由 `yong_shen`/`strength`/`kong_wang` 等真实字段 f-string 拼接生成，非固定文案
- 择日：不同"事项" → 神煞按事项过滤后独立算分

**自我纠错**：验证中曾怀疑奇门"下元元"文字重复为 bug，复查后确认是我自己测试脚本 print 语句手滑多打一个"元"字所致，`_YUAN_NAMES` 源数据本身干净无误——未计入真实问题，如实澄清。

**真实发现并修复（`api/date_selection.py`）**：择日 `best_days` 推荐排序此前用的是不分事项的通用 `score`，而非更精准的事项专属神煞净分 `shensha_purpose.net`（后者能识别"不将"等专属吉神、过滤掉与本事项无关的凶煞）。根因：`shensha_purpose` 在 `select_dates()` 排序**完成之后**才由 API 层补算，排序发生时该字段尚不存在。

- 修复分两层：① 在 `shensha_purpose` 算好后、后续 6 个下游模块（overview/synthesis/perspectives/audit/master_synthesis）读取 `best_days` 之前，插入精排逻辑；② 验证中发现仅精排还不够——`level:"忌"`（专忌此事）的日子仍会因通用分够高而排进前三，故追加过滤层：候选池先排除"忌"日，全月候选皆忌时才回退不过滤（避免 best_days 整月落空）
- 修复后验证：结婚/搬家/开业/出行/求医五个事项，best_days 均不再含"忌"判定、且严格按事项净分降序
- 守护：语法检查 OK · 择日相关 25 个既有测试全过 · 全量后端测试套件（648+ 用例）无回归
- 纯 API 层排序逻辑修正，未改动底层演算规则/神煞判定算法本身

### 每日守护分享图 · 重叠修复 + 杂志式重做 — 完成 (zip 166)
**用户上传截图指出："70分"评分与"麒麟仁兽"瑞兽名重叠；并要求整体更丰盛、更有杂志设计感。**

**根因**：原评分徽章（圆环）与瑞兽题名均用 `textAlign='center'` 在同一 X 位置垂直堆叠，圆环底边到瑞兽名之间只留 6px 间距，而 16px 粗体字本身的视觉高度（cap-height）就超过这个间隙，导致文字顶部窜入圆环内部。

**重做（非局部补丁，完整版面重构）**：
- **真正的杂志封面结构**：`genShare` 改为 async，异步加载 `/ruishou/{文件名}.png`（1.8s 超时保护）——**图片存在**则渲染左文右图的杂志式版头（右侧 214×286 竖版瑞兽肖像卡带朱色顶条，左侧农历大字+干支+纳音+旋转朱印评分徽章+诗句）；**图片不存在**（用户尚未放置图片时）优雅降级为纯文字版头，此时评分朱印与瑞兽题名改为**左右并排**而非垂直堆叠，从几何上彻底避免重叠可能，不再依赖"留白算得够不够"这种脆弱方式
- **双栏杂志排版**：节气/建除/天神/星宿/冲煞（左栏）与吉神/凶煞（右栏）改为左右两栏+竖向分隔线，不再是单栏从上到下的列表
- **摘引（pull-quote）样式**：建除详解、星宿歌诀改为大装饰引号（半透明64px衬线引号符）+ 左侧色条 + 斜体衬线正文的杂志编辑摘引样式，二者用不同强调色（朱砂/墨灰）区分
- 分享按钮加 `generating` 状态反馈（异步加载图片期间按钮显示"生成中…"，避免用户误以为点击无响应）

**自查发现并修正的高度预算错误**（两遍测量法要求预算阶段与实际绘制阶段的纵向推进量精确一致，逐行核对后发现 3 处真实低估，均已修正）：
- 有图版头：预算 216 vs 实际推进 338，少算 122px
- "方位+彭祖"整块 40px 在预算中完全遗漏（未出现在任何 `h+=` 累加项里）
- 建除详解/星宿歌诀两处摘引区块：预算 40 vs 实际固定开销 56（24px分隔线+32px摘引函数内部间距），各少算 16px
- 另有 3 处发丝分隔线预算 20 vs 实际 22，精确对齐

若不核对直接使用原预算，画布总高度会明显偏矮，导致建除详解/星宿歌诀甚至页脚被裁切到可视区域之外看不到——这类错误不会被语法检查或前端守护抓出，只能靠手工逐行核对预算与绘制两遍的数值一致性。

- 守护：esbuild 解析 OK · null-safety 71 文件 0 违规 · 路由 25 通过
- 纯前端 canvas 绘制重做，未改动数据获取逻辑；图片路径与上轮回复中的 `/ruishou/` 规范完全一致，用户后续放入图片后无需改代码即自动生效

### 每日守护分享图 · 重叠修复 + 杂志感升级 — 完成 (zip 166)
**用户上传截图："70分和麒麟仁兽重叠了，需要优化；内容能不能更丰盛，整个分享页更有设计感，类似杂志和现在的风格柔和到一起"**

**现状核查**：发现当前代码库中 `DailyGuardianPage.jsx` 的 `genShare` 已经是一个比预期更完善的版本（含 `_loadImg` 真实瑖兽图异步加载、"左文右图"杂志封面雏形结构），与截图所示的圆形评分章+垂直堆叠效果不一致——判断截图对应更早版本，不纠结来源，直接对当前最新代码做审查与升级。

**验证方法（非目测猜测）**：环境无法安装 `node-canvas` 做真实像素渲染（需从 nodejs.org 下载编译头文件，不在网络白名单），改为手写一个模拟 canvas 2D context（忠实还原 `fillText`/`measureText`/`arc`/`drawImage` 等调用，记录每次绘制的坐标包围盒），把源码原文注入 Node 环境实际执行，事后检测所有"文字 vs 文字"包围盒是否有几何交集——这是比人工审查代码更可靠的验证方式，直接命中问题的几何本质。

**发现并修复的真实问题**：无图降级版中，46px 大字农历日期（如"五月十八"）与下一行日期信息之间只留 16px 基线间距，对大号衬线字体而言明显不够，实测有 5px 真实重叠区间——已改为 28px 间距消除。同步更新了对应的高度预算换算值（避免预算与实际绘制推进量脱节导致后续内容错位/裁切）。

**杂志感升级（四项）**：
1. **有图版**：瑞兽题名从图片下方独立文字条，改为压在图片底部（渐变蒙层 + 白字），改为真正的杂志封面手法（文字叠加于图，而非图文分离）
2. **无图版**：原纯留白区改为装饰性地支篆字水印圆章（双线圆边框 + 大字地支 + 瑞兽名标注），弥补无真实图片时的视觉空洞感
3. 新增可复用 `drawKicker` 栏目眉标函数（朱砂小字 + 右延伸细线），统一应用于"今日纪要""宜忌提要""十二时辰吉凶"三处内容分区标题，营造编辑设计的节奏感与统一度
4. 全程未引入新的色彩体系或装饰滥用，保持与既有留白+印章+朱砂设计语言一致（用户要求"柔和融合"，非堆砌）

**端到端验证结果**：无图版/有图版两种场景，全部78/77处文字标记之间除4处刻意设计的半透明摘引装饰引号叠加（`drawPullQuote` 内 11% 不透明度背景引号，属经典杂志排版手法，非缺陷）外，**零文字间几何重叠**；高度预算与实际绘制推进量误差稳定在合理余量内（约58px，对应 H 计算中的缓冲项）

- 守护：esbuild 解析 OK · null-safety 71 文件 0 违规 · 路由 25 通过
- 纯前端 canvas 绘制逻辑调整，未触碰引擎/数据层
