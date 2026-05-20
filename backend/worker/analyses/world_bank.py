"""
World Bank development & climate indicators analysis.
Uses the wbgapi package — no API key required.

Researchers choose which indicators to include; the analysis fetches
each one from the World Bank Open Data API and returns a time-series
per indicator suitable for charting.
"""

import time
from typing import Any, Callable, Dict, List, Optional

import numpy as np

try:
    import wbgapi as wb
    _WB_AVAILABLE = True
except ImportError:
    _WB_AVAILABLE = False


# ---------------------------------------------------------------------------
# Curated indicator catalog — verified against the WB API
# ---------------------------------------------------------------------------

AVAILABLE_INDICATORS: Dict[str, Dict[str, str]] = {
    # Economy
    "NY.GDP.PCAP.CD":    {"label": "GDP per capita",           "unit": "current USD",      "category": "Economy"},
    "NY.GDP.PCAP.KD.ZG": {"label": "GDP per capita growth",    "unit": "%/year",            "category": "Economy"},
    "FP.CPI.TOTL.ZG":   {"label": "Inflation rate",            "unit": "%",                 "category": "Economy"},
    "GC.DOD.TOTL.GD.ZS": {"label": "Government debt",          "unit": "% of GDP",          "category": "Economy"},
    "NE.TRD.GNFS.ZS":   {"label": "Trade openness",            "unit": "% of GDP",          "category": "Economy"},
    # Social
    "SI.POV.GINI":       {"label": "GINI inequality index",     "unit": "0–100",             "category": "Social"},
    "SL.UEM.TOTL.ZS":   {"label": "Unemployment rate",         "unit": "%",                 "category": "Social"},
    "SP.URB.TOTL.IN.ZS": {"label": "Urban population",         "unit": "% of total",        "category": "Social"},
    "SP.DYN.TFRT.IN":   {"label": "Fertility rate",            "unit": "births per woman",  "category": "Social"},
    # Health
    "SP.DYN.LE00.IN":   {"label": "Life expectancy",           "unit": "years",             "category": "Health"},
    "SH.DYN.MORT":      {"label": "Child mortality",           "unit": "per 1,000 births",  "category": "Health"},
    "SH.XPD.CHEX.GD.ZS": {"label": "Health expenditure",      "unit": "% of GDP",          "category": "Health"},
    # Education
    "SE.XPD.TOTL.GD.ZS": {"label": "Education expenditure",   "unit": "% of GDP",          "category": "Education"},
    "IT.NET.USER.ZS":   {"label": "Internet users",            "unit": "% of population",   "category": "Education"},
    # Energy & Climate
    "EG.USE.PCAP.KG.OE": {"label": "Energy use per capita",   "unit": "kg oil equivalent", "category": "Energy & Climate"},
    "EG.FEC.RNEW.ZS":   {"label": "Renewable energy share",   "unit": "% of consumption",  "category": "Energy & Climate"},
    "EG.ELC.ACCS.ZS":   {"label": "Electricity access",       "unit": "% of population",   "category": "Energy & Climate"},
    # Demographics
    "SP.POP.TOTL":      {"label": "Total population",          "unit": "people",            "category": "Demographics"},
}

DEFAULT_INDICATORS = [
    "NY.GDP.PCAP.CD",
    "SL.UEM.TOTL.ZS",
    "SP.DYN.LE00.IN",
    "EG.FEC.RNEW.ZS",
]

DEFAULT_COUNTRIES = ["USA", "CHN", "DEU", "GBR", "FRA", "JPN", "IND", "BRA"]

COUNTRY_NAMES = {
    "USA": "United States", "CHN": "China",        "DEU": "Germany",
    "GBR": "United Kingdom","FRA": "France",        "JPN": "Japan",
    "IND": "India",         "BRA": "Brazil",        "CAN": "Canada",
    "AUS": "Australia",     "KOR": "South Korea",   "MEX": "Mexico",
    "IDN": "Indonesia",     "SAU": "Saudi Arabia",  "ZAF": "South Africa",
    "NGA": "Nigeria",       "ARG": "Argentina",     "TUR": "Turkey",
    "SWE": "Sweden",        "NOR": "Norway",
}


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def run_world_bank_indicators(
    dataset_id: str,
    parameters: Dict[str, Any],
    log_fn: Callable,
    metric_fn: Callable,
) -> Dict[str, Any]:
    if not _WB_AVAILABLE:
        raise RuntimeError("wbgapi is not installed. Run: pip install wbgapi")

    countries: List[str] = parameters.get("countries", DEFAULT_COUNTRIES)
    year_start: int = int(parameters.get("year_start", 2000))
    year_end: int = int(parameters.get("year_end", 2022))
    requested: List[str] = parameters.get("indicators", DEFAULT_INDICATORS)

    # Only fetch indicators that exist in our catalog
    to_fetch = {code: AVAILABLE_INDICATORS[code] for code in requested if code in AVAILABLE_INDICATORS}

    log_fn(f"Fetching {len(to_fetch)} World Bank indicators for {len(countries)} countries ({year_start}–{year_end})")
    log_fn(f"Indicators: {', '.join(m['label'] for m in to_fetch.values())}")
    log_fn(f"Countries:  {', '.join(COUNTRY_NAMES.get(c, c) for c in countries)}")

    fetched: List[Dict[str, Any]] = []

    for code, meta in to_fetch.items():
        log_fn(f"  GET {code} — {meta['label']}…")
        df = _fetch_with_fallback(code, countries, year_start, year_end)
        if df is not None:
            series = _to_series(df, countries, year_start, year_end, code, meta)
            fetched.append(series)
            metric_fn(rows_processed=len(countries) * (year_end - year_start + 1))
            log_fn(f"      {len(series['data'])} data points")
        else:
            log_fn(f"      WARNING: no data returned — skipping")
        time.sleep(0.1)

    log_fn(f"Building summary across {len(fetched)} indicators…")

    # Latest snapshot per country across all fetched indicators
    snapshot = _latest_snapshot(fetched, countries, year_end)

    summary = _build_summary(fetched, countries, year_start, year_end, snapshot)

    log_fn(f"Complete — {sum(len(s['data']) for s in fetched)} total data points from World Bank API")

    return {
        "chart_type": "world_bank_indicators",
        "summary": summary,
        "indicators": fetched,       # [{code, label, unit, category, data: [{year, country, label, value}]}]
        "countries": countries,
        "country_names": {c: COUNTRY_NAMES.get(c, c) for c in countries},
        "latest_snapshot": snapshot,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_with_fallback(
    code: str,
    countries: List[str],
    year_start: int,
    year_end: int,
) -> Optional[Any]:
    """Try fetching, walking back end year up to 3 years if the API errors."""
    for end in (year_end, year_end - 1, year_end - 2):
        try:
            df = wb.data.DataFrame(code, countries, time=range(year_start, end + 1))
            return df
        except Exception:
            pass
    return None


def _to_series(df: Any, countries: List[str], year_start: int, year_end: int,
               code: str, meta: Dict[str, str]) -> Dict[str, Any]:
    """Convert a wbgapi DataFrame to a clean series dict."""
    data = []
    for iso in countries:
        if iso not in df.index:
            continue
        row = df.loc[iso]
        for year in range(year_start, year_end + 1):
            col = f"YR{year}"
            if col not in row.index:
                continue
            val = row[col]
            if val is None or (isinstance(val, float) and np.isnan(val)):
                continue
            data.append({
                "year": year,
                "country": iso,
                "label": COUNTRY_NAMES.get(iso, iso),
                "value": round(float(val), 3),
            })
    return {
        "code": code,
        "label": meta["label"],
        "unit": meta["unit"],
        "category": meta["category"],
        "data": data,
    }


def _latest_snapshot(fetched: List[Dict], countries: List[str], year_end: int) -> List[Dict]:
    """Best available value per country across all fetched indicators."""
    rows = []
    for iso in countries:
        row: Dict[str, Any] = {"country": iso, "name": COUNTRY_NAMES.get(iso, iso)}
        for series in fetched:
            # Most recent non-null value within 3 years of year_end
            candidates = [
                d for d in series["data"]
                if d["country"] == iso and d["year"] >= year_end - 3
            ]
            if candidates:
                best = max(candidates, key=lambda d: d["year"])
                row[series["code"]] = best["value"]
        rows.append(row)
    return rows


def _build_summary(
    fetched: List[Dict],
    countries: List[str],
    year_start: int,
    year_end: int,
    snapshot: List[Dict],
) -> Dict[str, Any]:
    findings = []
    for series in fetched:
        code = series["code"]
        vals = [(r["name"], r[code]) for r in snapshot if code in r]
        if not vals:
            continue
        top = max(vals, key=lambda x: x[1])
        bot = min(vals, key=lambda x: x[1])
        findings.append(
            f"{series['label']}: highest {top[0]} ({_fmt(top[1], series['unit'])}), "
            f"lowest {bot[0]} ({_fmt(bot[1], series['unit'])})"
        )

    return {
        "countries_analyzed": len(countries),
        "indicators_fetched": len(fetched),
        "years_covered": f"{year_start}–{year_end}",
        "total_data_points": sum(len(s["data"]) for s in fetched),
        "data_source": "World Bank Open Data API (live)",
        "key_findings": findings,
    }


def _fmt(value: float, unit: str) -> str:
    if "USD" in unit:
        return f"${value:,.0f}"
    if unit in ("%", "%/year", "% of GDP", "% of total", "% of population", "% of consumption"):
        return f"{value:.1f}%"
    if "people" in unit:
        if value > 1e9:
            return f"{value/1e9:.1f}B"
        if value > 1e6:
            return f"{value/1e6:.0f}M"
        return f"{value:,.0f}"
    return f"{value:.1f}"
