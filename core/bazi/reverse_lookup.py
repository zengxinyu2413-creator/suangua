"""
core/bazi/reverse_lookup.py
===========================
八字反查 — Given four pillars (干支), find possible birth dates.
Searches a year range and returns matching dates.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from core.bazi.chart import build_chart


def reverse_lookup(
    year_gz: str,
    month_gz: Optional[str] = None,
    day_gz: Optional[str] = None,
    hour_gz: Optional[str] = None,
    year_range: tuple = (1940, 2050),
) -> List[Dict[str, Any]]:
    """
    Find birth dates matching the given GanZhi pillars.
    
    At minimum year_gz is required. Additional pillars narrow results.
    Returns list of {date, hour, year_pillar, month_pillar, day_pillar, hour_pillar}.
    """
    results = []
    
    for year in range(year_range[0], year_range[1] + 1):
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    # Validate date
                    dt = datetime(year, month, day)
                except ValueError:
                    continue
                
                # Quick year check first (cheapest)
                chart = build_chart(year, month, day, 12, 0)
                y_gz = chart["year_pillar"]["tiangan"] + chart["year_pillar"]["dizhi"]
                if y_gz != year_gz:
                    continue
                
                # Month check
                m_gz = chart["month_pillar"]["tiangan"] + chart["month_pillar"]["dizhi"]
                if month_gz and m_gz != month_gz:
                    continue
                
                # Day check
                d_gz = chart["day_pillar"]["tiangan"] + chart["day_pillar"]["dizhi"]
                if day_gz and d_gz != day_gz:
                    continue
                
                # Hour check — try all 12 hours if specified
                if hour_gz:
                    for h in [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]:
                        hc = build_chart(year, month, day, h, 0)
                        h_gz = hc["hour_pillar"]["tiangan"] + hc["hour_pillar"]["dizhi"]
                        if h_gz == hour_gz:
                            results.append({
                                "date": f"{year}-{month:02d}-{day:02d}",
                                "hour": h,
                                "year_gz": y_gz,
                                "month_gz": m_gz,
                                "day_gz": d_gz,
                                "hour_gz": h_gz,
                            })
                else:
                    results.append({
                        "date": f"{year}-{month:02d}-{day:02d}",
                        "hour": None,
                        "year_gz": y_gz,
                        "month_gz": m_gz,
                        "day_gz": d_gz,
                        "hour_gz": None,
                    })
                
                if len(results) >= 100:
                    return results
    
    return results


def quick_reverse(year_gz: str, day_gz: str,
                  year_range: tuple = (1960, 2030)) -> List[Dict[str, Any]]:
    """Quick reverse: only year + day GanZhi (most common use case)."""
    results = []
    for year in range(year_range[0], year_range[1] + 1):
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    datetime(year, month, day)
                except ValueError:
                    continue
                chart = build_chart(year, month, day, 12, 0)
                y = chart["year_pillar"]["tiangan"] + chart["year_pillar"]["dizhi"]
                d = chart["day_pillar"]["tiangan"] + chart["day_pillar"]["dizhi"]
                if y == year_gz and d == day_gz:
                    m = chart["month_pillar"]["tiangan"] + chart["month_pillar"]["dizhi"]
                    results.append({
                        "date": f"{year}-{month:02d}-{day:02d}",
                        "year_gz": y, "month_gz": m, "day_gz": d,
                    })
                    if len(results) >= 50:
                        return results
    return results
