import React from 'react'

export default function TaijiBg() {
  return (
    <div style={{position:"fixed",inset:0,zIndex:0,pointerEvents:"none",display:"flex",alignItems:"center",justifyContent:"center",overflow:"hidden"}}>
      <svg viewBox="-52 -52 104 104" style={{width:"min(36vh,36vw)",height:"min(36vh,36vw)",opacity:0.12,animation:"taiji-spin 240s linear infinite"}}>
        <circle cx="0" cy="0" r="50" fill="#000"/>
        <path d="M 0,-50 A 50,50 0 0,1 0,50 A 25,25 0 0,1 0,0 A 25,25 0 0,0 0,-50 Z" fill="#fff"/>
        <circle cx="0" cy="-25" r="7" fill="#fff"/>
        <circle cx="0" cy="25" r="7" fill="#000"/>
      </svg>
    </div>
  )
}
