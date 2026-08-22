import React, { useRef, useEffect, useState } from 'react'
import * as THREE from 'three'
import { knowledgeApi } from '../../api/client'

const P={taiji:'#d94025',yang:'#e8a840',yin:'#5090c0',sixiang:'#d4a030',bagua:'#2a9a6a',wuxing:'#e0a020',tiangan:'#d07830',dizhi:'#4080b8',h64:'#3a8a60',sub:'#909080',siling:'#40a868',xingxiu:'#5890b0',shishen:'#e06040',ziwei:'#a050c0',qimen:'#30a080',nayin:'#c08840'}
function cc(n){const L=n.layer||0;if(L===0)return P.taiji;if(L===1)return n.label==='阳'?P.yang:P.yin;if(L===2)return P.sixiang;if(L===3)return P.bagua;if(L===4)return P.wuxing;if(n.category==='tiangan')return P.tiangan;if(n.category==='dizhi')return P.dizhi;if(L===6)return P.h64;return P[n.category]||P.sub}
function mkL(t,c,fs){const cv=document.createElement('canvas');cv.width=512;cv.height=192;const x=cv.getContext('2d');x.font=`600 ${(fs||40)*3}px "Noto Serif SC","SimSun",serif`;x.textAlign='center';x.textBaseline='middle';x.fillStyle=c;x.fillText(t,256,96);const tx=new THREE.CanvasTexture(cv);tx.needsUpdate=true;return new THREE.Sprite(new THREE.SpriteMaterial({map:tx,transparent:true,depthTest:false}))}
function curve(a,b,d){const m=new THREE.Vector3().lerpVectors(a,b,0.5);m.y+=d||0;return new THREE.QuadraticBezierCurve3(a,m,b).getPoints(32)}
function nfo(n){if(!n)return null;const c=n.category;if(c==='root')return{t:'太极',d:'易有太极，是生两仪。两仪生四象，四象生八卦。',g:'系辞上传'};if(c==='yinyang')return{t:n.label,g:'两仪'};if(c==='bagua')return{t:`${n.label} ${n.symbol||''}`,d:`${n.nature||''}·${n.wuxing||''}`,g:'八经卦'};if(c==='hexagram64')return{t:`${n.label} ${n.symbol||''}`,d:n.judgment||'',s:n.image||'',g:n.nature||''};if(c==='wuxing')return{t:`${n.label}行`,g:'五行'};if(c==='tiangan')return{t:`天干·${n.label}`,d:`${n.yinyang||''}${n.wuxing||''}`,g:'十天干'};if(c==='dizhi')return{t:`地支·${n.label}`,d:`${n.wuxing||''}·${n.shengxiao||''}`,g:'十二地支'};return{t:n.label,d:n.desc||n.nature||'',g:c}}

export default function YiJingPage(){
  const mountRef=useRef(null)
  const cleanRef=useRef(null)
  const [g,setG]=useState(null)
  const [sel,setSel]=useState(null)
  const [ld,setLd]=useState(true)
  const [err,setErr]=useState(null)
  const [dbg,setDbg]=useState('')

  useEffect(()=>{
    let dead=false
    knowledgeApi.graph()
      .then(r=>{if(!dead){setG(r);setLd(false);setDbg(prev=>prev+`\nData: ${r?.nodes?.length||0} nodes`)}})
      .catch(e=>{if(!dead){setErr(String(e));setLd(false)}})
    return()=>{dead=true}
  },[])

  useEffect(()=>{
    const el=mountRef.current
    if(!g||!el) return
    if(cleanRef.current){cleanRef.current();cleanRef.current=null}

    // Wait for layout with retry
    let attempts=0
    const tryInit=()=>{
      const W=el.clientWidth||el.offsetWidth
      const H=el.clientHeight||el.offsetHeight
      setDbg(prev=>prev+`\nAttempt ${attempts}: ${W}x${H}`)

      if((W<50||H<50)&&attempts<10){
        attempts++
        setTimeout(tryInit,100)
        return
      }
      if(W<50||H<50){
        // Fallback: use window dimensions
        const fw=window.innerWidth-40
        const fh=window.innerHeight-160
        setDbg(prev=>prev+`\nFallback: ${fw}x${fh}`)
        initScene(el,fw,fh)
      }else{
        initScene(el,W,H)
      }
    }

    const initScene=(el,W,H)=>{
      try{
        const cs=getComputedStyle(document.documentElement)
        const bg=cs.getPropertyValue('--base').trim()||'#f3f0ea'
        const dk=bg.startsWith('#0')||bg.startsWith('#1')
        const CLR=dk?0x0c1e30:0xf3f0ea
        const LC=dk?'#d0c8b8':'#3a3020',LCF=dk?'#90887a':'#706858',LCSUB=dk?'#706860':'#908878'

        const scene=new THREE.Scene()
        const cam=new THREE.PerspectiveCamera(40,W/H,1,4000)
        cam.position.set(0,100,900)
        const ren=new THREE.WebGLRenderer({antialias:true})
        ren.setSize(W,H)
        ren.setPixelRatio(Math.min(window.devicePixelRatio,3))
        ren.setClearColor(CLR)
        // Clear mount and append
        while(el.firstChild)el.removeChild(el.firstChild)
        el.appendChild(ren.domElement)

        scene.add(new THREE.AmbientLight(0xffffff,dk?0.5:0.7))
        const dl=new THREE.DirectionalLight(dk?0xe0d0b0:0xfff0d0,0.5);dl.position.set(150,500,300);scene.add(dl)
        const pl1=new THREE.PointLight(0xd94025,0.5,1200);pl1.position.set(0,300,200);scene.add(pl1)
        const pl2=new THREE.PointLight(0x2a9a6a,0.4,800);pl2.position.set(-200,-100,100);scene.add(pl2)

        const{nodes,edges}=g,pos={},meshes=[],flowMats=[]
        const TY={0:300,1:200,2:100,3:-20}

        // Layout
        nodes.filter(n=>n.layer===0).forEach(n=>pos[n.id]=new THREE.Vector3(0,TY[0],0))
        nodes.filter(n=>n.layer===1).forEach((n,i)=>pos[n.id]=new THREE.Vector3(i===0?-100:100,TY[1],0))
        const L2=nodes.filter(n=>n.layer===2);[-210,-70,70,210].forEach((x,i)=>{if(L2[i])pos[L2[i].id]=new THREE.Vector3(x,TY[2],0)})
        const L3=nodes.filter(n=>n.layer===3);[-320,-230,-140,-50,50,140,230,320].forEach((x,i)=>{if(L3[i])pos[L3[i].id]=new THREE.Vector3(x,TY[3],0)})
        nodes.filter(n=>n.layer===4).forEach((n,i)=>{const a=(i/5)*Math.PI*2-Math.PI/2;pos[n.id]=new THREE.Vector3(Math.cos(a)*100,60+Math.sin(a)*50,150)})
        nodes.filter(n=>n.category==='tiangan').forEach((n,i)=>{const a=((i-4.5)/10)*Math.PI*0.8;pos[n.id]=new THREE.Vector3(-280+Math.sin(a)*80,-100+Math.cos(a)*30,120)})
        nodes.filter(n=>n.category==='dizhi').forEach((n,i)=>{const a=((i-5.5)/12)*Math.PI*0.9;pos[n.id]=new THREE.Vector3(280+Math.sin(a)*90,-100+Math.cos(a)*35,120)})
        nodes.filter(n=>n.layer===6).forEach((n,i)=>{const a=(i/64)*Math.PI*2-Math.PI/2;pos[n.id]=new THREE.Vector3(Math.cos(a)*420,-200,Math.sin(a)*160)})
        ;[7,8,9].forEach(layer=>{
          const LN=nodes.filter(n=>n.layer===layer),cats={};LN.forEach(n=>{if(!cats[n.category])cats[n.category]=[];cats[n.category].push(n)})
          const keys=Object.keys(cats),R=layer===7?480:layer===8?560:640,baseY=layer===7?-310:layer===8?-400:-480
          keys.forEach((ck,ci)=>{const grp=cats[ck],ba=((ci+0.5)/keys.length)*Math.PI*2,cx=Math.cos(ba)*R,cz=Math.sin(ba)*R*0.35,sp=Math.min(grp.length*8,65)
            grp.forEach((n,i)=>{const a=(i/grp.length)*Math.PI*2;pos[n.id]=new THREE.Vector3(cx+Math.cos(a)*sp,baseY+Math.sin(a)*sp*0.3,cz+40)})})
        })

        setDbg(prev=>prev+`\nPositioned: ${Object.keys(pos).length}/${nodes.length}`)

        // Edges
        const CORE=new Set(['生','分','演'])
        edges.forEach(e=>{
          const a=pos[e.source],b=pos[e.target];if(!a||!b)return
          const sn=nodes.find(n=>n.id===e.source),tn=nodes.find(n=>n.id===e.target)
          const sL=sn?.layer??99,tL=tn?.layer??99
          const isDeriv=CORE.has(e.relation)&&sL<=2,isGua=e.relation==='上卦'||e.relation==='下卦'
          const isWxC=e.relation==='生'&&sL===4&&tL===4,isWxL=(e.relation==='化'||e.relation==='属')&&(sL===4||tL===4)&&sL<=5&&tL<=5
          const isStr=e.relation==='统'||e.relation==='配'||e.relation==='象',isSub=sL>=7||tL>=7
          let color,opacity,flow=false
          if(isDeriv){color=dk?0x40c090:0x2a9a6a;opacity=0.6;flow=true}
          else if(isGua){color=dk?0x253530:0xe0d8c8;opacity=0.04}
          else if(isWxC){color=0xe0a020;opacity=0.35;flow=true}
          else if(isWxL){color=dk?0x3a5a48:0xc8c0a8;opacity=0.12}
          else if(isStr){color=dk?0x305848:0xc0b8a0;opacity=0.08}
          else if(isSub){color=dk?0x1a2a28:0xe8e0d8;opacity=0.03}
          else return
          const pts=flow?curve(a,b,20):[a,b]
          if(flow){const geo=new THREE.BufferGeometry().setFromPoints(pts);const m=new THREE.LineDashedMaterial({color,transparent:true,opacity,dashSize:6,gapSize:4});const ln=new THREE.Line(geo,m);ln.computeLineDistances();scene.add(ln);flowMats.push(m)}
          else{scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineBasicMaterial({color,transparent:true,opacity})))}
        })

        // Nodes
        nodes.forEach(n=>{
          const p=pos[n.id];if(!p)return;const L=n.layer||0,col=new THREE.Color(cc(n))
          let sz=L===0?14:L===1?8:L===2?6:L===3?6:L===4?6:L===5?3.5:L===6?1.5:L===7?2.8:L===8?2:1.6
          let geo=L===0?new THREE.IcosahedronGeometry(sz,2):L===1?new THREE.SphereGeometry(sz,48,32):L===2?new THREE.OctahedronGeometry(sz,1):L===3?new THREE.BoxGeometry(sz*1.2,sz*1.2,sz*1.2):L===4?new THREE.OctahedronGeometry(sz,0):L===7?new THREE.DodecahedronGeometry(sz,0):new THREE.SphereGeometry(sz,L<=5?12:8,L<=5?8:4)
          const mat=new THREE.MeshStandardMaterial({color:col,emissive:col,emissiveIntensity:L===0?0.6:L<=3?0.35:L<=4?0.3:L<=7?0.15:0.1,metalness:L<=3?0.35:0.1,roughness:L<=3?0.3:0.55,transparent:true,opacity:L>=9?0.5:L===8?0.55:L===6?0.45:L===7?0.65:0.92})
          const m=new THREE.Mesh(geo,mat);m.position.copy(p);m.userData=n;scene.add(m);meshes.push(m)
          if(L<=4){const halo=new THREE.Mesh(new THREE.CircleGeometry(sz*(L===0?3.5:2.2),48),new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:L===0?0.08:0.04,side:THREE.DoubleSide}));halo.position.set(p.x,p.y,p.z-1);scene.add(halo)}
          if(L<=9){
            const fs=L===0?22:L===1?18:L===2?15:L===3?14:L===4?14:L===5?13:L===6?8:L===7?11:L===8?9:8
            const sc=L===0?56:L===1?42:L===2?32:L===3?28:L===4?28:L===5?24:L===6?14:L===7?18:L===8?15:12
            const lbl=mkL(n.label+(n.symbol&&L===3?' '+n.symbol:''),L<=4?LC:L<=6?LCF:LCSUB,fs)
            lbl.scale.set(sc,sc*0.38,1);lbl.position.set(p.x,p.y-sz-sc*0.1,p.z);scene.add(lbl)
          }
        })

        setDbg(prev=>prev+`\nMeshes: ${meshes.length}`)

        // Particles
        const pa=new Float32Array(400*3);for(let i=0;i<400;i++){pa[i*3]=(Math.random()-0.5)*1400;pa[i*3+1]=(Math.random()-0.5)*1000;pa[i*3+2]=(Math.random()-0.5)*600}
        scene.add(new THREE.Points(new THREE.BufferGeometry().setAttribute('position',new THREE.BufferAttribute(pa,3)),new THREE.PointsMaterial({color:dk?0x304050:0xc8c0b0,size:0.5,transparent:true,opacity:0.12})))

        // Click
        const ray=new THREE.Raycaster(),mv=new THREE.Vector2()
        ren.domElement.addEventListener('click',ev=>{const r=ren.domElement.getBoundingClientRect();mv.x=((ev.clientX-r.left)/r.width)*2-1;mv.y=-((ev.clientY-r.top)/r.height)*2+1;ray.setFromCamera(mv,cam);const h=ray.intersectObjects(meshes);setSel(h.length?h[0].object.userData:null)})

        // Orbit
        let dr=false,px=0,py=0,rY=0,rX=0.08,D=900
        const dn=e=>{dr=true;const t=e.touches?e.touches[0]:e;px=t.clientX;py=t.clientY}
        const mo=e=>{if(!dr)return;const t=e.touches?e.touches[0]:e;rY+=(t.clientX-px)*0.003;rX=Math.max(-0.6,Math.min(0.6,rX+(t.clientY-py)*0.002));px=t.clientX;py=t.clientY}
        const up=()=>{dr=false},wh=e=>{D=Math.max(300,Math.min(1800,D+e.deltaY*0.5))}
        const cv=ren.domElement;cv.addEventListener('mousedown',dn);cv.addEventListener('mousemove',mo);cv.addEventListener('mouseup',up);cv.addEventListener('wheel',wh);cv.addEventListener('touchstart',dn);cv.addEventListener('touchmove',mo);cv.addEventListener('touchend',up)

        let fid;const anim=()=>{fid=requestAnimationFrame(anim);const t=Date.now()*0.001
          if(!dr)rY+=0.0003;cam.position.set(Math.sin(rY)*Math.cos(rX)*D,40+Math.sin(rX)*D*0.4,Math.cos(rY)*Math.cos(rX)*D);cam.lookAt(0,-30,0)
          flowMats.forEach(m=>{m.dashOffset=-t*3})
          const rt=meshes.find(m=>m.userData.id==='太极');if(rt){rt.rotation.y+=0.003;const s=1+Math.sin(t)*0.06;rt.scale.set(s,s,s)}
          meshes.filter(m=>(m.userData.layer||0)===3).forEach(m=>{m.rotation.y+=0.001})
          meshes.filter(m=>(m.userData.layer||0)===4).forEach(m=>{m.rotation.y+=0.003})
          ren.render(scene,cam)
        };anim()

        setDbg(prev=>prev+'\nRendering started ✓')

        const onR=()=>{const w=el.clientWidth||window.innerWidth-40,h=el.clientHeight||window.innerHeight-160;if(w>10&&h>10){cam.aspect=w/h;cam.updateProjectionMatrix();ren.setSize(w,h)}}
        window.addEventListener('resize',onR)

        cleanRef.current=()=>{cancelAnimationFrame(fid);window.removeEventListener('resize',onR);ren.dispose();try{while(el.firstChild)el.removeChild(el.firstChild)}catch(e){}}
      }catch(e){
        setErr(String(e))
        setDbg(prev=>prev+`\nERROR: ${e}`)
      }
    }

    requestAnimationFrame(tryInit)
    return()=>{if(cleanRef.current){cleanRef.current();cleanRef.current=null}}
  },[g])

  const d=nfo(sel)
  const LEG=[['太极',P.taiji],['八卦',P.bagua],['五行',P.wuxing],['干支',P.tiangan],['六十四卦',P.h64],['四灵',P.siling],['星宿',P.xingxiu],['紫微',P.ziwei],['奇门',P.qimen],['纳音',P.nayin]]

  return(
    <div style={{width:'100%',height:'calc(100vh - 100px)',position:'relative',overflow:'hidden'}}>
      {/* Three.js canvas container — explicit pixel height */}
      <div ref={mountRef} style={{width:'100%',height:'100%'}}/>

      {/* Overlays */}
      <div style={{position:'absolute',top:10,left:20,zIndex:10,pointerEvents:'none'}}>
        <div style={{fontSize:15,fontWeight:700,fontFamily:'var(--font-serif)',color:'var(--text-primary)',letterSpacing:3}}>易经知识图谱</div>
        <div style={{fontSize:10,color:'var(--text-faint)',fontFamily:'var(--font-mono)',marginTop:2}}>{g?`${g.nodes.length} 实体 · ${g.edges.length} 关系`:''}</div>
      </div>
      <div style={{position:'absolute',top:10,right:20,display:'flex',gap:8,zIndex:10,pointerEvents:'none',flexWrap:'wrap',maxWidth:360,justifyContent:'flex-end'}}>
        {LEG.map(([l,c])=><div key={l} style={{display:'flex',alignItems:'center',gap:2}}><div style={{width:6,height:6,background:c,borderRadius:'50%'}}/><span style={{fontSize:9,color:'var(--text-faint)'}}>{l}</span></div>)}
      </div>

      {ld&&<div style={{position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',background:'var(--base)',zIndex:20}}>
        <div style={{textAlign:'center'}}><div style={{fontSize:28,color:'var(--accent)',animation:'p 2s infinite'}}>☯</div><div style={{fontSize:12,color:'var(--text-muted)',fontFamily:'var(--font-serif)',marginTop:8}}>载入图谱…</div></div>
      </div>}

      {err&&!ld&&<div style={{position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',background:'var(--base)',zIndex:20}}>
        <div style={{color:'#c04030',fontSize:12,textAlign:'center',padding:20}}>
          <div>加载异常</div>
          <div style={{fontSize:10,color:'var(--text-muted)',marginTop:6,whiteSpace:'pre-wrap'}}>{err}</div>
          <pre style={{fontSize:9,color:'var(--text-faint)',marginTop:8,textAlign:'left',maxWidth:400,overflow:'auto'}}>{dbg}</pre>
        </div>
      </div>}

      {d&&<div style={{position:'absolute',bottom:14,left:14,maxWidth:350,zIndex:15,background:'var(--bg-card)',border:'1px solid var(--border)',padding:'14px 18px'}}>
        <div style={{display:'flex',alignItems:'center',gap:6,marginBottom:5}}>
          <div style={{width:4,height:4,borderRadius:'50%',background:'var(--accent)'}}/>
          <div style={{fontSize:14,fontWeight:700,color:'var(--text-primary)',fontFamily:'var(--font-serif)',letterSpacing:1,flex:1}}>{d.t}</div>
          <button onClick={()=>setSel(null)} style={{border:'none',background:'none',color:'var(--text-muted)',cursor:'pointer',padding:0,fontSize:13}}>×</button>
        </div>
        {d.d&&<div style={{fontSize:12,color:'var(--text-secondary)',fontFamily:'var(--font-serif)',lineHeight:1.8}}>{d.d}</div>}
        {d.s&&<div style={{fontSize:11,color:'var(--text-muted)',marginTop:3,fontFamily:'var(--font-serif)',lineHeight:1.6}}>{d.s}</div>}
        {d.g&&<div style={{marginTop:5,fontSize:10,color:'var(--accent)',padding:'1px 6px',border:'1px solid var(--accent-dim)',display:'inline-block'}}>{d.g}</div>}
      </div>}

      <div style={{position:'absolute',bottom:14,right:16,fontSize:9,color:'var(--text-faint)',fontFamily:'var(--font-mono)',zIndex:10}}>拖拽旋转 · 滚轮缩放 · 点击查看</div>
      <style>{`@keyframes p{0%,100%{opacity:1}50%{opacity:.4}}`}</style>
    </div>
  )
}
