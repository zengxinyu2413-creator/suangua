/**
 * shareRenderers.js — 七系统分享图内容渲染
 * ==========================================
 * 每个渲染函数签名一致：(ctx, data, W, H) => void
 * 均使用 shareCanvasKit 提供的共享绘制语言，保证七模块视觉统一。
 * 字段全部对齐各模块真实后端返回（与对应 Plate 组件同源验证）。
 */
import {
  INK, INK_2, INK_3, WX, VERMILION,
  drawHeader, drawHairline, drawGanZhiBig, drawCaption, drawParagraph, drawZhuSeal, drawFooter,
  SERIF, SANS,
} from './shareCanvasKit'

// ════════ 八字 ════════
export function renderBazi(ctx, data, W, H) {
  let y = drawHeader(ctx, { x: 24, y: 24, W: W - 48, seal: 'tianhuang', glyph: '柱', title: '四柱命盘', subtitle: '八字 · 干支五行 · 十神格局' })
  y += 14
  drawHairline(ctx, 24, y, W - 48)
  y += 30

  const cols = [
    { k: 'year_pillar', cap: '年柱' }, { k: 'month_pillar', cap: '月柱' },
    { k: 'day_pillar', cap: '日柱', day: true }, { k: 'hour_pillar', cap: '时柱' },
  ].map(c => ({ ...c, p: data[c.k] })).filter(c => c.p)
  if (!cols.length) return

  const colW = (W - 48) / 4
  cols.forEach((c, i) => {
    const cx = 24 + colW * i + colW / 2
    drawCaption(ctx, cx, y, c.cap + (c.day ? ' · 主' : ''), { align: 'center', color: c.day ? VERMILION : INK_3, weight: 600, size: 11 })
    drawGanZhiBig(ctx, cx, y + 42, c.p.tiangan, c.p.dizhi, c.p.wuxing_gan, c.p.wuxing_zhi, 26)
    if (c.p.shishen_gan) drawCaption(ctx, cx, y + 92, c.p.shishen_gan, { align: 'center', size: 10, color: INK_2 })
    if (c.p.canggan?.length) drawCaption(ctx, cx, y + 106, c.p.canggan.join(' '), { align: 'center', size: 9, color: INK_3 })
    if (c.p.nayin) drawCaption(ctx, cx, y + 120, c.p.nayin, { align: 'center', size: 9, color: '#c1953a' })
  })
  y += 140
  drawHairline(ctx, 24, y, W - 48)
  y += 24

  // 五行分布条
  const wxCount = { 木: 0, 火: 0, 土: 0, 金: 0, 水: 0 }
  cols.forEach(c => { if (wxCount[c.p.wuxing_gan] != null) wxCount[c.p.wuxing_gan]++; if (wxCount[c.p.wuxing_zhi] != null) wxCount[c.p.wuxing_zhi]++ })
  const wxMax = Math.max(1, ...Object.values(wxCount))
  drawCaption(ctx, 24, y, '五行', { size: 10 })
  let bx = 24
  ;['木', '火', '土', '金', '水'].forEach(w => {
    const bw = 30 + (wxCount[w] / wxMax) * 50
    ctx.fillStyle = WX[w]
    ctx.fillRect(bx, y + 8, bw, 6)
    drawCaption(ctx, bx, y + 26, `${w}${wxCount[w]}`, { size: 9, color: INK_3 })
    bx += 80
  })
  y += 46
  drawHairline(ctx, 24, y, W - 48)
  y += 24

  const pattern = data.pattern || ''
  const dm = data.day_master || ''
  drawCaption(ctx, 24, y, `${pattern} · 日主${dm}${data.strength ? '（' + data.strength + '）' : ''}`, { size: 13, color: VERMILION, weight: 700 })
  y += 22
  const verdict = data.master_synthesis?.headline || data.pattern_desc || data.tiaohou?.verdict || ''
  y = drawParagraph(ctx, 24, y, verdict, W - 48, { size: 12, maxLines: 3 })

  if (data.pattern) drawZhuSeal(ctx, W - 60, H - 90, pattern.slice(0, 4), '格局', 64)
  drawFooter(ctx, W, H, '八字四柱')
}

// ════════ 六爻 ════════
export function renderLiuyao(ctx, data, W, H) {
  let y = drawHeader(ctx, { x: 24, y: 24, W: W - 48, seal: 'furong', glyph: '卦', title: data.original?.name || '卦象', subtitle: `第${data.original?.number || ''}卦${data.palace_trigram ? ' · ' + data.palace_trigram + '宫' : ''}` })
  y += 14
  drawHairline(ctx, 24, y, W - 48)
  y += 30

  // 本卦→变卦
  ctx.font = `700 40px ${SERIF}`
  ctx.fillStyle = INK
  ctx.fillText(data.original?.name || '', 24, y + 36)
  if (data.changed) {
    drawCaption(ctx, 24, y + 54, `之 ${data.changed.name}（第${data.changed.number}卦）`, { size: 12, color: INK_3 })
  }
  y += 78
  drawHairline(ctx, 24, y, W - 48)
  y += 24

  // 世应 + 用神
  const yaos = data.yaos || []
  const shiYao = yaos.find(v => v.is_world)
  const yingYao = yaos.find(v => v.is_application)
  const yongShenName = data.topic_analysis?.yong_shen_name
  const dongCount = yaos.filter(v => v.is_changing).length

  const info = []
  if (shiYao) info.push(['世爻', `${shiYao.liu_qin || ''}${shiYao.stem || ''}${shiYao.branch || ''}`])
  if (yingYao) info.push(['应爻', `${yingYao.liu_qin || ''}${yingYao.stem || ''}${yingYao.branch || ''}`])
  if (yongShenName) info.push(['用神', yongShenName])
  info.push(['动爻', dongCount > 0 ? `${dongCount}爻动` : '静卦'])

  let ix = 24
  info.forEach(([label, val]) => {
    drawCaption(ctx, ix, y, label, { size: 10, color: INK_3 })
    drawCaption(ctx, ix, y + 18, val, { size: 14, color: VERMILION, weight: 700 })
    ix += 130
  })
  y += 46
  drawHairline(ctx, 24, y, W - 48)
  y += 24

  const verdict = data.master_synthesis?.headline || data.world_summary || data.interpretation || ''
  drawCaption(ctx, 24, y, `所占：${data.topic || data.question || '综合'}`, { size: 12, color: INK_2, weight: 600 })
  y += 22
  y = drawParagraph(ctx, 24, y, verdict, W - 48, { size: 12, maxLines: 3 })

  if (yongShenName) drawZhuSeal(ctx, W - 60, H - 90, yongShenName, '用神', 60)
  drawFooter(ctx, W, H, '六爻纳甲')
}

// ════════ 紫微 ════════
export function renderZiwei(ctx, data, W, H) {
  const rating = data.insights?.rating
  const meta = data.metadata || {}
  let y = drawHeader(ctx, { x: 24, y: 24, W: W - 48, seal: 'jixue', glyph: '星', title: '紫微命盘', subtitle: `${meta.five_elements || ''}${rating?.soul_stars?.length ? ' · 命宫 ' + rating.soul_stars.join('/') : ''}` })
  y += 14
  drawHairline(ctx, 24, y, W - 48)
  y += 30

  const soul = data.soul_palace
  if (soul) {
    ctx.font = `700 28px ${SERIF}`
    ctx.fillStyle = INK
    ctx.fillText(`${soul.stem_branch || ''}宫立命`, 24, y + 26)
    drawCaption(ctx, 24, y + 46, (soul.major_stars || []).join(' · ') || '无主星（借对宫）', { size: 13, color: VERMILION, weight: 600 })
    y += 66
  }

  if (rating?.overall) {
    drawCaption(ctx, 24, y, `命格 ${rating.overall} · 亮度评分 ${rating.score >= 0 ? '+' : ''}${rating.score?.toFixed(2) ?? ''}`, { size: 12, color: INK_2, weight: 600 })
    y += 20
  }

  const patterns = data.insights?.patterns
  if (patterns?.good?.length || patterns?.bad?.length) {
    const tags = [...(patterns.good || []).map(p => p.name), ...(patterns.bad || []).map(p => '⚠' + p.name)]
    drawCaption(ctx, 24, y, tags.slice(0, 5).join('　'), { size: 11, color: INK_3 })
    y += 24
  }
  drawHairline(ctx, 24, y, W - 48)
  y += 24

  const verdict = data.master_synthesis?.headline || rating?.summary || ''
  y = drawParagraph(ctx, 24, y, verdict, W - 48, { size: 12, maxLines: 4 })

  if (rating?.overall) drawZhuSeal(ctx, W - 60, H - 90, rating.overall, '命格', 64)
  drawFooter(ctx, W, H, '紫微斗数')
}

// ════════ 奇门 ════════
export function renderQimen(ctx, data, W, H) {
  let y = drawHeader(ctx, { x: 24, y: 24, W: W - 48, seal: 'qingtian', glyph: '门', title: '奇门遁甲', subtitle: `${data.ju_type || ''} 第${data.ju_number || ''}局${data.purpose ? ' · 占' + data.purpose : ''}` })
  y += 14
  drawHairline(ctx, 24, y, W - 48)
  y += 30

  const palaces = data.palaces || []
  const zhifu = palaces.find(p => p.is_zhifu)
  const zhishi = palaces.find(p => p.is_zhishi)
  const firstYs = data.yongshen_palaces?.items?.[0]
  const info = []
  if (zhifu) info.push(['值符', `${zhifu.star || ''}`])
  if (zhishi) info.push(['值使', `${zhishi.door || ''}`])
  if (firstYs) info.push([firstYs.role, firstYs.symbol])

  let ix = 24
  info.forEach(([label, val]) => {
    drawCaption(ctx, ix, y, label, { size: 10, color: INK_3 })
    drawCaption(ctx, ix, y + 18, val, { size: 16, color: VERMILION, weight: 700 })
    ix += 140
  })
  y += 50
  drawHairline(ctx, 24, y, W - 48)
  y += 24

  const verdict = data.master_synthesis?.headline || ''
  drawCaption(ctx, 24, y, `占问：${data.purpose || '综合'}`, { size: 12, color: INK_2, weight: 600 })
  y += 22
  y = drawParagraph(ctx, 24, y, verdict, W - 48, { size: 12, maxLines: 4 })

  drawFooter(ctx, W, H, '奇门遁甲')
}

// ════════ 玄空 ════════
export function renderXuankong(ctx, data, W, H) {
  let y = drawHeader(ctx, { x: 24, y: 24, W: W - 48, seal: 'balin', glyph: '飞', title: '玄空飞星', subtitle: `坐${data.sitting_gua || ''}向${data.facing_gua || ''} · ${data.yun?.yun_name || ''}` })
  y += 14
  drawHairline(ctx, 24, y, W - 48)
  y += 30

  if (data.yun) {
    drawCaption(ctx, 24, y, '当运', { size: 10, color: INK_3 })
    drawCaption(ctx, 24, y + 18, data.yun.yun_name || '', { size: 20, color: VERMILION, weight: 700 })
    y += 48
  }
  if (data.verdict) {
    drawCaption(ctx, 24, y, `令星判定：${data.verdict}`, { size: 13, color: INK_2, weight: 600 })
    y += 24
  }
  drawHairline(ctx, 24, y, W - 48)
  y += 24

  const verdict = data.master_synthesis?.headline || ''
  y = drawParagraph(ctx, 24, y, verdict, W - 48, { size: 12, maxLines: 4 })

  drawFooter(ctx, W, H, '玄空飞星')
}

// ════════ 阳宅 ════════
export function renderYangzhai(ctx, data, W, H) {
  let y = drawHeader(ctx, { x: 24, y: 24, W: W - 48, seal: 'balin', glyph: '宅', title: '阳宅三要', subtitle: '门主灶 · 大游年断' })
  y += 14
  drawHairline(ctx, 24, y, W - 48)
  y += 34

  const cells = [['大门', data.men], ['主房', data.zhu], ['灶位', data.zao]]
  const colW = (W - 48) / 3
  cells.forEach(([label, g], i) => {
    if (!g) return
    const cx = 24 + colW * i + colW / 2
    drawCaption(ctx, cx, y, label, { align: 'center', size: 10, color: INK_3 })
    ctx.textAlign = 'center'
    ctx.font = `700 26px ${SERIF}`
    ctx.fillStyle = INK
    ctx.fillText(g.gua || '', cx, y + 36)
    ctx.textAlign = 'left'
    drawCaption(ctx, cx, y + 54, `${g.direction || ''}·${g.wuxing || ''}`, { align: 'center', size: 10, color: INK_3 })
    drawCaption(ctx, cx, y + 68, g.group || '', { align: 'center', size: 10, color: g.group === '东四卦' ? '#2f8f63' : VERMILION, weight: 600 })
  })
  y += 96
  drawHairline(ctx, 24, y, W - 48)
  y += 24

  if (data.purity) {
    drawCaption(ctx, 24, y, data.purity.pure ? '★ 东西四纯一' : '⚠ 东西四驳杂', { size: 13, color: data.purity.pure ? '#2f8f63' : VERMILION, weight: 700 })
    y += 24
  }
  const verdict = data.master_synthesis?.headline || data.purity?.desc || ''
  y = drawParagraph(ctx, 24, y, verdict, W - 48, { size: 12, maxLines: 3 })

  drawFooter(ctx, W, H, '阳宅三要')
}

// ════════ 择日 ════════
export function renderDate(ctx, data, W, H) {
  const best = (data.best_days || [])[0]
  let y = drawHeader(ctx, { x: 24, y: 24, W: W - 48, seal: 'tianhuang', glyph: '历', title: '择日推算', subtitle: `${data.year || ''}年${data.month || ''}月 · 占「${data.purpose || ''}」` })
  y += 14
  drawHairline(ctx, 24, y, W - 48)
  y += 30

  if (best) {
    ctx.font = `700 40px ${SERIF}`
    ctx.fillStyle = VERMILION
    ctx.fillText(`${best.day}日`, 24, y + 36)
    drawCaption(ctx, 24, y + 54, `${best.officer || ''}日${best.star ? ' · ' + best.star + '宿' : ''}${best.score !== undefined ? ' · 评分 ' + (best.score > 0 ? '+' : '') + best.score : ''}`, { size: 12, color: INK_2 })
    y += 78
    drawHairline(ctx, 24, y, W - 48)
    y += 24
    if (best.reasons?.length) {
      best.reasons.slice(0, 3).forEach(r => {
        drawCaption(ctx, 24, y, '· ' + r, { size: 12, color: INK_2 })
        y += 20
      })
    }
  }
  y += 6
  const verdict = data.master_synthesis?.headline || ''
  if (verdict) { drawHairline(ctx, 24, y, W - 48); y += 20; y = drawParagraph(ctx, 24, y, verdict, W - 48, { size: 12, maxLines: 2 }) }

  drawFooter(ctx, W, H, '择日通书')
}

export const RENDERERS = {
  bazi: renderBazi,
  liuyao: renderLiuyao,
  ziwei: renderZiwei,
  qimen: renderQimen,
  xuankong: renderXuankong,
  yangzhai: renderYangzhai,
  date: renderDate,
}
