import React from 'react'
import '../../styles/plates.css'

const STAR_COLOR = {
  生气: '#27ae60', 天医: '#2980b9', 延年: '#16a085', 伏位: '#7f8c8d',
  祸害: '#e67e22', 六煞: '#9b59b6', 五鬼: '#c0392b', 绝命: '#8b0000',
}

function GuaCell({ label, g }) {
  if (!g) return null
  return (
    <div className="gv-yz-cell">
      <div className="k">{label}</div>
      <div className="gua">{g.gua}</div>
      <div className="dir">{g.direction} · {g.wuxing}</div>
      <div className="grp" style={{ color: g.group === '东四卦' ? 'var(--gv-mu)' : 'var(--gv-vermilion)' }}>{g.group}</div>
      <div className="person">{g.person}</div>
    </div>
  )
}

function RelRow({ rel }) {
  if (!rel) return null
  const color = STAR_COLOR[rel.younian] || 'var(--gv-ink-3)'
  return (
    <div className="gv-yz-rel">
      <div>
        <div className="lbl">{rel.label}</div>
        <div className="star" style={{ color }}>{rel.younian}</div>
        <div className="jx">{rel.jiuxing} · {rel.level}</div>
      </div>
      <div className="jd">{rel.judgment}</div>
    </div>
  )
}

export default function YangzhaiChainPlate({ result }) {
  if (!result || !result.men) return null
  const { men, zhu, zao, relations, purity } = result

  return (
    <div className="gv-plate">
      <div className="gv-sec-bar" style={{ marginBottom:'18px' }}>
        <span className="gv-seal" style={{ background:'#a890c0', color:'#281840' }}>宅</span>
        <span className="t">门主灶 · 生成链</span>
        <span className="cap">大游年翻卦 · 门定卦，门→主→灶递推</span>
      </div>

      <div className="gv-yz-chain">
        <GuaCell label="大门" g={men} />
        <div className="gv-yz-arrow">→</div>
        <GuaCell label="主房" g={zhu} />
        <div className="gv-yz-arrow">→</div>
        <GuaCell label="灶位" g={zao} />
      </div>

      {relations && (
        <div className="gv-yz-rels">
          <RelRow rel={relations.men_zhu} />
          <RelRow rel={relations.zhu_zao} />
          <RelRow rel={relations.men_zao} />
        </div>
      )}

      {purity && (
        <div className="gv-yz-purity">
          <span className="stamp" style={{ color: purity.pure ? 'var(--gv-mu)' : 'var(--gv-vermilion)' }}>
            {purity.pure ? '★ 东西四纯一' : '⚠ 东西四驳杂'}
          </span>
          <span style={{ color:'var(--gv-ink-2)' }}>
            门 {purity.men_group} ／ 主 {purity.zhu_group} ／ 灶 {purity.zao_group}
          </span>
          {purity.desc && <span className="desc">{purity.desc}</span>}
        </div>
      )}
    </div>
  )
}
