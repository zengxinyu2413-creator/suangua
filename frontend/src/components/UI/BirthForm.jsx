import React, { useState, useEffect } from 'react'

// ─── Province / city quick-select ────────────────────────────────────────────
// Major provinces + direct-controlled municipalities only (for brevity)
const PROVINCES = [
  '北京','天津','上海','重庆',
  '河北','山西','辽宁','吉林','黑龙江',
  '江苏','浙江','安徽','福建','江西','山东',
  '河南','湖北','湖南','广东','海南',
  '四川','贵州','云南','陕西','甘肃','青海',
  '内蒙古','广西','西藏','宁夏','新疆',
  '香港','澳门','台湾',
]

// ─── Lunar months (including leap month option) ───────────────────────────────
const LUNAR_MONTHS = [
  {v:1,  l:'正月（一月）'},
  {v:2,  l:'二月'},
  {v:3,  l:'三月'},
  {v:4,  l:'四月'},
  {v:5,  l:'五月'},
  {v:6,  l:'六月'},
  {v:7,  l:'七月'},
  {v:8,  l:'八月'},
  {v:9,  l:'九月'},
  {v:10, l:'十月'},
  {v:11, l:'十一月'},
  {v:12, l:'腊月（十二月）'},
]

const SOLAR_MONTH_DAYS = [0,31,29,31,30,31,30,31,31,30,31,30,31]

/**
 * BirthForm — unified date + location input
 *
 * values shape:
 *   { year, month, day, hour, minute, gender,
 *     is_lunar, is_leap_month, province, city }
 *
 * Defaults: is_lunar=true (农历 is the primary input)
 */
export default function BirthForm({
  values,
  onChange,
  showGender   = true,
  showLocation = true,
  title        = '出生信息',
}) {
  const set = (k, v) => onChange({ ...values, [k]: (typeof v === 'boolean' ? v : (Number(v) || v)) })

  const isLunar    = values.is_lunar    !== false   // default true
  const isLeap     = values.is_leap_month === true
  const maxDay     = isLunar ? 30 : (SOLAR_MONTH_DAYS[values.month] || 31)

  // Clamp day when month changes
  useEffect(() => {
    if (values.day > maxDay) onChange({ ...values, day: maxDay })
  }, [values.month, isLunar, maxDay])

  return (
    <div className="card">
      <div className="card-title">{title}</div>

      {/* ── Calendar mode toggle ── */}
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between',
                    marginBottom:'0.85rem' }}>
        <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)',
                       letterSpacing:'0.06em', textTransform:'uppercase', fontWeight:600 }}>
          历法
        </span>
        <div style={{ display:'flex', gap:'3px', background:'var(--bg-subtle)',
                      borderRadius:'var(--r-sm)', padding:'3px' }}>
          {[
            { v: true,  l: '农历（阴历）' },
            { v: false, l: '公历（阳历）' },
          ].map(({ v, l }) => (
            <button
              key={String(v)}
              onClick={() => onChange({ ...values, is_lunar: v, is_leap_month: false })}
              style={{
                padding: '4px 12px', borderRadius:0, border: 'none',
                background: isLunar === v ? 'var(--surface)' : 'transparent',
                color:      isLunar === v ? 'var(--accent)'  : 'var(--text-muted)',
                fontWeight: isLunar === v ? 600 : 400,
                fontSize: 'var(--text-xs)', cursor: 'pointer',
                boxShadow: isLunar === v ? 'var(--shadow-xs)' : 'none',
                transition: 'all var(--t-fast)',
              }}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      {/* ── Year / Month / Day ── */}
      <div className="form-row" style={{ gridTemplateColumns:'1fr 1fr 1fr' }}>
        <div className="form-group">
          <label>{isLunar ? '农历年' : '公历年'}</label>
          <input type="number" min="1900" max="2100" value={values.year}
            onChange={e => set('year', e.target.value)} />
        </div>

        <div className="form-group">
          <label>{isLunar ? '农历月' : '公历月'}</label>
          {isLunar ? (
            <select value={values.month} onChange={e => set('month', e.target.value)}>
              {LUNAR_MONTHS.map(m => (
                <option key={m.v} value={m.v}>{m.l}</option>
              ))}
            </select>
          ) : (
            <select value={values.month} onChange={e => set('month', e.target.value)}>
              {Array.from({ length:12 }, (_,i) => (
                <option key={i+1} value={i+1}>{i+1} 月</option>
              ))}
            </select>
          )}
        </div>

        <div className="form-group">
          <label>{isLunar ? '农历日' : '公历日'}</label>
          <input type="number" min="1" max={maxDay} value={values.day}
            onChange={e => set('day', e.target.value)} />
        </div>
      </div>

      {/* ── Leap month checkbox (lunar only) ── */}
      {isLunar && (
        <div style={{ display:'flex', alignItems:'center', gap:'0.5rem',
                      marginTop:'0.4rem', marginBottom:'0.2rem' }}>
          <label style={{
            display:'flex', alignItems:'center', gap:'0.45rem',
            fontSize:'var(--text-xs)', color:'var(--text-muted)',
            cursor:'pointer', userSelect:'none',
          }}>
            <input
              type="checkbox"
              checked={isLeap}
              onChange={e => onChange({ ...values, is_leap_month: e.target.checked })}
              style={{ width:14, height:14, accentColor:'var(--accent)', cursor:'pointer' }}
            />
            <span>闰月（当年有闰{values.month}月时勾选）</span>
          </label>
        </div>
      )}

      {/* ── Hour / Minute ── */}
      <div className="form-row" style={{ gridTemplateColumns:'1fr 1fr', marginTop:'0.75rem' }}>
        <div className="form-group">
          <label>时辰 Hour (0–23)</label>
          <select value={values.hour} onChange={e => set('hour', e.target.value)}>
            {[
              [0,'子时 (23-1点)'],[1,'子时'],[2,'丑时 (1-3点)'],[3,'丑时'],
              [4,'寅时 (3-5点)'],[5,'寅时'],[6,'卯时 (5-7点)'],[7,'卯时'],
              [8,'辰时 (7-9点)'],[9,'辰时'],[10,'巳时 (9-11点)'],[11,'巳时'],
              [12,'午时 (11-13点)'],[13,'午时'],[14,'未时 (13-15点)'],[15,'未时'],
              [16,'申时 (15-17点)'],[17,'申时'],[18,'酉时 (17-19点)'],[19,'酉时'],
              [20,'戌时 (19-21点)'],[21,'戌时'],[22,'亥时 (21-23点)'],[23,'亥时'],
            ].map(([h, label]) => (
              <option key={h} value={h}>{h}:00 {label}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>分 Minute</label>
          <input type="number" min="0" max="59" value={values.minute || 0}
            onChange={e => set('minute', e.target.value)} />
        </div>
      </div>

      {/* ── Gender ── */}
      {showGender && (
        <div className="form-group" style={{ marginTop:'0.75rem' }}>
          <label>性别 Gender</label>
          <div style={{ display:'flex', gap:'0.5rem' }}>
            {[['male','男 Male'],['female','女 Female']].map(([v,l]) => (
              <button key={v}
                className={`btn ${values.gender === v ? 'btn-primary' : ''}`}
                style={{ flex:1 }}
                onClick={() => onChange({ ...values, gender:v })}>
                {l}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Birthplace ── */}
      {showLocation && (
        <div style={{ marginTop:'0.85rem', paddingTop:'0.75rem',
                      borderTop:'1px solid var(--border)' }}>
          <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)',
                        letterSpacing:'0.06em', textTransform:'uppercase',
                        fontWeight:600, marginBottom:'0.55rem' }}>
            出生地（选填）
          </div>
          <div className="form-row" style={{ gridTemplateColumns:'1fr 1fr' }}>
            <div className="form-group">
              <label>省份 / 地区</label>
              <select
                value={values.province || ''}
                onChange={e => onChange({ ...values, province: e.target.value || null })}
              >
                <option value="">-- 选择省份 --</option>
                {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>城市</label>
              <input
                type="text"
                placeholder="如：成都、西安…"
                value={values.city || ''}
                onChange={e => onChange({ ...values, city: e.target.value || null })}
              />
            </div>
          </div>
          <div style={{ fontSize:'10.5px', color:'var(--text-faint)',
                        fontFamily:'var(--font-serif)', lineHeight:1.6,
                        marginTop:'0.35rem' }}>
            出生地影响地区五行偏性及真太阳时修正，有助于提高论命精准度
          </div>
        </div>
      )}
    </div>
  )
}
