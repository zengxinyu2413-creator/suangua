"""
core/daily_guardian.py — 每日守护（全动态推算）
所有内容按传入日期实时计算，无任何缓存或固定值。
"""
from datetime import date, datetime
from typing import Dict, Any, Optional

# 地支→瑞兽映射 + 图片文件名
DIZHI_RUISHOU = {
    "子":("玄武灵龟","ruishou_zi"),  "丑":("麒麟仁兽","ruishou_chou"),
    "寅":("白虎威兽","ruishou_yin"),  "卯":("青龙瑞兽","ruishou_mao"),
    "辰":("应龙云兽","ruishou_chen"), "巳":("腾蛇灵蛇","ruishou_si"),
    "午":("朱雀凤凰","ruishou_wu"),   "未":("獬豸正兽","ruishou_wei"),
    "申":("白猿智兽","ruishou_shen"), "酉":("金凤吉禽","ruishou_you"),
    "戌":("天狗守兽","ruishou_xu"),   "亥":("天猪福兽","ruishou_hai"),
}

# 日干→每日诗句
DAY_GAN_POEMS = {
    "甲":"大哉乾元，万物资始","乙":"地势坤，厚德载物",
    "丙":"日出东方，光照万里","丁":"灯烛辉映，温润如玉",
    "戊":"大地承载，厚重安稳","己":"田园沃土，孕育万物",
    "庚":"秋风肃杀，金石为开","辛":"珠玉含光，辛金清贵",
    "壬":"江河奔流，浩荡无边","癸":"雨露滋润，润物无声",
}

# 五行属性
WX_MAP = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}


def generate_daily_report(d: Optional[date] = None) -> Dict[str, Any]:
    """基于日期实时推算全部内容，每天每时辰都不同。"""
    if d is None:
        d = date.today()

    from lunar_python import Solar as LSolar
    from core.constants import NAYIN

    sol = LSolar.fromYmd(d.year, d.month, d.day)
    lun = sol.getLunar()

    # ── 基础干支（每天变化）──
    year_gz = lun.getYearInGanZhi()
    month_gz = lun.getMonthInGanZhi()
    day_gz = lun.getDayInGanZhi()
    day_gan = lun.getDayGan()
    day_zhi = lun.getDayZhi()
    weekday = ["一","二","三","四","五","六","日"][d.weekday()]
    lunar_month = lun.getMonthInChinese()
    lunar_day = lun.getDayInChinese()

    # ── 纳音（按干支组合推算）──
    year_nayin = lun.getYearNaYin()
    month_nayin = lun.getMonthNaYin()
    day_nayin = lun.getDayNaYin()

    # ── 节气（天文推算）──
    current_jieqi = lun.getJieQi() or ""
    prev_jieqi = lun.getPrevJieQi()
    next_jieqi = lun.getNextJieQi()
    jieqi_info = {"current": current_jieqi}
    if prev_jieqi:
        jieqi_info["prev"] = {"name": prev_jieqi.getName(), "date": prev_jieqi.getSolar().toYmd()}
    if next_jieqi:
        jieqi_info["next"] = {"name": next_jieqi.getName(), "date": next_jieqi.getSolar().toYmd()}

    # ── 建除十二神（按月支+日支推算）──
    from core.date_selection.selector import _get_officer, OFFICER_DATA
    month_zhi_str = lun.getMonthZhi()
    officer = _get_officer(day_zhi, month_zhi_str)
    officer_info = OFFICER_DATA.get(officer, {})

    # ── 黄道黑道天神（按日推算）──
    tian_shen = lun.getDayTianShen()
    tian_shen_type = lun.getDayTianShenType()
    tian_shen_luck = lun.getDayTianShenLuck()

    # ── 二十八星宿（按日轮转）──
    xiu = lun.getXiu()
    xiu_luck = lun.getXiuLuck()
    xiu_song = ""
    try: xiu_song = lun.getXiuSong()
    except: pass

    # ── 宜忌（按日干支+黄道推算，不足时补充时辰宜忌）──
    yi_raw = list(lun.getDayYi())
    ji_raw = list(lun.getDayJi())

    if len(yi_raw) <= 2 or '馀事勿取' in yi_raw:
        pool = set()
        for h in range(0, 24, 2):
            try:
                sh = LSolar.fromYmdHms(d.year, d.month, d.day, h, 0, 0).getLunar()
                for item in sh.getTimeYi(): pool.add(item)
            except: pass
        combined = list(dict.fromkeys(yi_raw + list(pool)))
        combined = [x for x in combined if x not in ('馀事勿取','诸事不宜')]
        if combined: yi_raw = combined[:12]

    if ji_raw == ['诸事不宜'] or not ji_raw:
        pool = set()
        for h in range(0, 24, 2):
            try:
                sh = LSolar.fromYmdHms(d.year, d.month, d.day, h, 0, 0).getLunar()
                for item in sh.getTimeJi(): pool.add(item)
            except: pass
        combined = list(dict.fromkeys(ji_raw + list(pool)))
        combined = [x for x in combined if x != '诸事不宜']
        if combined: ji_raw = combined[:10]

    # ── 吉神凶煞（按日推算）──
    ji_shen = list(lun.getDayJiShen())
    xiong_sha = list(lun.getDayXiongSha())

    # ── 彭祖百忌（按日干+日支推算）──
    pengzu_gan = lun.getPengZuGan()
    pengzu_zhi = lun.getPengZuZhi()

    # ── 冲煞空亡（按日推算）──
    chong = lun.getDayChongDesc()
    xun_kong = lun.getDayXunKong()

    # ── 方位（按日推算）──
    positions = {
        "喜神": lun.getDayPositionXiDesc(),
        "财神": lun.getDayPositionCaiDesc(),
        "福神": lun.getDayPositionFuDesc(),
    }
    try: positions["胎神"] = lun.getDayPositionTai()
    except: pass

    # ── 十二时辰（按日干起时法推算，每天不同）──
    SHICHEN = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    SHICHEN_HOURS = ["23-01","01-03","03-05","05-07","07-09","09-11",
                     "11-13","13-15","15-17","17-19","19-21","21-23"]
    hours = []
    for i, sc in enumerate(SHICHEN):
        try:
            # 五鼠遁日起时法
            tg_idx = "甲乙丙丁戊己庚辛壬癸".index(day_gan)
            base = [0,2,4,6,8][tg_idx % 5]
            h_gan_idx = (base + i) % 10
            h_gan = "甲乙丙丁戊己庚辛壬癸"[h_gan_idx]
            h_gz = f"{h_gan}{sc}"
            h_nayin = NAYIN.get(h_gz, "")
            # 时辰吉凶（按黄道十二神轮转）
            luck_seq = ["吉","吉","凶","凶","吉","吉","凶","吉","凶","凶","吉","凶"]
            luck_offset = SHICHEN.index(day_zhi) if day_zhi in SHICHEN else 0
            h_luck = luck_seq[(i + luck_offset) % 12]
            hours.append({"shichen":sc,"hours":SHICHEN_HOURS[i],"ganzhi":h_gz,"nayin":h_nayin,"luck":h_luck})
        except:
            hours.append({"shichen":sc,"hours":SHICHEN_HOURS[i],"ganzhi":"","luck":"中"})

    # ── 年飞星（按年推算）──
    try:
        from core.fengshui.flying_stars import get_annual_center_star
        annual_star = get_annual_center_star(d.year)
    except:
        annual_star = None

    # ── 瑞兽 + 图片（按日支推算）──
    rs_name, rs_img = DIZHI_RUISHOU.get(day_zhi, ("麒麟瑞兽","ruishou_chou"))

    # ── 综合评分（多因子动态计算）──
    score = 50
    # 黄道/黑道 (+15/-5)
    if tian_shen_type == "黄道": score += 15
    else: score -= 5
    # 星宿吉凶 (+12/-8)
    if xiu_luck == "吉": score += 12
    elif xiu_luck == "凶": score -= 8
    # 建除神 (+10/-10/+3)
    officer_nature = officer_info.get("nature","")
    if officer_nature == "吉": score += 10
    elif officer_nature == "凶": score -= 10
    else: score += 3
    # 吉神vs凶煞数量差
    god_diff = len(ji_shen) - len(xiong_sha)
    score += min(max(god_diff * 2, -8), 10)
    # 宜忌丰富度
    if len(yi_raw) >= 6: score += 5
    if len(ji_raw) <= 2: score += 3
    # 日干五行与月令关系加成
    day_wx = WX_MAP.get(day_gan,"")
    month_zhi_wx = {"寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土",
                    "申":"金","酉":"金","戌":"土","亥":"水","子":"水","丑":"土"}.get(month_zhi_str,"")
    SHENG = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
    if SHENG.get(month_zhi_wx) == day_wx: score += 5  # 月令生日干
    elif SHENG.get(day_wx) == month_zhi_wx: score -= 3  # 日干泄气

    score = max(25, min(98, score))

    # ── 诗句（按日干）──
    poem = DAY_GAN_POEMS.get(day_gan, "一阴一阳之谓道")

    return {
        "date": d.isoformat(),
        "weekday": f"星期{weekday}",
        "lunar": f"{lunar_month}月{lunar_day}",
        "year_gz": year_gz, "month_gz": month_gz, "day_gz": day_gz,
        "day_gan": day_gan, "day_zhi": day_zhi, "day_wuxing": day_wx,
        "nayin": {"year": year_nayin, "month": month_nayin, "day": day_nayin},
        "jieqi": jieqi_info,
        "officer": {"name": officer, "nature": officer_nature, "detail": officer_info.get("detail","")},
        "tianshen": {"name": tian_shen, "type": tian_shen_type, "luck": tian_shen_luck},
        "xingxiu": {"name": xiu, "luck": xiu_luck, "song": xiu_song or ""},
        "yi": yi_raw[:12], "ji": ji_raw[:10],
        "jishen": ji_shen, "xiongsha": xiong_sha,
        "pengzu": f"{pengzu_gan}　{pengzu_zhi}",
        "chong": chong, "xunkong": xun_kong,
        "positions": positions, "hours": hours,
        "annual_star": annual_star,
        "ruishou": rs_name, "ruishou_img": rs_img,
        "score": score, "poem": poem,
    }
