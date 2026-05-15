"""Housing affordability analysis using synthetic ACS-derived data."""

import time
from typing import Any, Callable, Dict, List

import numpy as np

US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

# Approximate real-world cost burden rates by state (% renters paying >30% income on housing)
_BASE_RATES: Dict[str, float] = {
    "CA": 0.54, "NY": 0.51, "FL": 0.50, "HI": 0.56, "MA": 0.48,
    "NJ": 0.47, "CT": 0.45, "MD": 0.44, "OR": 0.48, "WA": 0.46,
    "CO": 0.45, "NV": 0.47, "AZ": 0.44, "IL": 0.43, "RI": 0.46,
    "TX": 0.42, "GA": 0.43, "VA": 0.41, "NC": 0.40, "MI": 0.39,
    "MN": 0.38, "OH": 0.37, "PA": 0.38, "WI": 0.36, "TN": 0.38,
    "MO": 0.36, "IN": 0.35, "KY": 0.35, "AL": 0.36, "SC": 0.39,
    "ND": 0.29, "SD": 0.30, "WY": 0.31, "IA": 0.32, "NE": 0.33,
    "KS": 0.33, "MT": 0.34, "ID": 0.36, "AR": 0.37, "MS": 0.38,
}
_DEFAULT_RATE = 0.37


def run_housing_affordability(
    dataset_id: str,
    parameters: Dict[str, Any],
    log_fn: Callable,
    metric_fn: Callable,
) -> Dict[str, Any]:
    states: List[str] = parameters.get("states", US_STATES[:20])
    year_start: int = int(parameters.get("year_start", 2015))
    year_end: int = int(parameters.get("year_end", 2023))

    rng = np.random.default_rng(42)
    years = list(range(year_start, year_end + 1))

    log_fn(f"Loading ACS housing cost microdata for {len(states)} states ({year_start}–{year_end})")
    time.sleep(0.4)
    metric_fn(rows_processed=50_000)

    log_fn("Computing gross rent-to-income ratios by household...")
    time.sleep(0.3)
    metric_fn(rows_processed=200_000)

    # Per-state burden statistics
    burden_by_state = []
    for state in states:
        base = _BASE_RATES.get(state, _DEFAULT_RATE)
        noise = float(rng.normal(0, 0.015))
        rate = float(np.clip(base + noise, 0.15, 0.75))
        burden_by_state.append({
            "state": state,
            "cost_burden_rate": round(rate, 3),
            "severe_burden_rate": round(float(np.clip(rate * 0.46 + rng.normal(0, 0.01), 0.05, 0.40)), 3),
            "median_rent_pct_income": round(float(np.clip(rate * 95 + rng.normal(0, 2), 18, 72)), 1),
            "sample_size": int(rng.integers(1_500, 9_000)),
        })
    burden_by_state.sort(key=lambda x: x["cost_burden_rate"], reverse=True)

    log_fn("Computing year-over-year cost burden trend by income quintile...")
    time.sleep(0.5)
    metric_fn(rows_processed=500_000)

    # Quintile × year trend — lowest-income households are most burdened
    trend_by_quintile = []
    quintile_labels = ["Bottom 20%", "20–40%", "40–60%", "60–80%", "Top 20%"]
    quintile_bases = [0.72, 0.58, 0.40, 0.24, 0.10]
    for year in years:
        year_delta = (year - 2015) * 0.009
        for q_idx, (label, q_base) in enumerate(zip(quintile_labels, quintile_bases)):
            rate = q_base + year_delta + float(rng.normal(0, 0.008))
            trend_by_quintile.append({
                "year": year,
                "quintile": f"Q{q_idx + 1}",
                "label": label,
                "burden_rate": round(float(np.clip(rate, 0.04, 0.92)), 3),
            })

    # Severity distribution (for pie / donut chart)
    avg_rate = float(np.mean([s["cost_burden_rate"] for s in burden_by_state]))
    severity_distribution = [
        {"category": "Not burdened (<30%)", "value": round(1.0 - avg_rate, 3)},
        {"category": "Cost burdened (30–50%)", "value": round(avg_rate - avg_rate * 0.46, 3)},
        {"category": "Severely burdened (>50%)", "value": round(avg_rate * 0.46, 3)},
    ]

    log_fn("Aggregating summary statistics...")
    metric_fn(rows_processed=600_000)
    time.sleep(0.2)

    summary = {
        "total_states_analyzed": len(states),
        "years_covered": f"{year_start}–{year_end}",
        "avg_cost_burden_rate": round(avg_rate, 3),
        "avg_severe_burden_rate": round(avg_rate * 0.46, 3),
        "highest_burden_state": burden_by_state[0]["state"] if burden_by_state else "N/A",
        "highest_burden_rate": burden_by_state[0]["cost_burden_rate"] if burden_by_state else 0,
        "lowest_burden_state": burden_by_state[-1]["state"] if burden_by_state else "N/A",
        "lowest_burden_rate": burden_by_state[-1]["cost_burden_rate"] if burden_by_state else 0,
        "pct_states_above_40pct": round(
            len([s for s in burden_by_state if s["cost_burden_rate"] > 0.40]) / len(burden_by_state) * 100
            if burden_by_state else 0, 1
        ),
        "trend_direction": "increasing" if year_end > year_start else "stable",
        "key_finding": (
            f"On average, {round(avg_rate * 100, 1)}% of renter households in the selected states "
            f"spend more than 30% of income on housing costs. "
            f"{burden_by_state[0]['state'] if burden_by_state else 'N/A'} has the highest burden rate "
            f"({round(burden_by_state[0]['cost_burden_rate'] * 100, 1) if burden_by_state else 0}%)."
        ),
    }

    log_fn(
        f"Complete — avg burden {summary['avg_cost_burden_rate']:.1%}, "
        f"highest: {summary['highest_burden_state']} "
        f"({summary['highest_burden_rate']:.1%})"
    )

    return {
        "chart_type": "housing_affordability",
        "summary": summary,
        "burden_by_state": burden_by_state,
        "trend_by_quintile": trend_by_quintile,
        "severity_distribution": severity_distribution,
    }
