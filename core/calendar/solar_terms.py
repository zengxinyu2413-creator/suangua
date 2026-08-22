"""
core/calendar/solar_terms.py
=============================
Authoritative 节气 (Jié-Qì) data for all calendar calculations.

Uses lunarcalendar Festival classes for each of the 24 solar terms.
Falls back to ephem astronomical calculation when unavailable.
All datetime objects are timezone-naive China Standard Time (UTC+8).
"""
from datetime import datetime, date, timedelta
from typing import Optional, Tuple, List

# ─────────────────────────────────────────────────────────────
# 1. Primary: lunarcalendar Festival classes (date-only, no time)
# ─────────────────────────────────────────────────────────────
try:
    import lunarcalendar.solarterm as _lst
    _LUNARCAL_AVAILABLE = True
except ImportError:
    _LUNARCAL_AVAILABLE = False

# Map Chinese name → Festival class
_TERM_CLASSES = {}
if _LUNARCAL_AVAILABLE:
    _TERM_CLASSES = {
        "小寒": _lst.XiaoHan,  "大寒": _lst.DaHan,
        "立春": _lst.LiChun,   "雨水": _lst.YuShui,
        "惊蛰": _lst.JingZhe,  "春分": _lst.ChunFen,
        "清明": _lst.QingMing, "谷雨": _lst.GuYu,
        "立夏": _lst.LiXia,    "小满": _lst.XiaoMan,
        "芒种": _lst.MangZhong,"夏至": _lst.XiaZhi,
        "小暑": _lst.XiaoShu,  "大暑": _lst.DaShu,
        "立秋": _lst.LiQiu,    "处暑": _lst.ChuShu,
        "白露": _lst.BaiLu,    "秋分": _lst.QiuFen,
        "寒露": _lst.HanLu,    "霜降": _lst.ShuangJiang,
        "立冬": _lst.LiDong,   "小雪": _lst.XiaoXue,
        "大雪": _lst.DaXue,    "冬至": _lst.DongZhi,
    }

# ─────────────────────────────────────────────────────────────
# 2. Fallback: ephem solar longitude calculation (minute-accurate)
# ─────────────────────────────────────────────────────────────
# Each of 24 solar terms corresponds to 15° increments of solar longitude,
# starting at 小寒 = 285°.
_TERM_LONGITUDES = {
    "小寒":285, "大寒":300, "立春":315, "雨水":330,
    "惊蛰":345, "春分":  0, "清明": 15, "谷雨": 30,
    "立夏": 45, "小满": 60, "芒种": 75, "夏至": 90,
    "小暑":105, "大暑":120, "立秋":135, "处暑":150,
    "白露":165, "秋分":180, "寒露":195, "霜降":210,
    "立冬":225, "小雪":240, "大雪":255, "冬至":270,
}

def _ephem_solarterm(year: int, name: str) -> Optional[datetime]:
    """Calculate solar term datetime via ephem (UTC+8 CST, minute accuracy)."""
    try:
        import ephem, math
        target_lon = _TERM_LONGITUDES.get(name)
        if target_lon is None:
            return None

        # 二分搜索初值：节气大约每 15.2 天一个（精确 ephem 二分逼近至 1 秒精度）
        term_order = list(_TERM_LONGITUDES.keys()).index(name)
        approx_doy = int(term_order * 15.2) + 5
        approx_date = datetime(year, 1, 1) + timedelta(days=approx_doy)

        lo = ephem.Date(approx_date - timedelta(days=20))
        hi = ephem.Date(approx_date + timedelta(days=20))
        sun = ephem.Sun()

        # Binary search for exact moment sun crosses target longitude
        for _ in range(60):
            mid = (lo + hi) / 2
            sun.compute(mid, epoch=mid)
            lon_deg = float(sun.hlong) * 180.0 / math.pi

            # Handle wrap-around at 0°/360°
            diff = (lon_deg - target_lon + 360) % 360
            if diff > 180:
                hi = mid
            else:
                lo = mid
            if hi - lo < 1.0 / 86400:   # ~1 second precision
                break

        dt_utc = ephem.Date(lo).datetime()
        dt_cst = dt_utc + timedelta(hours=8)   # UTC → CST
        return dt_cst.replace(tzinfo=None)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# 3. Public API
# ─────────────────────────────────────────────────────────────

SOLAR_TERM_NAMES: List[str] = [
    "小寒", "大寒", "立春", "雨水", "惊蛰", "春分",
    "清明", "谷雨", "立夏", "小满", "芒种", "夏至",
    "小暑", "大暑", "立秋", "处暑", "白露", "秋分",
    "寒露", "霜降", "立冬", "小雪", "大雪", "冬至",
]

# Jié (节) — the 12 terms that open a new lunar month pillar
JIE_NAMES: List[str] = [
    "小寒", "立春", "惊蛰", "清明", "立夏", "芒种",
    "小暑", "立秋", "白露", "寒露", "立冬", "大雪",
]

# In-memory cache to avoid recomputing
_cache: dict = {}


def _get_solarterm_dt(year: int, name: str) -> Optional[datetime]:
    """
    Return the datetime of *name* solar term in *year* (CST, no timezone).
    Tries lunarcalendar first (date only, sets time to noon), then ephem
    for minute-level accuracy.
    """
    key = (year, name)
    if key in _cache:
        return _cache[key]

    result = None

    # Primary: lunarcalendar Festival class → returns date object
    if _LUNARCAL_AVAILABLE and name in _TERM_CLASSES:
        try:
            d = _TERM_CLASSES[name](year)
            if isinstance(d, date):
                # Use ephem to get the actual time within the day
                dt_ephem = _ephem_solarterm(year, name)
                if dt_ephem and dt_ephem.year == year:
                    result = dt_ephem
                else:
                    result = datetime(d.year, d.month, d.day, 12, 0)
        except Exception as _e1:
            from core.log import log_failure; log_failure("calendar", "装配(自动补充日志)", _e1)

    # Fallback: pure ephem calculation
    if result is None:
        result = _ephem_solarterm(year, name)

    _cache[key] = result
    return result


def get_jie_dates(year: int) -> List[Tuple[str, datetime]]:
    """
    Return list of (jie_name, datetime) for all 12 Jié in *year*,
    sorted chronologically.
    """
    result = []
    for name in JIE_NAMES:
        dt = _get_solarterm_dt(year, name)
        if dt:
            result.append((name, dt))
    result.sort(key=lambda x: x[1])
    return result


def get_month_dizhi_at(dt: datetime) -> str:
    """
    Return the lunar-month DiZhi for a given datetime,
    determined by which Jié boundary has most recently passed.
    """
    from core.constants import JIE_TO_DIZHI

    for year in (dt.year, dt.year - 1):
        for name, jie_dt in reversed(get_jie_dates(year)):
            if dt >= jie_dt:
                return JIE_TO_DIZHI[name]

    _FALLBACK = ["丑","寅","卯","辰","巳","午","未","申","酉","戌","亥","子"]
    return _FALLBACK[dt.month - 1]


def nearest_jie(dt: datetime) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Return (previous_jie_dt, next_jie_dt) bracketing *dt* for DaYun calculation."""
    all_jie: List[datetime] = []
    for year in (dt.year - 1, dt.year, dt.year + 1):
        for _, jie_dt in get_jie_dates(year):
            all_jie.append(jie_dt)
    all_jie.sort()

    prev_jie: Optional[datetime] = None
    next_jie: Optional[datetime] = None
    for jie_dt in all_jie:
        if jie_dt <= dt:
            prev_jie = jie_dt
        else:
            next_jie = jie_dt
            break
    return prev_jie, next_jie


def lichun_of_year(year: int) -> Optional[datetime]:
    """Return the datetime of 立春 for the given Gregorian year."""
    return _get_solarterm_dt(year, "立春")


# ─────────────────────────────────────────────────────────────
# 权威历法 helper（节气/干支统一出口 — 各模块一律走此，杜绝自造）
#
# 历史教训：六爻月令、奇门元、择日月支/节气名 四个同根 bug，皆因模块
# 绕过底座、自造 月支/节气 转换。今以下函数为唯一权威出口，全部基于
# lunar_python 节气历，确保跨模块一致、可回归。
# ─────────────────────────────────────────────────────────────

def _lunar_of(dt: datetime):
    """取 lunar_python Lunar 对象（节气历基准）。"""
    from lunar_python import Solar
    return Solar.fromYmdHms(dt.year, dt.month, dt.day,
                            getattr(dt, "hour", 0), getattr(dt, "minute", 0), 0).getLunar()


def day_ganzhi_at(dt: datetime) -> str:
    """该日之日干支（连续六十甲子，节气历）。返回如「丁亥」。"""
    try:
        return _lunar_of(dt).getDayInGanZhi()
    except Exception:
        # 退路：以 ganzhi 模块权威锚点（1900-01-01=甲戌, idx10）连续推日干支
        from core.calendar.ganzhi import ganzhi_from_index, _REF_DATE, _REF_DAY_IDX  # type: ignore
        delta = (dt.date() - _REF_DATE).days
        g, z = ganzhi_from_index((_REF_DAY_IDX + delta) % 60)
        return f"{g}{z}"


def month_ganzhi_at(dt: datetime) -> str:
    """该日之月柱干支（节气月，五虎遁年起月）。返回如「甲午」。"""
    try:
        return _lunar_of(dt).getMonthInGanZhi()
    except Exception:
        return "?" + get_month_dizhi_at(dt)


def month_dizhi_at(dt: datetime) -> str:
    """该日之月支（月建，节气定）。get_month_dizhi_at 的别名，统一命名。"""
    return get_month_dizhi_at(dt)


def solar_term_on(dt: datetime) -> Optional[str]:
    """若该日恰为某节气交节日，返回其名；否则 None。"""
    try:
        jq = _lunar_of(dt).getJieQi()
        return jq or None
    except Exception:
        return None


def current_solar_term(dt: datetime) -> Optional[str]:
    """返回当前统辖该日之节气名（最近已过之节气）。"""
    try:
        lunar = _lunar_of(dt)
        # lunar_python: getPrevJieQi 含节与气；取最近已过者
        jq = lunar.getPrevJieQi(True)
        return jq.getName() if jq else None
    except Exception:
        # 退路：扫本年节气
        try:
            for name, jdt in reversed(get_jie_dates(dt.year)):
                if dt >= jdt:
                    return name
        except Exception as _e2:
            from core.log import log_failure; log_failure("calendar", "装配(自动补充日志)", _e2)
        return None
