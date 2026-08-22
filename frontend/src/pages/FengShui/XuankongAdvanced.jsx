/**
 * XuankongAdvanced.jsx — 玄空飞星高级专业分析面板
 *
 * 展示 5 个最高级专业判断：
 *   1. 零正神（《天玉经》核心）
 *   2. 反伏吟（玄空大忌）
 *   3. 流年紫白叠加（实战应期）
 *   4. 太岁刑冲坐山
 *   5. 收山出煞（形理配合）
 *
 * 这些是普通飞星软件没有的真正高阶内容。
 */
import React from 'react'

const LEVEL_COLOR = {
  'auspicious_great': '#27ae60',
  'auspicious': '#16a085',
  'mixed': '#e67e22',
  'inauspicious': '#c0392b',
  'inauspicious_great': '#8b0000',
  'perfect': '#27ae60',
  'good': '#16a085',
  'bad': '#c0392b',
  'very_bad': '#8b0000',
  'neutral': '#7f8c8d',
}
const LEVEL_LABEL = {
  'auspicious_great': '大吉', 'auspicious': '吉',
  'mixed': '吉凶参半', 'inauspicious': '凶', 'inauspicious_great': '大凶',
  'perfect': '上吉局', 'good': '吉', 'bad': '凶', 'very_bad': '大凶', 'neutral': '平',
}

export default function XuankongAdvanced({ data }) {
  if (!data) return null
  
  return (
    <div className="card" style={{ padding: '1rem 1.15rem', borderLeft: '4px solid #9b59b6' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem' }}>
        <div className="card-title" style={{ marginBottom: 0, color: '#9b59b6' }}>
          🔮 高级专业分析
        </div>
        <div style={{ fontSize: '0.6rem', color: 'var(--text-faint)', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
          《天玉经》《青囊奥语》《章仲山宅断》
        </div>
      </div>
      
      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.85rem',
        fontFamily: 'var(--font-serif)', lineHeight: 1.7, padding: '0.5rem 0.7rem',
        background: 'rgba(155,89,182,0.06)', borderRadius: 'var(--r-sm)' }}>
        以下为玄空派最高级的判断内容，超越简单的"令星到位"层面，
        涉及零正神、反伏吟、流年紫白叠加、太岁刑冲等核心理论。
      </div>
      
      {/* 1. 零正神 */}
      {data.zheng_ling_shen && data.zheng_ling_shen.verdict && (
        <ZhengLingShenCard zl={data.zheng_ling_shen} />
      )}
      
      {/* 2. 反伏吟 */}
      {data.fan_fu_yin && (
        <FanFuYinCard ffy={data.fan_fu_yin} />
      )}
      
      {/* 3. 太岁刑冲 */}
      {data.taisui && (
        <TaisuiCard taisui={data.taisui} year={data.year} />
      )}
      
      {/* 4. 流年警示 */}
      {data.annual_warnings && data.annual_warnings.length > 0 && (
        <AnnualWarningsCard warnings={data.annual_warnings} year={data.year} />
      )}
      
      {/* 5. 收山出煞 */}
      {data.shoushan_chusha && data.shoushan_chusha.items && data.shoushan_chusha.items.length > 0 && (
        <ShoushanChushaCard ssc={data.shoushan_chusha} />
      )}
      
      {/* 6. 金龙四诀（蒋大鸿真传） */}
      {data.jinlong_juejue && (
        <JinlongJueJueCard jl={data.jinlong_juejue} />
      )}
    </div>
  )
}

function JinlongJueJueCard({ jl }) {
  const color = jl.verdict_level === 'auspicious_great' ? '#27ae60'
              : jl.verdict_level === 'auspicious' ? '#16a085'
              : jl.verdict_level === 'mixed' ? '#e67e22'
              : '#c0392b'
  return (
    <SubCard title="⑥ 金龙四诀（蒋大鸿真传）" color={color} source={jl.source}>
      <div style={{ padding: '0.55rem 0.7rem', background: `${color}11`,
        border: `1.5px solid ${color}55`, borderRadius: 'var(--r-sm)',
        marginBottom: '0.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
          flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.3rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>综合评级</span>
          <span style={{ padding: '2px 10px', borderRadius: '12px',
            background: color, color: '#fff', fontWeight: 700, fontSize: '0.78rem',
            fontFamily: 'var(--font-serif)' }}>
            {jl.verdict}
          </span>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        {jl.items.map((it, i) => {
          const c = it.status === 'auspicious_great' ? '#27ae60'
                  : it.status === 'auspicious' ? '#16a085'
                  : it.status === 'mixed' ? '#e67e22'
                  : '#c0392b'
          return (
            <div key={i} style={{ padding: '0.5rem 0.65rem',
              background: `${c}0a`, borderLeft: `3px solid ${c}`,
              borderRadius: 'var(--r-sm)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                marginBottom: '0.25rem', flexWrap: 'wrap', gap: '0.4rem' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: c,
                  fontFamily: 'var(--font-serif)' }}>
                  {it.name}
                </span>
                {it.source && (
                  <span style={{ fontSize: '0.6rem', color: 'var(--text-faint)',
                    fontStyle: 'italic' }}>
                    {it.source}
                  </span>
                )}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)',
                fontFamily: 'var(--font-serif)', lineHeight: 1.7 }}>
                {it.desc}
              </div>
            </div>
          )
        })}
      </div>
    </SubCard>
  )
}

function ZhengLingShenCard({ zl }) {
  const color = LEVEL_COLOR[zl.verdict] || '#7f8c8d'
  return (
    <SubCard title="① 零正神方位（《天玉经》核心）" color={color} source="《天玉经》「正神正位装，拨水入零堂」">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.6rem',
        marginBottom: '0.6rem' }}>
        <div style={{ padding: '0.55rem 0.7rem', background: 'rgba(231,76,60,0.06)',
          borderLeft: '3px solid #e74c3c', borderRadius: 'var(--r-sm)' }}>
          <div style={{ fontSize: '0.62rem', color: '#e74c3c', fontWeight: 700, marginBottom: '2px' }}>
            ⛰ 正神方位（宜见山）
          </div>
          <div style={{ fontSize: '1rem', color: '#e74c3c', fontWeight: 700,
            fontFamily: 'var(--font-display)' }}>
            {zl.zhengshen.zhengshen_dir}
          </div>
          <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>
            {zl.zhengshen.zhengshen_gua}卦 · {zl.zhengshen.zhengshen_num}
          </div>
        </div>
        <div style={{ padding: '0.55rem 0.7rem', background: 'rgba(52,152,219,0.06)',
          borderLeft: '3px solid #3498db', borderRadius: 'var(--r-sm)' }}>
          <div style={{ fontSize: '0.62rem', color: '#3498db', fontWeight: 700, marginBottom: '2px' }}>
            💧 零神方位（宜见水）
          </div>
          <div style={{ fontSize: '1rem', color: '#3498db', fontWeight: 700,
            fontFamily: 'var(--font-display)' }}>
            {zl.zhengshen.lingshen_dir}
          </div>
          <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>
            {zl.zhengshen.lingshen_gua}卦 · {zl.zhengshen.lingshen_num}
          </div>
        </div>
      </div>
      
      {/* 评级 */}
      <div style={{ padding: '0.55rem 0.7rem', background: `${color}11`,
        border: `1.5px solid ${color}55`, borderRadius: 'var(--r-sm)', marginBottom: '0.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>实际坐向评级</span>
          <span style={{
            padding: '2px 10px', borderRadius: '12px',
            background: color, color: '#fff',
            fontWeight: 700, fontSize: '0.78rem', fontFamily: 'var(--font-serif)',
          }}>
            {LEVEL_LABEL[zl.verdict] || zl.verdict}
          </span>
        </div>
        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)',
          fontFamily: 'var(--font-serif)', lineHeight: 1.75 }}>
          {zl.desc}
        </div>
      </div>
      
      {/* 建议 */}
      {zl.advice && zl.advice.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
          {zl.advice.map((a, i) => (
            <div key={i} style={{ fontSize: '0.7rem', color: 'var(--text-secondary)',
              fontFamily: 'var(--font-serif)', paddingLeft: '0.6rem',
              borderLeft: `2px solid ${color}55`, lineHeight: 1.65 }}>
              {a}
            </div>
          ))}
        </div>
      )}
    </SubCard>
  )
}

function FanFuYinCard({ ffy }) {
  if (!ffy.has_fan_fu_yin) {
    return (
      <SubCard title="② 反吟伏吟检测" color="#27ae60" source="《地理辨正·天玉经》">
        <div style={{ padding: '0.55rem 0.7rem', background: 'rgba(39,174,96,0.06)',
          borderLeft: '3px solid #27ae60', borderRadius: 'var(--r-sm)',
          fontSize: '0.78rem', color: '#27ae60', fontFamily: 'var(--font-serif)' }}>
          ✓ 未犯反吟伏吟。家运可正常发展，无停滞或反复之忧。
        </div>
      </SubCard>
    )
  }
  return (
    <SubCard title="② 反吟伏吟检测（玄空大忌）" color="#c0392b" source="《地理辨正·天玉经》「反吟伏吟泪淋淋」">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
        {ffy.patterns.map((p, i) => {
          const c = LEVEL_COLOR[p.level] || '#c0392b'
          return (
            <div key={i} style={{ padding: '0.55rem 0.75rem',
              background: `${c}11`, borderLeft: `3px solid ${c}`,
              borderRadius: 'var(--r-sm)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                marginBottom: '0.3rem', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: c, fontFamily: 'var(--font-serif)' }}>
                  {p.type}
                </span>
                <span style={{ fontSize: '0.65rem', color: 'var(--text-faint)', fontStyle: 'italic' }}>
                  {p.source}
                </span>
              </div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)',
                fontFamily: 'var(--font-serif)', lineHeight: 1.7 }}>
                {p.desc}
              </div>
            </div>
          )
        })}
      </div>
      {ffy.remedy && (
        <div style={{ marginTop: '0.5rem', padding: '0.4rem 0.6rem',
          background: 'rgba(212,160,64,0.06)', borderLeft: '2px solid #d4a040',
          fontSize: '0.7rem', color: '#d4a040', fontFamily: 'var(--font-serif)' }}>
          🛡 化解：{ffy.remedy}
        </div>
      )}
    </SubCard>
  )
}

function TaisuiCard({ taisui, year }) {
  if (!taisui.has_conflict) {
    return (
      <SubCard title={`③ 太岁刑冲（${year} 年太岁 ${taisui.taisui}）`} color="#27ae60" source="《择日要诀》">
        <div style={{ padding: '0.55rem 0.7rem', background: 'rgba(39,174,96,0.06)',
          borderLeft: '3px solid #27ae60', borderRadius: 'var(--r-sm)',
          fontSize: '0.78rem', color: '#27ae60', fontFamily: 'var(--font-serif)' }}>
          ✓ {taisui.desc}
        </div>
      </SubCard>
    )
  }
  const color = LEVEL_COLOR[taisui.level] || '#c0392b'
  return (
    <SubCard title={`③ 太岁刑冲（${year} 年太岁 ${taisui.taisui}）`} color={color} source="《择日要诀》">
      <div style={{ padding: '0.55rem 0.75rem',
        background: `${color}11`, borderLeft: `3px solid ${color}`,
        borderRadius: 'var(--r-sm)' }}>
        <div style={{ fontSize: '0.85rem', fontWeight: 700, color, fontFamily: 'var(--font-serif)',
          marginBottom: '0.3rem' }}>
          ⚠ {taisui.type}（{LEVEL_LABEL[taisui.level]}）
        </div>
        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)',
          fontFamily: 'var(--font-serif)', lineHeight: 1.75, marginBottom: '0.4rem' }}>
          {taisui.desc}
        </div>
        {taisui.remedy && (
          <div style={{ fontSize: '0.7rem', color: '#d4a040', fontFamily: 'var(--font-serif)' }}>
            🛡 化解：{taisui.remedy}
          </div>
        )}
      </div>
    </SubCard>
  )
}

function AnnualWarningsCard({ warnings, year }) {
  // 按 level 分类
  const aus = warnings.filter(w => w.level.startsWith('auspicious'))
  const inaus = warnings.filter(w => w.level.startsWith('inauspicious'))
  
  return (
    <SubCard title={`④ ${year} 年流年紫白叠加（飞星 + 流年）`} color="#9b59b6" source="《沈氏玄空学·流年紫白》">
      {aus.length > 0 && (
        <>
          <div style={{ fontSize: '0.7rem', color: '#27ae60', fontWeight: 700, marginBottom: '0.3rem' }}>
            ✓ 流年吉位（{aus.length}）
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginBottom: '0.5rem' }}>
            {aus.map((w, i) => {
              const c = LEVEL_COLOR[w.level] || '#27ae60'
              return (
                <div key={i} style={{ padding: '0.4rem 0.55rem',
                  background: `${c}0a`, borderLeft: `2px solid ${c}`,
                  borderRadius: 'var(--r-sm)' }}>
                  <div style={{ fontSize: '0.72rem', fontWeight: 600, color: c, fontFamily: 'var(--font-serif)' }}>
                    {w.title}
                  </div>
                  <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)',
                    fontFamily: 'var(--font-serif)', lineHeight: 1.55, marginTop: '2px' }}>
                    {w.desc}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
      
      {inaus.length > 0 && (
        <>
          <div style={{ fontSize: '0.7rem', color: '#c0392b', fontWeight: 700, marginBottom: '0.3rem' }}>
            ⚠ 流年凶位（{inaus.length}）
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            {inaus.map((w, i) => {
              const c = LEVEL_COLOR[w.level] || '#c0392b'
              return (
                <div key={i} style={{ padding: '0.4rem 0.55rem',
                  background: `${c}0a`, borderLeft: `2px solid ${c}`,
                  borderRadius: 'var(--r-sm)' }}>
                  <div style={{ fontSize: '0.72rem', fontWeight: 600, color: c, fontFamily: 'var(--font-serif)' }}>
                    {w.title}
                  </div>
                  <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)',
                    fontFamily: 'var(--font-serif)', lineHeight: 1.55, marginTop: '2px' }}>
                    {w.desc}
                  </div>
                  {w.remedy && (
                    <div style={{ fontSize: '0.62rem', color: '#d4a040',
                      fontFamily: 'var(--font-serif)', marginTop: '2px' }}>
                      🛡 {w.remedy}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </SubCard>
  )
}

function ShoushanChushaCard({ ssc }) {
  return (
    <SubCard title="⑤ 收山出煞（形理配合）" color="#16a085" source="《沈氏玄空学·形理》">
      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.4rem',
        fontFamily: 'var(--font-serif)', lineHeight: 1.65 }}>
        玄空理论必须配合实际形势：山星到坐宜见山（收山旺丁），向星到向宜见水（出煞旺财）。
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        {ssc.items.map((it, i) => {
          const c = LEVEL_COLOR[it.level] || '#16a085'
          return (
            <div key={i} style={{ padding: '0.5rem 0.7rem',
              background: `${c}0a`, borderLeft: `3px solid ${c}`,
              borderRadius: 'var(--r-sm)' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: c,
                fontFamily: 'var(--font-serif)', marginBottom: '0.3rem' }}>
                {it.type}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)',
                fontFamily: 'var(--font-serif)', lineHeight: 1.7 }}>
                {it.desc}
              </div>
              {it.advice && (
                <div style={{ fontSize: '0.66rem', color: '#d4a040',
                  fontFamily: 'var(--font-serif)', marginTop: '0.25rem', fontStyle: 'italic' }}>
                  ▸ {it.advice}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </SubCard>
  )
}

function SubCard({ title, color, source, children }) {
  return (
    <div style={{ marginBottom: '0.85rem',
      padding: '0.75rem 0.9rem', background: 'var(--bg-raised)',
      border: `1px solid ${color}33`, borderRadius: 'var(--r-md)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        marginBottom: '0.55rem', borderBottom: `1px dashed ${color}33`, paddingBottom: '0.3rem',
        gap: '0.5rem', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.85rem', fontWeight: 700, color, fontFamily: 'var(--font-serif)' }}>
          {title}
        </span>
        {source && (
          <span style={{ fontSize: '0.6rem', color: 'var(--text-faint)',
            fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
            {source}
          </span>
        )}
      </div>
      {children}
    </div>
  )
}
