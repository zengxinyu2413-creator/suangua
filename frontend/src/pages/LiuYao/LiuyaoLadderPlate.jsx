import React from 'react'
import '../../styles/plates.css'

const POS_LABEL = ['初','二','三','四','五','上']

// 单行渲染（本卦一侧）
function YaoRow({ y, i, isYongShen, fuByPos }) {
  const posLabel = POS_LABEL[i]
  const fu = fuByPos[i + 1]
  return (
    <div className={`gv-yao-row${y.is_changing ? ' dong' : ''}${isYongShen ? ' yong' : ''}`}>
      <div className="gv-ys">{y.liu_shen || ''}</div>
      <div className="gv-yq-wrap">
        <div className="gv-yq">
          <span className="qin">{y.liu_qin || '—'}</span>
          <span className="gz">{y.stem}{y.branch}</span>
          {y.kong_wang && <span className="kong">空</span>}
          {y.strength?.label && <span className="gv-ws">{y.strength.label}</span>}
        </div>
        {fu && (
          <div className="gv-fu">伏 {fu.fu_liuqin}{fu.fu_branch}</div>
        )}
      </div>
      <div className={`gv-yline ${y.line === '阳' ? 'yang' : 'yin'}`}>
        {y.line === '阳' ? <span /> : <><span /><span /></>}
      </div>
      <div className={`gv-mark${y.is_world ? ' shi' : ''}${y.is_application ? ' ying' : ''}${y.is_changing ? ' dong' : ''}`}>
        {y.is_world ? '世' : y.is_application ? '应' : y.is_changing ? '○' : ''}
      </div>
    </div>
  )
}

// 变卦一侧：动爻显示化出六亲干支，静爻显示原六亲干支（灰化）
function ChangedRow({ y, i }) {
  const posLabel = POS_LABEL[i]
  if (y.is_changing && y.changed_branch) {
    return (
      <div className="gv-yao-row dong">
        <div className="gv-ys"></div>
        <div className="gv-yq-wrap">
          <div className="gv-changed-tag">
            <span className="qin">{y.changed_liu_qin || ''}</span> {y.changed_stem}{y.changed_branch}
          </div>
        </div>
        <div className={`gv-yline ${(() => {
          // 变爻阴阳与本爻相反
          return y.line === '阳' ? 'yin' : 'yang'
        })()}`}>
          {y.line === '阳' ? <><span /><span /></> : <span />}
        </div>
        <div className="gv-mark dong">变</div>
      </div>
    )
  }
  return (
    <div className="gv-yao-row" style={{ opacity: 0.55 }}>
      <div className="gv-ys"></div>
      <div className="gv-yq-wrap">
        <div className="gv-yq"><span className="qin">{y.liu_qin || '—'}</span><span className="gz">{y.stem}{y.branch}</span></div>
      </div>
      <div className={`gv-yline ${y.line === '阳' ? 'yang' : 'yin'}`}>
        {y.line === '阳' ? <span /> : <><span /><span /></>}
      </div>
      <div className="gv-mark"></div>
    </div>
  )
}

export default function LiuyaoLadderPlate({ data }) {
  if (!data) return null
  const orig    = data.original
  const changed = data.changed
  const yaos    = data.yaos || []
  const ta      = data.topic_analysis || {}
  const fuList  = Array.isArray(data.fu_shen) ? data.fu_shen : (data.fu_shen ? [data.fu_shen] : [])
  const fuByPos = {}
  fuList.forEach(f => { if (f.position) fuByPos[f.position] = f })

  const dongCount = yaos.filter(y => y.is_changing).length
  const yongShenName = ta.yong_shen_name

  if (!orig || !yaos.length) return null

  // 从上爻到初爻显示
  const order = [...yaos.map((y, i) => ({ y, i }))].reverse()

  return (
    <div className="gv-plate">
      <div className="gv-sec-bar">
        <span className="gv-seal" style={{ background:'#e8b0c0', color:'#5a1e30' }}>卦</span>
        <span className="t">装卦竖梯</span>
        <span className="cap">
          {data.palace_trigram ? `${data.palace_trigram}宫 · ` : ''}
          {dongCount > 0 ? `${dongCount}爻动` : '静卦'}
        </span>
      </div>

      <div className="gv-ladder-wrap">
        {/* 本卦 */}
        <div>
          <div className="gv-gua-cap">
            {orig.name}
            <span className="gong">第{orig.number}卦{data.palace_trigram ? ` · ${data.palace_trigram}宫` : ''}</span>
          </div>
          {order.map(({ y, i }) => {
            const isYongShen = yongShenName && yongShenName !== '世爻' && yongShenName !== '应爻' && y.liu_qin === yongShenName
            return <YaoRow key={i} y={y} i={i} isYongShen={isYongShen} fuByPos={fuByPos} />
          })}
        </div>

        {/* 中轴 */}
        {changed && (
          <div className="gv-ladder-axis">
            <div>{dongCount}爻动</div>
            <div className="arrow">→</div>
            <div>之卦</div>
          </div>
        )}

        {/* 变卦 */}
        {changed && (
          <div>
            <div className="gv-gua-cap">
              {changed.name}
              <span className="gong">第{changed.number}卦</span>
            </div>
            {order.map(({ y, i }) => <ChangedRow key={i} y={y} i={i} />)}
          </div>
        )}
      </div>

      {yongShenName && (
        <div className="gv-verdict" style={{ gridTemplateColumns:'1fr' }}>
          <div className="gv-vb">
            <div className="gv-vb-h"><span className="em">用神 · {yongShenName}</span></div>
            {data.world_summary && <p>{data.world_summary}</p>}
          </div>
        </div>
      )}
    </div>
  )
}
