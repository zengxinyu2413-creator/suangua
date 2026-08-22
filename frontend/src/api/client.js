/**
 * api/client.js
 * Centralised fetch wrapper for all backend calls.
 * Base URL is read from the settings store.
 */
import { useSettingsStore } from '../store/settingsStore';

async function request(method, path, body = null) {
  const { apiBaseUrl } = useSettingsStore.getState();
  const url = `${apiBaseUrl}${path}`;

  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(url, opts);
  const data = await res.json();

  if (!res.ok || data.success === false) {
    throw new Error(data.detail || data.message || `HTTP ${res.status}`);
  }
  return data.data;
}

const get  = (path)        => request('GET',  path);
const post = (path, body)  => request('POST', path, body);

// ── BaZi ──────────────────────────────────────────────────
export const baziApi = {
  chart:         (birth)  => post('/api/v1/bazi/chart', birth),
  fortune:       (req)    => post('/api/v1/bazi/fortune', req),
  career:        (birth)  => post('/api/v1/bazi/career', birth),
  marriage:      (birth)  => post('/api/v1/bazi/marriage', birth),
  health:        (birth)  => post('/api/v1/bazi/health', birth),
  wealth:        (birth)  => post('/api/v1/bazi/wealth', birth),
  compatibility: (req)    => post('/api/v1/bazi/compatibility', req),
  chenggu:       (birth)  => post('/api/v1/bazi/chenggu', birth),
  reverse:       (req)    => post('/api/v1/bazi/reverse', req),
};

// ── LiuYao ────────────────────────────────────────────────
export const liuyaoApi = {
  divine:     (req)    => post('/api/v1/liuyao/divine', req),
  hexagrams:  ()       => get('/api/v1/liuyao/hexagrams'),
  hexagram:   (num)    => get(`/api/v1/liuyao/hexagram/${num}`),
  guaStatic:  (num, gender='male') => get(`/api/v1/liuyao/gua_static/${num}?gender=${encodeURIComponent(gender)}`),
  guaCatalog: ()       => get('/api/v1/liuyao/gua_catalog'),
};

// ── QiMen ─────────────────────────────────────────────────
export const qimenApi = {
  layout:     (req) => post('/api/v1/qimen/layout', req),
  now:        ()    => get('/api/v1/qimen/now'),
  hourNow:    ()    => get('/api/v1/qimen/hour-now'),
  hourLayout: (req) => post('/api/v1/qimen/hour-layout', req),
  zeji:       (req) => post('/api/v1/qimen/zeji', req),
};

// ── FengShui ──────────────────────────────────────────────
export const fengshuiApi = {
  analysis: (req) => post('/api/v1/fengshui/analysis', req),
  xuankong: (req) => post('/api/v1/fengshui/xuankong', req),
  yangzhaiSanyao: (req) => post('/api/v1/fengshui/yangzhai_sanyao', req),
  houseReport: (req) => post('/api/v1/fengshui/house_report', req),
  yangzhaiLayout: (men) => get('/api/v1/fengshui/yangzhai_layout?men=' + encodeURIComponent(men)),
  yangzhaiLiushi: (req) => post('/api/v1/fengshui/yangzhai_liushi', req),
  yangzhaiLiushiGuide: (men) => get('/api/v1/fengshui/yangzhai_liushi_guide?men=' + encodeURIComponent(men)),
};

// ── ZiWei ────────────────────────────────────────────
export const ziweiApi = {
  chart:   (req) => post('/api/v1/ziwei/chart', req),
  hours:   ()    => get('/api/v1/ziwei/hours'),
  decade:  (req) => post('/api/v1/ziwei/decade', req),
  triple:  (req) => post('/api/v1/ziwei/triple', req),
};

// ── DateSelection ─────────────────────────────────────────
export const dateApi = {
  select: (req) => post('/api/v1/date-selection/select', req),
};

// ── Knowledge ─────────────────────────────────────────────
export const knowledgeApi = {
  search:     (keyword, category) =>
    get(`/api/v1/knowledge/search?keyword=${encodeURIComponent(keyword)}${category ? `&category=${encodeURIComponent(category)}` : ''}`),
  categories: () => get('/api/v1/knowledge/categories'),
  smartSearch: (keyword) => post('/api/v1/knowledge/smart-search', { keyword }),
  graph:    ()     => get("/api/v1/knowledge/yijing-graph"),
  dailyGuardian: (date) => get(`/api/v1/knowledge/daily-guardian${date ? "?date="+date : ""}`),
};

// ── Health ────────────────────────────────────────────────
export const systemApi = {
  // Health returns { success, data: { status, version, modules, port } }
  // Use raw fetch so we don't go through the ApiResponse unwrapper
  health: async () => {
    const { apiBaseUrl } = useSettingsStore.getState();
    try {
      const res = await fetch(`${apiBaseUrl}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!res.ok) return { status: 'offline' };
      const json = await res.json();
      // Handle both old format { status:'ok' } and new { success:true, data:{ status:'ok' } }
      if (json.data?.status === 'ok') return json.data;
      if (json.status === 'ok') return json;
      return { status: 'offline' };
    } catch {
      return { status: 'offline' };
    }
  },
};

// ── Classical Knowledge ────────────────────────────────────
export const classicalApi = {
  shishen:      ()     => get('/api/v1/knowledge/classical/shishen'),
  shishenDetail:(name) => get(`/api/v1/knowledge/classical/shishen/${name}`),
  pillars:      ()     => get('/api/v1/knowledge/classical/pillars'),
  dizhi:        ()     => get('/api/v1/knowledge/classical/dizhi'),
  liuyaoTopics: ()     => get('/api/v1/knowledge/classical/liuyao-topics'),
  liuyaoRules:  ()     => get('/api/v1/knowledge/classical/liuyao-rules'),
  qimenMatrix:  ()     => get('/api/v1/knowledge/classical/qimen-matrix'),
  formulas:     ()     => get('/api/v1/knowledge/classical/formulas'),
  mountains:    ()     => get('/api/v1/knowledge/classical/24mountains'),
};

// ── 行文层（AI 叙事，下游护栏强制）──────────────────────────
export const narrationApi = {
  styles:     ()                       => get('/api/v1/narration/styles'),
  synthesize: (master_synthesis, style, use_ai = true) =>
                post('/api/v1/narration/synthesize', { master_synthesis, style, use_ai }),
  synthesizeFull: (chart_data, module, style, use_ai = true) =>
                post('/api/v1/narration/synthesize_full', { chart_data, module, style, use_ai }),
  synthesizeMulti: (charts, style, use_ai = true) =>
                post('/api/v1/narration/synthesize_multi', { charts, style, use_ai }),
  exportDoc:  (payload) => post('/api/v1/narration/export', payload),
  verify:     (master_synthesis, prose) =>
                post('/api/v1/narration/verify', { master_synthesis, prose }),
};
