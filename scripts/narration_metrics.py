#!/usr/bin/env python3
"""行文层护栏·量化回归脚本（CI 用）。

构建跨模块语料（本论 + 整盘 + 合参），跑 guard_metrics，断言：
  · 忠实通过率 == 1.0（零误报，绝不冤枉忠实转写）
  · 拦截率 >= 阈值（默认 0.98；4 类对抗：判断实体 / 吉凶翻转 / 干支 / 年份）
退出码非 0 表示护栏退化，CI 应拦下。

用法：python scripts/narration_metrics.py [--min-interception 0.98]
"""
import argparse
import json
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, ".")


def build_corpus():
    from fastapi.testclient import TestClient
    from main import app
    from core.narration import collect_facts, collect_facts_multi
    c = TestClient(app)
    ms_list = []

    def bazi(y):
        return c.post("/api/v1/bazi/chart", json={"year": y, "month": 6, "day": 15,
                      "hour": 10, "gender": "male", "is_lunar": False}).json()["data"]

    def ziwei(y):
        return c.post("/api/v1/ziwei/chart", json={"year": y, "month": 6, "day": 15,
                      "hour": 10, "gender": "男", "is_lunar": False}).json()["data"]

    # 八字 / 紫微：本论 + 整盘
    for y in (1980, 1985, 1990, 1995, 2000, 2005):
        rb = bazi(y)
        ms_list += [rb["master_synthesis"], collect_facts(rb, "bazi")]
        rz = ziwei(y)
        ms_list += [rz["master_synthesis"], collect_facts(rz, "ziwei")]
    # 玄空 / 阳宅
    for s in ("子", "午", "卯", "酉"):
        ms_list.append(c.post("/api/v1/fengshui/xuankong",
                       json={"sitting_mountain": s, "year": 2010}).json()["data"]["master_synthesis"])
    for a, b, d in [("坎", "巽", "震"), ("离", "乾", "坎"), ("震", "坤", "兑")]:
        ms_list.append(c.post("/api/v1/fengshui/yangzhai_sanyao",
                       json={"men": a, "zhu": b, "zao": d}).json()["data"]["master_synthesis"])
    # 六爻 / 奇门 / 择日
    for yv in ([7, 9, 8, 7, 8, 6], [8, 7, 6, 9, 7, 8], [6, 7, 8, 9, 8, 7]):
        ms_list.append(c.post("/api/v1/liuyao/divine", json={"method": "manual",
                       "yao_values": yv, "gender": "male", "topic": "求财",
                       "query_time": "2026-05-10T10:00:00"}).json()["data"]["master_synthesis"])
    for p in ("结婚", "安葬", "开业"):
        ms_list.append(c.post("/api/v1/date-selection/select",
                       json={"purpose": p, "year": 2026, "month": 3}).json()["data"]["master_synthesis"])
    # 合参
    ms_list.append(collect_facts_multi([(bazi(1990), "bazi"), (ziwei(1990), "ziwei")]))
    return ms_list


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-interception", type=float, default=0.98)
    args = ap.parse_args()

    from core.narration import guard_metrics
    corpus = build_corpus()
    m = guard_metrics(corpus)
    print(json.dumps(m, ensure_ascii=False, indent=2))

    ok = True
    if m["faithful_pass_rate"] != 1.0:
        print(f"✗ 忠实通过率 {m['faithful_pass_rate']} ≠ 1.0（出现误报，护栏冤枉了忠实转写）")
        ok = False
    if m["interception_rate"] < args.min_interception:
        print(f"✗ 拦截率 {m['interception_rate']} < {args.min_interception}（护栏漏判增多）")
        ok = False
    for k, v in m["by_kind"].items():
        if v["rate"] is not None and v["rate"] < args.min_interception:
            print(f"✗ [{k}] 拦截率 {v['rate']} < {args.min_interception}")
            ok = False

    if ok:
        print(f"\n✓ 护栏量化通过：{m['samples']} 盘语料，零误报，"
              f"拦截率 {m['interception_rate']}（{m['adversarial_total']} 对抗）")
        sys.exit(0)
    else:
        print("\n✗ 护栏量化回归失败 —— 护栏可能退化，请检查 verify_fidelity / 术语表")
        sys.exit(1)


if __name__ == "__main__":
    main()
