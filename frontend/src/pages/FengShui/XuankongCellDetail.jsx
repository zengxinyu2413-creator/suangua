/**
 * XuankongCellDetail.jsx — 玄空双星汇宫详解
 *
 * 玄空学最核心的判读法：每宫两星（山+向）的组合，
 * 决定该宫的具体吉凶。
 *
 * 参考典籍：
 *   - 《玄空秘旨》（蒋大鸿）— 双星组合的吉凶诀
 *   - 《紫白诀》— 二星同宫的具体应验
 *   - 《飞星赋》— 各种特殊组合
 *   - 《沈氏玄空学》— 沈竹礽集大成
 *
 * 每个组合包含：
 *   - 吉凶定性
 *   - 应事（健康、财运、人丁、官非等）
 *   - 古书原文
 *   - 化解建议
 */
import React, { useState } from 'react'

// 81 种双星汇宫组合（9×9）— 选最重要的常用组合
// 格式：'山-向': {评价, 应事, 古书原文, 化解}
const STAR_COMBINATIONS = {
  // ═══ 一白水星 ═══
  '1-1': { level: 'mixed', name: '比和水旺', event: '聪明文秀，但旺极反凶',
    classic: '《玄空秘旨》：一白比和，文章显达；旺水须防泛滥成灾。',
    remedy: '宜见动水（流水、喷泉）旺财，忌死水或大水冲射。' },
  '1-2': { level: 'inauspicious', name: '土克水·中男遇病符', event: '中男主健康不佳、肾病、泌尿系统、耳疾',
    classic: '《紫白诀》：黑白同来，发科甲之名（旧运吉）；但今时则土水相战。',
    remedy: '挂金属铜铃化二黑病气，忌摆放黄色饰物（增土）。' },
  '1-3': { level: 'inauspicious', name: '水木相生·官非斗讼', event: '主口舌官非、贼盗、刑伤、肝胆病',
    classic: '《玄空秘旨》：碧水汪洋，主刑妻而瞎眼。',
    remedy: '宜用红色（火）通关泄木气，避免摆放绿色植物或木材家具。' },
  '1-4': { level: 'auspicious', name: '文昌大利·一四同宫', event: '主聪明、考试、文笔、桃花、出贵',
    classic: '《玄空秘旨》：一四同宫，准发科名之显；蓬莱仙馆，文人致富。',
    remedy: '此方位最宜置书桌、文昌塔，能催发学业事业。但需防一四过旺生桃花。' },
  '1-5': { level: 'inauspicious_great', name: '水土相战·中男大病', event: '主膀胱病、肾病、耳聋、性病、中男遭厄',
    classic: '《紫白诀》：五黄到处，殃及池鱼；一五同宫，无极天罡，疾病丛生。',
    remedy: '速摆金属六帝古钱+铜葫芦，化五黄煞；忌动土翻修。' },
  '1-6': { level: 'auspicious', name: '金生水·官贵亨通', event: '主升官晋职、官贵扶持、文武全才',
    classic: '《玄空秘旨》：六白配一白，名「金水相涵」，主官星显赫。',
    remedy: '宜置文房、书柜，可大力催官，开运效果极佳。' },
  '1-7': { level: 'mixed', name: '水金相生·桃花酒色', event: '主桃花、酒色、口才（吉时为外交）',
    classic: '《飞星赋》：一七同宫，桃花泛滥；当令为艺术外交，失令为偷情。',
    remedy: '当运为利偏财、艺术；失运则需化以白瓷器+清水（防酒色乱性）。' },
  '1-8': { level: 'auspicious_great', name: '水土相济·财禄丰盈', event: '主大发财禄、置业添丁、家庭和睦',
    classic: '《玄空秘旨》：八白配一白，土水相涵，主田产丰盈。',
    remedy: '九运虽非八之运，但1-8组合仍为吉，可置鱼缸或瓷器以加强。' },
  '1-9': { level: 'auspicious_great', name: '水火既济·当令大吉', event: '九运中此组合最旺，主升官发财、贵显双全',
    classic: '《玄空秘旨》：九紫离明，配以坎水，水火既济，乃富贵之征。',
    remedy: '九运中此方位为最旺，宜常开窗、置明灯，催财催贵。' },
  
  // ═══ 二黑土星 ═══
  '2-2': { level: 'inauspicious_great', name: '土土比和·病符叠至', event: '主大病、女眷遭灾、寡妇当家',
    classic: '《紫白诀》：二黑飞临，主病符；二二同宫，连绵卧床。',
    remedy: '速挂金属铜葫芦、风铃，化病气；忌见黄土、陶瓷重物。' },
  '2-3': { level: 'inauspicious', name: '斗牛煞·斗讼破财', event: '主官司、口舌、母子不和、肠胃病',
    classic: '《玄空秘旨》：斗牛相会，必动干戈；二三同宫，是非纷争。',
    remedy: '红色物品通关化解，忌见黄绿配色。' },
  '2-4': { level: 'inauspicious', name: '风土相战·女姑不睦', event: '主婆媳不和、女性疾病、流产、不孕',
    classic: '《飞星赋》：风行地上，决主丰隆；但二四同宫，主母婆不睦。',
    remedy: '金属饰物泄土生水，化解女性病气。' },
  '2-5': { level: 'inauspicious_great', name: '二五交加·大病横死', event: '玄空最大凶组合，主重病、绝症、家破人亡',
    classic: '《紫白诀》：二五交加，罹死亡并生疾病；运行至此，吉者亦凶。',
    remedy: '【最严重】速用六帝古钱+铜葫芦+金属六字真言，必要时此方位避不居住。' },
  '2-6': { level: 'mixed', name: '土生金·得财但艰', event: '当令主财禄，失令主疲劳病变',
    classic: '《玄空秘旨》：天乙天德，福寿康宁；二六合十，富贵悠久（合十时）。',
    remedy: '九运中二六非吉非凶，可置金属财位摆件。' },
  '2-7': { level: 'inauspicious', name: '火土相生·先后天数', event: '主红伤、口腔病、女性损伤、官非',
    classic: '《飞星赋》：交剑煞兴多劫掠，斗牛祸起惹官刑。',
    remedy: '水化火气，避开此方位的明火。' },
  '2-8': { level: 'mixed', name: '土土比和·田产之利', event: '主地产、房屋、农业之利，但慢',
    classic: '《玄空秘旨》：八白助二黑，田产丰盈，但土厚滞重。',
    remedy: '九运中宜泄不宜助，可置白色金属化重土。' },
  '2-9': { level: 'inauspicious', name: '火土相生·二黑得火生', event: '九运中二黑反得火生而旺，主病符炽盛',
    classic: '《飞星赋》：火炎土燥，二黑得令；流产损丁，须防孕妇。',
    remedy: '【九运重点防范】此方位忌住人，尤其孕妇；速用金属铜钟+流水化解。' },
  
  // ═══ 三碧木星 ═══
  '3-3': { level: 'inauspicious', name: '震木重重·斗讼频仍', event: '主官非、口舌、震雷之灾、长子有难',
    classic: '《玄空秘旨》：碧绿相加，盗贼斗讼。',
    remedy: '红色化木气，忌植绿。' },
  '3-4': { level: 'inauspicious', name: '风木相争·疯狂自缢', event: '主精神病、自杀、家人离散',
    classic: '《飞星赋》：风行地而硬直当庭，体仁旧德；但木重而无金制，主疯癫。',
    remedy: '速以金属化木，忌摆木刻或绿植。' },
  '3-5': { level: 'inauspicious_great', name: '震雷遇五黄·绝命横祸', event: '主突发横祸、车祸、绝症',
    classic: '《紫白诀》：三五同宫，必出震雷之祸。',
    remedy: '【严重】铜葫芦、六字真言、金属六帝古钱齐用。' },
  '3-6': { level: 'inauspicious', name: '金克木·伤足肝病', event: '主长男车祸、手足伤、肝胆病',
    classic: '《玄空秘旨》：足以金而蹒跚；六三同宫，伤丁损财。',
    remedy: '水通关，化金生木。' },
  '3-7': { level: 'inauspicious', name: '穿心煞·盗贼血光', event: '主盗贼、车祸、肺病、官非',
    classic: '《玄空秘旨》：劫盗更见官灾，因穿心煞之力。',
    remedy: '红色帘幕，水汽化解。' },
  '3-8': { level: 'inauspicious', name: '木克土·小口损伤', event: '主小孩损伤、跌伤、家宅不安',
    classic: '《飞星赋》：青楼染疾，因星阴会，木旺克八白。',
    remedy: '红色饰物化木气。' },
  '3-9': { level: 'auspicious', name: '木火通明·聪明文秀', event: '九运中三九组合为吉，主聪明、文采、声名',
    classic: '《玄空秘旨》：木见离而生火，名为木火通明，主文章魁元。',
    remedy: '九运中此方位宜置书画、文具，催文章贵气。' },
  
  // ═══ 四绿木星 ═══
  '4-4': { level: 'mixed', name: '巽木重重·风过盈虚', event: '当令主文秀，失令主荡子妓女',
    classic: '《玄空秘旨》：木旺无金制，男女偷淫；四绿独显，文秀风流。',
    remedy: '金属化木，红色明火助文气。' },
  '4-5': { level: 'inauspicious_great', name: '巽风遇五黄·女人灾病', event: '主孕妇流产、乳腺病、女性绝症',
    classic: '《紫白诀》：四五同宫，主孕妇大病。',
    remedy: '【严重】速以金属化五黄，孕妇避开此位。' },
  '4-6': { level: 'inauspicious', name: '金木交战·长女伤', event: '主长女、长媳遭难，乳腺病、肝病',
    classic: '《玄空秘旨》：风金相战，肝胆病、男女不和。',
    remedy: '水通关。' },
  '4-7': { level: 'inauspicious', name: '酉风刀剑·桃花血光', event: '主桃花破财、刀伤、女命被害',
    classic: '《飞星赋》：辛卯逢酉，七四同宫，会血光之灾。',
    remedy: '红色化金气，黄玉饰品化煞。' },
  '4-8': { level: 'mixed', name: '风山相薄·儿童不利', event: '主小孩学业，但木克土仍主病',
    classic: '《玄空秘旨》：山风蛊也，儿童脾胃不和。',
    remedy: '红色明火化木助土。' },
  '4-9': { level: 'auspicious', name: '木火通明·文章显达', event: '九运中文昌大吉，主出贵子、考试中举',
    classic: '《玄空秘旨》：木入离乡，必得贵子；九紫文星，四绿文昌，双合大利。',
    remedy: '九运此位置最宜置书桌、文房，催发科名最强。' },
  
  // ═══ 五黄土 ═══
  '5-5': { level: 'inauspicious_great', name: '五黄双叠·至凶之地', event: '玄空最凶，主家破人亡、突发横祸',
    classic: '《紫白诀》：五黄正煞，不拘临方到向，均凶。',
    remedy: '【极凶】此宫位必须空置，不可开门、不可作卧室，速以铜钟+葫芦化解。' },
  '5-6': { level: 'inauspicious', name: '土生金·五黄克长男', event: '主头部病、长男头痛、官非',
    classic: '《玄空秘旨》：五六同宫，老父长男头痛。',
    remedy: '金属泄土气。' },
  '5-7': { level: 'inauspicious', name: '五黄遇七赤·火灾', event: '主火灾、口腔病、肺病、小女横祸',
    classic: '《飞星赋》：五七同宫，赤连碧紫，伤丁口。',
    remedy: '水化火气，金属化五黄。' },
  '5-8': { level: 'inauspicious', name: '土土叠加·迟钝病重', event: '土性沉重病气重，主慢性病',
    classic: '《玄空秘旨》：五八同宫，五黄强，土重难化。',
    remedy: '金属铜钟泄气。' },
  '5-9': { level: 'inauspicious_great', name: '火助五黄·凶上加凶', event: '九运中此为大凶，主大火、血光、绝症',
    classic: '《紫白诀》：五九同宫，紫黄毒药，邻宫尤忌。',
    remedy: '【九运重点防范】此方位必须避开，速以金属六帝古钱+水帘化解。' },
  
  // ═══ 六白金星 ═══
  '6-6': { level: 'mixed', name: '乾金双叠·武贵', event: '当令为武贵权威，失令为伤丁',
    classic: '《玄空秘旨》：六白比和，权位显达；旺极反招忌妒。',
    remedy: '水泄金气，红色化煞。' },
  '6-7': { level: 'inauspicious', name: '交剑煞·官非伤丁', event: '主官非、车祸、刀伤、兄弟阋墙',
    classic: '《飞星赋》：交剑煞兴多劫掠。',
    remedy: '【凶】速以水化解，避免金属饰物。' },
  '6-8': { level: 'auspicious', name: '金土相生·田产添丁', event: '主进田置业、添丁旺人',
    classic: '《玄空秘旨》：六八同宫，名为「武曲扶辅」，田产兴隆。',
    remedy: '宜置金属或瓷器，财位之上吉。' },
  '6-9': { level: 'inauspicious', name: '火克金·头疼脑热', event: '主头部病、心脏病、肺病',
    classic: '《飞星赋》：火烧天门，主家长有难。',
    remedy: '土通关，黄色饰物化解。' },
  
  // ═══ 七赤金星 ═══
  '7-7': { level: 'mixed', name: '兑金重重·当令主财', event: '当令时大发横财，失令主官非破财',
    classic: '《玄空秘旨》：七赤为先天火数，逢九紫为发禄之神。',
    remedy: '九运中七已退气，宜置水盆泄金气。' },
  '7-8': { level: 'auspicious', name: '金土相生·小口添丁', event: '主财禄、添丁、少男喜事',
    classic: '《飞星赋》：辅临七赤，三阳开泰。',
    remedy: '当运吉，可置陶瓷或铜器。' },
  '7-9': { level: 'inauspicious', name: '火烧丽宅·火灾血光', event: '主火灾、肺病、心脏病、小女血光',
    classic: '《飞星赋》：午酉逢而江湖花酒；七九合辙，火照天门，必当吐血。',
    remedy: '【火灾警示】速以水帘+金属化解，忌见明火。' },
  
  // ═══ 八白土星 ═══
  '8-8': { level: 'auspicious', name: '艮土比和·财禄堆叠', event: '八运中最旺，九运虽退仍为吉',
    classic: '《玄空秘旨》：八白比和，金玉满堂。',
    remedy: '宜置陶瓷或山石装饰，催财效果显著。' },
  '8-9': { level: 'auspicious_great', name: '火土相生·当令大吉', event: '九运中八九组合极旺，主大发财禄、贵显双全',
    classic: '《玄空秘旨》：九紫合八白，丁财两旺，贵不可言。',
    remedy: '九运此方位为天财位，最宜开窗、置明灯、置财位摆件。' },
  
  // ═══ 九紫火星 ═══
  '9-9': { level: 'auspicious_great', name: '九紫双叠·当令至旺', event: '九运中九九组合至旺，主大富大贵、文章显达',
    classic: '《玄空秘旨》：九紫离明，灯火辉煌，文章魁元。',
    remedy: '【九运最旺】此方位为本运正神，宜开门、置明灯、催财催贵。' },
}

// 自动反向查询：用 min-max 顺序
function getCombination(mountain, facing, palaceJudgments = null, pos = null) {
  // 优先用后端的 palace_judgments（专业版 81 组合断语）
  if (palaceJudgments && pos && palaceJudgments[pos]) {
    const p = palaceJudgments[pos]
    if (p.short) {
      return {
        level: p.nature || 'neutral',
        name: p.short,
        event: p.detailed || '',
        classic: p.source || '',
        remedy: '', // backend 暂无 remedy 字段
        // 高级专业字段
        health: p.health,
        wealth: p.wealth,
        relationships: p.relationships,
        wuxing_interaction: p.wuxing_interaction,
        from_backend: true,
      }
    }
  }
  // 回退到前端表
  const key1 = `${mountain}-${facing}`
  const key2 = `${facing}-${mountain}`
  return STAR_COMBINATIONS[key1] || STAR_COMBINATIONS[key2] || null
}

const LEVEL_META = {
  'auspicious_great': { color: '#27ae60', label: '大吉' },
  'auspicious':       { color: '#16a085', label: '吉' },
  'mixed':            { color: '#e67e22', label: '吉凶参半' },
  'inauspicious':     { color: '#c0392b', label: '凶' },
  'inauspicious_great': { color: '#8b0000', label: '大凶' },
}

const LUOSHU_GRID = [
  [4, 9, 2],
  [3, 5, 7],
  [8, 1, 6],
]

const POS_TO_DIR = {
  1:'北', 2:'西南', 3:'东', 4:'东南',
  5:'中', 6:'西北', 7:'西', 8:'东北', 9:'南',
}

export default function XuankongCellDetail({ data }) {
  const [selectedPos, setSelectedPos] = useState(null)
  
  if (!data || !data.combined) return null
  
  const sittingLuoshu = ({ '坎':1,'坤':2,'震':3,'巽':4,'乾':6,'兑':7,'艮':8,'离':9 })[data.sitting_gua]
  const facingLuoshu = ({ '坎':1,'坤':2,'震':3,'巽':4,'乾':6,'兑':7,'艮':8,'离':9 })[data.facing_gua]
  
  return (
    <div className="card" style={{ padding: '1rem 1.1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
        <div className="card-title" style={{ marginBottom: 0 }}>九宫双星汇宫详解</div>
        <div style={{ fontSize: '0.6rem', color: 'var(--text-faint)', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
          点击宫位查看详解 · 《玄空秘旨》《紫白诀》《飞星赋》
        </div>
      </div>
      
      {/* 顶部：9 宫位简版（不带星）+ 吉凶色 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '4px',
        maxWidth: '380px', margin: '0 auto 0.7rem' }}>
        {LUOSHU_GRID.flat().map(pos => {
          const cell = data.combined[pos]
          if (!cell) return <div key={pos} />
          const combo = getCombination(cell.mountain, cell.facing, data.palace_judgments, pos)
          const meta = combo ? LEVEL_META[combo.level] : { color: 'var(--text-faint)', label: '—' }
          const isSelected = pos === selectedPos
          const isSitting = pos === sittingLuoshu
          const isFacing = pos === facingLuoshu
          
          return (
            <button key={pos}
              onClick={() => setSelectedPos(isSelected ? null : pos)}
              style={{
                aspectRatio: '1', padding: '0.45rem 0.3rem',
                background: isSelected ? `${meta.color}33` : `${meta.color}10`,
                border: `${isSelected ? 2 : 1}px solid ${isSelected ? meta.color : `${meta.color}44`}`,
                borderRadius: 'var(--r-md)',
                cursor: 'pointer', textAlign: 'center',
                display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '0.1rem',
                outline: isSitting || isFacing ? '2px solid var(--accent)' : 'none',
                outlineOffset: '-2px',
              }}>
              <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>
                {cell.direction}
              </div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem',
                fontWeight: 700, color: meta.color, lineHeight: 1 }}>
                {cell.mountain}-{cell.facing}
              </div>
              <div style={{ fontSize: '0.62rem', color: meta.color, fontWeight: 700,
                fontFamily: 'var(--font-serif)' }}>
                {meta.label}
              </div>
              {(isSitting || isFacing) && (
                <div style={{ fontSize: '0.55rem', color: 'var(--accent)', fontWeight: 700 }}>
                  {isSitting && isFacing ? '坐+向' : isSitting ? '坐山' : '朝向'}
                </div>
              )}
            </button>
          )
        })}
      </div>
      
      {/* 选中宫位详解 */}
      {selectedPos && (() => {
        const cell = data.combined[selectedPos]
        const combo = getCombination(cell.mountain, cell.facing, data.palace_judgments, selectedPos)
        if (!combo) {
          return (
            <div style={{
              padding: '0.85rem 1rem',
              background: 'var(--bg-subtle)', borderRadius: 'var(--r-md)',
              fontSize: '0.78rem', color: 'var(--text-muted)',
              fontFamily: 'var(--font-serif)', lineHeight: 1.7,
            }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent)',
                marginBottom: '0.4rem' }}>
                {cell.direction}方 · 山{cell.mountain} 向{cell.facing} 运{cell.yun}
              </div>
              此组合未在常见判语中收录，需结合三元九运综合判读。
              一般而言，当令星到此为吉，失令星到此为凶。
            </div>
          )
        }
        
        const meta = LEVEL_META[combo.level]
        
        return (
          <div style={{
            padding: '0.85rem 1rem',
            background: `${meta.color}0a`, border: `1px solid ${meta.color}44`,
            borderLeft: `3px solid ${meta.color}`,
            borderRadius: 'var(--r-md)',
            display: 'flex', flexDirection: 'column', gap: '0.6rem',
          }}>
            {/* 标题 */}
            <div style={{ display: 'flex', justifyContent: 'space-between',
              alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)',
                  fontFamily: 'var(--font-serif)' }}>
                  {cell.direction}方 · 山{cell.mountain} ↔ 向{cell.facing}（运{cell.yun}）
                </div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: meta.color,
                  marginTop: '0.1rem', fontFamily: 'var(--font-serif)' }}>
                  {combo.name}
                </div>
              </div>
              <div style={{
                padding: '4px 12px', borderRadius: '14px',
                background: `${meta.color}22`, border: `1px solid ${meta.color}`,
                color: meta.color, fontWeight: 700, fontSize: '0.85rem',
                fontFamily: 'var(--font-serif)',
              }}>
                {meta.label}
              </div>
            </div>
            
            {/* 应事 */}
            <div>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-faint)',
                fontFamily: 'var(--font-serif)', marginBottom: '0.2rem' }}>
                ✦ 应事征象
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)',
                lineHeight: 1.7, fontFamily: 'var(--font-serif)' }}>
                {combo.event}
              </div>
            </div>
            
            {/* 三大应事专项（来自 backend 专业版） */}
            {combo.from_backend && (combo.health || combo.wealth || combo.relationships) && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                gap: '0.4rem' }}>
                {combo.health && (
                  <div style={{ padding: '0.4rem 0.55rem', background: 'rgba(231,76,60,0.06)',
                    borderLeft: '2px solid #e74c3c', borderRadius: '4px' }}>
                    <div style={{ fontSize: '0.62rem', color: '#e74c3c', fontWeight: 700, marginBottom: '2px' }}>
                      🩺 健康
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)',
                      fontFamily: 'var(--font-serif)', lineHeight: 1.55 }}>
                      {combo.health}
                    </div>
                  </div>
                )}
                {combo.wealth && (
                  <div style={{ padding: '0.4rem 0.55rem', background: 'rgba(212,160,64,0.06)',
                    borderLeft: '2px solid #d4a040', borderRadius: '4px' }}>
                    <div style={{ fontSize: '0.62rem', color: '#d4a040', fontWeight: 700, marginBottom: '2px' }}>
                      💰 财运
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)',
                      fontFamily: 'var(--font-serif)', lineHeight: 1.55 }}>
                      {combo.wealth}
                    </div>
                  </div>
                )}
                {combo.relationships && (
                  <div style={{ padding: '0.4rem 0.55rem', background: 'rgba(155,89,182,0.06)',
                    borderLeft: '2px solid #9b59b6', borderRadius: '4px' }}>
                    <div style={{ fontSize: '0.62rem', color: '#9b59b6', fontWeight: 700, marginBottom: '2px' }}>
                      👥 人际
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)',
                      fontFamily: 'var(--font-serif)', lineHeight: 1.55 }}>
                      {combo.relationships}
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {/* 五行生克 */}
            {combo.wuxing_interaction && combo.wuxing_interaction.relation !== '无' && (
              <div style={{ padding: '0.45rem 0.65rem', background: 'rgba(52,152,219,0.06)',
                borderLeft: '2px solid #3498db', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.62rem', color: '#3498db', fontWeight: 700, marginBottom: '2px' }}>
                  ☯ 五行 · {combo.wuxing_interaction.relation}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)',
                  fontFamily: 'var(--font-serif)', lineHeight: 1.6 }}>
                  {combo.wuxing_interaction.direction} — {combo.wuxing_interaction.desc}
                </div>
              </div>
            )}
            
            {/* 古书原文 */}
            <div style={{ padding: '0.5rem 0.7rem',
              background: 'rgba(212,160,64,0.05)',
              borderLeft: '2px solid var(--accent)',
              borderRadius: '4px',
            }}>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-faint)',
                fontFamily: 'var(--font-serif)', marginBottom: '0.2rem' }}>
                ✦ 典籍原文
              </div>
              <div style={{ fontSize: '0.76rem', color: 'var(--accent)',
                lineHeight: 1.75, fontFamily: 'var(--font-serif)',
                fontStyle: 'italic' }}>
                {combo.classic}
              </div>
            </div>
            
            {/* 化解建议 */}
            <div>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-faint)',
                fontFamily: 'var(--font-serif)', marginBottom: '0.2rem' }}>
                ✦ 化解之法
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)',
                lineHeight: 1.7, fontFamily: 'var(--font-serif)' }}>
                {combo.remedy}
              </div>
            </div>
          </div>
        )
      })()}
      
      {!selectedPos && (
        <div style={{
          padding: '0.6rem 0.8rem',
          background: 'var(--bg-subtle)', borderRadius: 'var(--r-sm)',
          fontSize: '0.7rem', color: 'var(--text-muted)',
          textAlign: 'center', fontFamily: 'var(--font-serif)',
        }}>
          点击上方任一宫位查看双星汇宫详解
        </div>
      )}
      
      {/* 通用判读说明 */}
      <div style={{
        marginTop: '0.65rem', padding: '0.5rem 0.7rem',
        background: 'var(--bg-subtle)', borderRadius: 'var(--r-sm)',
        fontSize: '0.66rem', color: 'var(--text-muted)',
        fontFamily: 'var(--font-serif)', lineHeight: 1.7,
      }}>
        <div style={{ marginBottom: '0.25rem' }}>
          <span style={{ color: 'var(--accent)', fontWeight: 700 }}>判读心法</span>：
          双星组合「山-向」并非简单数字加减，而是按《玄空秘旨》《飞星赋》古书所定的固定吉凶组合。
        </div>
        <div>
          <span style={{ color: 'var(--accent)', fontWeight: 700 }}>九运重点</span>：
          九紫离火当令（2024-2043），含 9 之组合多吉；含 5 黄、2 黑之组合多凶。
        </div>
      </div>
    </div>
  )
}
