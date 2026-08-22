import React, { useRef, useEffect, useCallback, useMemo } from 'react'

/* ═══════════════════════════════════════════════════════════════
   细腻粒子引擎
   
   审美: 墨尘·绢丝·晨雾
   粒径: 0.3–1.2px    (比笔尖还细)
   透明: 0.06–0.18    (若隐若现)
   轨迹: 3–5帧丝线    (蚕丝般渐隐)
   运动: Perlin噪声    (有机·无规则·缓慢)
   ═══════════════════════════════════════════════════════════════ */

// ─── Noise ───────────────────────────────────────────────────────
const PM = new Uint8Array(512)
;(()=>{const p=Array.from({length:256},(_,i)=>i);for(let i=255;i>0;i--){const j=0|Math.random()*(i+1);[p[i],p[j]]=[p[j],p[i]]};for(let i=0;i<512;i++)PM[i]=p[i&255]})()
function nz(x,y){
  const xi=Math.floor(x)&255,yi=Math.floor(y)&255
  const xf=x-Math.floor(x),yf=y-Math.floor(y)
  const u=xf*xf*(3-2*xf),v=yf*yf*(3-2*yf)
  const a=PM[xi]+yi,b=PM[xi+1]+yi
  const g=(h,dx,dy)=>((h&1)?-dx:dx)+((h&2)?-dy:dy)
  return(1+(1-u)*((1-v)*g(PM[a],xf,yf)+v*g(PM[a+1],xf,yf-1))+u*((1-v)*g(PM[b],xf-1,yf)+v*g(PM[b+1],xf-1,yf-1)))/2
}

// ─── Hook ────────────────────────────────────────────────────────
function useCanvas(ref,fn,deps=[]){
  const frame=useRef(0)
  useEffect(()=>{
    const c=ref.current;if(!c)return
    const ctx=c.getContext('2d'),dpr=window.devicePixelRatio||1
    const fit=()=>{const r=c.getBoundingClientRect();c.width=r.width*dpr;c.height=r.height*dpr;ctx.setTransform(dpr,0,0,dpr,0,0)}
    fit();const ro=new ResizeObserver(fit);ro.observe(c)
    const go=ts=>{const r=c.getBoundingClientRect();ctx.clearRect(0,0,r.width,r.height);fn(ctx,r.width,r.height,ts*.001);frame.current=requestAnimationFrame(go)}
    frame.current=requestAnimationFrame(go)
    return()=>{cancelAnimationFrame(frame.current);ro.disconnect()}
  },[ref,fn,...deps])
}

// ─── Ink dot (core draw primitive) ───────────────────────────────
function dot(ctx,x,y,r,rgb,a){
  ctx.fillStyle=`rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`
  ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill()
}
function silk(ctx,trail,rgb,baseA,baseR){
  for(let i=0;i<trail.length;i++){
    const f=i/trail.length
    dot(ctx,trail[i].x,trail[i].y, baseR*(0.3+f*0.7), rgb, baseA*f*f)
  }
}

// Bezier point
function bz(t,p0,p1,cp){
  const i=1-t
  return { x:i*i*p0.x+2*i*t*cp.x+t*t*p1.x, y:i*i*p0.y+2*i*t*cp.y+t*t*p1.y }
}

const WXR={木:[74,122,90],火:[160,78,50],土:[140,120,76],金:[90,90,120],水:[64,90,120]}
const HUAR={'化禄':[160,60,42],'化权':[64,90,120],'化科':[64,110,80],'化忌':[110,68,120]}

// ═══════════════════════════════════════════════════════════════
// ❶ 紫微 · 四化绢丝飞线
// ═══════════════════════════════════════════════════════════════

export function ZiweiVis({ palaces=[], feihua=[], soulIdx=0, layer='natal' }){
  const ref=useRef(null)
  const ps=useRef([])
  const dust=useRef([])
  const ZW=[[11,10,9,8],[0,-1,-1,7],[1,-1,-1,6],[2,3,4,5]]

  const pPos=useCallback((idx,w,h)=>{
    const M=4,CW=(w-M*2)/4,CH=(h-M*2)/4
    for(let r=0;r<4;r++)for(let c=0;c<4;c++)if(ZW[r][c]===idx)return{x:M+c*CW+CW/2,y:M+r*CH+CH/2}
    return{x:w/2,y:h/2}
  },[])

  useEffect(()=>{
    const arr=[]
    ;(feihua||[]).forEach(f=>{
      const col=HUAR[f.type]||[100,100,100]
      // fh_type 区分：离心自化（喷散）/向心自化（内收）/普通飞宫（贝塞尔流）
      // 离心 = self且向外，向心 = self但意向对宫，普通 = 跨宫
      const fhType = f.fh_type || (f.from===f.to ? '离心自化' : '普通飞宫')
      const isSelfOut = fhType === '离心自化'
      const isSelfIn  = fhType === '向心自化'
      const isFly     = fhType === '普通飞宫'
      const self = isSelfOut || isSelfIn  // 都是同宫起化
      
      // 粒子数：离心自化 = 喷散较多，向心自化 = 内收较少，普通 = 中等
      const count = isSelfOut ? 14 : isSelfIn ? 10 : 25
      for(let i=0;i<count;i++){
        arr.push({
          pr:i/count, sp:0.06+Math.random()*0.05,
          from:f.from, to:f.to, col,
          fhType,         // 'self_out' / 'self_in' / 'fly'
          isSelfOut, isSelfIn, isFly,
          rad: isSelfOut ? 14+Math.random()*10 : 10+Math.random()*6,
          ang:(i/count)*Math.PI*2,
          sz:0.3+Math.random()*0.9,
          trail:[], ph:Math.random()*6.28,
          // 化忌粒子加 dash 效果（让凶象视觉区分）
          isJi: f.type === '化忌',
        })
      }
    })
    // ambient dust
    const d=[]
    for(let i=0;i<30;i++) d.push({x:Math.random(),y:Math.random(),vx:(Math.random()-.5)*.0001,vy:(Math.random()-.5)*.0001,sz:.3+Math.random()*.4,ph:Math.random()*6.28})
    ps.current=arr; dust.current=d
  },[feihua,layer])

  const draw=useCallback((ctx,w,h,t)=>{
    // dust
    dust.current.forEach(d=>{
      d.x+=d.vx+nz(d.x*3,t*.3)*.0002
      d.y+=d.vy+nz(d.y*3+50,t*.3)*.0002
      if(d.x<0)d.x=1;if(d.x>1)d.x=0;if(d.y<0)d.y=1;if(d.y>1)d.y=0
      const a=.04+Math.sin(t*.4+d.ph)*.015
      dot(ctx,d.x*w,d.y*h,d.sz,[140,136,125],a)
    })
    // palace halos
    for(let i=0;i<Math.min(palaces.length,12);i++){
      const p=pPos(i,w,h)
      const pulse=Math.sin(t*1.2+i*.5)*.008+.025
      const c=i===soulIdx?[180,48,32]:[106,148,120]
      dot(ctx,p.x,p.y,Math.min(w,h)*.055,c,pulse)
    }
    // feihua streams — 三种飞化不同视觉
    ps.current.forEach(p=>{
      p.pr=(p.pr+p.sp*.016)%1
      const f=pPos(p.from,w,h),to=pPos(p.to,w,h)
      let px,py
      if(p.isSelfOut){
        // 离心自化：粒子从宫位中心向外喷散
        p.ang += p.sp*.04
        const r = p.rad * (0.4 + p.pr * 0.8)  // 半径随 pr 增长（喷散）
        px=f.x+Math.cos(p.ang)*r
        py=f.y+Math.sin(p.ang)*r
      } else if(p.isSelfIn){
        // 向心自化：粒子从宫位外围向中心内收，并暗示对宫
        p.ang += p.sp*.02
        const r = p.rad * (1.0 - p.pr * 0.7)  // 半径随 pr 缩小（内收）
        px=f.x+Math.cos(p.ang)*r
        py=f.y+Math.sin(p.ang)*r
      } else {
        // 普通飞宫：贝塞尔曲线从 from 流向 to
        const dx=to.x-f.x,dy=to.y-f.y,dist=Math.sqrt(dx*dx+dy*dy)||1
        const cx=(f.x+to.x)/2+(-dy/dist)*30, cy=(f.y+to.y)/2+(dx/dist)*30
        const pt=bz(p.pr,f,to,{x:cx,y:cy})
        px=pt.x; py=pt.y
      }
      px+=nz(px*.015+t*.5,py*.015)*2.5
      py+=nz(px*.015,py*.015+t*.5+30)*2.5
      p.trail.push({x:px,y:py})
      if(p.trail.length>5) p.trail.shift()
      // 化忌粒子稍微更亮 + 闪烁，让凶象醒目
      const baseA = p.isJi ? 0.18 : 0.14
      const pulse = p.isJi ? Math.sin(t*3+p.ph)*.06 : Math.sin(t*2+p.ph)*.04
      silk(ctx,p.trail,p.col,baseA,p.sz)
      dot(ctx,px,py,p.sz,p.col,baseA+pulse)
    })
  },[palaces,soulIdx,pPos])

  useCanvas(ref,draw,[feihua,layer])
  return <canvas ref={ref} style={{width:"100%",aspectRatio:"5/1",maxWidth:320,display:"block",margin:"0 auto 4px",opacity:0.6}}/>
}

// ═══════════════════════════════════════════════════════════════
// ❷ 六爻 · 爻线墨流
// ═══════════════════════════════════════════════════════════════

export function LiuyaoVis({ yaos=[] }){
  const ref=useRef(null)
  const ps=useRef([])

  useEffect(()=>{
    const arr=[]
    yaos.forEach((y,i)=>{
      const col=WXR[y.wuxing]||[100,100,100]
      const n=y.is_changing?35:12
      for(let j=0;j<n;j++){
        arr.push({
          yi:i, pr:Math.random(), sp:y.is_changing?.2+Math.random()*.15:.04+Math.random()*.04,
          col, sz:y.is_changing?.4+Math.random()*.8:.3+Math.random()*.5,
          yin:y.line==='阴', changing:y.is_changing, trail:[], ph:Math.random()*6.28,
        })
      }
    })
    ps.current=arr
  },[yaos])

  const draw=useCallback((ctx,w,h,t)=>{
    const LX=w*.16, LW=w*.52, yPos=i=>h-24-i*(h-48)/Math.max(yaos.length-1,5)

    // dim structure lines
    yaos.forEach((y,i)=>{
      const cy=yPos(i)
      ctx.strokeStyle='rgba(180,176,168,.12)'
      ctx.lineWidth=2.5; ctx.lineCap='round'
      if(y.line==='阳'){
        ctx.beginPath();ctx.moveTo(LX,cy);ctx.lineTo(LX+LW,cy);ctx.stroke()
      } else {
        const gap=8
        ctx.beginPath();ctx.moveTo(LX,cy);ctx.lineTo(LX+LW/2-gap,cy);ctx.stroke()
        ctx.beginPath();ctx.moveTo(LX+LW/2+gap,cy);ctx.lineTo(LX+LW,cy);ctx.stroke()
      }
    })

    // particles
    ps.current.forEach(p=>{
      p.pr=(p.pr+p.sp*.016)%1
      const cy=yPos(p.yi)
      let px
      if(p.yin){
        const half=LW/2,gap=8
        if(p.pr<.45) px=LX+p.pr/.45*(half-gap)
        else if(p.pr<.55) px=LX+half-gap+(p.pr-.45)/.1*gap*2
        else px=LX+half+gap+(p.pr-.55)/.45*(half-gap)
      } else {
        px=LX+p.pr*LW
      }
      const dy=nz(px*.012+p.yi,t*1.2)*(p.changing?6:2)
      const py=cy+dy

      p.trail.push({x:px,y:py})
      if(p.trail.length>(p.changing?5:3)) p.trail.shift()
      silk(ctx,p.trail,p.col,p.changing?.12:.07,p.sz)
      dot(ctx,px,py,p.sz,p.col,p.changing?.15:.08)
    })
  },[yaos])

  useCanvas(ref,draw,[yaos])
  return <canvas ref={ref} style={{width:"100%",aspectRatio:"6/1",maxWidth:360,display:"block",margin:"0 auto 4px",opacity:0.6}}/>
}

// ═══════════════════════════════════════════════════════════════
// ❸ 八字 · 五行晨雾
// ═══════════════════════════════════════════════════════════════

export function BaziVis({ pillars=[], dayun=[] }){
  const ref=useRef(null)
  const ps=useRef([])

  useEffect(()=>{
    const arr=[]
    pillars.forEach((p,i)=>{
      const cG=WXR[p.wuxing_gan]||[100,100,100]
      const cZ=WXR[p.wuxing_zhi]||[100,100,100]
      for(let j=0;j<15;j++){
        arr.push({pi:i,ang:Math.random()*6.28,rad:14+Math.random()*22,sp:(Math.random()-.5)*.3,col:cG,sz:.3+Math.random()*.7,yOff:-20,ph:Math.random()*6.28})
        arr.push({pi:i,ang:Math.random()*6.28,rad:14+Math.random()*22,sp:(Math.random()-.5)*.3,col:cZ,sz:.3+Math.random()*.7,yOff:20,ph:Math.random()*6.28})
      }
    })
    // timeline particles
    for(let i=0;i<20;i++){
      arr.push({tl:true,x:Math.random(),sp:.015+Math.random()*.02,sz:.3+Math.random()*.3,ph:Math.random()*6.28})
    }
    ps.current=arr
  },[pillars])

  const draw=useCallback((ctx,w,h,t)=>{
    const pw=w/5, startX=(w-pw*4)/2, cy=h*.38
    const tlY=h*.82

    // timeline line
    ctx.strokeStyle='rgba(180,176,168,.08)';ctx.lineWidth=1
    ctx.beginPath();ctx.moveTo(w*.08,tlY);ctx.lineTo(w*.92,tlY);ctx.stroke()

    // dayun dots on timeline
    const tlW=w*.84
    dayun.slice(0,6).forEach((d,i)=>{
      const x=w*.08+i/(Math.max(dayun.length-1,5))*tlW
      const col=d.quality==='吉'?[74,122,90]:[168,88,64]
      const pulse=.04+Math.sin(t*1.5+i)*.015
      dot(ctx,x,tlY,6,col,pulse)
      dot(ctx,x,tlY,1.5,col,.15)
    })

    // pillar aura particles
    ps.current.forEach(p=>{
      if(p.tl){
        p.x+=p.sp*.008;if(p.x>1)p.x=0
        const py=tlY+nz(p.x*5,t)*.01*h
        dot(ctx,p.x*w,py,p.sz,[140,136,125],.05)
        return
      }
      p.ang+=p.sp*.015
      const cx=startX+p.pi*pw+pw/2
      const cyy=cy+p.yOff
      const nr=nz(p.ang+p.pi,t*.4)*5
      const px=cx+Math.cos(p.ang)*(p.rad+nr)
      const py=cyy+Math.sin(p.ang)*(p.rad*.55+nr)
      const a=.06+Math.sin(t*.6+p.ph)*.025
      dot(ctx,px,py,p.sz*1.8,p.col,a*.4)
      dot(ctx,px,py,p.sz,p.col,a)
    })
  },[pillars,dayun])

  useCanvas(ref,draw,[pillars,dayun])
  return <canvas ref={ref} style={{width:"100%",aspectRatio:"6/1",maxWidth:380,display:"block",margin:"0 auto 4px",opacity:0.6}}/>
}

// ═══════════════════════════════════════════════════════════════
// ❹ 奇门 · 宫间烟丝
// ═══════════════════════════════════════════════════════════════

export function QimenVis({ palaces=[] }){
  const ref=useRef(null)
  const ps=useRef([])
  const order=[4,9,2,3,5,7,8,1,6]

  useEffect(()=>{
    const arr=[]
    for(let i=0;i<90;i++){
      const fi=Math.floor(Math.random()*9), ti=Math.floor(Math.random()*9)
      const fp=palaces.find(p=>p.position===order[fi])
      const col=fp?.is_auspicious?[74,122,90]:fp?.is_auspicious===false?[168,88,64]:[130,126,118]
      arr.push({
        fr:Math.floor(fi/3),fc:fi%3, tr:Math.floor(ti/3),tc:ti%3,
        pr:Math.random(), sp:.02+Math.random()*.03,
        col, sz:.3+Math.random()*.7, trail:[], ph:Math.random()*6.28,
      })
    }
    ps.current=arr
  },[palaces])

  const draw=useCallback((ctx,w,h,t)=>{
    const M=4,CW=(w-M*2)/3,CH=(h-M*2)/3

    // palace ambient glow
    order.forEach((pos,gi)=>{
      const r=Math.floor(gi/3),c=gi%3
      const p=palaces.find(pp=>pp.position===pos)
      if(!p) return
      const cx=M+c*CW+CW/2, cy=M+r*CH+CH/2
      const col=p.is_auspicious?[74,122,90]:p.is_auspicious===false?[168,88,64]:[130,126,118]
      const a=.025+Math.sin(t+gi)*.01
      dot(ctx,cx,cy,Math.min(CW,CH)*.3,col,a)
    })

    // flowing particles
    ps.current.forEach(p=>{
      p.pr=(p.pr+p.sp*.016)%1
      const fx=M+p.fc*CW+CW/2, fy=M+p.fr*CH+CH/2
      const tx=M+p.tc*CW+CW/2, ty=M+p.tr*CH+CH/2
      const px=fx+(tx-fx)*p.pr+nz(p.pr*4+t,p.fr+p.fc)*8
      const py=fy+(ty-fy)*p.pr+nz(p.pr*4+t+50,p.fr+p.fc)*8

      p.trail.push({x:px,y:py})
      if(p.trail.length>4)p.trail.shift()
      silk(ctx,p.trail,p.col,.08,p.sz)
      dot(ctx,px,py,p.sz,p.col,.1)
    })
  },[palaces])

  useCanvas(ref,draw,[palaces])
  return <canvas ref={ref} style={{width:"100%",aspectRatio:"3/1",maxWidth:280,display:"block",margin:"0 auto 4px",opacity:0.6}}/>
}

// ═══════════════════════════════════════════════════════════════
// ❺ 飞星 · 金尘罗盘
// ═══════════════════════════════════════════════════════════════

export function FengshuiVis({ palaces=[] }){
  const ref=useRef(null)
  const orbit=useRef([])
  const order=[4,9,2,3,5,7,8,1,6]

  useEffect(()=>{
    const arr=[]
    for(let i=0;i<50;i++){
      arr.push({
        ang:Math.random()*6.28, rad:.38+Math.random()*.04-.02,
        sp:.06+Math.random()*.1, sz:.3+Math.random()*.5, ph:Math.random()*6.28,
      })
    }
    orbit.current=arr
  },[])

  const draw=useCallback((ctx,w,h,t)=>{
    const cx=w/2,cy=h/2,R=Math.min(w,h)*.32

    // compass rings
    ctx.strokeStyle='rgba(180,176,168,.06)';ctx.lineWidth=.5
    ctx.beginPath();ctx.arc(cx,cy,R*1.15,0,Math.PI*2);ctx.stroke()
    ctx.beginPath();ctx.arc(cx,cy,R*1.25,0,Math.PI*2);ctx.stroke()

    // orbit particles (gold dust)
    orbit.current.forEach(p=>{
      p.ang+=p.sp*.004
      const r=p.rad*Math.min(w,h)
      const px=cx+Math.cos(p.ang)*r+nz(p.ang*2,t)*.01*w
      const py=cy+Math.sin(p.ang)*r+nz(p.ang*2+50,t)*.01*h
      const a=.06+Math.sin(t*.3+p.ph)*.025
      dot(ctx,px,py,p.sz*1.5,[180,160,100],a*.5)
      dot(ctx,px,py,p.sz,[180,160,100],a)
    })

    // palace cells glow
    const CW=Math.min(w,h)*.22
    order.forEach((pos,gi)=>{
      const r=Math.floor(gi/3),c=gi%3
      const px=cx+(c-1)*CW*1.1, py=cy+(r-1)*CW*1.1
      const pp=palaces.find(p=>p.position===pos)
      if(!pp) return
      const ms=pp.mountain_star,fs=pp.facing_star
      // subtle cell glow
      const a=.02+Math.sin(t*1.2+gi)*.008
      dot(ctx,px,py,CW*.35,[140,130,110],a)
    })

    // compass needle
    const nA=t*.25
    ctx.strokeStyle='rgba(180,60,40,.1)';ctx.lineWidth=1.5;ctx.lineCap='round'
    ctx.beginPath()
    ctx.moveTo(cx+Math.cos(nA)*10,cy+Math.sin(nA)*10)
    ctx.lineTo(cx-Math.cos(nA)*10,cy-Math.sin(nA)*10)
    ctx.stroke()
    dot(ctx,cx,cy,2,[180,60,40],.12)
  },[palaces])

  useCanvas(ref,draw,[palaces])
  return <canvas ref={ref} style={{width:"100%",aspectRatio:"3/1",maxWidth:260,display:"block",margin:"0 auto 4px",opacity:0.6}}/>
}
