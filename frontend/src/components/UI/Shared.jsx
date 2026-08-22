import React from 'react'
import { clickable } from '../../utils/a11y'

// ─── Stone Materials ─────────────────────────────────────────────

export const STONES = {
  tianhuang: { name:"田黄石", bg:"linear-gradient(145deg,#e8c868 0%,#d4a030 30%,#c8922a 60%,#dab048 100%)", glow:"rgba(212,160,48,0.3)", text:"#5a3a08", textSub:"#8a6a20", ink:"#5a3a08", inkLight:"rgba(90,58,8,0.12)", vein:"rgba(180,120,20,0.2)" },
  jixue:    { name:"鸡血石", bg:"linear-gradient(135deg,#e8e0d8 0%,#d0c4b8 25%,#c83028 45%,#d0c4b8 55%,#e0d8d0 70%,#c03020 85%,#d8ccc0 100%)", glow:"rgba(200,48,40,0.25)", text:"#581810", textSub:"#804030", ink:"#581810", inkLight:"rgba(88,24,16,0.1)", vein:"rgba(200,48,32,0.3)" },
  shoushan: { name:"寿山石", bg:"linear-gradient(150deg,#e8b870 0%,#d89848 35%,#c88040 65%,#daa058 100%)", glow:"rgba(200,128,64,0.25)", text:"#4a2808", textSub:"#7a5020", ink:"#4a2808", inkLight:"rgba(74,40,8,0.1)", vein:"rgba(160,100,40,0.2)" },
  qingtian: { name:"青田石", bg:"linear-gradient(140deg,#a8c8b8 0%,#88b0a0 30%,#78a898 55%,#90b8a8 80%,#80a898 100%)", glow:"rgba(120,168,152,0.3)", text:"#1a3a2e", textSub:"#3a6050", ink:"#1a3a2e", inkLight:"rgba(26,58,46,0.1)", vein:"rgba(100,160,130,0.25)" },
  furong:   { name:"芙蓉石", bg:"linear-gradient(135deg,#f0d0c8 0%,#e8b8b0 35%,#e0a8a0 60%,#ecc0b8 100%)", glow:"rgba(224,168,160,0.3)", text:"#5a2020", textSub:"#8a4848", ink:"#5a2020", inkLight:"rgba(90,32,32,0.08)", vein:"rgba(200,140,130,0.2)" },
  balin:    { name:"巴林石", bg:"linear-gradient(130deg,#c0b0d0 0%,#a890c0 30%,#9880b8 55%,#b0a0c8 80%,#a088b8 100%)", glow:"rgba(152,128,184,0.3)", text:"#281840", textSub:"#503870", ink:"#281840", inkLight:"rgba(40,24,64,0.08)", vein:"rgba(130,100,170,0.2)" },
  changhua: { name:"昌化石", bg:"linear-gradient(145deg,#6a5a50 0%,#584840 30%,#785030 50%,#5a4a40 75%,#685848 100%)", glow:"rgba(88,72,64,0.3)", text:"#e8d8c8", textSub:"#c0a890", ink:"#e8d8c8", inkLight:"rgba(232,216,200,0.12)", vein:"rgba(120,80,48,0.3)" },
  lichidong:{ name:"荔枝冻", bg:"linear-gradient(140deg,#f8f0f0 0%,#f0e0e8 25%,#e8d8e0 50%,#f0e8f0 75%,#f4eae8 100%)", glow:"rgba(240,224,232,0.4)", text:"#4a3040", textSub:"#7a5868", ink:"#4a3040", inkLight:"rgba(74,48,64,0.08)", vein:"rgba(220,180,200,0.25)" },
  heitian:  { name:"黑田石", bg:"linear-gradient(140deg,#2a2a28 0%,#1a1a18 30%,#3a3028 55%,#222220 80%,#1a1a18 100%)", glow:"rgba(40,40,30,0.4)", text:"#e8d8c0", textSub:"#a09080", ink:"#e8d8c0", inkLight:"rgba(232,216,192,0.10)", vein:"rgba(60,50,40,0.3)" },
  zhusha:   { name:"朱砂石", bg:"linear-gradient(140deg,#c83828 0%,#b03020 30%,#d04030 50%,#a82818 75%,#c03828 100%)", glow:"rgba(200,56,40,0.35)", text:"#fff0e0", textSub:"#f0d0b0", ink:"#fff0e0", inkLight:"rgba(255,240,224,0.12)", vein:"rgba(180,50,30,0.3)" },
}

export const MODULES = [
  { id:"guardian",  stone:"zhusha",   glyph:"守", name:"守护",   desc:"每日推送" },
  { id:"agent",     stone:"lichidong",glyph:"问", name:"问答",   desc:"AI解读" },
  { id:"yijing",    stone:"heitian",  glyph:"易", name:"易经",   desc:"知识图谱" },
  { id:"bazi",      stone:"tianhuang", glyph:"柱", name:"八字",   desc:"四柱格局" },
  { id:"ziwei",     stone:"jixue",    glyph:"星", name:"紫微",   desc:"十二宫星" },
  { id:"dayun",     stone:"shoushan", glyph:"运", name:"运程",   desc:"大运流年" },
  { id:"qimen",     stone:"qingtian", glyph:"门", name:"奇门",   desc:"九宫八门" },
  { id:"liuyao",    stone:"furong",   glyph:"卦", name:"六爻",   desc:"纳甲占断" },
  { id:"fengshui",  stone:"balin",    glyph:"宅", name:"飞星",   desc:"玄空风水" },
  { id:"knowledge", stone:"changhua", glyph:"典", name:"典籍",   desc:"古籍检索" },
]

export const WXC = { 木:"#4a7a5a", 火:"#b05838", 土:"#a08a5a", 金:"#6a6a8a", 水:"#4a6a8a" }

// ─── Seal Component ──────────────────────────────────────────────

export function Seal({ mod, isStamped, onClick }) {
  const st = STONES[mod.stone]
  return (
    <div {...clickable(onClick)} style={{width:74,cursor:"pointer",textAlign:"center",transition:"transform .15s",transform:isStamped?"rotate(-2deg)":"none"}}>
      <div style={{width:68,height:68,margin:"0 auto",position:"relative",background:st.bg,
        boxShadow:isStamped?`0 2px 10px ${st.glow},inset 0 1px 3px rgba(255,255,255,0.3)`:`0 1px 4px rgba(0,0,0,0.06),inset 0 1px 2px rgba(255,255,255,0.2)`,
        transition:"all .2s",overflow:"hidden"}}>
        <div style={{position:"absolute",inset:0,opacity:0.5,backgroundImage:`radial-gradient(ellipse at 20% 30%,${st.vein} 0%,transparent 50%),radial-gradient(ellipse at 70% 70%,${st.vein} 0%,transparent 40%),radial-gradient(ellipse at 50% 10%,rgba(255,255,255,0.15) 0%,transparent 30%)`}}/>
        <div style={{position:"absolute",inset:6,border:`2px solid ${st.ink}`,opacity:isStamped?0.7:0.15,transition:"opacity .2s"}}/>
        <div style={{position:"absolute",inset:10,border:`1px solid ${st.ink}`,opacity:isStamped?0.4:0.08,transition:"opacity .2s"}}/>
        <div style={{position:"absolute",inset:0,display:"flex",alignItems:"center",justifyContent:"center",
          fontSize:22,fontWeight:900,fontFamily:"var(--font-serif)",color:st.ink,opacity:isStamped?1:0.3,transition:"opacity .2s",lineHeight:1}}>
          {mod.glyph}
        </div>
        {isStamped && <>
          <div style={{position:"absolute",top:2,left:3,width:4,height:3,background:`${st.ink}30`}}/>
          <div style={{position:"absolute",bottom:4,right:2,width:3,height:3,background:`${st.ink}20`,transform:"rotate(15deg)"}}/>
        </>}
      </div>
      <div style={{marginTop:5,fontSize:12,fontWeight:isStamped?600:400,color:isStamped?st.text:"var(--muted)",fontFamily:"var(--font-serif)",transition:"color .2s"}}>{mod.name}</div>
      <div style={{fontSize:11,color:isStamped?st.textSub:"var(--faint)"}}>{st.name}</div>
    </div>
  )
}

// ─── Mountain Divider ────────────────────────────────────────────

export function Mtn({ color = "rgba(140,136,125,0.1)", h = 30, style }) {
  return (
    <svg viewBox="0 0 800 60" preserveAspectRatio="none" style={{width:"100%",height:h,display:"block",...style}}>
      <path d="M0 60 L0 42 Q80 30 160 38 Q240 20 340 32 Q420 12 500 28 Q580 18 660 30 Q740 22 800 35 L800 60Z" fill={color}/>
    </svg>
  )
}

// ─── Ink Border ──────────────────────────────────────────────────

export function InkBorder({ color = "var(--faint)", children, style, active }) {
  return (
    <div style={{
      position:"relative", padding:"12px 14px",
      borderLeft:`2px solid ${active ? "var(--accent)" : color}`,
      borderBottom:`1px solid ${color}`,
      background: active ? "rgba(207,59,44,0.03)" : "transparent",
      transition:"all .2s", ...style,
    }}>
      <div style={{position:"absolute",top:-2,left:-4,width:5,height:5,background:active?"var(--accent)":color,transform:"rotate(45deg)"}}/>
      {children}
    </div>
  )
}
