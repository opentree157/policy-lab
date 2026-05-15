"""Labor market trends analysis using synthetic BLS-derived data."""

import time
from typing import Any, Callable, Dict, List

import numpy as np

_SECTOR_BASE_RATES: Dict[str, float] = {
    "Manufacturing": 5.1,
    "Services": 4.4,
    "Government": 2.8,
    "Technology": 2.3,
    "Healthcare": 2.1,
    "Construction": 7.2,
    "Retail": 5.8,
    "Finance": 3.1,
}

# Simulated recession effect years (relative unemployment spikes)
_RECESSION_YEARS = {2009: 4.5, 2020: 7.8}


def run_labor_trends(
    dataset_id: str,
    parameters: Dict[str, Any],
    log_fn: Callable,
    metric_fn: Callable,
) -> Dict[str, Any]:
    sectors: List[str] = parameters.get("sectors", list(_SECTOR_BASE_RATES.keys())[:4])
    year_start: int = int(parameters.get("year_start", 2010))
    year_end: int = int(parameters.get("year_end", 2024))
    measure: str = parameters.get("measure", "u3")

    rng = np.random.default_rng(7)
    years = list(range(year_start, year_end + 1))

    log_fn(f"Loading BLS CPS microdata for {len(sectors)} sectors ({year_start}–{year_end})")
    time.sleep(0.4)
    metric_fn(rows_processed=80_000)

    log_fn("Applying seasonal adjustment via X-13ARIMA-SEATS...")
    time.sleep(0.35)
    metric_fn(rows_processed=200_000)

    # Trend by year × sector
    trend_by_year = []
    for year in years:
        recession_boost = 0.0
        for r_year, boost in _RECESSION_YEARS.items():
            if abs(year - r_year) <= 1:
                decay = 1.0 - abs(year - r_year) * 0.4
                recession_boost = boost * decay

        for sector in sectors:
            base = _SECTOR_BASE_RATES.get(sector, 4.5)
            # Gradual decline post-recession, tech stays low
            trend_factor = max(0.0, (2010 - year) * 0.08) if year >= 2010 else 0.0
            rate = base + recession_boost + trend_factor + float(rng.normal(0, 0.3))
            # U-6 is ~1.8x broader
            u6_rate = rate * 1.8 + float(rng.normal(0, 0.4))
            entry = {
                "year": year,
                "sector": sector,
                "u3_rate": round(float(np.clip(rate, 1.0, 20.0)), 2),
                "u6_rate": round(float(np.clip(u6_rate, 2.0, 32.0)), 2),
            }
            trend_by_year.append(entry)

    log_fn("Computing sector comparison statistics...")
    metric_fn(rows_processed=400_000)
    time.sleep(0.3)

    # Current snapshot (latest year)
    latest_year = year_end
    current_by_sector = []
    for sector in sectors:
        latest = [r for r in trend_by_year if r["year"] == latest_year and r["sector"] == sector]
        prior = [r for r in trend_by_year if r["year"] == latest_year - 1 and r["sector"] == sector]
        if latest and prior:
            current_rate = latest[0]["u3_rate"]
            prior_rate = prior[0]["u3_rate"]
            current_by_sector.append({
                "sector": sector,
                "current_rate": current_rate,
                "prior_year_rate": prior_rate,
                "yoy_change": round(current_rate - prior_rate, 2),
                "trend": "improving" if current_rate < prior_rate else "worsening",
                "labor_force_thousands": int(rng.integers(500, 25_000)),
            })
    current_by_sector.sort(key=lambda x: x["current_rate"])

    # Education premium — workers with more education have lower unemployment
    edu_levels = ["No diploma", "High school", "Some college", "Bachelor's", "Graduate"]
    edu_rates = [8.2, 5.4, 4.1, 2.8, 1.9]
    education_breakdown = [
        {
            "education_level": level,
            "u3_rate": round(rate + float(rng.normal(0, 0.2)), 2),
            "labor_force_participation": round(float(np.clip(45 + i * 9 + rng.normal(0, 1), 40, 80)), 1),
        }
        for i, (level, rate) in enumerate(zip(edu_levels, edu_rates))
    ]

    log_fn("Building aggregate summary...")
    metric_fn(rows_processed=500_000)
    time.sleep(0.2)

    avg_current = float(np.mean([s["current_rate"] for s in current_by_sector])) if current_by_sector else 0
    best = min(current_by_sector, key=lambda x: x["current_rate"]) if current_by_sector else {}
    worst = max(current_by_sector, key=lambda x: x["current_rate"]) if current_by_sector else {}

    summary = {
        "sectors_analyzed": len(sectors),
        "years_covered": f"{year_start}–{year_end}",
        "avg_current_u3_rate": round(avg_current, 2),
        "lowest_unemployment_sector": best.get("sector", "N/A"),
        "lowest_rate": best.get("current_rate", 0),
        "highest_unemployment_sector": worst.get("sector", "N/A"),
        "highest_rate": worst.get("current_rate", 0),
        "sectors_improving": len([s for s in current_by_sector if s["trend"] == "improving"]),
        "key_finding": (
            f"Among analyzed sectors, {best.get('sector', 'N/A')} shows the lowest unemployment "
            f"at {best.get('current_rate', 0):.1f}% while {worst.get('sector', 'N/A')} remains "
            f"highest at {worst.get('current_rate', 0):.1f}%. "
            f"{len([s for s in current_by_sector if s['trend'] == 'improving'])} of {len(sectors)} "
            f"sectors are trending toward improvement year-over-year."
        ),
    }

    log_fn(
        f"Complete — avg U-3 {summary['avg_current_u3_rate']:.1f}%, "
        f"best: {summary['lowest_unemployment_sector']}"
    )

    return {
        "chart_type": "labor_trends",
        "summary": summary,
        "trend_by_year": trend_by_year,
        "current_by_sector": current_by_sector,
        "education_breakdown": education_breakdown,
    }
