/**
 * NarrationPanel —— 「古文行文」面板（行文层前端入口）。
 *
 * 下游展示：把引擎已算定的事实，转写为流畅古文。
 * 三档文风（白话/半文/文言），全部经后端忠实度护栏（AI 越界则 fail-closed 退回确定性）。
 *
 * Props:
 *   ms       —— 该盘 master_synthesis（必填，available 为真才显示）
 *   fullData —— 可选，整盘响应 data；与 module 同传则启用「整盘综合」模式
 *   module   —— 可选，模块名（bazi/ziwei/liuyao/qimen/xuankong/yangzhai/date）
 *   companions —— 可选，[{ module, label, fetch }]；fetch 为 async()=>chart_data，
 *                 同传 fullData+module 则启用「合参」模式（如八字页合参紫微）
 *   title    —— 可选，面板标题（默认「古文行文」）
 */
import { useState } from 'react';
import { narrationApi } from '../api/client';

const STYLE_TABS = [
  { key: '白话', label: '白话' },
  { key: '半文', label: '半文' },
  { key: '文言', label: '文言' },
];

export default function NarrationPanel({ ms, fullData = null, module = null, companions = null, title = '古文行文' }) {
  const hasFull = !!(fullData && module);
  const hasMulti = !!(hasFull && companions && companions.length > 0);
  const [open, setOpen] = useState(false);
  const [style, setStyle] = useState('半文');
  const [scope, setScope] = useState(hasFull ? 'full' : 'single'); // full=整盘 / single=本论 / multi=合参
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cache, setCache] = useState({});
  const [companionData, setCompanionData] = useState(null); // 合参伙伴盘缓存

  if (!ms || ms.available === false) return null;

  const ck = (sc, st) => `${sc}|${st}`;
  const current = cache[ck(scope, style)];

  async function run(targetScope, targetStyle) {
    setScope(targetScope);
    setStyle(targetStyle);
    if (cache[ck(targetScope, targetStyle)]) return;
    setLoading(true);
    setError(null);
    try {
      let data;
      if (targetScope === 'multi') {
        // 懒取伙伴盘（缓存），与本盘合参
        let comps = companionData;
        if (!comps) {
          comps = [];
          for (const cp of companions) {
            const cd = await cp.fetch();
            comps.push({ chart_data: cd, module: cp.module, label: cp.label });
          }
          setCompanionData(comps);
        }
        const charts = [{ chart_data: fullData, module, label: '本盘' }, ...comps];
        data = await narrationApi.synthesizeMulti(charts, targetStyle, true);
      } else if (targetScope === 'full') {
        data = await narrationApi.synthesizeFull(fullData, module, targetStyle, true);
      } else {
        data = await narrationApi.synthesize(ms, targetStyle, true);
      }
      setCache((c) => ({ ...c, [ck(targetScope, targetStyle)]: data }));
    } catch (e) {
      setError(e.message || '行文失败');
    } finally {
      setLoading(false);
    }
  }

  function handleOpen() {
    setOpen(true);
    if (!cache[ck(scope, style)]) run(scope, style);
  }

  const [exporting, setExporting] = useState(false);
  async function handleExport() {
    setExporting(true);
    setError(null);
    try {
      // 整盘有 fullData 则导出整盘汇聚，否则导出本论 master_synthesis
      const payload = (hasFull && scope !== 'single')
        ? { chart_data: fullData, module, use_ai: true }
        : { master_synthesis: ms, use_ai: true };
      const data = await narrationApi.exportDoc(payload);
      const blob = new Blob([data.document], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename || '行文存档.md';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.message || '导出失败');
    } finally {
      setExporting(false);
    }
  }

  const sourceNote = (src, aiEnabled) => {
    if (src === 'ai') return { text: 'AI 行文 · 已过忠实度护栏', color: '#27ae60' };
    if (src === 'fallback_fidelity') return { text: 'AI 输出越界，已拦截并退回确定性文本', color: '#c0392b' };
    if (src === 'fallback_no_llm')
      return { text: aiEnabled === false ? '确定性行文（服务端未配置 AI）' : '确定性行文', color: 'var(--text-faint)' };
    return { text: '', color: 'var(--text-faint)' };
  };

  return (
    <div style={{ marginTop: '0.7rem' }}>
      {!open ? (
        <button
          onClick={handleOpen}
          className="btn btn-ghost"
          style={{
            fontFamily: 'var(--font-serif)', fontSize: 'var(--text-sm)',
            padding: '0.35rem 0.9rem', border: '1px solid var(--accent)',
            borderRadius: 'var(--r-sm)', color: 'var(--accent)',
            background: 'transparent', cursor: 'pointer',
          }}
        >
          ✶ {title} —— 将本盘结论转写为古文
        </button>
      ) : (
        <div style={{
          padding: '0.6rem 0.8rem', background: 'var(--bg-subtle)',
          borderRadius: 'var(--r-sm)', border: '1px solid var(--border)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--font-serif)', fontWeight: 700, fontSize: 'var(--text-sm)', color: 'var(--accent)' }}>
              ✶ {title}
            </span>
            {/* 范围切换：整盘综合 / 本论 / 合参 */}
            {(hasFull || hasMulti) && (
              <span style={{ display: 'inline-flex', gap: 4, marginLeft: 4 }}>
                {[['full', '整盘综合'], ['single', '本论'], ...(hasMulti ? [['multi', '合参']] : [])].map(([sc, lbl]) => (
                  <button key={sc} onClick={() => run(sc, style)}
                    style={{
                      fontSize: 'var(--text-xs)', padding: '0.15rem 0.5rem', borderRadius: 'var(--r-sm)',
                      cursor: 'pointer', border: '1px solid var(--border)',
                      background: scope === sc ? 'var(--bg-elev)' : 'transparent',
                      color: scope === sc ? 'var(--accent)' : 'var(--text-faint)',
                      fontWeight: scope === sc ? 700 : 400,
                    }}>
                    {lbl}
                  </button>
                ))}
              </span>
            )}
            <span style={{ flex: 1 }} />
            {STYLE_TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => run(scope, t.key)}
                style={{
                  fontFamily: 'var(--font-serif)', fontSize: 'var(--text-xs)',
                  padding: '0.2rem 0.6rem', borderRadius: 'var(--r-sm)', cursor: 'pointer',
                  border: style === t.key ? '1px solid var(--accent)' : '1px solid var(--border)',
                  background: style === t.key ? 'var(--accent)' : 'transparent',
                  color: style === t.key ? '#fff' : 'var(--text-secondary)',
                }}
              >
                {t.label}
              </button>
            ))}
            {/* 导出存档（三档行文 + 引擎判断 + 凭据，markdown 下载） */}
            <button
              onClick={handleExport}
              disabled={exporting}
              title="导出三档行文 + 引擎判断 + 凭据（markdown）"
              style={{
                fontSize: 'var(--text-xs)', padding: '0.2rem 0.6rem', borderRadius: 'var(--r-sm)',
                cursor: exporting ? 'default' : 'pointer', border: '1px solid var(--border)',
                background: 'transparent', color: 'var(--text-faint)', marginLeft: 4,
              }}
            >
              {exporting ? '导出中…' : '⤓ 导出存档'}
            </button>
          </div>

          {loading && <div style={{ color: 'var(--text-faint)', fontSize: 'var(--text-sm)', padding: '0.5rem 0' }}>行文中…</div>}
          {error && <div style={{ color: '#c0392b', fontSize: 'var(--text-sm)' }}>· {error}</div>}
          {!loading && !error && current && (
            <>
              <div style={{
                fontFamily: 'var(--font-serif)', fontSize: 'var(--text-base)', lineHeight: 2,
                color: 'var(--text-primary)', whiteSpace: 'pre-wrap',
                padding: '0.3rem 0.2rem', letterSpacing: '0.02em',
              }}>
                {current.prose}
              </div>
              {(() => {
                const n = sourceNote(current.source, current.ai_enabled);
                return (
                  <div style={{ marginTop: '0.4rem', fontSize: 'var(--text-xs)', color: n.color, textAlign: 'right' }}>
                    {n.text}
                  </div>
                );
              })()}
            </>
          )}
        </div>
      )}
    </div>
  );
}
