import React, { useEffect, useState, useCallback } from 'react'
import { knowledgeApi } from '../../api/client'
import { INK, INK_2, INK_3, INK_4, VERMILION, PAPER, drawHeader, drawFooter } from '../../utils/shareCanvasKit'

const DIZHI_IMG = {
  "子":"ruishou_zi.png","丑":"ruishou_chou.png","寅":"ruishou_yin.png","卯":"ruishou_mao.png",
  "辰":"ruishou_chen.png","巳":"ruishou_si.png","午":"ruishou_wu.png","未":"ruishou_wei.png",
  "申":"ruishou_shen.png","酉":"ruishou_you.png","戌":"ruishou_xu.png","亥":"ruishou_hai.png",
}

export default function DailyGuardianPage(){
  const [data,setData]=useState(null)
  const [loading,setLoading]=useState(true)
  const [dateStr,setDateStr]=useState('')
  const [shareUrl,setShareUrl]=useState(null)
  const [imgError,setImgError]=useState(false)
  const [generating,setGenerating]=useState(false)

  // Default to today, auto-refresh every minute
  useEffect(()=>{
    const today=()=>new Date().toISOString().slice(0,10)
    setDateStr(today())
    const timer=setInterval(()=>{
      const now=today()
      setDateStr(prev=>{if(prev!==now)return now;return prev})
    },60000)
    return()=>clearInterval(timer)
  },[])

  // Load data whenever date changes
  useEffect(()=>{
    if(!dateStr)return
    let dead=false
    setLoading(true)
    knowledgeApi.dailyGuardian(dateStr)
      .then(r=>{if(!dead){setData(r);setLoading(false);setImgError(false)}})
      .catch(()=>{if(!dead)setLoading(false)})
    return()=>{dead=true}
  },[dateStr])

  // 加载瑞兽图（存在则用真图做杂志封面式版头；不存在/加载失败则优雅降级为纯文字版头，不阻塞分享图生成）
  const _loadImg=(src)=>new Promise((resolve)=>{
    const img=new Image()
    const timer=setTimeout(()=>resolve(null),1800) // 超时保护，避免图片迟迟不响应卡住生成
    img.onload=()=>{clearTimeout(timer);resolve(img)}
    img.onerror=()=>{clearTimeout(timer);resolve(null)}
    img.src=src
  })

  // Share image
  const genShare=useCallback(async ()=>{
    if(!data)return;setGenerating(true)
    const d=data,W=1080,R=2,P=60 // padding
    const M={l:P,r:W-P,w:W-P*2} // margins
    const GREEN='#2f8f63',AMBER='#c1953a' // 吉/中 语义色（与 shareCanvasKit WX 一致）
    const ruishouFile=DIZHI_IMG[d.day_zhi]
    const ruishouPortrait=ruishouFile?await _loadImg(`/ruishou/${ruishouFile}`):null

    // Two-pass: measure then draw
    const tmpC=document.createElement('canvas');tmpC.width=1;tmpC.height=1
    const tx=tmpC.getContext('2d')

    // Measure wrapped text height
    const measureWrap=(text,font,maxW,lh)=>{
      tx.font=font;let line='',lines=1
      for(const ch of text){const t=line+ch;if(tx.measureText(t).width>maxW){lines++;line=ch}else line=t}
      return lines*lh
    }

    const jishenText=(d.jishen||[]).join('  ')
    const xiongshaText=(d.xiongsha||[]).join('  ')
    const colW=(M.w-32)/2 // 双栏栏宽

    // Calculate total height
    let h=0
    h+=60  // seal header
    h+=ruishouPortrait?320:252 // hero 区（与实际绘制推进量一致：有图 heroTop+316，无图 heroTop+248，各留4px余量）
    h+=22  // divider
    h+=18  // 「今日纪要」栏目眉标
    // facts 2-col: 左栏固定5行，右栏吉神+凶煞换行文本，取二者较高
    const leftFactsH=26*5
    const rightFactsH=measureWrap(jishenText,'13px serif',colW-40,20)
                     +measureWrap(xiongshaText,'13px serif',colW-40,20)+20+34
    h+=Math.max(leftFactsH,rightFactsH)+12
    h+=40  // 方位 + 彭祖（此前遗漏，跨栏两行）
    h+=22  // divider
    h+=18  // 「宜忌提要」栏目眉标
    // yi / ji
    const yiText=(d.yi||[]).join('　')
    const jiText=(d.ji||[]).join('　')
    h+=Math.max(
      measureWrap(yiText,'14px serif',M.w/2-60,20),
      measureWrap(jiText,'14px serif',M.w/2-60,20)
    )+34
    h+=20 // divider
    h+=18  // 「十二时辰吉凶」栏目眉标
    h+=50*2+6 // 12 hours 2 rows
    h+=22  // divider
    // officer detail（摘引样式：分隔线24 + drawPullQuote固定开销32 = 56，含装饰引号）
    if(d.officer?.detail) h+=measureWrap(d.officer.detail,'italic 14px serif',M.w-56,22)+56
    // xingxiu song（同上，固定开销56）
    if(d.xingxiu?.song) h+=measureWrap(d.xingxiu.song,'italic 14px serif',M.w-56,22)+56
    h+=50  // footer
    const H=Math.max(h+40,860)

    const c=document.createElement('canvas');c.width=W*R;c.height=H*R
    const x=c.getContext('2d');x.scale(R,R)

    // BG（近白留白纸面，无描边裱框）
    x.fillStyle=PAPER;x.fillRect(0,0,W,H)

    // Helper: 发丝分隔线
    const divider=(y)=>{x.strokeStyle='rgba(34,32,26,0.14)';x.lineWidth=0.5;x.beginPath();x.moveTo(P,y);x.lineTo(W-P,y);x.stroke()}
    // Helper: 栏目眉标（编辑设计中的 kicker/eyebrow）— 朱砂小字 + 右延伸细线，统一各内容分区的节奏感
    const drawKicker=(text,ky)=>{
      x.textAlign='left';x.font='bold 11px sans-serif';x.fillStyle=VERMILION
      x.fillText(text,P,ky)
      const tw=x.measureText(text).width
      x.strokeStyle='rgba(207,59,44,0.20)';x.lineWidth=0.5
      x.beginPath();x.moveTo(P+tw+10,ky-4);x.lineTo(W-P,ky-4);x.stroke()
    }
    // Helper: wrapped text draw, returns new y
    const drawWrap=(text,font,color,sx,sy,maxW,lh)=>{
      x.font=font;x.fillStyle=color;tx.font=font;let line='',ly=sy
      for(const ch of text){const t=line+ch;if(tx.measureText(t).width>maxW){x.fillText(line,sx,ly);ly+=lh;line=ch}else line=t}
      if(line)x.fillText(line,sx,ly);return ly+lh
    }
    // Helper: 摘引样式段落（大装饰引号 + 左侧色条 + 斜体衬线正文）
    const drawPullQuote=(label,text,accentColor,sy)=>{
      const qx=P+8
      x.font='italic bold 64px Georgia, serif';x.fillStyle=accentColor+'1c'
      x.textAlign='left';x.fillText('\u201C',qx-4,sy+34)
      x.fillStyle=accentColor;x.fillRect(P,sy-10,2,measureWrap(text,'italic 14px serif',M.w-56,22)+14)
      x.font='bold 12px sans-serif';x.fillStyle=accentColor;x.fillText(label,P+22,sy)
      return drawWrap(text,'italic 14px serif',INK_2,P+22,sy+22,M.w-56,22)+10
    }

    // 印石章首（朱砂石·守）
    let y=drawHeader(x,{x:P,y:24,W:W-P*2,seal:'zhusha',glyph:'守',title:'每日守护',subtitle:`${d.date}　${d.weekday}`})
    y+=14

    const scoreColor=d.score>=80?GREEN:d.score>=60?AMBER:VERMILION

    if(ruishouPortrait){
      // ── 有图版头：左文右图，真正的杂志封面结构 ──
      const heroTop=y
      const portraitW=214,portraitH=286 // 3:4 竖版肖像卡
      const px2=W-P-portraitW
      // 肖像卡：细边框 + 顶部朱色细条
      x.drawImage(ruishouPortrait,px2,heroTop,portraitW,portraitH)
      x.strokeStyle='rgba(34,32,26,0.16)';x.lineWidth=1;x.strokeRect(px2,heroTop,portraitW,portraitH)
      x.fillStyle=VERMILION;x.fillRect(px2,heroTop,portraitW,3)
      // 题名压在图片底部（渐变蒙层 + 白字），真正的杂志封面处理，而非图文分离
      const capH=64
      const grad=x.createLinearGradient(0,heroTop+portraitH-capH,0,heroTop+portraitH)
      grad.addColorStop(0,'rgba(20,16,10,0)');grad.addColorStop(1,'rgba(20,16,10,0.72)')
      x.fillStyle=grad;x.fillRect(px2,heroTop+portraitH-capH,portraitW,capH)
      x.textAlign='center';x.font='bold 17px serif';x.fillStyle='#fff8ec'
      x.fillText(d.ruishou,px2+portraitW/2,heroTop+portraitH-30)
      x.font='9px sans-serif';x.fillStyle='rgba(255,248,236,0.75)'
      x.fillText(`日支${d.day_zhi} · ${d.day_wuxing||''}行`,px2+portraitW/2,heroTop+portraitH-14)

      // 左侧文字栏
      const textW=px2-P-28
      x.textAlign='left'
      x.font='bold 44px serif';x.fillStyle=INK
      // 农历日期可能较长，超宽则缩字号
      let lunarSize=44; x.font=`bold ${lunarSize}px serif`
      while(x.measureText(d.lunar).width>textW && lunarSize>28){lunarSize-=2;x.font=`bold ${lunarSize}px serif`}
      x.fillText(d.lunar,P,heroTop+46)
      x.font='13px serif';x.fillStyle=INK_3
      x.fillText(`${d.date}　${d.weekday}`,P,heroTop+70)
      x.font='bold 17px serif';x.fillStyle=INK
      x.fillText(`${d.year_gz}年 · ${d.month_gz}月 · ${d.day_gz}日`,P,heroTop+96)
      x.font='12px serif';x.fillStyle=INK_3
      x.fillText(`${d.nayin.year} · ${d.nayin.month} · ${d.nayin.day}`,P,heroTop+118)

      // 评分朱印（旋转小方章，压在文字栏下方）
      x.save();x.translate(P+34,heroTop+172);x.rotate(-3*Math.PI/180)
      x.fillStyle='#fffdf8';x.strokeStyle=scoreColor;x.lineWidth=2
      x.fillRect(-34,-34,68,68);x.strokeRect(-34,-34,68,68)
      x.strokeStyle=scoreColor+'55';x.lineWidth=0.5;x.strokeRect(-30,-30,60,60)
      x.textAlign='center';x.fillStyle=scoreColor
      x.font='bold 30px sans-serif';x.fillText(String(d.score),0,6)
      x.font='9px sans-serif';x.fillText('综合评分',0,22)
      x.restore()

      x.font='italic 14px serif';x.fillStyle=INK_3;x.textAlign='left'
      x.fillText(`「${d.poem}」`,P+82,heroTop+180)

      y=heroTop+portraitH+30
    } else {
      // ── 无图降级版头：装饰性地支篆字水印圆章 + 文字，评分与瑞兽名左右并排避免碰撞 ──
      const heroTop=y
      // 圆章水印：细双线圆边框 + 大字地支（篆意留白装饰，替代真实肖像图的视觉锚点）
      const wmCx=W-P-80,wmCy=heroTop+78
      x.strokeStyle='rgba(207,59,44,0.22)';x.lineWidth=1.5
      x.beginPath();x.arc(wmCx,wmCy,66,0,Math.PI*2);x.stroke()
      x.strokeStyle='rgba(207,59,44,0.14)';x.lineWidth=0.5
      x.beginPath();x.arc(wmCx,wmCy,58,0,Math.PI*2);x.stroke()
      x.textAlign='center';x.font='84px serif';x.fillStyle='rgba(207,59,44,0.16)'
      x.fillText(d.day_zhi||'',wmCx,wmCy+30)
      x.font='10px sans-serif';x.fillStyle=INK_4
      x.fillText(d.ruishou,wmCx,wmCy+82)

      x.textAlign='left'
      x.font='bold 46px serif';x.fillStyle=INK;x.fillText(d.lunar,P,heroTop+42);y=heroTop+70
      x.font='14px serif';x.fillStyle=INK_3;x.fillText(`${d.date}　${d.weekday}`,P,y);y+=26
      x.font='bold 22px serif';x.fillStyle=INK;x.fillText(`${d.year_gz}年　${d.month_gz}月　${d.day_gz}日`,P,y);y+=30
      x.font='12px serif';x.fillStyle=INK_3;x.fillText(`${d.nayin.year}　·　${d.nayin.month}　·　${d.nayin.day}`,P,y);y+=32

      // 评分朱印（左）+ 瑞兽题名与诗句（右）— 左右并排，天然无碰撞
      const rowY=y+34,cx=P+34
      x.save();x.translate(cx,rowY);x.rotate(-3*Math.PI/180)
      x.fillStyle='#fffdf8';x.strokeStyle=scoreColor;x.lineWidth=2
      x.fillRect(-32,-32,64,64);x.strokeRect(-32,-32,64,64)
      x.textAlign='center';x.fillStyle=scoreColor
      x.font='bold 28px sans-serif';x.fillText(String(d.score),0,4)
      x.font='9px sans-serif';x.fillText('综合评分',0,20)
      x.restore()

      x.textAlign='left'
      x.font='bold 20px serif';x.fillStyle=VERMILION;x.fillText(d.ruishou,cx+50,rowY-6)
      x.font='italic 13px serif';x.fillStyle=INK_3;x.fillText(`「${d.poem}」`,cx+50,rowY+16)
      y=rowY+56
    }

    divider(y);y+=22

    // ── 双栏事实网格：左栏节气建除天神星宿冲煞 / 右栏吉神凶煞 ──
    drawKicker('今日纪要',y);y+=18
    x.textAlign='left'
    const factsTop=y
    const info=[
      ['节气',d.jieqi?.prev?`${d.jieqi.prev.name} (${d.jieqi.prev.date}) → ${d.jieqi.next?.name||''}`:d.jieqi?.current||'—'],
      ['建除',`${d.officer.name}日 · ${d.officer.nature}`],
      ['天神',`${d.tianshen.name} · ${d.tianshen.type} · ${d.tianshen.luck}`],
      ['星宿',`${d.xingxiu.name}宿 · ${d.xingxiu.luck}`],
      ['冲煞',`冲${d.chong}　空亡：${d.xunkong}`],
    ]
    let ly=factsTop
    info.forEach(([l,v])=>{
      x.font='12px sans-serif';x.fillStyle=INK_3;x.fillText(l,P,ly)
      x.font='bold 14px serif';x.fillStyle=INK;x.fillText(v,P+52,ly);ly+=26
    })

    const rx0=P+colW+32
    let ry=factsTop
    x.font='bold 12px sans-serif';x.fillStyle=GREEN;x.fillText('吉神',rx0,ry);ry+=18
    ry=drawWrap(jishenText,'13px serif',INK_2,rx0,ry,colW-40,20)+10
    x.font='bold 12px sans-serif';x.fillStyle=VERMILION;x.fillText('凶煞',rx0,ry);ry+=18
    ry=drawWrap(xiongshaText,'13px serif',INK_2,rx0,ry,colW-40,20)

    y=Math.max(ly,ry)+8
    // 竖向分隔细线（双栏之间）
    x.strokeStyle='rgba(34,32,26,0.10)';x.lineWidth=0.5
    x.beginPath();x.moveTo(P+colW+16,factsTop-14);x.lineTo(P+colW+16,y-6);x.stroke()

    // 方位 + 彭祖（跨栏，紧随其后）
    x.font='12px serif';x.fillStyle=INK_3
    x.fillText(Object.entries(d.positions||{}).map(([k,v])=>`${k}${v}`).join('　'),P,y);y+=20
    x.font='11px serif';x.fillStyle=INK_4;x.fillText(`彭祖：${d.pengzu}`,P,y);y+=20

    divider(y);y+=22

    // 宜（左侧朱砂细线标记，非色块底）
    drawKicker('宜忌提要',y);y+=18
    x.fillStyle=GREEN;x.fillRect(P,y-14,2,10+measureWrap(yiText,'14px serif',M.w/2-60,20))
    x.font='bold 15px serif';x.fillStyle=GREEN;x.fillText('宜',P+10,y+8)
    const yiEnd=drawWrap(yiText,'14px serif',INK_2,P+40,y+8,M.w/2-60,20)

    // 忌
    const rxx=W/2+4
    x.fillStyle=VERMILION;x.fillRect(rxx,y-14,2,10+measureWrap(jiText,'14px serif',M.w/2-60,20))
    x.font='bold 15px serif';x.fillStyle=VERMILION;x.fillText('忌',rxx+10,y+8)
    const jiEnd=drawWrap(jiText,'14px serif',INK_2,rxx+40,y+8,M.w/2-60,20)

    y=Math.max(yiEnd,jiEnd)+18
    divider(y);y+=22

    // 十二时辰（无格底色块，仅顶部细色条标吉）
    drawKicker('十二时辰吉凶',y);y+=18
    const cW=(M.w)/6
    d.hours.forEach((hh,i)=>{
      const col=i%6,rw=Math.floor(i/6)
      const cx=P+col*cW,cy=y+rw*50
      x.fillStyle=hh.luck==='吉'?GREEN:'rgba(34,32,26,0.14)'
      x.fillRect(cx+3,cy,cW-6,2)
      x.textAlign='center'
      x.font='bold 16px serif';x.fillStyle=hh.luck==='吉'?GREEN:INK_3;x.fillText(hh.shichen,cx+cW/2,cy+22)
      x.font='10px sans-serif';x.fillStyle=INK_4;x.fillText(hh.hours,cx+cW/2,cy+36)
      x.font='11px serif';x.fillStyle=INK_3;x.fillText(hh.ganzhi,cx+cW/2,cy+48)
      x.textAlign='left'
    });y+=106

    // 建除详解 — 摘引样式（大装饰引号 + 色条 + 斜体衬线）
    if(d.officer?.detail){
      divider(y);y+=24
      y=drawPullQuote(`${d.officer.name}日 · 建除详解`,d.officer.detail,VERMILION,y)
    }

    // 星宿歌诀 — 摘引样式（同款处理，墨色区分）
    if(d.xingxiu?.song){
      divider(y);y+=24
      y=drawPullQuote(`${d.xingxiu.name}宿 · 歌诀`,d.xingxiu.song,'#5a5548',y)
    }

    // Footer（与其余七模块分享图共用同一收尾）
    drawFooter(x,W,H,'每日守护',P)

    setShareUrl(c.toDataURL('image/png'))
    setGenerating(false)
  },[data])

  if(loading) return <div className="page" style={{display:'flex',alignItems:'center',justifyContent:'center',minHeight:400}}><div style={{fontSize:13,color:'var(--text-muted)',fontFamily:'var(--font-serif)'}}>载入每日守护…</div></div>
  if(!data) return <div className="page" style={{padding:20,color:'var(--text-muted)'}}>加载失败</div>

  const d=data
  const scoreColor=d.score>=80?'var(--accent)':d.score>=60?'#c89020':'#c04030'
  const ruishouImg=DIZHI_IMG[d.day_zhi]||null

  return(
    <div className="page" style={{overflow:'auto'}}>
      <div style={{maxWidth:900,margin:'0 auto',padding:'16px 16px 40px'}}>
        {/* Controls */}
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
          <div style={{display:'flex',alignItems:'center',gap:8}}>
            <input type="date" value={dateStr} onChange={e=>setDateStr(e.target.value)} style={{background:'var(--bg-subtle)',border:'1px solid var(--border)',padding:'4px 10px',fontSize:12,color:'var(--text-secondary)',fontFamily:'var(--font-mono)'}}/>
            <button onClick={()=>setDateStr(new Date().toISOString().slice(0,10))} style={{padding:'4px 10px',fontSize:11,border:'1px solid var(--border)',background:'var(--bg-subtle)',cursor:'pointer',color:'var(--text-secondary)'}}>今日</button>
          </div>
          <button onClick={genShare} disabled={generating} style={{padding:'5px 14px',fontSize:12,background:'var(--accent)',color:'#fff',border:'none',cursor:generating?'wait':'pointer',fontFamily:'var(--font-serif)',letterSpacing:1,opacity:generating?0.6:1}}>{generating?'生成中…':'生成分享图'}</button>
        </div>

        {/* Two columns */}
        <div style={{display:'grid',gridTemplateColumns:'1fr 280px',gap:16}}>
          {/* LEFT */}
          <div style={{display:'flex',flexDirection:'column',gap:12}}>
            {/* Card 1: Date + Score */}
            <div style={{background:'var(--surface)',border:'1px solid var(--border)',padding:'20px',position:'relative'}}>
              <div style={{position:'absolute',top:0,left:0,right:0,height:3,background:'var(--accent)'}}/>
              <div style={{display:'flex',alignItems:'center',gap:20}}>
                <div style={{flex:1}}>
                  <div style={{fontSize:11,color:'var(--text-faint)',fontFamily:'var(--font-mono)',letterSpacing:1}}>{d.date} {d.weekday}</div>
                  <div style={{fontSize:32,fontWeight:900,fontFamily:'var(--font-serif)',color:'var(--text-primary)',letterSpacing:4,margin:'4px 0'}}>{d.lunar}</div>
                  <div style={{fontSize:14,color:'var(--text-secondary)',fontFamily:'var(--font-serif)',letterSpacing:2}}>{d.year_gz}年　{d.month_gz}月　{d.day_gz}日</div>
                  <div style={{display:'flex',gap:6,marginTop:8}}>
                    {[d.nayin.year,d.nayin.month,d.nayin.day].map((n,i)=><span key={i} style={{fontSize:10,padding:'1px 6px',background:'var(--accent-bg)',color:'var(--accent)',border:'1px solid var(--accent-dim)',fontFamily:'var(--font-serif)'}}>{n}</span>)}
                  </div>
                </div>
                <div style={{textAlign:'center',padding:'0 16px',borderLeft:'1px solid var(--border)'}}>
                  <div style={{fontSize:40,fontWeight:900,color:scoreColor,fontFamily:'var(--font-mono)',lineHeight:1}}>{d.score}</div>
                  <div style={{fontSize:9,color:'var(--text-faint)',marginTop:2}}>综合评分</div>
                  <div style={{fontSize:12,color:'var(--accent)',fontFamily:'var(--font-serif)',marginTop:4,fontWeight:700}}>{d.ruishou}</div>
                </div>
              </div>
              <div style={{fontSize:12,color:'var(--text-muted)',fontFamily:'var(--font-serif)',fontStyle:'italic',marginTop:8,textAlign:'center',borderTop:'1px solid var(--border)',paddingTop:8}}>「{d.poem}」</div>
            </div>

            {/* Card 2: Key indicators */}
            <div style={{background:'var(--surface)',border:'1px solid var(--border)',padding:'14px 16px',display:'grid',gridTemplateColumns:'1fr 1fr 1fr 1fr',gap:10}}>
              <Ind label="节气" value={d.jieqi?.prev?.name||d.jieqi?.current||'—'} sub={d.jieqi?.next?`→${d.jieqi.next.name}`:''} />
              <Ind label="建除" value={`${d.officer.name}日`} sub={d.officer.nature} color={d.officer.nature==='吉'?'#1a8a4a':'#c04030'} />
              <Ind label="天神" value={d.tianshen.name} sub={d.tianshen.type} color={d.tianshen.type==='黄道'?'#c89020':'#6a6a60'} />
              <Ind label="星宿" value={`${d.xingxiu.name}宿`} sub={d.xingxiu.luck} color={d.xingxiu.luck==='吉'?'#1a8a4a':'#c04030'} />
            </div>

            {/* Card 3: Yi / Ji */}
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:12}}>
              <div style={{background:'var(--surface)',border:'1px solid var(--border)',padding:'12px 14px'}}>
                <div style={{display:'flex',alignItems:'center',gap:6,marginBottom:8}}><div style={{width:3,height:14,background:'#1a8a4a'}}/><span style={{fontSize:13,fontWeight:700,color:'#1a8a4a',fontFamily:'var(--font-serif)'}}>宜</span></div>
                <div style={{fontSize:13,color:'var(--text-secondary)',lineHeight:2,fontFamily:'var(--font-serif)'}}>{d.yi.join('　')}</div>
              </div>
              <div style={{background:'var(--surface)',border:'1px solid var(--border)',padding:'12px 14px'}}>
                <div style={{display:'flex',alignItems:'center',gap:6,marginBottom:8}}><div style={{width:3,height:14,background:'#c04030'}}/><span style={{fontSize:13,fontWeight:700,color:'#c04030',fontFamily:'var(--font-serif)'}}>忌</span></div>
                <div style={{fontSize:13,color:'var(--text-secondary)',lineHeight:2,fontFamily:'var(--font-serif)'}}>{d.ji.join('　')}</div>
              </div>
            </div>

            {/* Card 4: Gods + Positions */}
            <div style={{background:'var(--surface)',border:'1px solid var(--border)',padding:'12px 14px'}}>
              <Row label="吉神" text={d.jishen.join('　')}/>
              <Row label="凶煞" text={d.xiongsha.join('　')}/>
              <div style={{borderTop:'1px solid var(--border)',marginTop:8,paddingTop:8,display:'flex',gap:16,flexWrap:'wrap'}}>
                {Object.entries(d.positions).map(([k,v])=><span key={k} style={{fontSize:12,color:'var(--text-secondary)',fontFamily:'var(--font-serif)'}}><span style={{fontSize:10,color:'var(--text-faint)'}}>{k}</span> {v}</span>)}
              </div>
              <div style={{fontSize:11,color:'var(--text-muted)',marginTop:6}}>冲{d.chong}　空亡{d.xunkong}</div>
              <div style={{fontSize:10,color:'var(--text-faint)',marginTop:4,fontFamily:'var(--font-serif)'}}>{d.pengzu}</div>
            </div>

            {/* Card 5: 12 Hours */}
            <div style={{background:'var(--surface)',border:'1px solid var(--border)',padding:'12px 14px'}}>
              <div style={{fontSize:11,color:'var(--text-faint)',fontFamily:'var(--font-mono)',marginBottom:8}}>十二时辰</div>
              <div style={{display:'grid',gridTemplateColumns:'repeat(6,1fr)',gap:3}}>
                {d.hours.map(h=><div key={h.shichen} style={{textAlign:'center',padding:'5px 0',background:h.luck==='吉'?'rgba(26,138,74,0.06)':'var(--bg-subtle)',border:'1px solid var(--border)'}}>
                  <div style={{fontSize:14,fontWeight:700,color:h.luck==='吉'?'#1a8a4a':'var(--text-secondary)',fontFamily:'var(--font-serif)'}}>{h.shichen}</div>
                  <div style={{fontSize:8,color:'var(--text-faint)'}}>{h.hours}</div>
                  <div style={{fontSize:10,color:'var(--text-muted)',fontFamily:'var(--font-serif)'}}>{h.ganzhi}</div>
                  <div style={{fontSize:9,color:h.luck==='吉'?'#1a8a4a':'var(--text-faint)'}}>{h.luck}</div>
                </div>)}
              </div>
            </div>
          </div>

          {/* RIGHT sidebar */}
          <div style={{display:'flex',flexDirection:'column',gap:12}}>
            {/* Ruishou image */}
            <div style={{background:'var(--surface)',border:'1px solid var(--border)',position:'relative',overflow:'hidden'}}>
              <div style={{position:'absolute',top:0,left:0,right:0,height:2,background:'var(--accent)'}}/>
              {ruishouImg && !imgError ? (
                <img src={`/ruishou/${ruishouImg}`} alt={d.ruishou}
                  onError={()=>setImgError(true)}
                  style={{width:'100%',display:'block',aspectRatio:'3/4',objectFit:'cover'}}/>
              ) : (
                <div style={{aspectRatio:'3/4',display:'flex',alignItems:'center',justifyContent:'center',padding:20}}>
                  <div style={{textAlign:'center'}}>
                    <div style={{fontSize:64,lineHeight:1,opacity:0.12,fontFamily:'var(--font-serif)',color:'var(--accent)'}}>{d.ruishou?.slice(0,1)||'瑞'}</div>
                    <div style={{fontSize:10,color:'var(--text-faint)',marginTop:8}}>放置瑞兽图至 /ruishou/</div>
                  </div>
                </div>
              )}
              <div style={{padding:'8px 12px',borderTop:'1px solid var(--border)',textAlign:'center'}}>
                <div style={{fontSize:14,color:'var(--accent)',fontFamily:'var(--font-serif)',fontWeight:700}}>{d.ruishou}</div>
                <div style={{fontSize:10,color:'var(--text-faint)',marginTop:2}}>日支{d.day_zhi} · {d.day_wuxing}行</div>
              </div>
            </div>

            {/* Xingxiu song */}
            {d.xingxiu.song&&<div style={{background:'var(--surface)',border:'1px solid var(--border)',padding:'12px 14px'}}>
              <div style={{fontSize:10,color:'var(--text-faint)',fontFamily:'var(--font-mono)',marginBottom:6}}>{d.xingxiu.name}宿歌诀</div>
              <div style={{fontSize:12,color:'var(--text-secondary)',fontFamily:'var(--font-serif)',lineHeight:2.2}}>{d.xingxiu.song}</div>
            </div>}

            {/* Officer detail */}
            {d.officer.detail&&<div style={{background:'var(--surface)',border:'1px solid var(--border)',padding:'12px 14px'}}>
              <div style={{fontSize:10,color:'var(--text-faint)',fontFamily:'var(--font-mono)',marginBottom:6}}>{d.officer.name}日详解</div>
              <div style={{fontSize:12,color:'var(--text-secondary)',fontFamily:'var(--font-serif)',lineHeight:1.8}}>{d.officer.detail}</div>
            </div>}

            {/* Jieqi */}
            {d.jieqi?.prev&&<div style={{background:'var(--surface)',border:'1px solid var(--border)',padding:'10px 14px',fontSize:11,color:'var(--text-muted)',fontFamily:'var(--font-serif)',lineHeight:1.8}}>
              <div>节气：{d.jieqi.prev.name} {d.jieqi.prev.date}</div>
              {d.jieqi.next&&<div>中气：{d.jieqi.next.name} {d.jieqi.next.date}</div>}
            </div>}
          </div>
        </div>
      </div>

      {/* Share modal */}
      {shareUrl&&<div style={{position:'fixed',inset:0,zIndex:9999,background:'rgba(0,0,0,0.5)',display:'flex',alignItems:'center',justifyContent:'center'}} onClick={()=>setShareUrl(null)}>
        <div style={{background:'var(--surface)',padding:16,maxHeight:'92vh',overflow:'auto'}} onClick={e=>e.stopPropagation()}>
          <div style={{textAlign:'center',marginBottom:10}}>
            <a href={shareUrl} download={`每日守护_${d.date}.png`} style={{display:'inline-block',padding:'6px 16px',background:'var(--accent)',color:'#fff',textDecoration:'none',fontSize:13,fontFamily:'var(--font-serif)'}}>下载分享图</a>
            <button onClick={()=>setShareUrl(null)} style={{marginLeft:12,padding:'6px 12px',border:'1px solid var(--border)',background:'var(--bg-subtle)',cursor:'pointer',fontSize:12}}>关闭</button>
          </div>
          <img src={shareUrl} style={{maxWidth:'100%',maxHeight:'75vh',display:'block',margin:'0 auto'}} alt=""/>
        </div>
      </div>}
    </div>
  )
}

function Ind({label,value,sub,color}){
  return <div style={{textAlign:'center'}}>
    <div style={{fontSize:9,color:'var(--text-faint)',fontFamily:'var(--font-mono)',marginBottom:3}}>{label}</div>
    <div style={{fontSize:15,fontWeight:700,color:'var(--text-primary)',fontFamily:'var(--font-serif)'}}>{value}</div>
    {sub&&<div style={{fontSize:10,color:color||'var(--text-faint)',marginTop:2}}>{sub}</div>}
  </div>
}
function Row({label,text}){
  return <div style={{marginBottom:6}}>
    <span style={{fontSize:10,color:'var(--text-faint)',fontFamily:'var(--font-mono)',marginRight:8}}>{label}</span>
    <span style={{fontSize:12,color:'var(--text-secondary)',fontFamily:'var(--font-serif)',lineHeight:1.8}}>{text}</span>
  </div>
}
function wrapDraw(ctx,text,x,y,maxW,lh){let line='',ly=y;for(const ch of text){const t=line+ch;if(ctx.measureText(t).width>maxW){ctx.fillText(line,x,ly);ly+=lh;line=ch}else line=t};if(line)ctx.fillText(line,x,ly)}
