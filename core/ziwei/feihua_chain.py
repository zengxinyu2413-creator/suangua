"""
core/ziwei/feihua_chain.py
==========================
紫微斗数·飞星派飞化链路多步串联分析。

单宫飞化只见一跳（A宫干化X入B宫）；飞星派之精微，在「飞化网络」之串联——
  · 互化   —— A化入B、B亦化入A，两宫相缠（双禄交流·双忌交战·施怨…）。
  · 化忌连环 —— A忌入B、B宫干又忌入C…忌气层层传递，破败连绵。
  · 化禄流通 —— 禄气由A流B流C，福气流转、资源活络。
  · 飞化焦点 —— 某宫为多宫飞化所汇（禄忌交集），成一盘之枢机。
  · 生年串联 —— 生年禄/忌所在宫之宫干再飞化（禄随忌走·忌上加忌）。

复用 chart 之 feihua（每宫干四化去向）与 birth_sihua（生年四化），构有向图后
逐链追溯，与排盘同源。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple


def _build_graph(feihua: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """构飞化有向图：palace_idx → {name, stem, edges:{化禄:idx,...}, self:set}。"""
    g: Dict[int, Dict[str, Any]] = {}
    for e in feihua:
        pidx = e.get("palace_idx")
        if pidx is None:
            continue
        edges, selfs = {}, set()
        for t in e.get("transformations", []):
            ht = t.get("hua_type", "")
            tgt = t.get("target_palace_idx")
            edges[ht] = {"idx": tgt, "name": t.get("target_palace_name", ""),
                         "star": t.get("target_star", "")}
            if t.get("is_self_transform"):
                selfs.add(ht)
        g[pidx] = {"name": e.get("palace_name", ""), "stem": e.get("stem", ""),
                   "edges": edges, "self": selfs}
    return g


def _name(g, idx):
    return g.get(idx, {}).get("name", f"宫{idx}")


# ── 1. 互化 ──
def _detect_mutual(g: Dict[int, Dict]) -> List[Dict[str, Any]]:
    out, seen = [], set()
    for a, ainfo in g.items():
        for ha, ea in ainfo["edges"].items():
            b = ea["idx"]
            if b is None or b == a or b not in g:
                continue
            for hb, eb in g[b]["edges"].items():
                if eb["idx"] == a:
                    key = tuple(sorted([a, b]))
                    if key in seen:
                        continue
                    seen.add(key)
                    na, nb = _name(g, a), _name(g, b)
                    pair = {ha[-1], hb[-1]}
                    if pair == {"忌"}:
                        nat, desc = "凶", f"{na}↔{nb} 双忌交战——两宫互化忌，彼此纠缠牵绊、损耗连绵，为一生难解之债，此二事最相妨。"
                    elif pair == {"禄"}:
                        nat, desc = "吉", f"{na}↔{nb} 双禄交流——两宫互化禄，互利共生、福禄相长，此二事相得益彰。"
                    elif "忌" in pair and "禄" in pair:
                        nat, desc = "中", f"{na}({ha[-1]})↔{nb}({hb[-1]}) 禄忌互化——一方施予一方损，好意未必得好报、付出与牵绊并存。"
                    else:
                        nat, desc = "中", f"{na}({ha[-1]})↔{nb}({hb[-1]}) 互化——两宫关系密切、动静相连。"
                    out.append({"type": "互化", "palaces": [na, nb],
                                "hua": [ha, hb], "nature": nat, "desc": desc})
    return out


# ── 2. 化X连环链 ──
def _trace_chain(g: Dict[int, Dict], start: int, hua: str,
                 max_len: int = 5) -> List[int]:
    """沿某一化（如化忌）逐宫追链，遇环或断则止。"""
    chain, visited, cur = [start], {start}, start
    while len(chain) < max_len:
        edge = g.get(cur, {}).get("edges", {}).get(hua)
        if not edge or edge["idx"] is None:
            break
        nxt = edge["idx"]
        chain.append(nxt)
        if nxt in visited or nxt not in g:
            break
        visited.add(nxt)
        cur = nxt
    return chain


def _detect_hua_chains(g: Dict[int, Dict], hua: str) -> List[Dict[str, Any]]:
    """找出该化之最长链（≥3宫方为连环）。"""
    out, covered = [], set()
    # 以入度0或未被覆盖之宫为起点，取较长链
    chains = []
    for start in g:
        ch = _trace_chain(g, start, hua)
        if len(ch) >= 3:
            chains.append(ch)
    # 去重子链：保留极大链
    chains.sort(key=len, reverse=True)
    for ch in chains:
        sig = tuple(ch)
        if any(set(ch).issubset(set(c)) and ch != c for c in [x["idx_chain"] for x in out]):
            continue
        names = [_name(g, i) for i in ch]
        is_cycle = ch[-1] == ch[0] or ch[-1] in ch[:-1]
        out.append({"idx_chain": ch, "names": names, "is_cycle": is_cycle})
        if len(out) >= 3:
            break
    return out


# ── 3. 飞化焦点（多宫所汇） ──
def _detect_focus(g: Dict[int, Dict]) -> List[Dict[str, Any]]:
    incoming: Dict[int, List[Tuple[str, int]]] = {}
    for a, ainfo in g.items():
        for h, e in ainfo["edges"].items():
            t = e["idx"]
            if t is None or t == a:
                continue
            incoming.setdefault(t, []).append((h[-1], a))
    out = []
    for t, srcs in incoming.items():
        huas = [h for h, _ in srcs]
        if len(srcs) >= 3:
            has_lu = "禄" in huas
            has_ji = "忌" in huas
            tag = "禄忌交集" if (has_lu and has_ji) else ("众禄所归" if has_lu else "众忌所冲" if has_ji else "众化所汇")
            out.append({
                "palace": _name(g, t), "count": len(srcs),
                "huas": huas, "tag": tag,
                "desc": f"{_name(g, t)}为飞化焦点（{len(srcs)}宫飞入·{tag}）——"
                        f"此宫乃一盘枢机，{('禄忌交集、成败相依、福祸所系' if (has_lu and has_ji) else '众化所归、力量集中于此')}。",
            })
    out.sort(key=lambda x: x["count"], reverse=True)
    return out[:3]


# ── 4. 生年四化串联 ──
def _detect_birth_chain(g: Dict[int, Dict],
                        birth_sihua: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    sihua = (birth_sihua or {}).get("sihua", {})
    name_to_idx = {info["name"]: idx for idx, info in g.items()}
    for hua_key, label in (("化禄", "生年禄"), ("化忌", "生年忌")):
        info = sihua.get(hua_key)
        if not info:
            continue
        pidx = name_to_idx.get(info["palace"])
        if pidx is None:
            continue
        edges = g[pidx]["edges"]
        # 该宫干再飞化之忌去向
        ji_edge = edges.get("化忌")
        if ji_edge and ji_edge["idx"] is not None and ji_edge["idx"] != pidx:
            if hua_key == "化禄":
                out.append({
                    "type": "禄随忌走", "nature": "凶",
                    "desc": f"{label}在【{info['palace']}】，而{info['palace']}宫干再化忌入【{ji_edge['name']}】——"
                            f"禄随忌走，福源被牵动而泄，得而复失、福中藏患，{ji_edge['name']}之事尤须留意。",
                })
            else:
                out.append({
                    "type": "忌上加忌", "nature": "凶",
                    "desc": f"{label}在【{info['palace']}】，{info['palace']}宫干又化忌入【{ji_edge['name']}】——"
                            f"忌上加忌、债转他宫，执念由{info['palace']}牵连至{ji_edge['name']}，连环之患。",
                })
    return out


def analyze_feihua_chains(chart: Dict[str, Any],
                          birth_sihua: Optional[Dict[str, Any]] = None,
                          feihua_list: Optional[List[Dict[str, Any]]] = None,
                          layer: str = "本命") -> Dict[str, Any]:
    """飞化链路多步串联总入口。feihua_list 给定则用之（大限/流年盘），否则用本命。"""
    feihua = feihua_list if feihua_list is not None else chart.get("feihua", [])
    if not feihua:
        return {"available": False}
    g = _build_graph(feihua)

    mutual = _detect_mutual(g)
    ji_chains = _detect_hua_chains(g, "化忌")
    lu_chains = _detect_hua_chains(g, "化禄")
    focus = _detect_focus(g)
    birth_chain = _detect_birth_chain(g, birth_sihua or {})

    # 链条成文
    ji_chain_txt = []
    for ch in ji_chains:
        arrow = "→".join(ch["names"])
        cyc = "（成环·自缚不解）" if ch["is_cycle"] else ""
        ji_chain_txt.append(f"化忌连环：{arrow}{cyc}——忌气层层传递，破耗波及诸宫，链上各事互相牵累。")
    lu_chain_txt = []
    for ch in lu_chains:
        arrow = "→".join(ch["names"])
        lu_chain_txt.append(f"化禄流通：{arrow}——禄气流转，福源资源于此数宫间活络流通。")

    # 汇总
    parts = []
    if birth_chain:
        parts.append(birth_chain[0]["desc"])
    if ji_chain_txt:
        parts.append(ji_chain_txt[0])
    if any(m["nature"] == "凶" for m in mutual):
        parts.append(next(m["desc"] for m in mutual if m["nature"] == "凶"))
    if focus:
        parts.append(focus[0]["desc"])
    summary = "　".join(parts) if parts else "本盘飞化各自为政，无显著多步串联之链。"

    return {
        "available": True,
        "layer": layer,
        "mutual": mutual,
        "ji_chains": [{"names": c["names"], "is_cycle": c["is_cycle"], "text": t}
                      for c, t in zip(ji_chains, ji_chain_txt)],
        "lu_chains": [{"names": c["names"], "text": t}
                      for c, t in zip(lu_chains, lu_chain_txt)],
        "focus": focus,
        "birth_chain": birth_chain,
        "summary": summary,
    }


# ─────────────────────────────────────────────────────────────
# 运限盘飞化链路（大限 / 流年）
# ─────────────────────────────────────────────────────────────

# 五虎遁：年干 → 寅宫起遁之天干
_WUHU = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚",
         "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}
_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"


def _wuhu_branch_stems(year_stem: str) -> Dict[str, str]:
    """五虎遁：由年干定十二宫（按地支）之宫干。寅宫起遁，顺布。"""
    start = _WUHU.get(year_stem)
    if not start:
        return {}
    gi = _GAN.index(start)
    out = {}
    order = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
    for k, br in enumerate(order):
        out[br] = _GAN[(gi + k) % 10]
    return out


def _build_layer_feihua(palaces: List[Dict[str, Any]],
                        branch_to_stem: Dict[str, str]) -> List[Dict[str, Any]]:
    """据 宫支→宫干 映射，构运限盘飞化列表（格式同本命 feihua）。"""
    from core.ziwei.feihua_advanced import ZHONGZHOU_SIHUA, _build_star_to_palace_idx
    # iztro 原始天干键 → 中文
    raw2cn = {"jiaHeavenly": "甲", "yiHeavenly": "乙", "bingHeavenly": "丙",
              "dingHeavenly": "丁", "wuHeavenly": "戊", "jiHeavenly": "己",
              "gengHeavenly": "庚", "xinHeavenly": "辛", "renHeavenly": "壬",
              "guiHeavenly": "癸"}
    star_to_idx = _build_star_to_palace_idx(palaces)
    idx_to_name = {p.get("index"): p.get("name", "") for p in palaces}
    out = []
    for p in palaces:
        br = p.get("earthly_branch", "")
        stem = branch_to_stem.get(br, "")
        stem = raw2cn.get(stem, stem)   # 译原始键
        if stem not in ZHONGZHOU_SIHUA:
            continue
        sihua = ZHONGZHOU_SIHUA.get(stem, {})
        transforms = []
        for hua_type, star in sihua.items():
            tgt = star_to_idx.get(star)
            transforms.append({
                "hua_type": hua_type, "target_star": star,
                "target_palace_idx": tgt,
                "target_palace_name": idx_to_name.get(tgt, ""),
                "is_self_transform": (tgt == p.get("index")),
            })
        out.append({
            "palace_idx": p.get("index"), "palace_name": p.get("name", ""),
            "stem": stem, "transformations": transforms,
        })
    return out


def analyze_layer_feihua_chains(chart: Dict[str, Any], layer: str,
                                year_stem: Optional[str] = None,
                                birth_sihua: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    运限盘飞化链路：
      layer='大限' —— 用各宫 decadal_stem（大限宫干）。
      layer='流年' —— 用 year_stem 经五虎遁定各宫流年宫干。
    """
    palaces = chart.get("palaces", [])
    if not palaces:
        return {"available": False}

    if layer == "大限":
        branch_to_stem = {p.get("earthly_branch", ""): p.get("decadal_stem", "")
                          for p in palaces if p.get("decadal_stem")}
    elif layer == "流年" and year_stem:
        branch_to_stem = _wuhu_branch_stems(year_stem)
    else:
        return {"available": False}

    fh = _build_layer_feihua(palaces, branch_to_stem)
    if not fh:
        return {"available": False}
    return analyze_feihua_chains(chart, birth_sihua, feihua_list=fh, layer=layer)
