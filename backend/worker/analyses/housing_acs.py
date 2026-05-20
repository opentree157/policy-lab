"""
ACS Housing Cost Burden Analysis — real Census Bureau data pipeline.

Fetches table B25070 (Gross Rent as a Percentage of Household Income)
from the Census Bureau Data API for each requested year, distributing
year-fetches across parallel Ray workers.

Data source: https://api.census.gov/data/{year}/acs/acs1
No API key required. ACS 1-year estimates cover 2005–present.
Note: 2020 ACS 1-year was not released (COVID collection disruption).

Cost burden definition (HUD standard):
  Cost burdened   = gross rent > 30% of household income
  Severely burdened = gross rent > 50% of household income
"""

import time
from typing import Any, Callable, Dict, List, Optional, Set

import httpx
import numpy as np

try:
    import ray
    _RAY_AVAILABLE = True
except ImportError:
    _RAY_AVAILABLE = False

CENSUS_API = "https://api.census.gov/data"

# B25070 variables — gross rent as % of income buckets + margins of error
B25070_VARS = [
    "B25070_001E",  # Total renter-occupied units
    "B25070_007E",  # 30.0–34.9 percent
    "B25070_008E",  # 35.0–39.9 percent
    "B25070_009E",  # 40.0–49.9 percent
    "B25070_010E",  # 50.0 percent or more (severely burdened)
    "B25070_001M",  # Margin of error — total (90% confidence interval)
    "B25070_010M",  # Margin of error — severely burdened
]

# Census encodes suppressed/not-applicable cells with these sentinel values
CENSUS_NULL = {-666666666, -222222222, -333333333, -888888888}

# 2020 ACS 1-year estimates were not released due to COVID disruptions
SKIP_YEARS = {2020}

STATE_ABBR_TO_FIPS: Dict[str, str] = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08",
    "CT": "09", "DE": "10", "DC": "11", "FL": "12", "GA": "13", "HI": "15",
    "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21",
    "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27",
    "MS": "28", "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33",
    "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46",
    "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53",
    "WV": "54", "WI": "55", "WY": "56",
}

FIPS_TO_NAME: Dict[str, str] = {
    "01": "Alabama",        "02": "Alaska",          "04": "Arizona",
    "05": "Arkansas",       "06": "California",      "08": "Colorado",
    "09": "Connecticut",    "10": "Delaware",        "11": "District of Columbia",
    "12": "Florida",        "13": "Georgia",         "15": "Hawaii",
    "16": "Idaho",          "17": "Illinois",        "18": "Indiana",
    "19": "Iowa",           "20": "Kansas",          "21": "Kentucky",
    "22": "Louisiana",      "23": "Maine",           "24": "Maryland",
    "25": "Massachusetts",  "26": "Michigan",        "27": "Minnesota",
    "28": "Mississippi",    "29": "Missouri",        "30": "Montana",
    "31": "Nebraska",       "32": "Nevada",          "33": "New Hampshire",
    "34": "New Jersey",     "35": "New Mexico",      "36": "New York",
    "37": "North Carolina", "38": "North Dakota",    "39": "Ohio",
    "40": "Oklahoma",       "41": "Oregon",          "42": "Pennsylvania",
    "44": "Rhode Island",   "45": "South Carolina",  "46": "South Dakota",
    "47": "Tennessee",      "48": "Texas",           "49": "Utah",
    "50": "Vermont",        "51": "Virginia",        "53": "Washington",
    "54": "West Virginia",  "55": "Wisconsin",       "56": "Wyoming",
}


def _safe_int(val: Any) -> Optional[int]:
    """Parse a Census API value string; return None for nulls and sentinels."""
    if val is None:
        return None
    try:
        v = int(val)
        return None if (v in CENSUS_NULL or v < 0) else v
    except (ValueError, TypeError):
        return None


def _fetch_year(year: int, fips_filter: Optional[Set[str]]) -> List[Dict[str, Any]]:
    """
    Fetch B25070 for all states for one ACS 1-year estimate.

    Returns a list of parsed state records. Returns an empty list if the year
    is skipped (2020), if the API is unreachable, or if the response is malformed.
    """
    if year in SKIP_YEARS:
        return []

    variables = ",".join(B25070_VARS)
    url = f"{CENSUS_API}/{year}/acs/acs1?get={variables}&for=state:*"

    try:
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    if len(data) < 2:
        return []

    headers = [h.strip() for h in data[0]]
    records: List[Dict[str, Any]] = []

    for row in data[1:]:
        r = dict(zip(headers, row))
        fips = r.get("state", "").zfill(2)

        if fips_filter and fips not in fips_filter:
            continue

        total = _safe_int(r.get("B25070_001E"))
        if not total:
            continue

        b30 = _safe_int(r.get("B25070_007E"))
        b35 = _safe_int(r.get("B25070_008E"))
        b40 = _safe_int(r.get("B25070_009E"))
        b50 = _safe_int(r.get("B25070_010E"))

        # Skip states with any suppressed bucket estimates
        if any(v is None for v in [b30, b35, b40, b50]):
            continue

        cost_burdened = b30 + b35 + b40 + b50  # type: ignore[operator]
        severely_burdened = b50

        # Reliability flag: CV > 30% means the estimate is statistically unreliable
        moe_total = _safe_int(r.get("B25070_001M"))
        unreliable = False
        if moe_total and total:
            se = moe_total / 1.645   # 90% confidence interval → standard error
            unreliable = (se / total) > 0.30

        records.append({
            "year": year,
            "fips": fips,
            "state": FIPS_TO_NAME.get(fips, fips),
            "total_renters": total,
            "cost_burdened": cost_burdened,
            "severely_burdened": severely_burdened,
            "cost_burden_rate": round(cost_burdened / total, 4),
            "severe_burden_rate": round(severely_burdened / total, 4),  # type: ignore[operator]
            "moe_pct": round((moe_total / total) * 100, 1) if moe_total else None,
            "unreliable": unreliable,
        })

    return records


if _RAY_AVAILABLE:
    @ray.remote
    def _fetch_years_chunk(years: List[int], fips_filter: Optional[Set[str]]) -> List[Dict[str, Any]]:
        """Ray worker: fetch and process ACS B25070 for a list of years."""
        results: List[Dict[str, Any]] = []
        for year in years:
            results.extend(_fetch_year(year, fips_filter))
            time.sleep(0.3)   # polite delay between Census API requests
        return results


def _fetch_years_chunk_local(years: List[int], fips_filter: Optional[Set[str]]) -> List[Dict[str, Any]]:
    """Thread-pool fallback — identical logic, no Ray dependency."""
    results: List[Dict[str, Any]] = []
    for year in years:
        results.extend(_fetch_year(year, fips_filter))
        time.sleep(0.3)
    return results


def run_housing_affordability(
    dataset_id: str,
    parameters: Dict[str, Any],
    log_fn: Callable,
    metric_fn: Callable,
) -> Dict[str, Any]:
    """
    Real ACS housing cost burden analysis via the Census Bureau Data API.

    Partitions the requested year range into chunks and dispatches each
    chunk to a parallel Ray worker. Each worker fetches B25070 estimates
    for all requested states and returns parsed state-year records.

    Computes per-state time series, linear trend slopes, pre/post-COVID
    comparisons, and a population-weighted national average series.
    """
    year_start = int(parameters.get("year_start", 2015))
    year_end   = int(parameters.get("year_end",   2022))
    state_abbrs: List[str] = parameters.get("states", [])

    fips_filter: Optional[Set[str]] = None
    if state_abbrs:
        fips_filter = {STATE_ABBR_TO_FIPS[s] for s in state_abbrs if s in STATE_ABBR_TO_FIPS}

    years = [y for y in range(year_start, year_end + 1) if y not in SKIP_YEARS]
    if not years:
        raise ValueError("No valid ACS years in range (2020 not available; check year_start/year_end)")

    scope = f"{len(fips_filter)} states" if fips_filter else "all states"
    log_fn("ACS B25070 — Housing Cost Burden Analysis (Census Bureau Data API)")
    log_fn(f"Years: {years[0]}–{years[-1]}  ({len(years)} surveys; 2020 excluded — no ACS 1-year release)")
    log_fn(f"Geography: {scope}")
    log_fn(f"Variables: gross rent >30% income (burdened) and >50% (severely burdened)")

    n_workers = min(4, len(years))
    chunks = [years[i::n_workers] for i in range(n_workers)]
    log_fn(f"Dispatching {len(years)} year-fetches across {n_workers} parallel Ray workers…")

    all_records: List[Dict[str, Any]] = []

    if _RAY_AVAILABLE:
        futures = [_fetch_years_chunk.remote(chunk, fips_filter) for chunk in chunks]
        for i, batch in enumerate(ray.get(futures), 1):
            all_records.extend(batch)
            log_fn(f"  Worker {i}/{n_workers} done — {len(all_records):,} state-year records so far")
            metric_fn(rows_processed=len(all_records))
    else:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            fs = [pool.submit(_fetch_years_chunk_local, chunk, fips_filter) for chunk in chunks]
            for i, f in enumerate(fs, 1):
                all_records.extend(f.result())
                log_fn(f"  Worker {i}/{n_workers} done — {len(all_records):,} state-year records so far")
                metric_fn(rows_processed=len(all_records))

    if not all_records:
        raise RuntimeError(
            "Census API returned no data. Check year range (2005–2022 supported) and network access."
        )

    log_fn(f"Collected {len(all_records):,} state-year records — computing statistics…")

    # -----------------------------------------------------------------------
    # Per-state time series + trend slopes
    # -----------------------------------------------------------------------
    state_trends = []
    for fips in sorted({r["fips"] for r in all_records}):
        recs = sorted([r for r in all_records if r["fips"] == fips], key=lambda x: x["year"])

        series = [
            {
                "year": r["year"],
                "cost_burden_rate": r["cost_burden_rate"],
                "severe_burden_rate": r["severe_burden_rate"],
                "total_renters": r["total_renters"],
                "unreliable": r["unreliable"],
            }
            for r in recs
        ]

        rates = np.array([s["cost_burden_rate"] for s in series])
        yrs   = np.array([s["year"] for s in series])
        slope = float(np.polyfit(yrs - yrs.mean(), rates, 1)[0]) if len(rates) >= 3 else 0.0

        pre_covid  = [s["cost_burden_rate"] for s in series if s["year"] < 2020]
        post_covid = [s["cost_burden_rate"] for s in series if s["year"] >= 2021]

        state_trends.append({
            "fips":               fips,
            "state":              recs[0]["state"],
            "series":             series,
            "current_rate":       series[-1]["cost_burden_rate"],
            "current_severe":     series[-1]["severe_burden_rate"],
            "trend_slope":        round(slope, 5),
            "improving":          slope < -0.002,
            "pre_covid_avg":      round(float(np.mean(pre_covid)),  4) if pre_covid  else None,
            "post_covid_avg":     round(float(np.mean(post_covid)), 4) if post_covid else None,
        })

    state_trends.sort(key=lambda x: x["current_rate"], reverse=True)

    # -----------------------------------------------------------------------
    # Population-weighted national average per year
    # -----------------------------------------------------------------------
    yearly_avgs = []
    for year in years:
        yr_recs = [r for r in all_records if r["year"] == year and not r["unreliable"]]
        if yr_recs:
            total_renters  = sum(r["total_renters"]      for r in yr_recs)
            total_burdened = sum(r["cost_burdened"]      for r in yr_recs)
            total_severe   = sum(r["severely_burdened"]  for r in yr_recs)
            yearly_avgs.append({
                "year":             year,
                "avg_burden_rate":  round(total_burdened / total_renters, 4),
                "avg_severe_rate":  round(total_severe   / total_renters, 4),
                "states_in_sample": len(yr_recs),
            })

    # -----------------------------------------------------------------------
    # Snapshot table: all states, latest year, sorted by burden rate
    # -----------------------------------------------------------------------
    latest_year = max(r["year"] for r in all_records)
    national_snapshot = [
        {
            "state":       t["state"],
            "fips":        t["fips"],
            "rate":        t["current_rate"],
            "severe_rate": t["current_severe"],
            "trend_dir":   "↓" if t["improving"] else ("↑" if t["trend_slope"] > 0.002 else "→"),
        }
        for t in state_trends
    ]

    top    = state_trends[0]
    bottom = state_trends[-1]
    nat    = yearly_avgs[-1]["avg_burden_rate"] if yearly_avgs else 0.0
    key_finding = (
        f"In {latest_year}, {top['state']} had the highest renter cost burden "
        f"({top['current_rate']*100:.1f}%) and {bottom['state']} the lowest "
        f"({bottom['current_rate']*100:.1f}%). National average: {nat*100:.1f}%."
    )

    log_fn(f"Complete. {key_finding}")

    return {
        "chart_type":          "housing_acs",
        "summary": {
            "states_analyzed":     len(state_trends),
            "years_covered":       f"{years[0]}–{years[-1]}",
            "total_records":       len(all_records),
            "data_source":         "U.S. Census Bureau ACS 1-Year Estimates, Table B25070",
            "key_finding":         key_finding,
        },
        "state_trends":        state_trends,
        "national_snapshot":   national_snapshot,
        "yearly_national_avg": yearly_avgs,
        "latest_year":         latest_year,
    }
